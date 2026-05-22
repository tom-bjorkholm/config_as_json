#! /usr/local/bin/python3
"""Tests for the e38 write-side conversion hook teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from example.cmd_line_handling import SetValues
from example.e38_write_side_hook import (
    Priority, ReviewState, TaskConfig, e38_write_side_hook_print,
    e38_write_side_hook_set)
from example.e38_write_side_hook import main as e38_main
from .helpers import assert_rt_out, assert_write_command_output


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e38_default_writes_names() -> None:
    """``IntEnum`` values become symbolic names in the JSON file."""
    cfg = TaskConfig()
    text = cfg.as_json_string(stderr_file=sys.stderr)
    payload = json.loads(text)
    assert payload == {
        'project': 'config-as-json',
        'output_file': 'reports/tasks.json',
        'review_state': 'DRAFT',
        'priority': 'MEDIUM'}


def test_e38_roundtrip_values() -> None:
    """The write/parse converter pair recovers the original Python types."""
    cfg = TaskConfig()
    cfg.priority = Priority.HIGH
    cfg.output_file = Path('/var/log/tasks.json')
    cfg.review_state = ReviewState.PUBLISHED
    text = cfg.as_json_string(stderr_file=sys.stderr)
    cfg2 = TaskConfig(from_json_data_text=text)
    assert cfg2.priority is Priority.HIGH
    assert cfg2.output_file == Path('/var/log/tasks.json')
    assert cfg2.review_state is ReviewState.PUBLISHED


def test_e38_set_writes_overrides(capsys: pytest.CaptureFixture[str]) -> None:
    """The set command writes user overrides via the write-side hook."""
    set_values = cast(SetValues, {
        'project': 'examples',
        'priority': Priority.HIGH,
        'output_file': '/tmp/out.json',
        'review_state': ReviewState.PUBLISHED})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/write_side_hook.cfg'
        e38_write_side_hook_set(set_values, config_file)
        json_data = read_json_data(config_file)
        cfg = TaskConfig(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert json_data == {
        'project': 'examples',
        'output_file': '/tmp/out.json',
        'review_state': 'PUBLISHED',
        'priority': 'HIGH'}
    assert cfg.priority is Priority.HIGH
    assert cfg.output_file == Path('/tmp/out.json')
    assert cfg.review_state is ReviewState.PUBLISHED


def test_e38_print_shows_values(capsys: pytest.CaptureFixture[str]) -> None:
    """The print command formats rich Python values for the user."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/write_side_hook.cfg'
        e38_write_side_hook_set({}, config_file)
        _ = capsys.readouterr()
        e38_write_side_hook_print(config_file)
        out, err = capsys.readouterr()
    assert err == ''
    assert 'Priority: MEDIUM (numeric value 5)' in out
    assert 'Review state: DRAFT' in out


def test_e38_main_roundtrip(capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip default values through the command line."""
    assert_rt_out(capsys, e38_main, 'write_side_hook.cfg', [],
                  ['Project: config-as-json',
                   'Output file: reports/tasks.json',
                   'Review state: DRAFT',
                   'Priority: MEDIUM (numeric value 5)'])
