"""Tests verifying offline CLI execution and exit codes."""

import io
import json
import sys
import pytest
from tokwhois.cli import main


def test_cli_demo_offline(capsys):
    ret = main(["demo"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "tokwhois" in captured.out
    assert "family" in captured.out
    assert "glm4" in captured.out or "class" in captured.out


def test_cli_demo_json_output(capsys):
    ret = main(["demo", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "family" in data
    assert "l1_distance" in data
    assert data["l1_distance"] == 0
    assert "rankings" in data


def test_cli_selftest_flag(capsys):
    ret = main(["--selftest"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "ALL CHECKS PASSED" in captured.out


def test_cli_missing_model_for_url(capsys):
    ret = main(["https://api.example.com/v1"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error: --model" in captured.err
