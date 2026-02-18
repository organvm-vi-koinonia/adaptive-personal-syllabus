"""Tests for the CLI interface using Click's test runner."""

from __future__ import annotations

import json

from click.testing import CliRunner

from adaptive_personal_syllabus.core import cli


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "adaptive-personal-syllabus" in result.output


def test_generate_text_format():
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", "--organs", "I", "--format", "text"])
    assert result.exit_code == 0
    assert "Learning Path" in result.output


def test_generate_json_format():
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", "--organs", "I", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "path_id" in data
    assert "modules" in data


def test_generate_md_format():
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", "--organs", "I,V", "--format", "md"])
    assert result.exit_code == 0
    assert "# Learning Path" in result.output
    assert "**Learner:**" in result.output


def test_generate_missing_organs():
    runner = CliRunner()
    result = runner.invoke(cli, ["generate"])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()
