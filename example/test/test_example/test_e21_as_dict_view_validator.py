#! /usr/local/bin/python3
"""Tests for the as-dict-view validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
from pytest import CaptureFixture, MonkeyPatch
import example.e21_as_dict_view_validator as e21_module
from example.cmd_line_handling import SetValues
from example.e21_as_dict_view_validator import ExampleConfig21, RetryPolicy
from example.e21_as_dict_view_validator import e21_as_dict_view_print
from example.e21_as_dict_view_validator import e21_as_dict_view_set
from example.e21_as_dict_view_validator import main as e21_main
from example.e21_as_dict_view_validator import retry_policy_object
from .helpers import ExampleProgramSpec
from .helpers import assert_print_validator_error
from .helpers import assert_rt_out
from .helpers import assert_set_validator_error
from .helpers import assert_write_command_output


E21_SPEC = ExampleProgramSpec(module=e21_module,
                              factory_name='ExampleConfig21',
                              config_factory=ExampleConfig21,
                              set_command=e21_as_dict_view_set,
                              print_command=e21_as_dict_view_print,
                              config_basename='as_dict_view_validator.cfg')


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e21_default_is_object() -> None:
    """The default configuration stores the runtime object form."""
    config = ExampleConfig21()
    policy = retry_policy_object(config.retry_policy)
    assert isinstance(config.retry_policy, RetryPolicy)
    assert policy.mode == 'fixed'
    assert policy.max_attempts == 3
    assert policy.backoff_seconds == 30


def test_e21_set_defaults(capsys: CaptureFixture[str]) -> None:
    """Write defaults through the dictionary representation."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/as_dict_view_validator.cfg'
        e21_as_dict_view_set({}, config_file)
        config = ExampleConfig21(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    policy = retry_policy_object(config.retry_policy)
    assert_write_command_output(capsys, config_file)
    assert isinstance(config.retry_policy, RetryPolicy)
    assert policy.mode == 'fixed'
    assert policy.max_attempts == 3
    assert policy.backoff_seconds == 30
    assert json_data == {
        'retry_policy': {
            'mode': 'fixed',
            'max_attempts': 3,
            'backoff_seconds': 30}}


def test_e21_set_dict_override(capsys: CaptureFixture[str]) -> None:
    """Accept and normalize the dictionary form before writing."""
    set_values: SetValues = {
        'retry_policy': {
            'mode': 'EXPONENTIAL',
            'max_attempts': 5,
            'backoff_seconds': 60}}
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/as_dict_view_validator.cfg'
        e21_as_dict_view_set(set_values, config_file)
        config = ExampleConfig21(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    policy = retry_policy_object(config.retry_policy)
    assert_write_command_output(capsys, config_file)
    assert policy.mode == 'exponential'
    assert policy.max_attempts == 5
    assert policy.backoff_seconds == 60
    assert json_data['retry_policy'] == {
        'mode': 'exponential',
        'max_attempts': 5,
        'backoff_seconds': 60}


def test_e21_set_rejects_attempts(capsys: CaptureFixture[str],
                                  monkeypatch: MonkeyPatch) -> None:
    """Reject invalid values while validating the dictionary form."""
    set_values: SetValues = {
        'retry_policy': {
            'mode': 'fixed',
            'max_attempts': 11,
            'backoff_seconds': 60}}
    assert_set_validator_error(capsys, monkeypatch, E21_SPEC, set_values, [
        'retry_policy[max_attempts]',
        'greater than maximum 10'])


def test_e21_print_rejects_mode(capsys: CaptureFixture[str],
                                monkeypatch: MonkeyPatch) -> None:
    """Reject invalid values after parsing JSON into the object form."""
    assert_print_validator_error(capsys, monkeypatch, E21_SPEC, {
        'retry_policy': {
            'mode': 'custom',
            'max_attempts': 5,
            'backoff_seconds': 60}
    }, ['retry_policy[mode]', 'fixed, exponential'])


def test_e21_print_rejects_extra(capsys: CaptureFixture[str],
                                 monkeypatch: MonkeyPatch) -> None:
    """Reject unknown keys after projecting the object back to a dict view."""
    assert_print_validator_error(capsys, monkeypatch, E21_SPEC, {
        'retry_policy': {
            'mode': 'fixed',
            'max_attempts': 5,
            'backoff_seconds': 60,
            'jitter': True}
    }, ["Unknown key 'jitter' in retry_policy"])


def test_e21_main_round_trip(capsys: CaptureFixture[str]) -> None:
    """Round-trip the as-dict-view example through the command line."""
    retry_policy = (
        '{"mode": "EXPONENTIAL", "max_attempts": 5, '
        '"backoff_seconds": 60}')
    assert_rt_out(
        capsys, e21_main, 'as_dict_view_validator.cfg',
        ['--retry-policy', retry_policy], [
            'Retry mode: exponential',
            'Max attempts: 5',
            'Backoff seconds: 60',
            'Runtime policy object: exponential, 5 attempts'
        ])
