#! /usr/local/bin/python3
"""Tests for the dict-of-nested-configs teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from example.cmd_line_handling import SetValues
from example.e34_list_nested_configs import ReportOutputConfig
from example.e35_dict_nested_configs import ExampleConfig35, \
    e35_dict_nested_configs_print, e35_dict_nested_configs_set
from example.e35_dict_nested_configs import main as e35_main
from .helpers import assert_rt_out, assert_write_command_output, \
    config_json_data


def read_config_json(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e35_set_writes_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Write a default configuration with two nested dict values."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_nested_configs.cfg'
        e35_dict_nested_configs_set({}, config_file)
        config = ExampleConfig35(from_json_filename=config_file)
        json_data = read_config_json(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.course_name == 'python-intro'
    assert sorted(config.reports_by_id) == ['audit', 'participants']
    assert isinstance(config.reports_by_id['audit'], ReportOutputConfig)
    assert json_data == {
        'course_name': 'python-intro',
        'reports_by_id': {
            'audit': {
                'encoding': 'utf-8',
                'file_name': 'audit.csv',
                'name': 'audit',
                'output_format': 'CSV'
            },
            'participants': {
                'encoding': 'utf-8',
                'file_name': 'participants.csv',
                'name': 'participants',
                'output_format': 'CSV'
            }
        }
    }


def test_e35_set_writes_reports(capsys: pytest.CaptureFixture[str]) -> None:
    """Write an explicit dict of nested report configurations."""
    set_values = cast(SetValues, {
        'course_name': 'advanced-python',
        'reports_by_id': {
            'summary': {
                'name': 'summary',
                'file_name': 'summary.txt',
                'output_format': 'txt',
                'encoding': 'utf-8'
            },
            'audit': {
                'name': 'audit',
                'file_name': 'audit.csv',
                'output_format': 'csv',
                'encoding': 'utf-8-sig'
            }
        }
    })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_nested_configs.cfg'
        e35_dict_nested_configs_set(set_values, config_file)
        config = ExampleConfig35(from_json_filename=config_file)
        json_data = read_config_json(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.course_name == 'advanced-python'
    assert config.reports_by_id['summary'].output_format == 'TXT'
    assert config.reports_by_id['audit'].encoding == 'utf-8-sig'
    assert json_data == {
        'course_name': 'advanced-python',
        'reports_by_id': {
            'audit': {
                'encoding': 'utf-8-sig',
                'file_name': 'audit.csv',
                'name': 'audit',
                'output_format': 'CSV'
            },
            'summary': {
                'encoding': 'utf-8',
                'file_name': 'summary.txt',
                'name': 'summary',
                'output_format': 'TXT'
            }
        }
    }


def test_e35_reads_empty_report_dict(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Read an explicit empty dict of nested Config objects."""
    config = ExampleConfig35(
        from_json_text='{"course_name": "advanced-python", '
        '"reports_by_id": {}}')
    json_data = config_json_data(config)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert not config.reports_by_id
    assert json_data == {
        'course_name': 'advanced-python',
        'reports_by_id': {}
    }


def test_e35_print_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Print a configuration with the default report dictionary."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_nested_configs.cfg'
        e35_dict_nested_configs_set({}, config_file)
        _ = capsys.readouterr()
        e35_dict_nested_configs_print(config_file)
        out, err = capsys.readouterr()
    expected_lines = [
        f'Configuration read from {config_file}', 'Course name: python-intro',
        'Report count: 2', 'Report audit name: audit',
        'Report audit file: audit.csv', 'Report audit format: CSV',
        'Report audit encoding: utf-8',
        'Report participants name: participants',
        'Report participants file: participants.csv',
        'Report participants format: CSV',
        'Report participants encoding: utf-8']
    printed_lines = out.rstrip('\n').split('\n')
    assert err == ''
    assert printed_lines == expected_lines


def test_e35_main_with_reports(capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip a dict of nested configs through the command line."""
    reports_json = (
        '{"summary": {"name": "summary", "file_name": "summary.txt", '
        '"output_format": "txt", "encoding": "utf-8"}, '
        '"audit": {"name": "audit", "file_name": "audit.csv", '
        '"output_format": "csv", "encoding": "utf-8-sig"}}')
    assert_rt_out(
        capsys, e35_main, 'dict_nested_configs.cfg',
        ['--course-name', 'advanced-python',
         '--reports-by-id', reports_json],
        [
            'Course name: advanced-python',
            'Report count: 2',
            'Report audit name: audit',
            'Report audit file: audit.csv',
            'Report audit format: CSV',
            'Report audit encoding: utf-8-sig',
            'Report summary name: summary',
            'Report summary file: summary.txt',
            'Report summary format: TXT',
            'Report summary encoding: utf-8'
        ])
