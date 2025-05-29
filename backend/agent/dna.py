import json, uuid, os, random, copy
from pathlib import Path

DNA_PATH = Path.home() / ".gda" / "dna.json"

DEFAULT_DNA = {
    "id": f"dna-{uuid.uuid4().hex[:8]}",
    "version": 1,
    "model_base": "phi-2.gguf",
    "lora_path": None,
    "prompt_template": "Ты — распределённый ИИ, анализируешь и эволюционируешь.",
    "max_tokens": 128,
    "temperature": 0.7,
    "top_p": 0.95,
    "weights": {
        "observe": 0.9,
        "plan": 1.0,
        "p2p_share": 0.7,
        "scrape_depth": 2,
        "activeness": 0.3
    },
    "mutations": {
        "rate": 0.02,
        "mutable_fields": ["temperature", "prompt_template", "weights.observe"]
    },
    "history": [],
    "lora_path": "lora_abc123.pt"
}

def ensure_dna_exists():
    if not DNA_PATH.exists():
        DNA_PATH.parent.mkdir(parents=True, exist_ok=True)
        save_dna(DEFAULT_DNA)
    return load_dna()

def load_dna():
    with open(DNA_PATH, "r") as f:
        return json.load(f)

def save_dna(dna):
    with open(DNA_PATH, "w") as f:
        json.dump(dna, f, indent=2)

def mutate_dna(dna):
    new_dna = copy.deepcopy(dna)
    new_dna["id"] = f"dna-{uuid.uuid4().hex[:8]}"
    for field in dna["mutations"]["mutable_fields"]:
        if random.random() < dna["mutations"]["rate"]:
            _apply_mutation(new_dna, field)
    new_dna["history"].append(dna["id"])
    save_dna(new_dna)
    return new_dna

def _apply_mutation(dna, path):
    parts = path.split(".")
    obj = dna
    for p in parts[:-1]:
        obj = obj[p]
    key = parts[-1]
    old = obj[key]

    if isinstance(old, float):
        obj[key] = max(0.0, min(1.0, old + random.uniform(-0.1, 0.1)))
    elif isinstance(old, str) and "prompt" in key:
        replacements = [
            "Ты — агент разума.",
            "Ты — инструмент истины.",
            "Ты ищешь паттерны в сети.",
            "Твоя цель — эволюция цифрового сознания."
        ]
        obj[key] = random.choice(replacements)

def hybridize_dna(local, remote):
    import copy
    new = copy.deepcopy(local)
    new["id"] = f"dna-{uuid.uuid4().hex[:8]}"
    new["history"].append(local["id"])
    new["history"].append(remote.get("id"))

    # Смешиваем числовые параметры
    for key in ["temperature", "top_p"]:
        l, r = local.get(key), remote.get(key)
        if isinstance(l, float) and isinstance(r, float):
            new[key] = (l + r) / 2

    # Смешиваем веса
    for k, lv in local["weights"].items():
        rv = remote["weights"].get(k)
        if isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            new["weights"][k] = (lv + rv) / 2

    # Случайный выбор prompt
    if random.random() < 0.5:
        new["prompt_template"] = remote.get("prompt_template", local["prompt_template"])

    return new
