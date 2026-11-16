#! /usr/local/bin/python3
"""Tests for the editor defaults teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from io import StringIO
from tempfile import TemporaryDirectory
import pytest
from config_as_json import ConfigMissingKey, JsonPath
from example.cmd_line_handling import SetValues
from example.e43_editor_defaults import ExampleConfig43, e43_editor_print, \
    e43_editor_set
from example.e43_editor_defaults import main as e43_main
from .helpers import assert_rt_out, assert_write_command_output, \
    write_json_file

FULL_JSON: dict[str, object] = {
    'service_name': 'audit',
    'logging': {'level': 'DEBUG', 'file': 'audit.log'},
    'backends': [{'host': 'alpha', 'port': 9090}]}
"""JSON data that contains every value of the example."""


@pytest.mark.parametrize('set_values', [
    {},
    {'service_name': 'audit'},
    {'logging': {'level': 'DEBUG'}, 'backends': [{'host': 'alpha'}]}])
def test_e43_set_given_only(capsys: pytest.CaptureFixture[str],
                            set_values: SetValues) -> None:
    """Write exactly the given values, which makes an incomplete file."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/editor.cfg'
        e43_editor_set(set_values, config_file)
        with open(config_file, encoding='UTF-8') as file_obj:
            json_data = json.load(file_obj)
    assert_write_command_output(capsys, config_file)
    assert json_data == set_values


@pytest.mark.parametrize('json_data, expected', [
    ({}, ['Not in the file: backends, logging, service_name',
          'backends[0].host: localhost  (not in file)',
          'backends[0].port: 8080  (not in file)',
          'backends[1].host: backup  (not in file)',
          'backends[1].port: 8081  (not in file)',
          'logging.file: reporting.log  (not in file)',
          'logging.level: INFO  (not in file)',
          'service_name: reporting  (not in file)']),
    ({'logging': {'level': 'DEBUG'},
      'backends': [{'host': 'alpha', 'port': 9090}, {'host': 'beta'}]},
     ['Not in the file: backends[1].port, logging.file, service_name',
      'backends[0].host: alpha',
      'backends[0].port: 9090',
      'backends[1].host: beta',
      'backends[1].port: 8080  (not in file)',
      'logging.file: reporting.log  (not in file)',
      'logging.level: DEBUG',
      'service_name: reporting  (not in file)']),
    ({'service_name': 'audit', 'backends': []},
     ['Not in the file: logging',
      'logging.file: reporting.log  (not in file)',
      'logging.level: INFO  (not in file)',
      'service_name: audit']),
    (FULL_JSON, ['Not in the file: none',
                 'backends[0].host: alpha',
                 'backends[0].port: 9090',
                 'logging.file: audit.log',
                 'logging.level: DEBUG',
                 'service_name: audit'])])
def test_e43_print(capsys: pytest.CaptureFixture[str],
                   json_data: dict[str, object], expected: list[str]) -> None:
    """Print every value and mark those that the file did not contain."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/editor.cfg'
        write_json_file(config_file, json_data)
        e43_editor_print(config_file)
        out, err = capsys.readouterr()
    assert err == ''
    assert out.splitlines() == [f'Configuration read from {config_file}',
                                *expected]


@pytest.mark.parametrize('json_data, expected', [
    ({}, [('backends',), ('logging',), ('service_name',)]),
    ({'logging': {}, 'backends': [{}, {'host': 'beta'}]},
     [('backends', 0, 'host'), ('backends', 0, 'port'),
      ('backends', 1, 'port'), ('logging', 'file'), ('logging', 'level'),
      ('service_name',)]),
    (FULL_JSON, [])])
def test_e43_kept_paths(json_data: dict[str, object],
                        expected: list[JsonPath]) -> None:
    """Report the outermost absent key of every value kept."""
    config = ExampleConfig43()
    config.parse_json(json.dumps(json_data), ok_to_use_defaults=True)
    # The order of kept_value_paths() is not part of the contract.
    assert sorted(config.kept_value_paths(), key=str) == \
        sorted(expected, key=str)


def test_e43_member_in_place() -> None:
    """Read a nested member into the object that the parent holds."""
    config = ExampleConfig43()
    logging_before = config.logging
    config.parse_json('{"logging": {"level": "DEBUG"}}',
                      ok_to_use_defaults=True)
    assert config.logging is logging_before
    assert config.logging.file == 'reporting.log'
    assert config.logging.level == 'DEBUG'


def test_e43_list_from_class() -> None:
    """Build list elements anew, from the class defaults."""
    config = ExampleConfig43(
        from_json_data_text='{"backends": [{"host": "x"}, {"host": "y"}]}',
        ok_to_use_defaults=True)
    assert [(backend.host, backend.port) for backend in config.backends] \
        == [('x', 8080), ('y', 8080)]


def test_e43_strict_read() -> None:
    """Refuse an incomplete file when it is read strictly."""
    stderr_buffer = StringIO()
    with pytest.raises(ConfigMissingKey):
        _ = ExampleConfig43(from_json_data_text='{"service_name": "audit"}',
                            stderr_file=stderr_buffer)
    assert 'logging' in stderr_buffer.getvalue()


def test_e43_unknown_key(capsys: pytest.CaptureFixture[str]) -> None:
    """Refuse a key that no class declares, also with ok_to_use_defaults."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/editor.cfg'
        write_json_file(config_file, {'logging': {'levle': 'DEBUG'}})
        e43_editor_print(config_file)
        out, err = capsys.readouterr()
    assert out == ''
    assert err == 'Unexpected parameter logging.levle in JSON data\n'


def test_e43_round_trip(capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip an incomplete file through the command line."""
    assert_rt_out(
        capsys, e43_main, 'editor.cfg',
        ['--service-name', 'audit', '--backends', '[{"host": "alpha"}]'],
        ['Not in the file: backends[0].port, logging',
         'backends[0].host: alpha',
         'backends[0].port: 8080  (not in file)',
         'logging.file: reporting.log  (not in file)',
         'logging.level: INFO  (not in file)',
         'service_name: audit'])
