import uuid
import time

class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskManager:
    def __init__(self, agent_id="agent_001"):
        self.agent_id = agent_id
        self.memory = Memory()
        self.tasks = {}

    def create(self, task_str, reply_to=None):
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "id": task_id,
            "task": task_str,
            "reply_to": reply_to,
            "status": TaskStatus.PENDING,
            "created_at": time.time(),
            "result": None
            }
            self.memory.store_task(task_id, self.agent_id, task_str, reply_to)
            return self.tasks[task_id]

    def mark_running(self, task_id):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = TaskStatus.RUNNING
            self.memory.update_task_status(task_id, TaskStatus.RUNNING)

    def mark_done(self, task_id, result):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = TaskStatus.COMPLETED
            self.tasks[task_id]["result"] = result
            self.memory.update_task_status(task_id, TaskStatus.COMPLETED, result)
            self.task_stats["completed"] += 1

    def mark_failed(self, task_id, error):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = TaskStatus.FAILED
            self.tasks[task_id]["result"] = error
            self.memory.update_task_status(task_id, TaskStatus.FAILED, error)
            self.task_stats["failed"] += 1

    def get_status(self, task_id):
        return self.tasks.get(task_id, None)
    
    def get_reward_score(self):
    c = self.stats["completed"]
    f = self.stats["failed"]
    return c / (c + f + 1e-5)
