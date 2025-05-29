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
        
    def store_task(self, task_id, agent_id, task_str, reply_to):
        now = datetime.utcnow()
        host, port = reply_to if reply_to else (None, None)
        self.session.execute(f"""
            INSERT INTO agent_tasks (task_id, agent_id, task, reply_host, reply_port, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (task_id, agent_id, task_str, host, port, "pending", now, now))

    def update_task_status(self, task_id, status, result=None):
        now = datetime.utcnow()
        self.session.execute(f"""
            UPDATE agent_tasks
            SET status = %s, result = %s, updated_at = %s
            WHERE task_id = %s
        """, (status, result, now, task_id))

    def get_all_tasks(self, limit=50):
        query = f"SELECT * FROM agent_tasks LIMIT %s"
        return self.session.execute(query, (limit,))

    def get_task_by_id(self, task_id: str):
        query = f"SELECT * FROM agent_tasks WHERE task_id = %s"
        rows = self.session.execute(query, (task_id,))
        return rows.one()
    
    def get_expired_tasks(self, older_than_sec=60):
        import datetime
        from datetime import timedelta

        threshold = datetime.datetime.utcnow() - timedelta(seconds=older_than_sec)
        query = f"""
            SELECT * FROM agent_tasks
            WHERE status IN ('pending', 'running') ALLOW FILTERING
        """
        rows = self.session.execute(query)
        return [r for r in rows if r.updated_at < threshold]

    def bump_retry(self, task_id):
        self.session.execute(f"""
            UPDATE agent_tasks
            SET retry_count = coalesce(retry_count, 0) + 1, updated_at = toTimestamp(now())
            WHERE task_id = %s
        """, (task_id,))


