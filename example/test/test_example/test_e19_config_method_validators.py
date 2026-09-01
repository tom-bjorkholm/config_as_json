#! /usr/local/bin/python3
"""Tests for the config-method validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
from pytest import CaptureFixture, MonkeyPatch
import example.e19_config_method_validators as e19_module
from example.cmd_line_handling import SetValues
from example.e19_config_method_validators import ExampleConfig19
from example.e19_config_method_validators import \
    e19_config_method_validators_print
from example.e19_config_method_validators import \
    e19_config_method_validators_set
from example.e19_config_method_validators import main as e19_main
from .helpers import ExampleProgramSpec
from .helpers import assert_rt_out
from .helpers import assert_print_validator_error
from .helpers import assert_set_validator_error
from .helpers import assert_write_command_output


E19_SPEC = ExampleProgramSpec(module=e19_module,
                              factory_name='ExampleConfig19',
                              config_factory=ExampleConfig19,
                              set_command=e19_config_method_validators_set,
                              print_command=e19_config_method_validators_print,
                              config_basename='config_method_validators.cfg')


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e19_set_defaults(capsys: CaptureFixture[str]) -> None:
    """Write the default method-validator configuration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/config_method_validators.cfg'
        e19_config_method_validators_set({}, config_file)
        config = ExampleConfig19(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.region == 'eu-west'
    assert config.retry_count == 3
    assert config.endpoint == 'https://eu-west.example.invalid/jobs'
    assert json_data == {
        'region': 'eu-west',
        'retry_count': 3,
        'endpoint': 'https://eu-west.example.invalid/jobs'
    }


def test_e19_set_normalizes_region(capsys: CaptureFixture[str]) -> None:
    """Normalize a member with a method before built-in validation."""
    set_values: SetValues = {
        'region': ' US_EAST ',
        'retry_count': 5,
        'endpoint': 'https://us-east.example.invalid/jobs'
    }
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/config_method_validators.cfg'
        e19_config_method_validators_set(set_values, config_file)
        config = ExampleConfig19(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.region == 'us-east'
    assert config.retry_count == 5
    assert json_data['region'] == 'us-east'


def test_e19_set_rejects_retry_count(capsys: CaptureFixture[str],
                                     monkeypatch: MonkeyPatch) -> None:
    """Report validation-only method rejection when writing."""
    set_values: SetValues = {
        'region': 'eu-west',
        'retry_count': 0,
        'endpoint': 'https://eu-west.example.invalid/jobs'
    }
    messages = ['Method check_retry_count for retry_count returned False']
    assert_set_validator_error(capsys, monkeypatch, E19_SPEC, set_values,
                               messages)


def test_e19_print_rejects_endpoint_region(capsys: CaptureFixture[str],
                                           monkeypatch: MonkeyPatch) -> None:
    """Report whole-config method rejection when reading."""
    config_values: dict[str, object] = {
        'region': 'us-east',
        'retry_count': 3,
        'endpoint': 'https://eu-west.example.invalid/jobs'
    }
    messages = ['Method check_endpoint_matches_region returned False']
    assert_print_validator_error(capsys, monkeypatch, E19_SPEC, config_values,
                                 messages)


def test_e19_main_round_trip(capsys: CaptureFixture[str]) -> None:
    """Round-trip the method-validator example through the command line."""
    args = [
        '--region', 'US_EAST',
        '--retry-count', '4',
        '--endpoint', 'https://us-east.example.invalid/jobs']
    expected_lines = [
        'Region: us-east',
        'Retry count: 4',
        'Endpoint: https://us-east.example.invalid/jobs']
    assert_rt_out(capsys, e19_main, 'config_method_validators.cfg', args,
                  expected_lines)
