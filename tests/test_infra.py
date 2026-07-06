"""Tests for logging setup and the lazy analyzer-import machinery (no models)."""

import logging

import pytest

import src.analyzers as analyzers
from src.utils.logging_config import get_logger, setup_logging


class TestLoggingConfig:
    def test_setup_logging_console(self):
        setup_logging("INFO")
        logger = get_logger("test.logger")
        assert isinstance(logger, logging.Logger)
        logger.info("hello")  # should not raise

    def test_setup_logging_to_file(self, tmp_path):
        log_file = tmp_path / "app.log"
        setup_logging("DEBUG", log_file=str(log_file))
        get_logger("test.file").debug("written")
        assert log_file.exists()

    def test_get_logger_returns_named_logger(self):
        assert get_logger("abc").name == "abc"


class TestLazyAnalyzerImports:
    def test_lazy_class_is_importable(self):
        # Accessing a heavy analyzer name triggers __getattr__ and returns the
        # class object without instantiating (no torch model load).
        cls = analyzers.GPT2Analyzer
        assert cls.__name__ == "GPT2Analyzer"

    def test_all_lazy_names_resolve(self):
        for name in ("GPT2Analyzer", "RoBERTaAnalyzer", "BinocularsAnalyzer", "EnsembleAnalyzer"):
            assert getattr(analyzers, name).__name__ == name

    def test_unknown_attribute_raises(self):
        with pytest.raises(AttributeError):
            _ = analyzers.NotARealAnalyzer

    def test_dir_lists_public_api(self):
        names = dir(analyzers)
        assert "NLTKAnalyzer" in names
        assert "EnsembleAnalyzer" in names
