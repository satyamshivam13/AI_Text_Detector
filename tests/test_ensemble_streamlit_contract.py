"""Static contract checks for Ensemble Streamlit entrypoint."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def test_ensemble_page_config_and_primary_action_present() -> None:
    content = _read("ensemble.py")
    assert "st.set_page_config(" in content
    assert "Analyze with Ensemble" in content


def test_ensemble_uses_shared_ui_contract_helpers() -> None:
    content = _read("ensemble.py")
    assert "build_mode_guidance_markdown(" in content
    assert "build_limitations_markdown()" in content
    assert "build_result_reminder_markdown()" in content


def test_ensemble_contains_launch_hint_and_probabilistic_warning() -> None:
    content = _read("ensemble.py")
    assert "streamlit run ensemble.py" in content
    assert "probabilistic" in content.lower()


def test_ensemble_keeps_analyzer_comparison_section() -> None:
    content = _read("ensemble.py")
    assert "Analyzer Comparison" in content
