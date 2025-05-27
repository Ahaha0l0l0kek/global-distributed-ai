import time
from memory.cassandra_client import Memory
from llm.runtime import LLM
from observation.web_scraper import scrape_page
from loguru import logger

AGENT_ID = "agent_001"
SCRAPE_URL = "https://news.ycombinator.com/"  # можно позже сделать динамическим

class AgentCore:
    def __init__(self):
        logger.info("Инициализация ядра агента...")
        self.memory = Memory()
        self.llm = LLM()

    def observe(self) -> str:
        """Сканируем внешнюю среду"""
        html = scrape_page(SCRAPE_URL)
        logger.info("🧿 OBSERVE: Получен HTML.")
        return html

    def plan(self, observation: str) -> str:
        """LLM вырабатывает намерение или гипотезу"""
        prompt = f"""
Ты — автономный ИИ-агент, сканирующий интернет.
Вот выдержка из страницы (обрезанная):
<<<
{observation}
>>>
На основе содержимого, что ты считаешь важным сделать? Ответь чётким действием, одной строкой.
"""
        plan = self.llm.generate(prompt, max_tokens=64)
        logger.info(f"🧠 PLAN: {plan}")
        return plan

    def act(self, plan: str) -> str:
        """Исполнение плана — пока только фиксация в логах"""
        logger.info(f"🤖 ACT: {plan}")
        # В будущем — действия: API, навигация, обучение
        return f"Действие выполнено: {plan}"

    def learn(self, obs: str, plan: str, result: str):
        """Запись в память"""
        self.memory.store(AGENT_ID, obs, plan, result)
        logger.info("🧬 LEARN: Состояние записано.")

    def print_recent_memory(self):
        recent = self.memory.recent(AGENT_ID)
        if recent:
            logger.info("🧠 Последние записи памяти:")
            for row in recent:
                logger.info(f"[{row.timestamp}] План: {row.plan} → Результат: {row.result}")

    def run(self):
        logger.info("🚀 Агент запущен.")
        while True:
            try:
                obs = self.observe()
                plan = self.plan(obs)
                result = self.act(plan)
                self.learn(obs, plan, result)
                self.print_recent_memory()
                time.sleep(30)
            except Exception as e:
                logger.error(f"🔥 Ошибка в цикле: {e}")
                time.sleep(10)

if __name__ == "__main__":
    agent = AgentCore()
    agent.run()
