from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

TaskStatus = Literal["pending", "in_progress", "blocked", "done"]


@dataclass(slots=True)
class TaskItem:
    id: str
    title: str
    status: TaskStatus
    spec: str
    section: str
    order: int
    indent: int
    source: Path
    parent_id: str | None = None
    dependencies: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)

    @property
    def blocker_reason(self) -> str:
        if self.status != "blocked":
            return ""
        return self.details[0] if self.details else "Motivo ainda não registrado no tasks.md."


@dataclass(slots=True)
class DevelopmentSnapshot:
    tasks: list[TaskItem]
    files: list[Path]
    loaded_at: datetime
    signature: str

    @property
    def task_by_id(self) -> dict[str, TaskItem]:
        return {task.id: task for task in self.tasks}

    @property
    def leaf_tasks(self) -> list[TaskItem]:
        parent_ids = {task.parent_id for task in self.tasks if task.parent_id}
        return [task for task in self.tasks if task.id not in parent_ids]
