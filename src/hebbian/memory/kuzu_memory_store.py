import kuzu
from pathlib import Path
from datetime import datetime, timezone
from hebbian.memory.memory_store import MemoryStore

class KuzuMemoryStore(MemoryStore):
    def __init__(self, db_path="./data/hebb_db", read_only=False):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
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

    def add_memory(self, content, context_name, embedding, last_seen):
        self.conn.execute("""
            MERGE (m:Memory {content: $content})
            ON MATCH SET m.last_seen = $last_seen
            ON CREATE SET m.weight = 1, m.last_seen = $last_seen, m.embedding = $embedding
        """, {"content": content, "embedding": embedding, "last_seen": last_seen})
        self.associate_context(content, context_name)

    def associate_context(self, content, context_name):
        self.conn.execute("MERGE (c:Context {name: $name})", {"name": context_name})
        self.conn.execute("""
            MATCH (m:Memory), (c:Context) WHERE m.content = $content AND c.name = $name
            MERGE (m)-[r:ASSOCIATED_WITH]->(c)
        """, {"content": content, "name": context_name})

    def increment_weight(self, content, context_name, last_seen):
        self.conn.execute("""
            MATCH (m:Memory), (c:Context) WHERE m.content = $content AND c.name = $name
            SET m.weight = m.weight + 1, m.last_seen = $last_seen
        """, {"content": content, "name": context_name, "last_seen": last_seen})

    def recall_memories(self, context_name, limit, ttl):
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
            if ttl and last_seen:
                try:
                    dt = last_seen
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    age = (now - dt).total_seconds()
                    if age > int(ttl):
                        expired_contents.add(content)
                        continue
                except Exception:
                    pass
            memories.append({"content": content, "weight": weight, "is_context": is_context, "embedding": embedding})
        if expired_contents:
            for content in expired_contents:
                self.delete_memory(content)
        return memories

    def delete_memory(self, content):
        self.conn.execute("MATCH (m:Memory {content: $content}) DETACH DELETE m", {"content": content})

    def clear_all(self):
        self.conn.execute("MATCH (m:Memory) DETACH DELETE m")
        self.conn.execute("MATCH (c:Context) DETACH DELETE c")
    
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
