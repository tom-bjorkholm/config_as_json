#! /usr/local/bin/python3
"""Tests for the nested-config teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from example.cmd_line_handling import SetValues
from example.e33_nested_configs import ExampleConfig33, TableOutputConfig, \
    e33_nested_configs_print, e33_nested_configs_set
from example.e33_nested_configs import main as e33_main
from .helpers import assert_rt_out, assert_write_command_output


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e33_set_writes_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Write a default configuration with only the mandatory nested member."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/nested_configs.cfg'
        e33_nested_configs_set({}, config_file)
        config = ExampleConfig33(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.course_name == 'python-intro'
    assert isinstance(config.participant_output, TableOutputConfig)
    assert config.audit_output is None
    assert json_data == {
        'course_name': 'python-intro',
        'participant_output': {
            'encoding': 'utf-8',
            'file_name': 'participants.csv',
            'output_format': 'CSV'
        }
    }


def test_e33_set_writes_audit(capsys: pytest.CaptureFixture[str]) -> None:
    """Write both mandatory and optional nested configuration sections."""
    set_values = cast(SetValues, {
        'course_name': 'advanced-python',
        'participant_file_name': 'participants.txt',
        'participant_output_format': 'txt',
        'audit_file_name': 'audit.txt',
        'audit_output_format': 'txt',
        'audit_encoding': 'utf-8-sig'
    })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/nested_configs.cfg'
        e33_nested_configs_set(set_values, config_file)
        config = ExampleConfig33(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.course_name == 'advanced-python'
    assert config.participant_output.file_name == 'participants.txt'
    assert config.participant_output.output_format == 'TXT'
    assert config.audit_output is not None
    assert config.audit_output.file_name == 'audit.txt'
    assert config.audit_output.output_format == 'TXT'
    assert config.audit_output.encoding == 'utf-8-sig'
    assert json_data == {
        'audit_output': {
            'encoding': 'utf-8-sig',
            'file_name': 'audit.txt',
            'output_format': 'TXT'
        },
        'course_name': 'advanced-python',
        'participant_output': {
            'encoding': 'utf-8',
            'file_name': 'participants.txt',
            'output_format': 'TXT'
        }
    }


def test_e33_reads_null_audit(capsys: pytest.CaptureFixture[str]) -> None:
    """Read JSON null as None for the optional nested configuration."""
    config = ExampleConfig33(
        from_json_text='{"audit_output": null, '
        '"course_name": "advanced-python", '
        '"participant_output": {"encoding": "utf-8", '
        '"file_name": "participants.txt", "output_format": "txt"}}')
    json_data = json.loads(config.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert config.audit_output is None
    assert config.participant_output.output_format == 'TXT'
    assert json_data == {
        'course_name': 'advanced-python',
        'participant_output': {
            'encoding': 'utf-8',
            'file_name': 'participants.txt',
            'output_format': 'TXT'
        }
    }


def test_e33_print_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Print a configuration without an optional audit output."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/nested_configs.cfg'
        e33_nested_configs_set({}, config_file)
        _ = capsys.readouterr()
        e33_nested_configs_print(config_file)
        out, err = capsys.readouterr()
    assert err == ''
    assert out == '\n'.join([
        f'Configuration read from {config_file}',
        'Course name: python-intro',
        'Participant output file: participants.csv',
        'Participant output format: CSV',
        'Participant output encoding: utf-8',
        'Audit output: not configured'
    ]) + '\n'


def test_e33_main_with_audit(capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip nested configuration through the command line."""
    assert_rt_out(
        capsys, e33_main, 'nested_configs.cfg',
        ['--course-name', 'advanced-python',
         '--participant-file-name', 'participants.txt',
         '--participant-output-format', 'txt',
         '--audit-file-name', 'audit.txt',
         '--audit-output-format', 'txt'],
        [
            'Course name: advanced-python',
            'Participant output file: participants.txt',
            'Participant output format: TXT',
            'Participant output encoding: utf-8',
            'Audit output file: audit.txt',
            'Audit output format: TXT',
            'Audit output encoding: utf-8',
        ])
