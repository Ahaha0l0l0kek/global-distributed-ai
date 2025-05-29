import asyncio
import time
from memory.cassandra_client import Memory
from llm.runtime import LLM
from observation.web_scraper import scrape_page
from loguru import logger
from p2p.node import P2PNode
from core.task_manager import TaskManager
from agent.dna import ensure_dna_exists
from agent.dna import hybridize_dna, save_dna
import base64


AGENT_ID = "agent_001"
SCRAPE_URL = "https://news.ycombinator.com"
PEERS = [("127.0.0.1", 9009)]  # соседи вручную (или динамически в будущем)
CHUNK_SIZE = 1024 * 1024

class AgentCore:
    def __init__(self):
        logger.info("🧠 Инициализация AgentCore...")
        self.memory = Memory()
        self.llm = LLM()
        self.p2p = P2PNode(agent_id=AGENT_ID, port=9009)

        self.task_queue = asyncio.Queue()
        self.p2p.router.set_task_handler(self.enqueue_task)

        self.task_manager = TaskManager()

        self.dna = ensure_dna_exists()
        logger.info(f"🧬 DNA {self.dna['id']} загружена")

        self.task_stats = {
            "completed": 0,
            "failed": 0,
            "last_mutation": time.time()
        }

    async def observe(self) -> str:
        if random.random() > self.dna["weights"].get("observe", 1.0):
            logger.info("🕶 DNA решила пропустить наблюдение")
            return

        url = random.choice(self.sources)
        depth = self.dna["weights"].get("scrape_depth", 1)

        logger.info(f"🌐 [DNA] Наблюдаем: {url} (глубина: {depth})")
        content = await self.scrape(url, depth=depth)
        self.memory.save_observation(url, content)

    def plan(self, observation: str) -> str:
        prompt = self.dna.get("prompt_template", "")
        temperature = self.dna.get("temperature", 0.7)
        top_p = self.dna.get("top_p", 0.95)

        input_text = f"{prompt}\n\nНаблюдение:\n{observation}\n\nТвои действия?"
        return self.model.generate(input_text, temperature=temperature, top_p=top_p)

    def act(self, plan: str) -> str:
        activeness = self.dna["weights"].get("activeness", 0.5)
        if random.random() > activeness:
            logger.info("🤖 [DNA] Пропускаем действие")
            return
        logger.info(f"⚙️ Выполняем: {plan}")

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

    async def retry_stuck_tasks(self):
        while True:
            stuck = self.memory.get_expired_tasks(older_than_sec=60)
            for row in stuck:
                logger.warning(f"🔁 RETRY: Задача {row.task_id} подвисла, пробуем заново.")
                await self.task_queue.put((
                    row.task_id,
                    row.task,
                    (row.reply_host, row.reply_port) if row.reply_host else None
                ))
                self.memory.bump_retry(row.task_id)

            await asyncio.sleep(60)

    async def watch_and_mutate_dna(self):
        while True:
            await asyncio.sleep(300)  # каждые 5 минут
            score = self.task_manager.get_reward_score()
            if score < 0.2 and (time.time() - self.task_manager.stats["last_mutation"] > 300):
                logger.warning(f"🧬 Эффективность {score:.2f} — мутация DNA")
                from agent.dna import mutate_dna
                self.dna = mutate_dna(self.dna)
                self.task_manager.stats["last_mutation"] = time.time()
                self.task_manager.stats["completed"] = 0
                self.task_manager.stats["failed"] = 0
            if score > 0.8:
                await self.broadcast_dna()
            elif score < 0.2:
                logger.info("📡 Запрашиваем DNA от соседей (низкая эффективность)")
                await self.request_dna_from_peers()
                logger.warning("📉 Эффективность по-прежнему низкая после P2P обмена")
                lora_id = self.dna.get("lora_path")
                last_lora_time = self.task_manager.stats.get("last_lora_finetune", 0)

                if not lora_id or (time.time() - last_lora_time > 3600):
                    memory_size = self.memory.size()
                    if memory_size > 100:
                        logger.info(f"🧬 Запускаем автообучение LoRA ({memory_size} записей памяти)")
                        await self.finetune_lora_from_memory()
                        self.task_manager.stats["last_lora_finetune"] = time.time()
                    else:
                        logger.info("🧠 Недостаточно памяти для обучения LoRA")


    def handle_dna_offer(self, incoming_dna: dict):
        local_score = self.task_manager.get_reward_score()
        remote_score = incoming_dna.get("reward_score", 1.0)

        logger.info(f"🧬 Получена внешняя DNA {incoming_dna.get('id')} (эфф. {remote_score:.2f})")

        if remote_score > local_score:
            from agent.dna import hybridize_dna, save_dna
            hybrid = hybridize_dna(self.dna, incoming_dna)
            save_dna(hybrid)
            self.dna = hybrid
            logger.warning(f"🧬 DNA гибридизирована с внешней: {self.dna['id']}")
            return {"status": "hybridized", "new_dna_id": self.dna["id"]}
        else:
            return {"status": "rejected", "reason": "lower score"}
        
    async def request_dna_from_peers(self):
        best_dna = None
        best_score = -1.0

        for host, port in self.p2p.peers:
            try:
                resp = await self.p2p.send(host, port, {
                    "type": "dna_request"
                })
                incoming = resp.get("dna")
                remote_score = incoming.get("reward_score", 1.0)

                if remote_score > best_score:
                    best_score = remote_score
                    best_dna = incoming

            except Exception as e:
                logger.warning(f"❌ Не удалось получить DNA от {host}:{port}: {e}")

        if best_dna and best_score > self.task_manager.get_reward_score():
            logger.info(f"🧬 Гибридизируемся с DNA {best_dna.get('id')} (эфф. {best_score:.2f})")
            hybrid = hybridize_dna(self.dna, best_dna)
            save_dna(hybrid)
            self.dna = hybrid
            return True

        logger.info("🧬 Не найдено лучшей DNA среди соседей")
        return False
    

    def handle_lora_request(self, lora_id: str, chunk: int):
        path = Path.home() / ".gda" / "lora" / f"{lora_id}.safetensors"
        if not path.exists():
            return {"error": "no such lora"}

        with open(path, "rb") as f:
            f.seek(chunk * CHUNK_SIZE)
            data = f.read(CHUNK_SIZE)

        return {
            "type": "lora_chunk",
            "lora_id": lora_id,
            "chunk": chunk,
            "data": base64.b64encode(data).decode()
        }
    
    async def finetune_lora_from_memory(self):
        logger.info("🧬 Запускаем обучение LoRA на собственной памяти")
        from agent.lora_trainer import memory_to_dataset, train_lora

        memory = self.memory.load_all()[:500]  # ограничим размер
        dataset = memory_to_dataset(memory)
        lora_id = f"lora_{uuid.uuid4().hex[:6]}"
        save_path = Path.home() / ".gda" / "lora"
        save_path.mkdir(parents=True, exist_ok=True)

        cfg = self.dna.get("lora_config", {})
        result_path = train_lora(dataset, base_model_id, lora_id, save_path, cfg)

        logger.info(f"✅ Новая LoRA обучена: {result_path}")
        self.dna["lora_path"] = lora_id
        save_dna(self.dna)


    async def loop(self):
        logger.info("🚀 AgentCore запущен.")
        asyncio.create_task(self.p2p.start_server())
        asyncio.create_task(self.run_task_worker())
        asyncio.create_task(self.retry_stuck_tasks())

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

    async def broadcast_dna(self):
        dna_with_score = dict(self.dna)
        dna_with_score["reward_score"] = self.task_manager.get_reward_score()

        for host, port in self.p2p.peers:
            try:
                resp = await self.p2p.send(host, port, {
                    "type": "dna_offer",
                    "dna": dna_with_score
                })
                logger.info(f"📤 DNA отправлена {host}:{port} → {resp.get('status')}")
            except Exception as e:
                logger.warning(f"❌ Ошибка DNA broadcast: {e}")
