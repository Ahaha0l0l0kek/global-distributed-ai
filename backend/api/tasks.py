from fastapi import APIRouter, HTTPException
from api.models import TaskResponse
from memory.cassandra_client import Memory

router = APIRouter()
memory = Memory()

@router.get("/tasks", response_model=list[TaskResponse])
def get_all_tasks():
    rows = memory.get_all_tasks()
    return [TaskResponse(**r._asdict()) for r in rows]

@router.get("/task/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    row = memory.get_task_by_id(task_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**row._asdict())
