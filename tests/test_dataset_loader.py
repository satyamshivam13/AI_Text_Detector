"""Tests for the benchmark dataset loader error handling."""

import pytest

from src.evaluation.dataset import Sample, load_dataset


def _write(tmp_path, text):
    p = tmp_path / "data.jsonl"
    p.write_text(text, encoding="utf-8")
    return p


class TestDatasetLoader:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_dataset(tmp_path / "nope.jsonl")

    def test_valid_records(self, tmp_path):
        p = _write(
            tmp_path,
            '{"id": "h1", "label": "human", "source": "s", "text": "hello world"}\n'
            '{"id": "a1", "label": "ai", "source": "s", "text": "generated text"}\n',
        )
        samples = load_dataset(p)
        assert [s.label for s in samples] == [0, 1]
        assert samples[1].is_ai is True
        assert samples[0].is_ai is False

    def test_blank_lines_skipped(self, tmp_path):
        p = _write(
            tmp_path,
            '\n{"id": "h1", "label": "human", "text": "hi there"}\n\n',
        )
        assert len(load_dataset(p)) == 1

    def test_invalid_json_raises(self, tmp_path):
        p = _write(tmp_path, "{not valid json}\n")
        with pytest.raises(ValueError):
            load_dataset(p)

    def test_unknown_label_raises(self, tmp_path):
        p = _write(tmp_path, '{"id": "x", "label": "robot", "text": "hi"}\n')
        with pytest.raises(ValueError):
            load_dataset(p)

    def test_empty_text_raises(self, tmp_path):
        p = _write(tmp_path, '{"id": "x", "label": "ai", "text": "   "}\n')
        with pytest.raises(ValueError):
            load_dataset(p)

    def test_all_blank_raises(self, tmp_path):
        p = _write(tmp_path, "\n\n\n")
        with pytest.raises(ValueError):
            load_dataset(p)

    def test_default_id_when_missing(self, tmp_path):
        p = _write(tmp_path, '{"label": "human", "text": "no id here"}\n')
        samples = load_dataset(p)
        assert samples[0].id == "sample-1"

    def test_sample_dataclass(self):
        s = Sample(id="i", label=1, source="s", text="t")
        assert s.is_ai
