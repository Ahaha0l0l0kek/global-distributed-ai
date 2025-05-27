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
