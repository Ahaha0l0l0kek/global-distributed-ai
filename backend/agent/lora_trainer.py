from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import get_peft_model, LoraConfig, TaskType
import torch

cfg = config or {}
r = cfg.get("r", 8)
alpha = cfg.get("alpha", 16)
dropout = cfg.get("dropout", 0.05)
epochs = cfg.get("epochs", 2)
target = cfg.get("target_modules", ["query_key_value"])

LoraConfig(
    r=r,
    lora_alpha=alpha,
    lora_dropout=dropout,
    target_modules=target,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

def memory_to_dataset(memory_entries):
    pairs = []
    for entry in memory_entries:
        obs = entry.get("observation")
        plan = entry.get("plan")
        if obs and plan:
            input_text = f"Ты наблюдаешь:\n{obs}\n\nЧто делать?"
            pairs.append({"instruction": input_text, "output": plan})
    return Dataset.from_list(pairs)

def train_lora(dataset, base_model_id, lora_id, save_path, config: dict):    model = AutoModelForCausalLM.from_pretrained(base_model_id, load_in_8bit=True, device_map="auto")
    tokenizer = AutoTokenizer.from_pretrained(base_model_id)

    config = LoraConfig(
        r=8, lora_alpha=16, target_modules=["query_key_value"],
        lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM
    )

    model = get_peft_model(model, config)

    def tokenize(sample):
        full_text = sample["instruction"] + "\n\n" + sample["output"]
        return tokenizer(full_text, truncation=True, padding="max_length", max_length=512)

    tokenized = dataset.map(tokenize)
    args = TrainingArguments(
        per_device_train_batch_size=4,
        num_train_epochs=2,
        logging_dir="./logs",
        output_dir=save_path,
        save_strategy="epoch"
    )

    trainer = Trainer(model=model, train_dataset=tokenized, args=args)
    trainer.train()

    lora_state = model.state_dict()
    torch.save(lora_state, f"{save_path}/{lora_id}.pt")

    return f"{save_path}/{lora_id}"