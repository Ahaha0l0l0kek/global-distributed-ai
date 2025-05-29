from llama_cpp import Llama

class LLM:
    def __init__(self, model_path="./model/phi-2.gguf", n_ctx=1024):
        self.model = Llama(model_path=model_path, n_ctx=n_ctx)

    def generate(self, prompt: str, max_tokens: int = 128) -> str:
        output = self.model(
            prompt=prompt,
            max_tokens=max_tokens,
            stop=["\n"]
        )
        return output["choices"][0]["text"].strip()
    
    def load_model(dna):
        model_id = dna.get("model_base", "phi-2.gguf")
        lora_path = dna.get("lora_path")
        lora_id = self.dna.get("lora_path")

        model = LLM(model_id)

        if lora_id:
            lora_file = await self.ensure_lora_available(lora_id)
            if lora_file:
                model.load_lora(lora_file)

        if lora_path and os.path.exists(lora_path):
            model.load_lora(lora_path)
            logger.info(f"🧬 LoRA адаптация подключена: {lora_path}")
        else:
            logger.info("🧬 Используем базовую модель")

        return model
    
    async def ensure_lora_available(self, lora_id):
        local_path = Path.home() / ".gda" / "lora" / f"{lora_id}.safetensors"
        if local_path.exists():
            return str(local_path)

        logger.info(f"📡 Запрашиваем LoRA: {lora_id}")
        for host, port in self.p2p.peers:
            chunks = []
            chunk = 0
            while True:
                try:
                    resp = await self.p2p.send(host, port, {
                        "type": "lora_request",
                        "lora_id": lora_id,
                        "chunk": chunk
                    })
                    data = base64.b64decode(resp["data"])
                    chunks.append(data)
                    if len(data) < CHUNK_SIZE:
                        break
                    chunk += 1
                except Exception as e:
                    logger.warning(f"❌ Ошибка получения LoRA: {e}")
                    break

            if chunks:
                local_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path, "wb") as f:
                    for c in chunks:
                        f.write(c)
                return str(local_path)
        return None
    
def load_lora_from_file(model, lora_path: str):
    import torch
    from peft import inject_adapter_in_model

    state_dict = torch.load(lora_path, map_location="cpu")
    inject_adapter_in_model(model, state_dict)

