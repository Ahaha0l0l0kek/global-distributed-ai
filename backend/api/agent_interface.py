from memory.cassandra_client import Memory
from observation.web_scraper import scrape_page
from llm.runtime import LLM
from api.models import AgentMemoryEntry
from datetime import datetime

AGENT_ID = "agent_001"

class AgentAPI:
    def __init__(self):
        self.memory = Memory()
        self.llm = LLM()

    def process_url(self, url: str) -> AgentMemoryEntry:
        observation = scrape_page(url)
        prompt = f"""
Ты — ИИ-агент. Вот текст страницы:
<<<
{observation}
>>>
Что ты сделаешь дальше? Кратко."""
        plan = self.llm.generate(prompt)
        result = f"План принят: {plan}"
        self.memory.store(AGENT_ID, observation, plan, result)
        return AgentMemoryEntry(
            timestamp=datetime.utcnow(),
            observation=observation[:200],
            plan=plan,
            result=result
        )

    def recent_memory(self, limit=5) -> list[AgentMemoryEntry]:
        rows = self.memory.recent(AGENT_ID, limit=limit)
        return [AgentMemoryEntry(**row._asdict()) for row in rows]