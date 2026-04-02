"""Tests for shared Streamlit UI copy contract helpers."""

from src.utils.ui_contract import (
    LIMITATIONS_BULLETS,
    build_limitations_markdown,
    build_mode_guidance_markdown,
    build_result_reminder_markdown,
)


def test_limitations_bullets_contract_tokens() -> None:
    assert len(LIMITATIONS_BULLETS) == 3
    joined = " ".join(LIMITATIONS_BULLETS)
    assert "probabilistic" in joined
    assert "English-first" in joined
    assert "sole evidence" in joined


def test_build_limitations_markdown_contains_heading_and_bullets() -> None:
    content = build_limitations_markdown()
    assert "### ⚠️ Limitations" in content
    for bullet in LIMITATIONS_BULLETS:
        assert f"- {bullet}" in content


def test_build_result_reminder_markdown_contract() -> None:
    content = build_result_reminder_markdown()
    assert content.startswith("ℹ️")
    assert "writing history" in content


def test_build_mode_guidance_markdown_includes_all_inputs() -> None:
    content = build_mode_guidance_markdown(
        "NLTK", "streamlit run app.py", "<1s", "<1 GB"
    )
    assert "### 🧭 Mode Guidance" in content
    assert "NLTK" in content
    assert "streamlit run app.py" in content
    assert "<1s" in content
    assert "<1 GB" in content
