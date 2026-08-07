#! /usr/local/bin/python3
"""Tests for the nested read-old-configuration teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from config_as_json import ConfigAutoChangeHook
from example.e37_read_old_nested_configuration_file import \
    CURRENT_FORMAT_VERSION, Example37MigrateWarnHook, ExampleConfig37, \
    OldOutputFormat, OutputFormat, e37_migrate_config, e37_print_config, \
    e37_write_new_config, e37_write_old_config
from example.e37_read_old_nested_configuration_file import main as e37_main
from .test_e31_read_old_configuration_file import \
    assert_migration_refused_existing_output


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def old_file_warning(kind_counts: list[str], supplied: list[str]) -> str:
    """Return the full stderr text expected when reading an old e37 file.

    Args:
        kind_counts: Expected ``count x KIND`` texts in sorted kind order.
        supplied: Expected ``path = value`` texts for supplied values.

    Returns:
        The complete expected stderr text.
    """
    lines = ['Old-file compatibility changed this configuration:']
    lines.extend(f'  {count}' for count in kind_counts)
    lines.extend(f'Value supplied by this application version: {text}'
                 for text in supplied)
    return Example37MigrateWarnHook.migrate_warn_msg() + \
        '\n'.join(lines) + '\n'


def old_file_with_output_warning() -> str:
    """Return the expected stderr for an old file that has an output."""
    return old_file_warning(
        kind_counts=['1 x KEY_PRUNED', '1 x KEY_RENAMED',
                     '1 x MISSING_VALUE_ADDED', '3 x PATH_MOVED'],
        supplied=['format_version = 2'])


def run_old_print_roundtrip(
        config_file: str,
        capsys: pytest.CaptureFixture[str]) -> tuple[str, str]:
    """Use the e37 command-line entry point for one old-file round-trip."""
    write_args = ['write-old', '--output', config_file,
                  '--course-title', 'operations',
                  '--default-format', 'plain',
                  '--output-format', 'plain',
                  '--output-name', 'audit']
    e37_main(write_args)
    _ = capsys.readouterr()
    e37_main(['print', '--input', config_file])
    return capsys.readouterr()


def test_e37_write_old_shape(capsys: pytest.CaptureFixture[str]) -> None:
    """Write an old file with an optional direct output object."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e37_write_old_config(config_file=config_file,
                             course_title='advanced-python',
                             default_format=OldOutputFormat.PLAIN_TEXT,
                             output_name='audit',
                             output_format=OldOutputFormat.PLAIN_TEXT,
                             output_encoding='latin-1',
                             output_file_name='audit.txt', debug_trace=True)
        json_data = read_json_data(config_file)
    out, err = capsys.readouterr()
    assert out == f'Old configuration written to {config_file}\n'
    assert err == ''
    assert json_data == {
        'course_title': 'advanced-python',
        'debug_trace': True,
        'default_format': 'PLAIN_TEXT',
        'output': {'encoding': 'latin-1',
                   'file_name': 'audit.txt',
                   'format': 'PLAIN_TEXT',
                   'name': 'audit'}
    }


def test_e37_old_omits_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Write an old file where the optional output object is absent."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e37_write_old_config(config_file=config_file, without_output=True)
        json_data = read_json_data(config_file)
    out, err = capsys.readouterr()
    assert out == f'Old configuration written to {config_file}\n'
    assert err == ''
    assert json_data == {'course_title': 'python-intro',
                         'debug_trace': False,
                         'default_format': 'COMMA_SEPARATED_VALUES'}


def test_e37_write_new_shape(capsys: pytest.CaptureFixture[str]) -> None:
    """Write a current file with a nested list of output objects."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/current.cfg'
        e37_write_new_config(config_file=config_file,
                             course_name='advanced-python',
                             default_output_format=OutputFormat.TXT,
                             output_name='audit',
                             output_format=OutputFormat.TXT,
                             output_encoding='latin-1',
                             output_file_name='audit.txt')
        json_data = read_json_data(config_file)
    out, err = capsys.readouterr()
    assert out == f'Current configuration written to {config_file}\n'
    assert err == ''
    assert json_data == {
        'course_name': 'advanced-python',
        'default_output_format': 'TXT',
        'format_version': CURRENT_FORMAT_VERSION,
        'outputs': [{'encoding': 'latin-1',
                     'file_name': 'audit.txt',
                     'name': 'audit',
                     'output_format': 'TXT'}]
    }


def test_e37_print_old_warns(capsys: pytest.CaptureFixture[str]) -> None:
    """Read an old nested file, print current values, and warn."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e37_write_old_config(config_file=config_file)
        _ = capsys.readouterr()
        e37_print_config(config_file)
        out, err = capsys.readouterr()
    assert out == '\n'.join([
        f'Configuration read from {config_file}',
        f'Format version: {CURRENT_FORMAT_VERSION}',
        'Course name: python-intro',
        'Default output format: CSV',
        'Output count: 1',
        'Output 0 name: participants',
        'Output 0 file: participants.csv',
        'Output 0 format: CSV',
        'Output 0 encoding: utf-8'
    ]) + '\n'
    assert err == old_file_with_output_warning()
    assert 'e37_read_old_nested_configuration_file migrate' in err


