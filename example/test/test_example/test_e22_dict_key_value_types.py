#! /usr/local/bin/python3
"""Tests for the dict key/value type teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
from pytest import CaptureFixture, MonkeyPatch
import example.e22_dict_key_value_types as e22_module
from example.cmd_line_handling import SetValues
from example.e22_dict_key_value_types import ExampleConfig22
from example.e22_dict_key_value_types import e22_dict_key_value_types_print
from example.e22_dict_key_value_types import e22_dict_key_value_types_set
from example.e22_dict_key_value_types import main as e22_main
from .helpers import ExampleProgramSpec
from .helpers import assert_print_validator_error
from .helpers import assert_rt_out
from .helpers import assert_set_validator_error
from .helpers import assert_write_command_output


E22_SPEC = ExampleProgramSpec(module=e22_module,
                              factory_name='ExampleConfig22',
                              config_factory=ExampleConfig22,
                              set_command=e22_dict_key_value_types_set,
                              print_command=e22_dict_key_value_types_print,
                              config_basename='dict_key_value_types.cfg')


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e22_set_defaults(capsys: CaptureFixture[str]) -> None:
    """Write and read the default uniform dict configuration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_key_value_types.cfg'
        e22_dict_key_value_types_set({}, config_file)
        config = ExampleConfig22(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.service_ports == {'http': 80, 'https': 443}
    assert config.sample_weights == {'fast': [0.2, 0.8],
                                     'balanced': [0.5, 0.5]}
    assert json_data == {
        'service_ports': {'http': 80, 'https': 443},
        'sample_weights': {'fast': [0.2, 0.8],
                           'balanced': [0.5, 0.5]}}


def test_e22_set_overrides(capsys: CaptureFixture[str]) -> None:
    """Accept open dict keys when the key and value types are uniform."""
    set_values = cast(SetValues, {
        'service_ports': {'http': 8080, 'metrics': 9090},
        'sample_weights': {'fast': [0.1, 0.9], 'safe': [0.5, 0.5]}})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_key_value_types.cfg'
        e22_dict_key_value_types_set(set_values, config_file)
        config = ExampleConfig22(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.service_ports == {'http': 8080, 'metrics': 9090}
    assert config.sample_weights == {'fast': [0.1, 0.9],
                                     'safe': [0.5, 0.5]}


def test_e22_set_rejects_bad_port(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Reject a write-time override with a non-int dict value."""
    set_values = cast(SetValues, {
        'service_ports': {'http': '8080'},
        'sample_weights': {'fast': [0.1, 0.9]}})
    assert_set_validator_error(capsys, monkeypatch, E22_SPEC, set_values, [
        'service_ports[http]',
        'not of type int'])


def test_e22_print_rejects_weight(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Reject a read-time sample_weights entry that is not a list."""
    assert_print_validator_error(capsys, monkeypatch, E22_SPEC, {
        'service_ports': {'http': 80},
        'sample_weights': {'fast': 0.5}
    }, [
        'sample_weights[fast]',
        'not of type list'])


def test_e22_print_bad_weight_item(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Reject a value inside one nested weights list."""
    assert_print_validator_error(capsys, monkeypatch, E22_SPEC, {
        'service_ports': {'http': 80},
        'sample_weights': {'fast': [0.1, 'bad']}
    }, [
        'sample_weights[fast]',
        'index 1',
        'not of type float'])


def test_e22_main_round_trip(capsys: CaptureFixture[str]) -> None:
    """Round-trip the dict key/value types example through the CLI."""
    weights_json = '{"fast": [0.1, 0.9], "safe": [0.4, 0.6]}'
    assert_rt_out(
        capsys, e22_main, 'dict_key_value_types.cfg',
        ['--service-ports', 'http=8080', 'metrics=9090',
         '--sample-weights', weights_json], [
             "Service ports: {'http': 8080, 'metrics': 9090}",
             "Sample weights: {'fast': [0.1, 0.9], "
             "'safe': [0.4, 0.6]}",
             'HTTP port: 8080',
             'Fast weights: [0.1, 0.9]'
        ])
