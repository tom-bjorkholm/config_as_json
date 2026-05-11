#! /usr/local/bin/python3
"""Tests for the list-of-nested-configs teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from example.cmd_line_handling import SetValues
from example.e34_list_nested_configs import ExampleConfig34, \
    ReportOutputConfig, e34_list_nested_configs_print, \
    e34_list_nested_configs_set
from example.e34_list_nested_configs import main as e34_main
from .helpers import assert_rt_out, assert_write_command_output


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e34_set_writes_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Write a default configuration with two nested list elements."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_nested_configs.cfg'
        e34_list_nested_configs_set({}, config_file)
        config = ExampleConfig34(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.course_name == 'python-intro'
    assert len(config.reports) == 2
    assert isinstance(config.reports[0], ReportOutputConfig)
    assert json_data == {
        'course_name': 'python-intro',
        'reports': [{
            'encoding': 'utf-8',
            'file_name': 'participants.csv',
            'name': 'participants',
            'output_format': 'CSV'
        }, {
            'encoding': 'utf-8',
            'file_name': 'audit.csv',
            'name': 'audit',
            'output_format': 'CSV'
        }]
    }


def test_e34_set_writes_reports(capsys: pytest.CaptureFixture[str]) -> None:
    """Write an explicit list of nested report configurations."""
    set_values = cast(SetValues, {
        'course_name': 'advanced-python',
        'reports': [{
            'name': 'summary',
            'file_name': 'summary.txt',
            'output_format': 'txt',
            'encoding': 'utf-8'
        }, {
            'name': 'audit',
            'file_name': 'audit.csv',
            'output_format': 'csv',
            'encoding': 'utf-8-sig'
        }]
    })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_nested_configs.cfg'
        e34_list_nested_configs_set(set_values, config_file)
        config = ExampleConfig34(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.course_name == 'advanced-python'
    assert config.reports[0].output_format == 'TXT'
    assert config.reports[1].encoding == 'utf-8-sig'
    assert json_data == {
        'course_name': 'advanced-python',
        'reports': [{
            'encoding': 'utf-8',
            'file_name': 'summary.txt',
            'name': 'summary',
            'output_format': 'TXT'
        }, {
            'encoding': 'utf-8-sig',
            'file_name': 'audit.csv',
            'name': 'audit',
            'output_format': 'CSV'
        }]
    }


def test_e34_reads_empty_report_list(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Read an explicit empty list of nested Config objects."""
    config = ExampleConfig34(
        from_json_text='{"course_name": "advanced-python", "reports": []}')
    json_data = json.loads(config.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert config.reports == []
    assert json_data == {
        'course_name': 'advanced-python',
        'reports': []
    }


def test_e34_print_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Print a configuration with the default report list."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_nested_configs.cfg'
        e34_list_nested_configs_set({}, config_file)
        _ = capsys.readouterr()
        e34_list_nested_configs_print(config_file)
        out, err = capsys.readouterr()
    assert err == ''
    assert out.splitlines() == [
        f'Configuration read from {config_file}',
        'Course name: python-intro',
        'Report count: 2',
        'Report 0 name: participants',
        'Report 0 file: participants.csv',
        'Report 0 format: CSV',
        'Report 0 encoding: utf-8',
        'Report 1 name: audit',
        'Report 1 file: audit.csv',
        'Report 1 format: CSV',
        'Report 1 encoding: utf-8']


def test_e34_main_with_reports(capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip a list of nested configs through the command line."""
    reports_json = (
        '[{"name": "summary", "file_name": "summary.txt", '
        '"output_format": "txt", "encoding": "utf-8"}, '
        '{"name": "audit", "file_name": "audit.csv", '
        '"output_format": "csv", "encoding": "utf-8-sig"}]')
    assert_rt_out(
        capsys, e34_main, 'list_nested_configs.cfg',
        ['--course-name', 'advanced-python', '--reports', reports_json],
        [
            'Course name: advanced-python',
            'Report count: 2',
            'Report 0 name: summary',
            'Report 0 file: summary.txt',
            'Report 0 format: TXT',
            'Report 0 encoding: utf-8',
            'Report 1 name: audit',
            'Report 1 file: audit.csv',
            'Report 1 format: CSV',
            'Report 1 encoding: utf-8-sig'
        ])
