"""Static contract checks for NLTK and GPT-2 Streamlit entrypoints."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def test_app_py_contains_mode_guidance_and_launch_hint() -> None:
    content = _read("app.py")
    assert "streamlit run app.py" in content
    assert "build_mode_guidance_markdown(" in content


def test_test_py_contains_mode_guidance_and_launch_hint() -> None:
    content = _read("test.py")
    assert "streamlit run test.py" in content
    assert "build_mode_guidance_markdown(" in content


def test_both_files_contain_shared_limitations_and_reminder_calls() -> None:
    app_content = _read("app.py")
    gpt_content = _read("test.py")
    assert "build_limitations_markdown()" in app_content
    assert "build_limitations_markdown()" in gpt_content
    assert "build_result_reminder_markdown()" in app_content
    assert "build_result_reminder_markdown()" in gpt_content


def test_entrypoints_keep_page_config_and_analyze_buttons() -> None:
    app_content = _read("app.py")
    gpt_content = _read("test.py")
    assert "st.set_page_config(" in app_content
    assert "st.set_page_config(" in gpt_content
    assert "Analyze Text" in app_content
    assert "Deep Analyze with GPT-2" in gpt_content
