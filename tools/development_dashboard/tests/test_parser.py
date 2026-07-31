from pathlib import Path

from dashboard.parser import load_snapshot, parse_tasks_file


def test_parser_reads_status_hierarchy_and_metadata(tmp_path: Path) -> None:
    spec_dir = tmp_path / "demo"
    spec_dir.mkdir()
    tasks_file = spec_dir / "tasks.md"
    tasks_file.write_text(
        """# Tasks
## Wave 1
- [~] 1. Construir base
  - Dependências: 0
  - [x] 1.1 Entregar fundação
  - [!] 1.2 Resolver integração
    - Serviço indisponível na homologação.
    - _Requisitos: RF-01, RNF-02_
""",
        encoding="utf-8",
    )

    tasks = parse_tasks_file(tasks_file)

    assert [task.id for task in tasks] == ["1", "1.1", "1.2"]
    assert [task.status for task in tasks] == ["in_progress", "done", "blocked"]
    assert tasks[0].dependencies == ["0"]
    assert tasks[1].parent_id == "1"
    assert tasks[2].blocker_reason == "Serviço indisponível na homologação."
    assert tasks[2].requirements == ["RF-01", "RNF-02"]
    assert tasks[2].section == "Wave 1"


def test_load_snapshot_reads_only_spec_task_files(tmp_path: Path) -> None:
    specs = tmp_path / ".kiro" / "specs"
    (specs / "a").mkdir(parents=True)
    (specs / "b").mkdir()
    (specs / "a" / "tasks.md").write_text("- [x] A1. Pronto", encoding="utf-8")
    (specs / "b" / "tasks.md").write_text("- [ ] B1. Fazer", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=nao-ler", encoding="utf-8")

    snapshot = load_snapshot(tmp_path)

    assert len(snapshot.files) == 2
    assert [task.id for task in snapshot.tasks] == ["A1", "B1"]
    assert snapshot.signature
