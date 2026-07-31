from datetime import datetime
from pathlib import Path

from dashboard.models import DevelopmentSnapshot, TaskItem
from dashboard.planner import recommend_next, unmet_dependencies


def task(
    task_id: str,
    status: str,
    order: int,
    *,
    parent_id: str | None = None,
    dependencies: list[str] | None = None,
) -> TaskItem:
    return TaskItem(
        id=task_id,
        title=f"Tarefa {task_id}",
        status=status,  # type: ignore[arg-type]
        spec="demo",
        section="Wave",
        order=order,
        indent=0 if parent_id is None else 2,
        source=Path("tasks.md"),
        parent_id=parent_id,
        dependencies=dependencies or [],
    )


def snapshot(*tasks: TaskItem) -> DevelopmentSnapshot:
    return DevelopmentSnapshot(
        tasks=list(tasks),
        files=[],
        loaded_at=datetime.now(),
        signature="test",
    )


def test_recommendation_keeps_focus_on_leaf_in_progress() -> None:
    data = snapshot(
        task("0", "done", 0),
        task("1", "in_progress", 1, dependencies=["0"]),
        task("1.1", "done", 2, parent_id="1"),
        task("1.2", "in_progress", 3, parent_id="1"),
    )

    recommendation = recommend_next(data)

    assert recommendation.task is not None
    assert recommendation.task.id == "1.2"
    assert recommendation.kind == "in_progress"


def test_recommendation_selects_first_ready_pending_leaf() -> None:
    data = snapshot(
        task("0", "done", 0),
        task("1", "pending", 1, dependencies=["0"]),
        task("2", "pending", 2, dependencies=["missing"]),
    )

    recommendation = recommend_next(data)

    assert recommendation.task is not None
    assert recommendation.task.id == "1"
    assert recommendation.kind == "ready"
    assert unmet_dependencies(data.tasks[2], data) == ["missing"]


def test_recommendation_explains_blocker_when_nothing_is_ready() -> None:
    blocked = task("1", "blocked", 0)
    blocked.details.append("Aguardando decisão do produto.")
    data = snapshot(blocked)

    recommendation = recommend_next(data)

    assert recommendation.task == blocked
    assert recommendation.kind == "blocked"
    assert "decisão" in recommendation.reason
