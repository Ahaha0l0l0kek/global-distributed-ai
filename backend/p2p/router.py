from loguru import logger
from memory.cassandra_client import Memory
from datetime import datetime

memory = Memory()  # можно заменить DI-подключением

class Router:
    def __init__(self, agent_id="agent_001"):
        self.agent_id = agent_id

    async def route(self, message: dict) -> dict:
        msg_type = message.get("type")

        if msg_type == "ping":
            return {"type": "pong", "from": self.agent_id}

        elif msg_type == "memory_share":
            return self._handle_memory_share(message)

        elif msg_type == "task":
            return self._handle_task(message)

        elif msg_type == "weights":
            return {"status": "not_implemented"}

        else:
            logger.warning(f"Неизвестный тип сообщения: {msg_type}")
            return {"error": "unknown message type"}

    def _handle_memory_share(self, message: dict) -> dict:
        """Принимаем кусок чужой памяти"""
        try:
            entry = message["entry"]
            memory.store(
                agent_id=f"{self.agent_id}_foreign",
                observation=entry["observation"],
                plan=entry["plan"],
                result=entry["result"]
            )
            return {"status": "ok", "stored": True}
        except Exception as e:
            return {"status": "error", "details": str(e)}

    def _handle_task(self, message: dict) -> dict:
        """В будущем: выполнение заданной задачи"""
        return {"status": "todo", "details": "task execution not implemented"}