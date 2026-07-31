from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.models import DevelopmentSnapshot, TaskItem
from dashboard.planner import Recommendation, unmet_dependencies

STATUS_META = {
    "pending": ("Pendente", ":material/schedule:", "blue"),
    "in_progress": ("Em desenvolvimento", ":material/construction:", "orange"),
    "blocked": ("Bloqueado", ":material/error:", "red"),
    "done": ("Entregue", ":material/check_circle:", "green"),
}


def render_task_card(task: TaskItem, snapshot: DevelopmentSnapshot) -> None:
    label, icon, color = STATUS_META[task.status]
    with st.container(border=True, gap="small"):
        st.badge(label, icon=icon, color=color)
        st.markdown(f"**{task.id} · {task.title}**")
        st.caption(f"{task.spec} · {task.section}")
        if task.status == "blocked":
            st.error(task.blocker_reason, icon=":material/report:")
        dependencies = unmet_dependencies(task, snapshot)
        if dependencies and task.status == "pending":
            st.caption(f"Aguarda: {', '.join(dependencies)}")
        if task.requirements:
            with st.expander("Rastreabilidade", icon=":material/account_tree:"):
                st.write(", ".join(task.requirements))
        if task.details and task.status != "blocked":
            with st.expander("Detalhes", icon=":material/description:"):
                for detail in task.details:
                    st.write(f"• {detail}")


def render_recommendation(recommendation: Recommendation) -> None:
    icon_by_kind = {
        "in_progress": ":material/play_circle:",
        "ready": ":material/rocket_launch:",
        "blocked": ":material/lock_open:",
        "waiting": ":material/hourglass:",
        "done": ":material/task_alt:",
    }
    with st.container(border=True):
        st.caption("PRÓXIMA ETAPA RECOMENDADA")
        st.header(
            recommendation.headline,
            anchor=False,
            help="A recomendação prioriza trabalho em andamento e depois tarefas prontas.",
        )
        st.write(recommendation.reason)
        st.info(recommendation.action, icon=icon_by_kind[recommendation.kind])
        if recommendation.task:
            st.caption(f"Fonte: {recommendation.task.spec} · {recommendation.task.section}")


def render_metrics(tasks: list[TaskItem]) -> None:
    counts = Counter(task.status for task in tasks)
    total = len(tasks)
    done = counts["done"]
    progress = done / total if total else 0
    with st.container(horizontal=True):
        st.metric("Entregues", done, border=True)
        st.metric("Em desenvolvimento", counts["in_progress"], border=True)
        st.metric("Bloqueadas", counts["blocked"], border=True)
        st.metric("Pendentes", counts["pending"], border=True)
    st.progress(progress, text=f"Progresso verificado: {progress:.0%} · {done} de {total} etapas")


def status_dataframe(tasks: list[TaskItem]) -> pd.DataFrame:
    counts = Counter(task.status for task in tasks)
    return pd.DataFrame(
        [
            {"Estado": STATUS_META[status][0], "Etapas": counts[status]}
            for status in ("done", "in_progress", "blocked", "pending")
        ]
    )


def source_label(path: Path) -> str:
    return path.parent.name
