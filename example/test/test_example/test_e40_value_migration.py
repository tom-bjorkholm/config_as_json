#! /usr/local/bin/python3
"""Tests for the value-migration teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from example.e40_value_migration import CURRENT_FORMAT_VERSION, \
    Example40MigrateWarnHook, ExampleConfig40, e40_migrate_config, \
    e40_print_config, e40_write_new_config, e40_write_old_config
from example.e40_value_migration import main as e40_main


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def current_json(report_name: str, detail: bool,
                 retention_days: int) -> dict[str, object]:
    """Return the expected current JSON shape for e40 tests."""
    return {
        'format_version': CURRENT_FORMAT_VERSION,
        'report_name': report_name,
        'reports': {'detail': {'enabled': detail},
                    'summary': {'enabled': not detail}},
        'retention': {'max_days': retention_days,
                      'min_days': retention_days // 2}
    }


def assert_detail_print(out: str, config_file: str) -> None:
    """Assert printed values for a migrated detail-report configuration."""
    for expected in [
            f'Configuration read from {config_file}',
            f'Format version: {CURRENT_FORMAT_VERSION}',
            'Report name: daily-summary',
            'Summary report: False',
            'Detail report: True',
            'Retention min days: 20',
            'Retention max days: 40']:
        assert expected + '\n' in out


def test_e40_write_old_shape(capsys: pytest.CaptureFixture[str]) -> None:
    """Write an old file with one routed and one split value."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e40_write_old_config(config_file=config_file, report_name='operations',
                             report_kind='detail', retention_days=40)
        json_data = read_json_data(config_file)
    out, err = capsys.readouterr()
    assert out == f'Old configuration written to {config_file}\n'
    assert err == ''
    assert json_data == {'report_kind': 'detail',
                         'report_name': 'operations',
                         'retention_days': 40}


def test_e40_write_new_shape(capsys: pytest.CaptureFixture[str]) -> None:
    """Write a current file with current nested values."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/current.cfg'
        e40_write_new_config(config_file=config_file, report_name='operations',
                             summary_enabled=False, detail_enabled=True,
                             retention_days=40)
        json_data = read_json_data(config_file)
    out, err = capsys.readouterr()
    assert out == f'Current configuration written to {config_file}\n'
    assert err == ''
    assert json_data == current_json(report_name='operations', detail=True,
                                     retention_days=40)


def test_e40_print_old_warns(capsys: pytest.CaptureFixture[str]) -> None:
    """Read an old file, print current values, and warn about migration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e40_write_old_config(config_file=config_file, report_kind='detail',
                             retention_days=40)
        _ = capsys.readouterr()
        e40_print_config(config_file)
        out, err = capsys.readouterr()
    assert_detail_print(out, config_file)
    assert err == Example40MigrateWarnHook.migrate_warn_msg()
    assert 'e40_value_migration migrate' in err


def test_e40_print_current_ok(capsys: pytest.CaptureFixture[str]) -> None:
    """Read a current file without a migration warning."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/current.cfg'
        e40_write_new_config(config_file=config_file)
        _ = capsys.readouterr()
        e40_print_config(config_file)
        out, err = capsys.readouterr()
    assert 'Summary report: True\n' in out
    assert 'Detail report: False\n' in out
    assert err == ''


def test_e40_config_reads_old(capsys: pytest.CaptureFixture[str]) -> None:
    """Create the current config object directly from an old JSON file."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e40_write_old_config(config_file=config_file, report_kind='summary',
                             retention_days=50)
        _ = capsys.readouterr()
        config = ExampleConfig40(from_json_filename=config_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert config.reports == {'detail': {'enabled': False},
                              'summary': {'enabled': True}}
    assert config.retention == {'max_days': 50, 'min_days': 25}


def test_e40_migrate_shape(capsys: pytest.CaptureFixture[str]) -> None:
    """Migrate an old file to the current JSON shape."""
    with TemporaryDirectory() as dirname:
        old_file = dirname + '/old.cfg'
        new_file = dirname + '/new.cfg'
        e40_write_old_config(config_file=old_file, report_kind='detail',
                             retention_days=40)
        _ = capsys.readouterr()
        e40_migrate_config(infile=old_file, outfile=new_file)
        json_data = read_json_data(new_file)
    out, err = capsys.readouterr()
    assert out == f'Configuration migrated to {new_file}\n'
    assert err == ''
    assert json_data == current_json(report_name='daily-summary', detail=True,
                                     retention_days=40)


def test_e40_main_migrate(capsys: pytest.CaptureFixture[str]) -> None:
    """Migrate an old file through the command-line entry point."""
    with TemporaryDirectory() as dirname:
        old_file = dirname + '/old.cfg'
        new_file = dirname + '/new.cfg'
        e40_main(['write-old', '--output', old_file,
                  '--report-kind', 'detail',
                  '--retention-days', '40'])
        _ = capsys.readouterr()
        e40_main(['migrate', '--input', old_file, '--output', new_file])
        json_data = read_json_data(new_file)
        out, err = capsys.readouterr()
    assert out == f'Configuration migrated to {new_file}\n'
    assert err == ''
    assert json_data['reports'] == {'detail': {'enabled': True},
                                    'summary': {'enabled': False}}
