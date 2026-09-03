#! /usr/local/bin/python3
"""Tests for the nested member path teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from io import StringIO
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from config_as_json import InvalidConfiguration
import example.e42_nested_member_paths as e42_module
from example.cmd_line_handling import SetValues
from example.e42_nested_member_paths import BackendConfig, ExampleConfig42
from example.e42_nested_member_paths import e42_member_paths_print
from example.e42_nested_member_paths import e42_member_paths_set
from example.e42_nested_member_paths import main as e42_main
from .helpers import ExampleProgramSpec, assert_rt_out, \
    assert_set_validator_error, assert_write_command_output


E42_SPEC = ExampleProgramSpec(module=e42_module,
                              factory_name='ExampleConfig42',
                              config_factory=ExampleConfig42,
                              set_command=e42_member_paths_set,
                              print_command=e42_member_paths_print,
                              config_basename='nested_member_paths.cfg')

REFUSED_PORT = 99999
"""One port number that is above the highest port the example accepts."""


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def _config_json(port: int, backend_ports: list[int]) -> dict[str, object]:
    """Return JSON data for the example with the given port numbers."""
    backends = [{'host': f'host{index}', 'port': backend_port}
                for index, backend_port in enumerate(backend_ports)]
    return {'service_name': 'reporting', 'port': port, 'backends': backends}


def _assert_port_refused(json_data: dict[str, object], reported: str) -> None:
    """Assert that reading refuses one port and names it by ``reported``."""
    stderr_buffer = StringIO()
    with pytest.raises(InvalidConfiguration):
        _ = ExampleConfig42(from_json_text=json.dumps(json_data),
                            stderr_file=stderr_buffer)
    expected = (f'Invalid configuration: Value {REFUSED_PORT} for '
                f'{reported} is greater than maximum 65535.')
    assert stderr_buffer.getvalue().splitlines() == [expected]


@pytest.mark.parametrize('bad_index', [0, 1])
def test_e42_backend_path(bad_index: int) -> None:
    """Name the backend whose port is out of range by its whole path."""
    backend_ports = [80, 81]
    backend_ports[bad_index] = REFUSED_PORT
    _assert_port_refused(_config_json(443, backend_ports),
                         f'backends[{bad_index}].port')


def test_e42_top_level_path() -> None:
    """Name a top level member by its plain name and not by a path."""
    _assert_port_refused(_config_json(REFUSED_PORT, [80, 81]), 'port')


def test_e42_set_defaults(capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default configuration with its two nested backends."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/nested_member_paths.cfg'
        e42_member_paths_set({}, config_file)
        config = ExampleConfig42(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.service_name == 'reporting'
    assert config.port == 443
    assert isinstance(config.backends[1], BackendConfig)
    assert json_data == {
        'service_name': 'reporting',
        'port': 443,
        'backends': [{'host': 'localhost', 'port': 8080},
                     {'host': 'backup', 'port': 8081}]}


def test_e42_set_backends(capsys: pytest.CaptureFixture[str]) -> None:
    """Write a configuration with backends taken from the command line."""
    set_values = cast(SetValues, {'service_name': 'audit',
                                  'backends': {'alpha': 8080, 'beta': 9090}})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/nested_member_paths.cfg'
        e42_member_paths_set(set_values, config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert json_data == {
        'service_name': 'audit',
        'port': 443,
        'backends': [{'host': 'alpha', 'port': 8080},
                     {'host': 'beta', 'port': 9090}]}


def test_e42_write_time_path(capsys: pytest.CaptureFixture[str],
                             monkeypatch: pytest.MonkeyPatch) -> None:
    """Name the path of a refused backend port while writing a file."""
    set_values = cast(SetValues, {'backends': {'alpha': REFUSED_PORT}})
    assert_set_validator_error(capsys, monkeypatch, E42_SPEC, set_values,
                               ['backends[0].port',
                                'greater than maximum 65535'])


def test_e42_print_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Print a configuration and show the path of every nested value."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/nested_member_paths.cfg'
        e42_member_paths_set({}, config_file)
        _ = capsys.readouterr()
        e42_member_paths_print(config_file)
        out, err = capsys.readouterr()
    assert err == ''
    assert out.splitlines() == [
        f'Configuration read from {config_file}',
        'service_name: reporting',
        'port: 443',
        'backends[0].host: localhost',
        'backends[0].port: 8080',
        'backends[1].host: backup',
        'backends[1].port: 8081']


def test_e42_round_trip(capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the nested member path example through the CLI."""
    assert_rt_out(
        capsys, e42_main, 'nested_member_paths.cfg',
        ['--service-name', 'audit', '--port', '8443',
         '--backends', 'alpha=8080', 'beta=9090'],
        [
            'service_name: audit',
            'port: 8443',
            'backends[0].host: alpha',
            'backends[0].port: 8080',
            'backends[1].host: beta',
            'backends[1].port: 9090'
        ])
