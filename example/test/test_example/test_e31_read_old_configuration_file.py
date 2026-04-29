#! /usr/local/bin/python3
"""Tests for the read-old-configuration-file teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from config_as_json import ConfigAutoChangeHook
from example.e31_read_old_configuration_file import CURRENT_FORMAT_VERSION, \
    Example31MigrateWarnHook, ExampleConfig31, OutputFormat, \
    e31_migrate_config, e31_print_config, \
    e31_write_new_config, e31_write_old_config
from example.e31_read_old_configuration_file import main as e31_main


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def assert_migration_refused_existing_output(err: str) -> None:
    """Assert the standard message for refusing migration overwrite."""
    expected_fragments = [
        'Output configuration file',
        'already exists.',
        'Cowardly refusing to overwrite existing configuration file'
    ]
    for fragment in expected_fragments:
        assert fragment in err


def test_e31_write_old_creates_old_shape(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write an old file with old key names and no current-only keys."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e31_write_old_config(
            config_file=config_file,
            title='operations',
            output_format=OutputFormat.TEXT,
            refresh_interval=120)
        json_data = read_json_data(config_file)
    out, err = capsys.readouterr()
    assert out == f'Old configuration written to {config_file}\n'
    assert err == ''
    assert json_data == {'output_format': 'TEXT',
                         'refresh_interval': 120,
                         'title': 'operations'}


def test_e31_write_new_creates_current_shape(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write a current file with current key names."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/current.cfg'
        e31_write_new_config(
            config_file=config_file,
            report_name='operations',
            output_format=OutputFormat.TEXT,
            refresh_seconds=120,
            max_items=10)
        json_data = read_json_data(config_file)
    out, err = capsys.readouterr()
    assert out == f'Current configuration written to {config_file}\n'
    assert err == ''
    assert json_data == {'format_version': CURRENT_FORMAT_VERSION,
                         'max_items': 10,
                         'output_format': 'TEXT',
                         'refresh_seconds': 120,
                         'report_name': 'operations'}


def test_e31_print_reads_old_file_with_custom_warning(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Read an old file, print current values, and warn about migration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e31_write_old_config(config_file=config_file)
        _ = capsys.readouterr()
        e31_print_config(config_file)
        out, err = capsys.readouterr()
    assert out == '\n'.join([
        f'Configuration read from {config_file}',
        f'Format version: {CURRENT_FORMAT_VERSION}',
        'Report name: daily-summary',
        'Output format: HTML',
        'Refresh seconds: 300',
        'Max items: 25'
    ]) + '\n'
    assert err == Example31MigrateWarnHook.migrate_warn_msg()
    assert 'e31_read_old_configuration_file migrate' in err


def test_e31_print_reads_current_file_without_warning(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Read a current file without a migration warning."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/current.cfg'
        e31_write_new_config(config_file=config_file)
        _ = capsys.readouterr()
        e31_print_config(config_file)
        out, err = capsys.readouterr()
    assert out == '\n'.join([
        f'Configuration read from {config_file}',
        f'Format version: {CURRENT_FORMAT_VERSION}',
        'Report name: daily-summary',
        'Output format: HTML',
        'Refresh seconds: 300',
        'Max items: 25'
    ]) + '\n'
    assert err == ''


def test_e31_current_config_reads_old_file(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Create the current config object directly from an old JSON file."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e31_write_old_config(
            config_file=config_file,
            title='support',
            refresh_interval=900)
        _ = capsys.readouterr()
        config = ExampleConfig31(from_json_filename=config_file,
                                 auto_ch_hook=ConfigAutoChangeHook())
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert isinstance(config, ExampleConfig31)
    assert config.format_version == CURRENT_FORMAT_VERSION
    assert config.report_name == 'support'
    assert config.refresh_seconds == 900
    assert config.max_items == 25


def test_e31_migrate_writes_current_shape_without_warning(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Migrate an old file to the current JSON shape."""
    with TemporaryDirectory() as dirname:
        old_file = dirname + '/old.cfg'
        new_file = dirname + '/new.cfg'
        e31_write_old_config(
            config_file=old_file,
            title='support',
            output_format=OutputFormat.TEXT,
            refresh_interval=900)
        _ = capsys.readouterr()
        e31_migrate_config(infile=old_file, outfile=new_file)
        json_data = read_json_data(new_file)
    out, err = capsys.readouterr()
    assert out == f'Configuration migrated to {new_file}\n'
    assert err == ''
    assert json_data == {'format_version': CURRENT_FORMAT_VERSION,
                         'max_items': 25,
                         'output_format': 'TEXT',
                         'refresh_seconds': 900,
                         'report_name': 'support'}


def test_e31_migrate_refuses_existing_output(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Refuse to overwrite an existing migration output file."""
    with TemporaryDirectory() as dirname:
        old_file = dirname + '/old.cfg'
        new_file = dirname + '/new.cfg'
        e31_write_old_config(config_file=old_file)
        e31_write_new_config(config_file=new_file)
        _ = capsys.readouterr()
        with pytest.raises(SystemExit):
            e31_migrate_config(infile=old_file, outfile=new_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert_migration_refused_existing_output(err)


def test_e31_main_write_old_and_print(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip an old file through the command-line entry point."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e31_main(['write-old', '--output', config_file,
                  '--title', 'operations',
                  '--output-format', 'text',
                  '--refresh-interval', '120'])
        _ = capsys.readouterr()
        e31_main(['print', '--input', config_file])
        out, err = capsys.readouterr()
    assert 'Report name: operations\n' in out
    assert 'Output format: TEXT\n' in out
    assert 'Refresh seconds: 120\n' in out
    assert err == Example31MigrateWarnHook.migrate_warn_msg()


def test_e31_main_migrate(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Migrate an old file through the command-line entry point."""
    with TemporaryDirectory() as dirname:
        old_file = dirname + '/old.cfg'
        new_file = dirname + '/new.cfg'
        e31_main(['write-old', '--output', old_file])
        _ = capsys.readouterr()
        e31_main(['migrate', '--input', old_file, '--output', new_file])
        json_data = read_json_data(new_file)
        out, err = capsys.readouterr()
    assert out == f'Configuration migrated to {new_file}\n'
    assert err == ''
    assert 'title' not in json_data
    assert 'refresh_interval' not in json_data
    assert json_data['report_name'] == 'daily-summary'
