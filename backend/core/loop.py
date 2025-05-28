import asyncio
import time
from memory.cassandra_client import Memory
from llm.runtime import LLM
from observation.web_scraper import scrape_page
from loguru import logger
from p2p.node import P2PNode
from core.task_manager import TaskManager

AGENT_ID = "agent_001"
SCRAPE_URL = "https://news.ycombinator.com"
PEERS = [("127.0.0.1", 9009)]  # соседи вручную (или динамически в будущем)

class AgentCore:
    def __init__(self):
        logger.info("🧠 Инициализация AgentCore...")
        self.memory = Memory()
        self.llm = LLM()
        self.p2p = P2PNode(agent_id=AGENT_ID, port=9009)

        self.task_queue = asyncio.Queue()
        self.p2p.router.set_task_handler(self.enqueue_task)

        self.task_manager = TaskManager()

    async def observe(self) -> str:
        html = scrape_page(SCRAPE_URL)
        logger.info("🧿 OBSERVE: HTML загружен.")
        return html

    def plan(self, observation: str) -> str:
        prompt = f"""
Ты — ИИ-агент, анализирующий сайт.
<<<
{observation}
>>>
Сформулируй, что нужно сделать (1 строка).
"""
        return self.llm.generate(prompt, max_tokens=64)

    def act(self, plan: str) -> str:
        logger.info(f"🤖 ACT: {plan}")
        return f"Действие выполнено: {plan}"

    def learn(self, obs: str, plan: str, result: str):
        self.memory.store(AGENT_ID, obs, plan, result)

    def recent_entries(self, limit=3):
        return self.memory.recent(AGENT_ID, limit=limit)

    async def share_memory(self):
        entries = self.recent_entries(limit=1)
        if not entries:
            return

        for host, port in PEERS:
            try:
                await self.p2p.send(
                    host, port,
                    {
                        "type": "memory_share",
                        "entry": {
                            "observation": entries[0].observation[:300],
                            "plan": entries[0].plan,
                            "result": entries[0].result,
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"❌ Не удалось отправить память {host}:{port}: {e}")

    async def enqueue_task(self, task_str, reply_to=None, task_id=None):
    if not task_id:
        entry = self.task_manager.create(task_str, reply_to)
        task_id = entry["id"]
    await self.task_queue.put((task_id, task_str, reply_to))

    async def run_task_worker(self):
        while True:
            task_id, task_str, reply_to = await self.task_queue.get()
            logger.info(f"📥 Выполняем задачу {task_id}: {task_str}")
            self.task_manager.mark_running(task_id)

            result = "Задача не выполнена."

            try:
                if task_str.startswith("observe "):
                    url = task_str[len("observe "):].strip()
                    observation = scrape_page(url)
                    plan = self.plan(observation)
                    result = self.act(plan)
                    self.learn(observation, plan, result)
                    self.task_manager.mark_done(task_id, result)
                    logger.info(f"✅ Задача {task_id} выполнена.")
                else:
                    raise ValueError("Неизвестный формат задачи")
            except Exception as e:
                result = f"❌ Ошибка: {e}"
                self.task_manager.mark_failed(task_id, result)

            if reply_to:
                host, port = reply_to
                await self.p2p.send(host, port, {
                    "type": "task_result",
                    "task_id": task_id,
                    "task": task_str,
                    "result": result,
                    "from": self.agent_id,
                    "to": f"{host}:{port}"
                })

    async def loop(self):
        logger.info("🚀 AgentCore запущен.")
        asyncio.create_task(self.p2p.start_server())
        asyncio.create_task(self.run_task_worker())

        while True:
            try:
                obs = await self.observe()
                plan = self.plan(obs)
                result = self.act(plan)
                self.learn(obs, plan, result)
                await self.share_memory()
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"🔥 Ошибка в цикле: {e}")
                await asyncio.sleep(10)

    def run_agent():
        agent = AgentCore()
        asyncio.run(agent.loop())

    if __name__ == "__main__":
        run_agent()
