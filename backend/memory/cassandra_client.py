from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from datetime import datetime
from loguru import logger

class Memory:
    def __init__(self, keyspace="agent_data", table="agent_memory", hosts=["127.0.0.1"]):
        self.cluster = Cluster(hosts)
        self.session = self.cluster.connect()
        self.keyspace = keyspace
        self.table = table

        try:
            self.session.set_keyspace(self.keyspace)
        except Exception as e:
            logger.error(f"Ошибка установки keyspace: {e}")
            raise

    def store(self, agent_id: str, observation: str, plan: str, result: str):
        now = datetime.utcnow()
        try:
            query = SimpleStatement(f"""
                INSERT INTO {self.table} (agent_id, timestamp, observation, plan, result)
                VALUES (%s, %s, %s, %s, %s)
            """)
            self.session.execute(query, (agent_id, now, observation, plan, result))
            logger.debug("Память обновлена.")
        except Exception as e:
            logger.error(f"Ошибка записи в Cassandra: {e}")

    def recent(self, agent_id: str, limit: int = 5):
        try:
            rows = self.session.execute(f"""
                SELECT timestamp, observation, plan, result
                FROM {self.table}
                WHERE agent_id = %s
                LIMIT %s
            """, (agent_id, limit))
            return list(rows)
        except Exception as e:
            logger.error(f"Ошибка выборки из Cassandra: {e}")
            return []

