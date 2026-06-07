#! /usr/local/bin/python3
"""Tests for the key-ordering validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from tempfile import TemporaryDirectory
from typing import cast
from pytest import CaptureFixture, MonkeyPatch
import example.e26_key_ordering_validator as e26_module
from example.cmd_line_handling import SetValues
from example.e26_key_ordering_validator import ExampleConfig26
from example.e26_key_ordering_validator import e26_key_ordering_print
from example.e26_key_ordering_validator import e26_key_ordering_set
from example.e26_key_ordering_validator import main as e26_main
from .helpers import ExampleProgramSpec
from .helpers import assert_print_validator_error
from .helpers import assert_rt_out
from .helpers import assert_set_validator_error
from .helpers import assert_write_command_output


E26_SPEC = ExampleProgramSpec(module=e26_module,
                              factory_name='ExampleConfig26',
                              config_factory=ExampleConfig26,
                              set_command=e26_key_ordering_set,
                              print_command=e26_key_ordering_print,
                              config_basename='key_ordering.cfg')


DEFAULT_STEPS = [
    {'step': 10, 'name': 'build'},
    {'step': 20, 'name': 'test', 'owner': 'qa'},
    {'step': 30, 'name': 'deploy', 'owner': 'ops'}
]
"""Normalized default release steps used by the e26 example."""


def test_e26_set_defaults(capsys: CaptureFixture[str]) -> None:
    """Write and read the default key-ordering example."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/key_ordering.cfg'
        e26_key_ordering_set({}, config_file)
        config = ExampleConfig26(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.release_steps == DEFAULT_STEPS


def test_e26_set_normalizes_steps(capsys: CaptureFixture[str]) -> None:
    """Sort release steps and remove duplicate step numbers."""
    set_values = cast(SetValues, {'release_steps': [
        {'step': 30, 'name': 'deploy'},
        {'step': 20, 'name': 'test'},
        {'step': 10, 'name': 'build'},
        {'step': 20, 'name': 'duplicate'}]})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/key_ordering.cfg'
        e26_key_ordering_set(set_values, config_file)
        config = ExampleConfig26(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.release_steps == [{'step': 10, 'name': 'build'},
                                    {'step': 20, 'name': 'test'},
                                    {'step': 30, 'name': 'deploy'}]


def test_e26_rejects_missing_step(capsys: CaptureFixture[str],
                                  monkeypatch: MonkeyPatch) -> None:
    """Reject a release step where the ordering key is absent."""
    assert_print_validator_error(capsys, monkeypatch, E26_SPEC, {
        'release_steps': [{'name': 'build'}]
    }, [
        "Mandatory key 'step' is missing",
        'release_steps[0]'])


def test_e26_rejects_non_int_step(capsys: CaptureFixture[str],
                                  monkeypatch: MonkeyPatch) -> None:
    """Reject a release step where the ordering key is not an int."""
    assert_print_validator_error(capsys, monkeypatch, E26_SPEC, {
        'release_steps': [{'step': '10', 'name': 'build'}]
    }, [
        'release_steps[0][step]',
        'not of type int'])


def test_e26_set_rejects_no_step(capsys: CaptureFixture[str],
                                 monkeypatch: MonkeyPatch) -> None:
    """Reject write-time overrides with missing ordering keys."""
    set_values = cast(SetValues, {
        'release_steps': [{'name': 'build'}]})
    assert_set_validator_error(capsys, monkeypatch, E26_SPEC, set_values, [
        "Mandatory key 'step' is missing",
        'release_steps[0]'])


def test_e26_main_round_trip(capsys: CaptureFixture[str]) -> None:
    """Round-trip the key-ordering example through the CLI."""
    assert_rt_out(
        capsys, e26_main, 'key_ordering.cfg',
        ['--release-steps',
         '[{"step":20,"name":"test"},{"step":10,"name":"build"}]'], [
             "Release steps: [{'name': 'build', 'step': 10}, "
             "{'name': 'test', 'step': 20}]",
             'Step 0: 10 build owned by unassigned',
             'Step 1: 20 test owned by unassigned'
        ])
