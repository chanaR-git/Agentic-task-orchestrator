from typing import List, Optional

from .entities import Task

class TodoService:
    def __init__(self) -> None:
        self._tasks: List[Task] = []

    def get_tasks(self) -> List[Task]:
        return list(self._tasks)

    def add_task(self, task: Task) -> None:
        self._tasks.append(task)

    def update_task(self, code: str, *,
                    title: Optional[str] = None,
                    description: Optional[str] = None,
                    type: Optional[str] = None,
                    start_date: Optional = None,
                    end_date: Optional = None,
                    status: Optional = None) -> bool:
        for task in self._tasks:
            if task.code == code:
                if title is not None:
                    task.title = title
                if description is not None:
                    task.description = description
                if type is not None:
                    task.type = type
                if start_date is not None:
                    task.start_date = start_date
                if end_date is not None:
                    task.end_date = end_date
                if status is not None:
                    task.status = status
                return True
        return False

    def delete_task(self, code: str) -> bool:
        for idx, task in enumerate(self._tasks):
            if task.code == code:
                del self._tasks[idx]
                return True
        return False
