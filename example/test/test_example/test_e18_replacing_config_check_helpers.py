#! /usr/local/bin/python3
"""Tests for the old Config check helper replacement example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
import example.e18_replacing_config_check_helpers as e18_module
from example.cmd_line_handling import SetValues
from example.e18_replacing_config_check_helpers import ExampleConfig18
from example.e18_replacing_config_check_helpers import \
    e18_replacing_config_check_helpers_print
from example.e18_replacing_config_check_helpers import \
    e18_replacing_config_check_helpers_set
from example.e18_replacing_config_check_helpers import main as e18_main
from .helpers import ExampleProgramSpec
from .helpers import assert_main_round_trip_print_output
from .helpers import assert_print_command_reports_validator_error
from .helpers import assert_write_command_output


E18_SPEC = ExampleProgramSpec(
    module=e18_module,
    factory_name='ExampleConfig18',
    config_factory=ExampleConfig18,
    set_command=e18_replacing_config_check_helpers_set,
    print_command=e18_replacing_config_check_helpers_print,
    config_basename='replacing_config_check_helpers.cfg'
)


DEFAULT_DATA: dict[str, object] = {
    'column_mappings': [{'column': 'first_name', 'source': 'First Name'}],
    'merge_rules': [{'columns': ['first_name', 'last_name'],
                     'separator': ' '}],
    'rewrite_rules': [{'kind': 'strip', 'column': 'phone', 'chars': ' '}]
}
"""Default values stored by the helper-replacement example."""


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e18_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default helper-replacement configuration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/replacing_config_check_helpers.cfg'
        e18_replacing_config_check_helpers_set({}, config_file)
        config = ExampleConfig18(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.column_mappings == DEFAULT_DATA['column_mappings']
    assert config.merge_rules == DEFAULT_DATA['merge_rules']
    assert config.rewrite_rules == DEFAULT_DATA['rewrite_rules']
    assert json_data == DEFAULT_DATA


def test_e18_set_accepts_extra_keys_and_normalizes_kind(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Accept open dict shapes and normalize discriminated rule kinds."""
    set_values = cast(SetValues, {
        'column_mappings': [{
            'column': 'first_name',
            'source': 'First Name',
            'display_order': 1
        }],
        'merge_rules': [{
            'columns': ['first_name', 'last_name'],
            'separator': ' ',
            'label': 'full_name'
        }],
        'rewrite_rules': [{
            'kind': 'REMOVE_CHARS',
            'column': 'phone',
            'chars': [' ', '-'],
            'comment': 'digits only'
        }]
    })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/replacing_config_check_helpers.cfg'
        e18_replacing_config_check_helpers_set(set_values, config_file)
        config = ExampleConfig18(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.column_mappings[0]['display_order'] == 1
    assert config.merge_rules[0]['label'] == 'full_name'
    assert config.rewrite_rules == [{
        'chars': [' ', '-'],
        'column': 'phone',
        'comment': 'digits only',
        'kind': 'remove_chars'
    }]


def test_e18_print_reports_missing_column_mapping_key(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a mapping row that lacks the required scalar key."""
    data = dict(DEFAULT_DATA)
    data['column_mappings'] = [{'source': 'First Name'}]
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E18_SPEC,
        data,
        ['column_mappings[0]', "Mandatory key 'column'", 'missing']
    )


def test_e18_print_reports_column_mapping_type_error(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a mapping row whose required key has the wrong type."""
    data = dict(DEFAULT_DATA)
    data['column_mappings'] = [{'column': 3, 'source': 'First Name'}]
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E18_SPEC,
        data,
        ['column_mappings[0][column]', 'not of type str']
    )


def test_e18_print_reports_empty_merge_columns(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a merge rule whose checked list is too short."""
    data = dict(DEFAULT_DATA)
    data['merge_rules'] = [{'columns': [], 'separator': ' '}]
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E18_SPEC,
        data,
        ['merge_rules[0][columns]', 'size 0', 'minimum 1']
    )


def test_e18_print_reports_merge_column_type_error(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a checked inner list that contains the wrong value type."""
    data = dict(DEFAULT_DATA)
    data['merge_rules'] = [{'columns': ['first_name', 4], 'separator': ' '}]
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E18_SPEC,
        data,
        ['merge_rules[0][columns]', 'index 1', 'not of type str']
    )


def test_e18_print_reports_missing_rewrite_variant_key(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a kind-selected dict that lacks a variant key."""
    data = dict(DEFAULT_DATA)
    data['rewrite_rules'] = [{
        'kind': 'replace',
        'column': 'country',
        'from': 'SE'
    }]
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E18_SPEC,
        data,
        ['rewrite_rules[0]', "Mandatory key 'to'", 'missing']
    )


def test_e18_print_reports_rewrite_variant_type_error(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a kind-selected dict whose value has the wrong type."""
    data = dict(DEFAULT_DATA)
    data['rewrite_rules'] = [{
        'kind': 'remove_chars',
        'column': 'phone',
        'chars': ' -'
    }]
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E18_SPEC,
        data,
        ['rewrite_rules[0][chars]', 'not a list']
    )


def test_e18_main_round_trip_with_json_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the example through its JSON command-line inputs."""
    column_mappings = '[{"column":"first_name","source":"First Name"}]'
    merge_rules = '[{"columns":["first_name","last_name"],"separator":" "}]'
    rewrite_rules = (
        '[{"kind":"REPLACE","column":"country","from":"SE","to":"Sweden"}]'
    )
    assert_main_round_trip_print_output(
        capsys,
        e18_main,
        'replacing_config_check_helpers.cfg',
        ['--column-mappings', column_mappings,
         '--merge-rules', merge_rules,
         '--rewrite-rules', rewrite_rules],
        ["Column mappings: [{'column': 'first_name', "
         "'source': 'First Name'}]",
         "Merge rules: [{'columns': ['first_name', 'last_name'], "
         "'separator': ' '}]",
         "Rewrite rules: [{'column': 'country', 'from': 'SE', "
         "'kind': 'replace', 'to': 'Sweden'}]"]
    )
