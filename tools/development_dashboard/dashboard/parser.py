import hashlib
import re
from datetime import datetime
from pathlib import Path

from dashboard.models import DevelopmentSnapshot, TaskItem, TaskStatus

TASK_PATTERN = re.compile(r"^(?P<indent>\s*)-\s+\[(?P<marker>[ xX~!])\]\s+(?P<body>.+?)\s*$")
TASK_ID_PATTERN = re.compile(
    r"^(?P<id>(?:[A-Za-z]+-)?(?:\d+[A-Za-z]?|[A-Za-z]+\d+)"
    r"(?:\.\d+)*)(?:\.)?\s+(?P<title>.+)$"
)
SECTION_PATTERN = re.compile(r"^##\s+(?P<section>.+?)\s*$")
REQUIREMENTS_PATTERN = re.compile(r"_?Requisitos:\s*(?P<value>.+?)_?$", re.IGNORECASE)
DEPENDENCIES_PATTERN = re.compile(r"Dependências:\s*(?P<value>.+)$", re.IGNORECASE)

MARKER_TO_STATUS: dict[str, TaskStatus] = {
    " ": "pending",
    "~": "in_progress",
    "!": "blocked",
    "x": "done",
    "X": "done",
}


def _split_values(value: str) -> list[str]:
    clean = value.strip().strip("_")
    if clean.lower() in {"", "nenhuma", "nenhum"}:
        return []
    return [item.strip().rstrip(".") for item in clean.split(",") if item.strip()]


def _task_from_match(
    match: re.Match[str],
    *,
    spec: str,
    section: str,
    order: int,
    source: Path,
    parent_id: str | None,
) -> TaskItem:
    body = match.group("body")
    identity = TASK_ID_PATTERN.match(body)
    if identity:
        task_id = identity.group("id")
        title = identity.group("title")
    else:
        task_id = f"{spec.upper()}-{order + 1}"
        title = body
    return TaskItem(
        id=task_id,
        title=title,
        status=MARKER_TO_STATUS[match.group("marker")],
        spec=spec,
        section=section,
        order=order,
        indent=len(match.group("indent").expandtabs(2)),
        source=source,
        parent_id=parent_id,
    )


def parse_tasks_file(path: Path, order_start: int = 0) -> list[TaskItem]:
    """Interpreta tarefas Markdown sem executar ou modificar o conteúdo."""
    spec = path.parent.name
    section = "Sem seção"
    tasks: list[TaskItem] = []
    stack: list[TaskItem] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        section_match = SECTION_PATTERN.match(raw_line)
        if section_match:
            section = section_match.group("section")
            stack.clear()
            continue

        task_match = TASK_PATTERN.match(raw_line)
        if task_match:
            indent = len(task_match.group("indent").expandtabs(2))
            while stack and stack[-1].indent >= indent:
                stack.pop()
            parent_id = stack[-1].id if stack else None
            task = _task_from_match(
                task_match,
                spec=spec,
                section=section,
                order=order_start + len(tasks),
                source=path,
                parent_id=parent_id,
            )
            tasks.append(task)
            stack.append(task)
            continue

        stripped = raw_line.strip()
        if not stripped or not stack:
            continue

        line_indent = len(raw_line) - len(raw_line.lstrip())
        target = next((task for task in reversed(stack) if task.indent < line_indent), None)
        if target is None:
            continue

        content = stripped.removeprefix("-").strip()
        dependency_match = DEPENDENCIES_PATTERN.search(content)
        requirement_match = REQUIREMENTS_PATTERN.search(content)
        if dependency_match:
            target.dependencies = _split_values(dependency_match.group("value"))
        elif requirement_match:
            target.requirements = _split_values(requirement_match.group("value"))
        elif not content.startswith(("Arquivos:", "Verificação:")):
            target.details.append(content)

    return tasks


def load_snapshot(repo_root: Path) -> DevelopmentSnapshot:
    specs_root = (repo_root / ".kiro" / "specs").resolve()
    files = sorted(specs_root.glob("*/tasks.md"))
    tasks: list[TaskItem] = []
    digest = hashlib.sha256()

    for path in files:
        raw_bytes = path.read_bytes()
        digest.update(path.relative_to(repo_root).as_posix().encode())
        digest.update(raw_bytes)
        parsed = parse_tasks_file(path, order_start=len(tasks))
        tasks.extend(parsed)

    return DevelopmentSnapshot(
        tasks=tasks,
        files=files,
        loaded_at=datetime.now().astimezone(),
        signature=digest.hexdigest()[:10],
    )
