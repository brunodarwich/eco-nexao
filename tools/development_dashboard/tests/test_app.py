from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_smoke() -> None:
    app_path = Path(__file__).parents[1] / "streamlit_app.py"

    app = AppTest.from_file(app_path, default_timeout=20).run()

    assert not app.exception
    assert [title.value for title in app.title] == ["Pulso do desenvolvimento"]
    assert any(header.value.startswith(("Continue ", "Comece ")) for header in app.header)
    assert {metric.label for metric in app.metric} >= {
        "Entregues",
        "Em desenvolvimento",
        "Bloqueadas",
        "Pendentes",
    }
