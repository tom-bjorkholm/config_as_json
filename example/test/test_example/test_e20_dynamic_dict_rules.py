#! /usr/local/bin/python3
"""Tests for the dynamic dict-rule teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
from pytest import CaptureFixture, MonkeyPatch
import example.e20_dynamic_dict_rules as e20_module
from example.cmd_line_handling import SetValues
from example.e20_dynamic_dict_rules import ExampleConfig20
from example.e20_dynamic_dict_rules import e20_dynamic_dict_rules_print
from example.e20_dynamic_dict_rules import e20_dynamic_dict_rules_set
from example.e20_dynamic_dict_rules import main as e20_main
from .helpers import ExampleProgramSpec
from .helpers import assert_rt_out
from .helpers import assert_print_validator_error
from .helpers import assert_write_command_output

E20_SPEC = ExampleProgramSpec(module=e20_module,
                              factory_name='ExampleConfig20',
                              config_factory=ExampleConfig20,
                              set_command=e20_dynamic_dict_rules_set,
                              print_command=e20_dynamic_dict_rules_print,
                              config_basename='dynamic_dict_rules.cfg')


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e20_set_uses_defaults(capsys: CaptureFixture[str]) -> None:
    """Write the default dynamic-dict configuration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dynamic_dict_rules.cfg'
        e20_dynamic_dict_rules_set({}, config_file)
        config = ExampleConfig20(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.cache_tunables == {
        'frontend_seconds': 60,
        'backend_seconds': 120,
        'image_slots': 4,
        'note': 'development defaults'}
    assert config.pool_sizes == {'default': 2, 'analytics': 4}
    assert json_data == {
        'cache_tunables': {'backend_seconds': 120, 'frontend_seconds': 60,
                           'image_slots': 4, 'note': 'development defaults'},
        'pool_sizes': {'analytics': 4, 'default': 2}}


def test_e20_set_accepts_open_dict_overrides(
        capsys: CaptureFixture[str]) -> None:
    """Apply valid open-dict overrides with user-defined keys."""
    set_values: SetValues = {
        'cache_tunables': {'frontend_seconds': 30, 'plugin_seconds': 300,
                           'image_slots': 8, 'note': 'platform'},
        'pool_sizes': {'default': 1, 'analytics': 8, 'adhoc': 4}}
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dynamic_dict_rules.cfg'
        e20_dynamic_dict_rules_set(set_values, config_file)
        config = ExampleConfig20(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.cache_tunables == set_values['cache_tunables']
    assert config.pool_sizes == set_values['pool_sizes']


def test_e20_print_rejects_seconds_below_minimum(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Predicate-selected seconds keys are checked as integer seconds."""
    assert_print_validator_error(
        capsys, monkeypatch, E20_SPEC, {
            'cache_tunables': {
                'frontend_seconds': 0,
                'image_slots': 4,
                'note': 'too small'
            },
            'pool_sizes': {
                'default': 2
            }
        }, [
            'cache_tunables[frontend_seconds]',
            'less than minimum 1',
        ])


def test_e20_print_rejects_slot_count_not_allowed(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Predicate-selected slot keys use dynamic numeric allowed values."""
    assert_print_validator_error(
        capsys, monkeypatch, E20_SPEC, {
            'cache_tunables': {
                'frontend_seconds': 30,
                'image_slots': 3,
                'note': 'unsupported slot count'
            },
            'pool_sizes': {
                'default': 2
            }
        }, ['cache_tunables[image_slots]', '1, 2, 4, 8'])


def test_e20_print_rejects_pool_size_not_allowed(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """The accept-all rule validates every pool-size value."""
    assert_print_validator_error(
        capsys, monkeypatch, E20_SPEC, {
            'cache_tunables': {
                'frontend_seconds': 30,
                'image_slots': 4,
                'note': 'valid'
            },
            'pool_sizes': {
                'default': 3
            }
        }, ['pool_sizes[default]', '1, 2, 4, 8'])


def test_e20_main_round_trip_prints_dynamic_dicts(
        capsys: CaptureFixture[str]) -> None:
    """Round-trip the dynamic dict-rule example through the CLI."""
    cache_tunables = (
        '{"frontend_seconds": 30, "image_slots": 8, "note": "fast"}')
    pool_sizes = '{"default": 4, "analytics": 8}'
    assert_rt_out(
        capsys, e20_main, 'dynamic_dict_rules.cfg',
        ['--cache-tunables', cache_tunables, '--pool-sizes', pool_sizes], [
            "Cache tunables: {'frontend_seconds': 30, 'image_slots': 8,"
            " 'note': 'fast'}", "Pool sizes: {'analytics': 8, 'default': 4}",
            'Frontend seconds: 30', 'Default pool size: 4'
        ])
