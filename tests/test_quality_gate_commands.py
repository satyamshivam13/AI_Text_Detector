"""Static contract tests for quality-gate command references."""

from pathlib import Path


def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_makefile_test_target_has_pytest_with_coverage_flags() -> None:
    makefile = _read_text("Makefile")

    assert "test:" in makefile
    assert "-m pytest tests/" in makefile
    assert "--cov=src" in makefile
    assert "--cov-report=html" in makefile
    assert "--cov-report=term-missing" in makefile


def test_pytest_ini_registers_slow_marker() -> None:
    pytest_ini = _read_text("pytest.ini")

    assert "[pytest]" in pytest_ini
    assert "markers" in pytest_ini
    assert "slow" in pytest_ini


def test_readme_mentions_canonical_quality_gate_command() -> None:
    readme = _read_text("README.md")

    assert "make test" in readme


def test_core_test_modules_exist_for_quality_gate_scope() -> None:
    required = [
        Path("tests/test_nltk_analyzer.py"),
        Path("tests/test_gpt2_analyzer.py"),
        Path("tests/test_ensemble_analyzer.py"),
        Path("tests/test_text_processing.py"),
        Path("tests/test_result_model.py"),
    ]

    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing expected core test modules: {missing}"
