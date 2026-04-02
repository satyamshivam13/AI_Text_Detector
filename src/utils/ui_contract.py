"""Shared UI copy contract helpers for Streamlit entrypoints."""

from __future__ import annotations

LIMITATIONS_BULLETS = [
    "Results are probabilistic indicators, not definitive proof of authorship.",
    "Tool behavior is English-first and may be less reliable for other languages.",
    "Do not use this result as sole evidence in academic or legal decisions.",
]

RESULT_LEVEL_REMINDER = (
    "Interpret this score alongside context, writing history, and human review."
)


def build_limitations_markdown() -> str:
    """Build standardized limitations markdown for sidebar usage."""
    bullets = "\n".join(f"- {item}" for item in LIMITATIONS_BULLETS)
    return f"### ⚠️ Limitations\n\n{bullets}"


def build_result_reminder_markdown() -> str:
    """Build standardized reminder markdown for verdict sections."""
    return f"ℹ️ {RESULT_LEVEL_REMINDER}"


def build_mode_guidance_markdown(
    mode_label: str,
    launch_command: str,
    speed_hint: str,
    memory_hint: str,
) -> str:
    """Build mode guidance markdown with stable structure across apps."""
    return (
        "### 🧭 Mode Guidance\n\n"
        f"- Mode: {mode_label}\n"
        f"- Run: `{launch_command}`\n"
        f"- Typical Speed: {speed_hint}\n"
        f"- Memory Profile: {memory_hint}"
    )
