from sentence_transformers import SentenceTransformer
import numpy as np
import kuzu
from pathlib import Path

class HebbianBrain:
    def __init__(self, db_path="./data/hebb_db", read_only=False):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Kuzu 0.7.1 single-file mode
        if read_only:
            self.db = kuzu.Database(db_path, read_only=True)
        else:
            self.db = kuzu.Database(db_path)
            
        self.conn = kuzu.Connection(self.db)
        if not read_only:
            self._init_schema()

    def _init_schema(self):
        try:
            self.conn.execute("CREATE NODE TABLE Memory(content STRING, weight INT64, last_seen TIMESTAMP, embedding STRING, PRIMARY KEY (content))")
            self.conn.execute("CREATE NODE TABLE Context(name STRING, PRIMARY KEY (name))")
            self.conn.execute("CREATE REL TABLE ASSOCIATED_WITH(FROM Memory TO Context)")
        except:
            pass

    def strengthen(self, content, context_name):
        # Compute embedding for the content
        embedding = self.model.encode(content)
        embedding_str = ','.join(map(lambda x: f"{x:.4f}", embedding.tolist()))
        # Only create or update last_seen, do NOT increment weight
        self.conn.execute("""
            MERGE (m:Memory {content: $content})
            ON MATCH SET m.last_seen = current_timestamp()
            ON CREATE SET m.weight = 1, m.last_seen = current_timestamp(), m.embedding = $embedding
        """, {"content": content, "embedding": embedding_str})
        self.conn.execute("MERGE (c:Context {name: $name})", {"name": context_name})
        self.conn.execute("""
            MATCH (m:Memory), (c:Context) WHERE m.content = $content AND c.name = $name
            MERGE (m)-[r:ASSOCIATED_WITH]->(c)
        """, {"content": content, "name": context_name})

    def increment_weight(self, content, context_name):
        # Increment weight only when pasted
        self.conn.execute("""
            MATCH (m:Memory), (c:Context) WHERE m.content = $content AND c.name = $name
            SET m.weight = m.weight + 1, m.last_seen = current_timestamp()
        """, {"content": content, "name": context_name})

    def recall_smart(self, context_name, limit=15):
        """Prioritizes current context, then weight/recency."""
        query = """
        MATCH (m:Memory)-[:ASSOCIATED_WITH]->(c:Context)
        WITH m, c, (c.name = $ctx) as is_context
        RETURN m.content, m.weight, is_context, m.embedding
        ORDER BY is_context DESC, m.weight DESC, m.last_seen DESC
        LIMIT $limit
        """
        res = self.conn.execute(query, {"ctx": context_name, "limit": limit})
        memories = []
        while res.has_next():
            row = res.get_next()
            memories.append({"content": row[0], "weight": row[1], "is_context": row[2], "embedding": row[3]})
        return memories

    def get_full_graph_summary(self):
        query = """
        MATCH (m:Memory)-[:ASSOCIATED_WITH]->(c:Context)
        RETURN c.name, m.content, m.weight
        ORDER BY c.name, m.last_seen DESC
        """
        res = self.conn.execute(query)
        data = {}
        while res.has_next():
            row = res.get_next()
            ctx = row[0]
            if ctx not in data: data[ctx] = []
            data[ctx].append({"content": row[1], "weight": row[2]})
        return data

    def search_globally(self, search_term, limit=10):
        query = """
        MATCH (m:Memory)-[:ASSOCIATED_WITH]->(c:Context)
        WHERE m.content CONTAINS $term
        RETURN c.name, m.content, m.weight
        ORDER BY m.weight DESC, m.last_seen DESC
        LIMIT $limit
        """
        res = self.conn.execute(query, {"term": search_term, "limit": limit})
        results = []
        while res.has_next():
            row = res.get_next()
            results.append((row[0], row[1], row[2]))
        return results

    def clear_all_memories(self):
        self.conn.execute("MATCH (m:Memory) DETACH DELETE m")
        self.conn.execute("MATCH (c:Context) DETACH DELETE c")
