from dataclasses import dataclass

from dashboard.models import DevelopmentSnapshot, TaskItem


@dataclass(frozen=True, slots=True)
class Recommendation:
    task: TaskItem | None
    headline: str
    reason: str
    action: str
    kind: str


def _ancestor_chain(task: TaskItem, task_by_id: dict[str, TaskItem]) -> list[TaskItem]:
    ancestors: list[TaskItem] = []
    current = task
    visited: set[str] = set()
    while current.parent_id and current.parent_id not in visited:
        visited.add(current.parent_id)
        parent = task_by_id.get(current.parent_id)
        if parent is None:
            break
        ancestors.append(parent)
        current = parent
    return ancestors


def effective_dependencies(task: TaskItem, snapshot: DevelopmentSnapshot) -> list[str]:
    dependencies = list(task.dependencies)
    for parent in _ancestor_chain(task, snapshot.task_by_id):
        dependencies.extend(parent.dependencies)
    return list(dict.fromkeys(dependencies))


def unmet_dependencies(task: TaskItem, snapshot: DevelopmentSnapshot) -> list[str]:
    task_by_id = snapshot.task_by_id
    return [
        dependency
        for dependency in effective_dependencies(task, snapshot)
        if dependency not in task_by_id or task_by_id[dependency].status != "done"
    ]


def recommend_next(snapshot: DevelopmentSnapshot) -> Recommendation:
    leaves = sorted(snapshot.leaf_tasks, key=lambda task: task.order)

    active = next((task for task in leaves if task.status == "in_progress"), None)
    if active:
        return Recommendation(
            task=active,
            headline=f"Continue {active.id}",
            reason=(
                "Esta etapa já está em desenvolvimento; terminar o que começou "
                "reduz troca de contexto."
            ),
            action=f"Concluir e verificar: {active.title}",
            kind="in_progress",
        )

    ready = next(
        (
            task
            for task in leaves
            if task.status == "pending" and not unmet_dependencies(task, snapshot)
        ),
        None,
    )
    if ready:
        return Recommendation(
            task=ready,
            headline=f"Comece {ready.id}",
            reason="É a primeira etapa pendente com todas as dependências concluídas.",
            action=f"Marcar como [~] e iniciar: {ready.title}",
            kind="ready",
        )

    blocked = next((task for task in leaves if task.status == "blocked"), None)
    if blocked:
        return Recommendation(
            task=blocked,
            headline=f"Desbloqueie {blocked.id}",
            reason=blocked.blocker_reason,
            action="Definir responsável e registrar a decisão necessária no tasks.md.",
            kind="blocked",
        )

    pending = next((task for task in leaves if task.status == "pending"), None)
    if pending:
        missing = ", ".join(unmet_dependencies(pending, snapshot)) or "dependências anteriores"
        return Recommendation(
            task=pending,
            headline="Nenhuma etapa está pronta ainda",
            reason=f"A próxima candidata depende de: {missing}.",
            action="Concluir ou revisar as dependências antes de iniciar outra frente.",
            kind="waiting",
        )

    return Recommendation(
        task=None,
        headline="Tudo entregue",
        reason="Não há tarefas folha pendentes, em andamento ou bloqueadas.",
        action="Registrar a verificação final e celebrar a entrega.",
        kind="done",
    )
