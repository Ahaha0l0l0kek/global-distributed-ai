distributed_ai_agent/
├── backend/               # Сервер + агентное ядро
│   ├── core/              # Цикл observe-plan-act-learn
│   ├── memory/            # Cassandra
│   ├── llm/               # llama.cpp runtime
│   ├── observation/       # веб, сенсоры
│   ├── p2p/               # Federated sync / libp2p
│   ├── api/               # REST/gRPC для связи с Flutter
│   ├── requirements.txt
│   └── main.py
├── client/                # Flutter-приложение (Android/iOS/desktop/web)
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   ├── services/      # HTTP/gRPC + локальный runtime (в будущем)
│   │   └── widgets/
│   └── pubspec.yaml
├── model/                 # Весовые файлы LLM (gguf и LoRA адаптеры)
│   └── phi-2.gguf
├── .env                   # конфиги
└── README.md