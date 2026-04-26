#! /usr/local/bin/python3
"""Tests for the dict-validator teaching examples."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
import example.e10_dict_basic_validators as e10_module
import example.e11_dict_for_each as e11_module
import example.e12_dict_for_each_ordering as e12_module
from example.cmd_line_handling import SetValues
from example.e10_dict_basic_validators import ExampleConfig10
from example.e10_dict_basic_validators import \
    e10_dict_basic_validators_print
from example.e10_dict_basic_validators import \
    e10_dict_basic_validators_set
from example.e10_dict_basic_validators import main as e10_main
from example.e11_dict_for_each import ExampleConfig11
from example.e11_dict_for_each import e11_dict_for_each_print
from example.e11_dict_for_each import e11_dict_for_each_set
from example.e11_dict_for_each import main as e11_main
from example.e12_dict_for_each_ordering import ExampleConfig12
from example.e12_dict_for_each_ordering import \
    e12_dict_for_each_ordering_print
from example.e12_dict_for_each_ordering import \
    e12_dict_for_each_ordering_set
from example.e12_dict_for_each_ordering import main as e12_main
from .helpers import ExampleProgramSpec
from .helpers import assert_main_round_trip_print_output
from .helpers import assert_print_command_reports_validator_error
from .helpers import assert_set_command_reports_validator_error
from .helpers import assert_write_command_output


E10_SPEC = ExampleProgramSpec(module=e10_module,
                              factory_name='ExampleConfig10',
                              config_factory=ExampleConfig10,
                              set_command=e10_dict_basic_validators_set,
                              print_command=e10_dict_basic_validators_print,
                              config_basename='dict_basic_validators.cfg')

E11_SPEC = ExampleProgramSpec(module=e11_module,
                              factory_name='ExampleConfig11',
                              config_factory=ExampleConfig11,
                              set_command=e11_dict_for_each_set,
                              print_command=e11_dict_for_each_print,
                              config_basename='dict_for_each.cfg')

E12_SPEC = ExampleProgramSpec(module=e12_module,
                              factory_name='ExampleConfig12',
                              config_factory=ExampleConfig12,
                              set_command=e12_dict_for_each_ordering_set,
                              print_command=e12_dict_for_each_ordering_print,
                              config_basename='dict_for_each_ordering.cfg')


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e10_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default dict configuration for the basic dict example."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_basic_validators.cfg'
        e10_dict_basic_validators_set({}, config_file)
        config = ExampleConfig10(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.feature_flags == {'logging': True, 'metrics': True}
    assert config.port_assignments == {'http': 80, 'https': 443}
    assert json_data == {
        'feature_flags': {'logging': True, 'metrics': True},
        'port_assignments': {'http': 80, 'https': 443}
    }


def test_e10_set_accepts_optional_keys_in_feature_flags(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Accept optional keys in addition to the mandatory ones."""
    set_values: SetValues = {
        'feature_flags': {'logging': True, 'metrics': False, 'debug': True}
    }
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_basic_validators.cfg'
        e10_dict_basic_validators_set(set_values, config_file)
        config = ExampleConfig10(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.feature_flags == {
        'logging': True, 'metrics': False, 'debug': True
    }


def test_e10_set_reports_missing_mandatory_feature_flag(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a feature flags dict that lacks a mandatory key."""
    assert_set_command_reports_validator_error(
        capsys,
        monkeypatch,
        E10_SPEC,
        {'feature_flags': {'logging': True}},
        ['feature_flags', "Mandatory key 'metrics'", 'missing']
    )


def test_e10_print_reports_unknown_feature_flag_key(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a feature flags dict that contains an unknown key."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E10_SPEC,
        {
            'feature_flags': {'logging': True, 'metrics': True,
                              'extra': True},
            'port_assignments': {'http': 80, 'https': 443}
        },
        ['feature_flags', "Unknown key 'extra'"]
    )


def test_e10_print_reports_unknown_port_assignment_key(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject extra keys in the exact-shape port_assignments dict."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E10_SPEC,
        {
            'feature_flags': {'logging': True, 'metrics': True},
            'port_assignments': {'http': 80, 'https': 443, 'ftp': 21}
        },
        ['port_assignments', "Unknown key 'ftp'"]
    )


def test_e10_main_round_trip_prints_dict_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the basic dict example through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e10_main,
        'dict_basic_validators.cfg',
        ['--feature-flags', 'logging=true', 'metrics=false', 'debug=true'],
        ["Feature flags: {'debug': True, 'logging': True, 'metrics': False}",
         "Port assignments: {'http': 80, 'https': 443}"]
    )


def test_e11_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default cache settings without overrides."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_for_each.cfg'
        e11_dict_for_each_set({}, config_file)
        config = ExampleConfig11(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.cache_settings == {
        'ttl_seconds': 300,
        'refresh_seconds': 60,
        'max_entries': 1000,
        'eviction_policy': 'lru'
    }
    assert json_data == {
        'cache_settings': {
            'ttl_seconds': 300,
            'refresh_seconds': 60,
            'max_entries': 1000,
            'eviction_policy': 'lru'
        }
    }


def test_e11_set_accepts_full_cache_settings_override(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Apply a full cache settings override that passes every rule."""
    set_values: SetValues = {
        'cache_settings': {
            'ttl_seconds': 60,
            'refresh_seconds': 30,
            'max_entries': 100,
            'eviction_policy': 'fifo'
        }
    }
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_for_each.cfg'
        e11_dict_for_each_set(set_values, config_file)
        config = ExampleConfig11(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.cache_settings == {
        'ttl_seconds': 60,
        'refresh_seconds': 30,
        'max_entries': 100,
        'eviction_policy': 'fifo'
    }


def test_e11_print_reports_value_below_minimum_seconds(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a value that is below the seconds-rule minimum."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E11_SPEC,
        {
            'cache_settings': {
                'ttl_seconds': 0,
                'refresh_seconds': 30,
                'max_entries': 100,
                'eviction_policy': 'lru'
            }
        },
        ['cache_settings[ttl_seconds]', 'less than minimum 1']
    )


def test_e11_print_reports_value_above_maximum_max_entries(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a max_entries value above the rule's maximum."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E11_SPEC,
        {
            'cache_settings': {
                'ttl_seconds': 60,
                'refresh_seconds': 30,
                'max_entries': 1000000,
                'eviction_policy': 'lru'
            }
        },
        ['cache_settings[max_entries]', 'greater than maximum 10000']
    )


def test_e11_print_reports_unknown_eviction_policy(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an eviction policy that is not in the allowed list."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E11_SPEC,
        {
            'cache_settings': {
                'ttl_seconds': 60,
                'refresh_seconds': 30,
                'max_entries': 100,
                'eviction_policy': 'random'
            }
        },
        ['cache_settings[eviction_policy]', 'lru', 'lfu', 'fifo']
    )


def test_e11_main_round_trip_prints_cache_settings(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the cache settings example through the command line."""
    json_override = (
        '{"ttl_seconds": 60, "refresh_seconds": 30, '
        '"max_entries": 100, "eviction_policy": "fifo"}'
    )
    assert_main_round_trip_print_output(
        capsys,
        e11_main,
        'dict_for_each.cfg',
        ['--cache-settings', json_override],
        ["Cache settings: {'eviction_policy': 'fifo', 'max_entries': 100,"
         " 'refresh_seconds': 30, 'ttl_seconds': 60}",
         'Time-to-live: 60 seconds',
         'Eviction policy: fifo']
    )


def test_e12_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default canonical team tags without overrides."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_for_each_ordering.cfg'
        e12_dict_for_each_ordering_set({}, config_file)
        config = ExampleConfig12(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.team_tags == {
        'region': 'Eu',
        'environment': 'Production',
        'team': 'Engineering'
    }
    assert json_data == {
        'team_tags': {
            'region': 'Eu',
            'environment': 'Production',
            'team': 'Engineering'
        }
    }


def test_e12_set_normalizes_case_through_rule_threading(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Show that Rule A's normalization is visible to Rules B and C."""
    set_values: SetValues = {
        'team_tags': {
            'region': 'us',
            'environment': 'staging',
            'team': 'MARKETING'
        }
    }
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/dict_for_each_ordering.cfg'
        e12_dict_for_each_ordering_set(set_values, config_file)
        config = ExampleConfig12(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.team_tags == {
        'region': 'Us',
        'environment': 'Staging',
        'team': 'Marketing'
    }
    assert json_data == {
        'team_tags': {
            'region': 'Us',
            'environment': 'Staging',
            'team': 'Marketing'
        }
    }


def test_e12_print_reports_region_outside_rule_b_subset(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a region that passes Rule A but not the narrower Rule B."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E12_SPEC,
        {
            'team_tags': {
                'region': 'As',
                'environment': 'Production',
                'team': 'Engineering'
            }
        },
        ['team_tags[region]', 'As', 'Eu', 'Us']
    )


def test_e12_print_reports_team_outside_rule_c_subset(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a team that passes Rule A but not the narrower Rule C."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E12_SPEC,
        {
            'team_tags': {
                'region': 'Eu',
                'environment': 'Production',
                'team': 'Test'
            }
        },
        ['team_tags[team]', 'Engineering', 'Marketing', 'Support']
    )


def test_e12_print_reports_value_outside_rule_a_canonical_set(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a value that is not in the canonical set Rule A allows."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E12_SPEC,
        {
            'team_tags': {
                'region': 'Antarctica',
                'environment': 'Production',
                'team': 'Engineering'
            }
        },
        ['team_tags[region]', 'Antarctica']
    )


def test_e12_main_round_trip_prints_normalized_team_tags(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the ordering example through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e12_main,
        'dict_for_each_ordering.cfg',
        ['--team-tags', 'region=eu', 'environment=production',
         'team=engineering'],
        ["Team tags: {'environment': 'Production', 'region': 'Eu',"
         " 'team': 'Engineering'}",
         'Region: Eu',
         'Environment: Production',
         'Team: Engineering']
    )
