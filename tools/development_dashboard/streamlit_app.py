from pathlib import Path

import streamlit as st

from dashboard.models import TaskItem
from dashboard.parser import load_snapshot
from dashboard.planner import recommend_next, unmet_dependencies
from dashboard.view_helpers import (
    STATUS_META,
    render_metrics,
    render_recommendation,
    render_task_card,
    source_label,
    status_dataframe,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LOGO_PATH = REPO_ROOT / "assets" / "brand" / "logo-horizontal.png"
REFRESH_OPTIONS = {
    "10 segundos": 10,
    "30 segundos": 30,
    "1 minuto": 60,
    "5 minutos": 300,
}

st.set_page_config(
    page_title="Pulso do desenvolvimento · ECOnexão",
    page_icon=":material/ecg_heart:",
    layout="wide",
)
st.logo(str(LOGO_PATH), size="large")

initial_snapshot = load_snapshot(REPO_ROOT)
all_specs = sorted({task.spec for task in initial_snapshot.tasks})
all_sections = sorted({task.section for task in initial_snapshot.tasks})

with st.sidebar:
    st.subheader("Filtros", anchor=False)
    selected_specs = st.multiselect("Specs", all_specs, default=all_specs)
    selected_sections = st.multiselect("Etapas do plano", all_sections, default=all_sections)
    search = st.text_input(
        "Buscar tarefa",
        placeholder="Ex.: tema, mapa, DEV-1",
        icon=":material/search:",
    )
    st.subheader("Atualização", anchor=False)
    auto_refresh = st.toggle("Atualização automática", value=True)
    refresh_label = st.selectbox(
        "Intervalo",
        list(REFRESH_OPTIONS),
        index=1,
        disabled=not auto_refresh,
    )
    focus_mode = st.toggle(
        "Modo foco",
        value=False,
        help="Mostra só a orientação principal e o trabalho em desenvolvimento.",
    )
    st.caption("Fonte única: `.kiro/specs/**/tasks.md` · somente leitura")

query = search.casefold().strip()


def matches(task: TaskItem) -> bool:
    searchable = f"{task.id} {task.title} {task.spec} {task.section}".casefold()
    return (
        task.spec in selected_specs
        and task.section in selected_sections
        and (not query or query in searchable)
    )


run_every = REFRESH_OPTIONS[refresh_label] if auto_refresh else None


@st.fragment(run_every=run_every)
def render_live_dashboard() -> None:
    snapshot = load_snapshot(REPO_ROOT)
    leaves = snapshot.leaf_tasks
    filtered = [task for task in leaves if matches(task)]
    recommendation = recommend_next(snapshot)

    with st.container(
        horizontal=True,
        horizontal_alignment="distribute",
        vertical_alignment="center",
    ):
        st.caption(
            f"Leitura {snapshot.loaded_at:%d/%m/%Y às %H:%M:%S} · "
            f"{len(snapshot.files)} specs · versão {snapshot.signature}"
        )
        if auto_refresh:
            st.badge(
                f"Atualiza a cada {refresh_label}",
                icon=":material/sync:",
                color="green",
            )
        else:
            st.badge("Atualização pausada", icon=":material/pause:", color="gray")
        if st.button("Atualizar agora", icon=":material/refresh:", type="tertiary"):
            st.rerun(scope="fragment")

    st.title("Pulso do desenvolvimento", anchor=False)
    st.caption("Veja o essencial, escolha um foco e só depois abra os detalhes.")
    render_recommendation(recommendation)

    if focus_mode:
        st.subheader("Em desenvolvimento agora", anchor=False)
        active = [task for task in filtered if task.status == "in_progress"]
        if active:
            for task in active:
                render_task_card(task, snapshot)
        else:
            st.info("Nenhuma etapa filtrada está em desenvolvimento.", icon=":material/info:")
        return

    render_metrics(filtered)
    view = st.segmented_control(
        "Visualização",
        ["Visão geral", "Kanban", "Bloqueios", "Como usar"],
        default="Visão geral",
        label_visibility="collapsed",
        width="stretch",
    )

    if view == "Visão geral":
        left, right = st.columns([1.1, 1], gap="medium")
        with left:
            with st.container(border=True):
                st.subheader("Distribuição do trabalho", anchor=False)
                st.bar_chart(
                    status_dataframe(filtered),
                    x="Estado",
                    y="Etapas",
                    horizontal=True,
                )
        with right:
            with st.container(border=True):
                st.subheader("Em desenvolvimento agora", anchor=False)
                active = [task for task in filtered if task.status == "in_progress"]
                if active:
                    for task in active:
                        render_task_card(task, snapshot)
                else:
                    st.info("Nenhuma etapa em desenvolvimento.", icon=":material/info:")

        st.subheader("Specs acompanhadas", anchor=False)
        with st.container(horizontal=True):
            for path in snapshot.files:
                spec_tasks = [task for task in leaves if task.spec == source_label(path)]
                done = sum(task.status == "done" for task in spec_tasks)
                total = len(spec_tasks)
                st.metric(
                    source_label(path),
                    f"{done}/{total}",
                    f"{done / total:.0%}" if total else "sem tarefas",
                    border=True,
                )

    elif view == "Kanban":
        if not filtered:
            st.info(
                "Nenhuma tarefa corresponde aos filtros atuais.", icon=":material/filter_alt_off:"
            )
        show_all_cards = st.toggle(
            "Mostrar todos os cartões",
            value=False,
            help="Desative para reduzir a carga visual e ver somente os primeiros cartões.",
        )
        columns = st.columns(4, gap="small")
        for column, status in zip(
            columns,
            ("pending", "in_progress", "blocked", "done"),
            strict=True,
        ):
            label, icon, _ = STATUS_META[status]
            status_tasks = [task for task in filtered if task.status == status]
            visible_tasks = status_tasks if show_all_cards else status_tasks[:8]
            with column:
                st.subheader(f"{icon} {label} · {len(status_tasks)}", anchor=False)
                if not status_tasks:
                    st.caption("Nenhuma etapa aqui.")
                for task in visible_tasks:
                    render_task_card(task, snapshot)
                hidden_count = len(status_tasks) - len(visible_tasks)
                if hidden_count:
                    st.caption(
                        f"+ {hidden_count} cartões ocultos. Use “Mostrar todos os cartões” "
                        "ou aplique um filtro."
                    )

    elif view == "Bloqueios":
        blocked = [task for task in filtered if task.status == "blocked"]
        if not blocked:
            st.success(
                "Nenhum bloqueio explícito nos filtros atuais.",
                icon=":material/check_circle:",
            )
        for task in blocked:
            render_task_card(task, snapshot)

        waiting = [
            task
            for task in filtered
            if task.status == "pending" and unmet_dependencies(task, snapshot)
        ]
        if waiting:
            st.subheader("Aguardando dependências", anchor=False)
            for task in waiting:
                render_task_card(task, snapshot)

    else:
        st.subheader("Como manter o painel atualizado", anchor=False)
        st.markdown(
            """
            1. Marque `[~]` ao iniciar uma tarefa.
            2. Use `[x]` somente depois de verificar e registrar a evidência.
            3. Use `[!]` quando houver bloqueio e escreva o motivo logo abaixo.
            4. O painel relê os arquivos automaticamente no intervalo escolhido.
            """
        )
        st.info(
            "O painel nunca edita o planejamento. Ele apenas traduz os `tasks.md` "
            "para uma visão gráfica.",
            icon=":material/verified_user:",
        )


render_live_dashboard()
