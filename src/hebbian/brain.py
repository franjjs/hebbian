from sentence_transformers import SentenceTransformer
import numpy as np
import kuzu
from pathlib import Path

class HebbianBrain:
    def __init__(self, db_path="./data/hebb_db", read_only=False):
        self.model = None
        if not read_only:
            from sentence_transformers import SentenceTransformer
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
        from datetime import datetime, timezone
        # Compute embedding for the content (only if model is loaded)
        embedding_str = ''
        if self.model:
            embedding = self.model.encode(content)
            embedding_str = ','.join(map(lambda x: f"{x:.4f}", embedding.tolist()))
        # Store last_seen as Python datetime for TIMESTAMP
        now_utc = datetime.now(timezone.utc)
        self.conn.execute("""
            MERGE (m:Memory {content: $content})
            ON MATCH SET m.last_seen = $now_utc
            ON CREATE SET m.weight = 1, m.last_seen = $now_utc, m.embedding = $embedding
        """, {"content": content, "embedding": embedding_str, "now_utc": now_utc})
        self.conn.execute("MERGE (c:Context {name: $name})", {"name": context_name})
        self.conn.execute("""
            MATCH (m:Memory), (c:Context) WHERE m.content = $content AND c.name = $name
            MERGE (m)-[r:ASSOCIATED_WITH]->(c)
        """, {"content": content, "name": context_name})

    def increment_weight(self, content, context_name):
        from datetime import datetime, timezone
        now_utc = datetime.now(timezone.utc)
        self.conn.execute("""
            MATCH (m:Memory), (c:Context) WHERE m.content = $content AND c.name = $name
            SET m.weight = m.weight + 1, m.last_seen = $now_utc
        """, {"content": content, "name": context_name, "now_utc": now_utc})

    def recall_smart(self, context_name, limit=15, ttl=None):
        """Prioritizes current context, then weight/recency. Purges memories older than ttl (seconds) in Python using ISO UTC."""
        from datetime import datetime, timezone
        # Get TTL from config if not provided
        if ttl is None:
            try:
                from hebbian.config import load_config
                config = load_config()
                ttl = config.get('settings', {}).get('ttl', None)
            except Exception:
                ttl = None
        query = """
        MATCH (m:Memory)-[:ASSOCIATED_WITH]->(c:Context)
        WITH m, c, (c.name = $ctx) as is_context
        RETURN m.content, m.weight, is_context, m.embedding, m.last_seen
        ORDER BY is_context DESC, m.weight DESC, m.last_seen DESC
        LIMIT $limit
        """
        res = self.conn.execute(query, {"ctx": context_name, "limit": limit})
        now = datetime.now(timezone.utc)
        memories = []
        expired_contents = set()
        while res.has_next():
            row = res.get_next()
            content, weight, is_context, embedding, last_seen = row
            # last_seen is Python datetime (TIMESTAMP from KùzuDB)
            if ttl and last_seen:
                try:
                    dt = last_seen
                    # Ensure both are timezone-aware UTC
                    if dt.tzinfo is None:
                        from datetime import timezone
                        dt = dt.replace(tzinfo=timezone.utc)
                    age = (now - dt).total_seconds()
                    if age > int(ttl):
                        expired_contents.add(content)
                        continue
                except Exception:
                    pass
            memories.append({"content": content, "weight": weight, "is_context": is_context, "embedding": embedding})
        # Optionally, delete expired from DB
        if expired_contents:
            for content in expired_contents:
                self.conn.execute("MATCH (m:Memory {content: $content}) DETACH DELETE m", {"content": content})
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
