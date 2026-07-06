"""Smoke tests for the Streamlit entry points.

These render each app headlessly with Streamlit's AppTest harness and assert the
script runs without raising. Model loading is gated behind the Analyze button,
so a bare run does not download or build any model (fast).

They exist primarily as a safety net for the shared-UI refactor: if extracting
common components breaks an app's layout or imports, these fail immediately.
"""

from pathlib import Path

import pytest

from streamlit.testing.v1 import AppTest

_ROOT = Path(__file__).resolve().parents[1]
_APPS = ["app.py", "gpt2_app.py", "ensemble.py"]


@pytest.mark.parametrize("app_file", _APPS)
def test_app_renders_without_exception(app_file):
    at = AppTest.from_file(str(_ROOT / app_file), default_timeout=60)
    at.run()
    assert not at.exception, f"{app_file} raised: {at.exception}"


@pytest.mark.parametrize("app_file", _APPS)
def test_app_has_sidebar_and_body(app_file):
    at = AppTest.from_file(str(_ROOT / app_file), default_timeout=60)
    at.run()
    # Every app renders markdown (headers/CSS) in the main body and sidebar.
    assert len(at.markdown) > 0
    assert len(at.sidebar.markdown) > 0


@pytest.mark.parametrize("app_file", _APPS)
def test_app_has_analyze_button(app_file):
    at = AppTest.from_file(str(_ROOT / app_file), default_timeout=60)
    at.run()
    labels = " ".join(b.label for b in at.button).lower()
    assert "analyze" in labels
