#! /usr/local/bin/python3
"""Tests for the dict-by-key nested-config teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from example.cmd_line_handling import SetValues
from example.e34_list_nested_configs import ReportOutputConfig
from example.e36_dict_by_key_nested_configs import ExampleConfig36, \
    WebhookOutputConfig, e36_dict_by_key_print, e36_dict_by_key_set
from example.e36_dict_by_key_nested_configs import main as e36_main
from .helpers import assert_rt_out, assert_write_command_output, \
    config_json_data


def read_config_json(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def _participants(config: ExampleConfig36) -> ReportOutputConfig:
    """Return the participant report with its precise type."""
    return cast(ReportOutputConfig, config.reports_by_key['participants'])


def _audit(config: ExampleConfig36) -> WebhookOutputConfig:
    """Return the audit webhook with its precise type."""
    return cast(WebhookOutputConfig, config.reports_by_key['audit'])


def _participant_json(name: str, file_name: str,
                      output_format: str) -> dict[str, object]:
    """Return expected JSON data for the participant report."""
    return {
        'name': name,
        'file_name': file_name,
        'output_format': output_format,
        'encoding': 'utf-8'
    }


def _audit_json(url: str, method: str,
                timeout_seconds: int) -> dict[str, object]:
    """Return expected JSON data for the audit webhook."""
    return {
        'url': url,
        'method': method,
        'timeout_seconds': timeout_seconds
    }


def _print_default_config(
        capsys: pytest.CaptureFixture[str]) -> tuple[str, list[str], str]:
    """Write, print, and return the default e36 output."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_by_key_nested_configs.cfg'
        e36_dict_by_key_set({}, config_file)
        _ = capsys.readouterr()
        e36_dict_by_key_print(config_file)
        out, err = capsys.readouterr()
    return config_file, out.splitlines(), err


def test_e36_set_writes_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Write a default configuration with two keyed nested values."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_by_key_nested_configs.cfg'
        e36_dict_by_key_set({}, config_file)
        config = ExampleConfig36(from_json_filename=config_file)
        json_data = read_config_json(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.course_name == 'python-intro'
    assert isinstance(_participants(config), ReportOutputConfig)
    assert isinstance(_audit(config), WebhookOutputConfig)
    assert _audit(config).created_by_factory()
    assert json_data == {
        'course_name': 'python-intro',
        'reports_by_key': {
            'audit': _audit_json('https://example.invalid/audit', 'POST', 30),
            'max_attempts': 3,
            'owner': 'training-team',
            'participants': _participant_json(name='participants',
                                              file_name='participants.csv',
                                              output_format='CSV')
        }
    }


def test_e36_set_writes_reports(capsys: pytest.CaptureFixture[str]) -> None:
    """Write explicit keyed nested values and plain JSON values."""
    set_values = cast(SetValues, {
        'course_name': 'advanced-python',
        'reports_by_key': {
            'participants': _participant_json(name='summary',
                                              file_name='summary.txt',
                                              output_format='txt'),
            'audit': _audit_json('https://example.invalid/hooks/audit', 'put',
                                 45),
            'owner': 'ops',
            'max_attempts': 5,
            'labels': {'team': 'data'}
        }
    })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_by_key_nested_configs.cfg'
        e36_dict_by_key_set(set_values, config_file)
        config = ExampleConfig36(from_json_filename=config_file)
        json_data = read_config_json(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.course_name == 'advanced-python'
    assert _participants(config).output_format == 'TXT'
    assert _audit(config).method == 'PUT'
    assert _audit(config).created_by_factory()
    assert config.reports_by_key['labels'] == {'team': 'data'}
    assert json_data == {
        'course_name': 'advanced-python',
        'reports_by_key': {
            'audit': _audit_json('https://example.invalid/hooks/audit', 'PUT',
                                 45),
            'labels': {'team': 'data'},
            'max_attempts': 5,
            'owner': 'ops',
            'participants': _participant_json(name='summary',
                                              file_name='summary.txt',
                                              output_format='TXT')
        }
    }


def test_e36_reads_only_plain_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Read a dict where no configured nested keys are present."""
    config = ExampleConfig36(
        from_json_text='{"course_name": "advanced-python", '
        '"reports_by_key": {"owner": "ops", "limits": {"retries": 2}}}')
    json_data = config_json_data(config)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert config.reports_by_key == {
        'owner': 'ops',
        'limits': {'retries': 2}
    }
    assert json_data == {
        'course_name': 'advanced-python',
        'reports_by_key': {
            'limits': {'retries': 2},
            'owner': 'ops'
        }
    }


def test_e36_print_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Print a configuration with keyed nested values."""
    config_file, printed_lines, err = _print_default_config(capsys)
    assert err == ''
    assert printed_lines == [
        f'Configuration read from {config_file}',
        'Course name: python-intro',
        'Dictionary entry count: 4',
        'Audit webhook URL: https://example.invalid/audit',
        'Audit webhook method: POST',
        'Audit webhook timeout: 30',
        'Audit webhook created by factory: yes',
        'Plain value max_attempts: 3',
        'Plain value owner: "training-team"',
        'Participants report name: participants',
        'Participants report file: participants.csv',
        'Participants report format: CSV',
        'Participants report encoding: utf-8']


def test_e36_main_with_reports(capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip keyed nested configs through the command line."""
    reports_json = (
        '{"participants": {"name": "summary", '
        '"file_name": "summary.txt", "output_format": "txt", '
        '"encoding": "utf-8"}, '
        '"audit": {"url": "https://example.invalid/hooks/audit", '
        '"method": "put", "timeout_seconds": 45}, '
        '"owner": "ops", "max_attempts": 5}')
    assert_rt_out(
        capsys, e36_main, 'dict_by_key_nested_configs.cfg',
        ['--course-name', 'advanced-python',
         '--reports-by-key', reports_json],
        [
            'Course name: advanced-python',
            'Dictionary entry count: 4',
            'Audit webhook URL: https://example.invalid/hooks/audit',
            'Audit webhook method: PUT',
            'Audit webhook timeout: 45',
            'Audit webhook created by factory: yes',
            'Plain value max_attempts: 5',
            'Plain value owner: "ops"',
            'Participants report name: summary',
            'Participants report file: summary.txt',
            'Participants report format: TXT',
            'Participants report encoding: utf-8'
        ])