def test_e37_print_no_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Read an old file without output and get an empty current list."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e37_write_old_config(config_file=config_file, without_output=True)
        _ = capsys.readouterr()
        e37_print_config(config_file)
        out, err = capsys.readouterr()
    assert out == '\n'.join([
        f'Configuration read from {config_file}',
        f'Format version: {CURRENT_FORMAT_VERSION}',
        'Course name: python-intro',
        'Default output format: CSV',
        'Output count: 0'
    ]) + '\n'
    # Without an old output object the current empty ``outputs`` list is also
    # supplied, so one more missing value is recorded and one move less.
    assert err == old_file_warning(
        kind_counts=['1 x KEY_PRUNED', '1 x KEY_RENAMED',
                     '2 x MISSING_VALUE_ADDED', '1 x PATH_MOVED'],
        supplied=['format_version = 2', 'outputs = []'])


def test_e37_config_reads_old(capsys: pytest.CaptureFixture[str]) -> None:
    """Create the current config object directly from an old JSON file."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        e37_write_old_config(config_file=config_file, course_title='support',
                             default_format=OldOutputFormat.PLAIN_TEXT,
                             output_format=OldOutputFormat.PLAIN_TEXT)
        _ = capsys.readouterr()
        config = ExampleConfig37(from_json_filename=config_file,
                                 auto_ch_hook=ConfigAutoChangeHook())
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert isinstance(config, ExampleConfig37)
    assert config.format_version == CURRENT_FORMAT_VERSION
    assert config.course_name == 'support'
    assert config.default_output_format == OutputFormat.TXT
    assert len(config.outputs) == 1
    assert config.outputs[0].output_format == OutputFormat.TXT


def test_e37_migrate_shape(capsys: pytest.CaptureFixture[str]) -> None:
    """Migrate an old nested file to the current JSON shape."""
    with TemporaryDirectory() as dirname:
        old_file = dirname + '/old.cfg'
        new_file = dirname + '/new.cfg'
        e37_write_old_config(config_file=old_file, course_title='support',
                             default_format=OldOutputFormat.PLAIN_TEXT)
        _ = capsys.readouterr()
        e37_migrate_config(infile=old_file, outfile=new_file)
        json_data = read_json_data(new_file)
    out, err = capsys.readouterr()
    assert out == f'Configuration migrated to {new_file}\n'
    assert err == ''
    assert json_data == {
        'course_name': 'support',
        'default_output_format': 'TXT',
        'format_version': CURRENT_FORMAT_VERSION,
        'outputs': [{'encoding': 'utf-8',
                     'file_name': 'participants.csv',
                     'name': 'participants',
                     'output_format': 'CSV'}]
    }


def test_e37_migrate_no_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Migrate an old file without output to a current empty list."""
    with TemporaryDirectory() as dirname:
        old_file = dirname + '/old.cfg'
        new_file = dirname + '/new.cfg'
        e37_write_old_config(config_file=old_file, without_output=True)
        _ = capsys.readouterr()
        e37_migrate_config(infile=old_file, outfile=new_file)
        json_data = read_json_data(new_file)
    out, err = capsys.readouterr()
    assert out == f'Configuration migrated to {new_file}\n'
    assert err == ''
    assert json_data['outputs'] == []


def test_e37_migrate_refuses_output(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Refuse to overwrite an existing migration output file."""
    with TemporaryDirectory() as dirname:
        old_file = dirname + '/old.cfg'
        new_file = dirname + '/new.cfg'
        e37_write_old_config(config_file=old_file)
        e37_write_new_config(config_file=new_file)
        _ = capsys.readouterr()
        with pytest.raises(SystemExit):
            e37_migrate_config(infile=old_file, outfile=new_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert_migration_refused_existing_output(err)


def assert_e37_main_print(out: str, err: str) -> None:
    """Assert the e37 command-line old-file print output."""
    assert 'Course name: operations\n' in out
    assert 'Default output format: TXT\n' in out
    assert 'Output 0 name: audit\n' in out
    assert 'Output 0 format: TXT\n' in out
    assert err == old_file_with_output_warning()


def test_e37_main_old_print(capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip an old nested file through the command-line entry point."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/old.cfg'
        out, err = run_old_print_roundtrip(config_file, capsys)
    assert_e37_main_print(out, err)


def test_e37_main_migrate(capsys: pytest.CaptureFixture[str]) -> None:
    """Migrate an old nested file through the command-line entry point."""
    with TemporaryDirectory() as dirname:
        old_file = dirname + '/old.cfg'
        new_file = dirname + '/new.cfg'
        e37_main(['write-old', '--output', old_file])
        _ = capsys.readouterr()
        e37_main(['migrate', '--input', old_file, '--output', new_file])
        json_data = read_json_data(new_file)
        out, err = capsys.readouterr()
    assert out == f'Configuration migrated to {new_file}\n'
    assert err == ''
    assert 'course_title' not in json_data
    assert 'default_format' not in json_data
    assert 'debug_trace' not in json_data
    assert json_data['course_name'] == 'python-intro'
