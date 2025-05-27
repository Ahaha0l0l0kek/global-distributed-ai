from fastapi import FastAPI
from api.models import ObservationRequest, AgentMemoryEntry
from api.agent_interface import AgentAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
agent = AgentAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # позже ограничить
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/memory", response_model=list[AgentMemoryEntry])
def get_memory():
    return agent.recent_memory()

@app.post("/observe", response_model=AgentMemoryEntry)
def observe_page(req: ObservationRequest):
    return agent.process_url(req.url)

@app.get("/")
def root():
    return {"status": "agent-api ready"}