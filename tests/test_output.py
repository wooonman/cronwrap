"""Tests for cronwrap.output."""
import pytest
from pathlib import Path

from cronwrap.output import (
    OutputConfig,
    CapturedOutput,
    truncate_output,
    process_output,
    load_stored_output,
)


# --- OutputConfig ---

def test_output_config_defaults():
    cfg = OutputConfig()
    assert cfg.max_bytes == 64 * 1024
    assert cfg.store_dir is None
    assert cfg.include_stderr is True


def test_output_config_from_dict():
    cfg = OutputConfig.from_dict({"max_bytes": 1024, "store_dir": "/tmp", "include_stderr": False})
    assert cfg.max_bytes == 1024
    assert cfg.store_dir == "/tmp"
    assert cfg.include_stderr is False


def test_output_config_from_dict_defaults():
    cfg = OutputConfig.from_dict({})
    assert cfg.max_bytes == 64 * 1024
    assert cfg.include_stderr is True


# --- truncate_output ---

def test_truncate_no_truncation_needed():
    text, was = truncate_output("hello", 100)
    assert text == "hello"
    assert was is False


def test_truncate_triggers():
    text, was = truncate_output("abcdef", 3)
    assert was is True
    assert "...[truncated]" in text
    assert text.startswith("abc")


def test_truncate_exact_boundary():
    text, was = truncate_output("abc", 3)
    assert was is False
    assert text == "abc"


# --- process_output ---

def test_process_output_no_store():
    cfg = OutputConfig(max_bytes=1000)
    result = process_output("out", "err", cfg)
    assert result.stdout == "out"
    assert result.stderr == "err"
    assert result.stored_path is None
    assert result.truncated is False


def test_process_output_exclude_stderr():
    cfg = OutputConfig(include_stderr=False)
    result = process_output("out", "err", cfg)
    assert result.stderr == ""


def test_process_output_truncated():
    cfg = OutputConfig(max_bytes=5)
    result = process_output("hello world", "", cfg)
    assert result.truncated is True


def test_process_output_stores_file(tmp_path):
    cfg = OutputConfig(store_dir=str(tmp_path))
    result = process_output("output text", "", cfg, run_id="run-123")
    assert result.stored_path is not None
    assert Path(result.stored_path).exists()
    assert Path(result.stored_path).read_text() == "output text"


def test_process_output_no_store_without_run_id(tmp_path):
    cfg = OutputConfig(store_dir=str(tmp_path))
    result = process_output("output text", "", cfg, run_id=None)
    assert result.stored_path is None


# --- load_stored_output ---

def test_load_stored_output_exists(tmp_path):
    (tmp_path / "abc.log").write_text("hello")
    text = load_stored_output(str(tmp_path), "abc")
    assert text == "hello"


def test_load_stored_output_missing(tmp_path):
    result = load_stored_output(str(tmp_path), "nope")
    assert result is None
