from loguru import logger
from memory.cassandra_client import Memory
from datetime import datetime

memory = Memory()  # можно заменить DI-подключением

class Router:
    def __init__(self, agent_id="agent_001"):
        self.agent_id = agent_id
        self.task_handler = None

    async def route(self, message: dict) -> dict:
        msg_type = message.get("type")

        if msg_type == "ping":
            return {"type": "pong", "from": self.agent_id}

        elif msg_type == "memory_share":
            return self._handle_memory_share(message)

        elif msg_type == "task":
            return self._handle_task(message)
        
        elif msg_type == "task_result":
            task_id = message.get("task_id")
            task = message.get("task")
            result = message.get("result")
            logger.info(f"📩 Результат задачи {task_id}:\n🔸 {task}\n✅ {result}")
            return {"status": "received", "task_id": task_id}

        elif msg_type == "weights":
            return self.handle_weights(self.agent_id)

        else:
            logger.warning(f"Неизвестный тип сообщения: {msg_type}")
            return {"error": "unknown message type"}

    def handle_memory_share(self, message: dict) -> dict:
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

    def set_task_handler(self, handler):
        self.task_handler = handler

    async def _handle_task(self, message: dict) -> dict:
        try:
            task = message.get("task")
            reply_to = message.get("reply_to")

            if not task:
                return {"error": "No task provided"}

            logger.info(f"📥 Принята задача: {task}")

            if self.task_handler:
                await self.task_handler(task, reply_to)
            else:
                memory.store(
                    agent_id=f"{self.agent_id}_task",
                    observation=f"TASK: {task}",
                    plan="Handler not set",
                    result="Not executed"
                )
                return {"status": "saved", "note": "handler not set"}

            return {"status": "accepted", "task": task}
        except Exception as e:
            return {"error": str(e)}

    def handle_weights(self, message: dict) -> dict:
        return {"todo"}