#! /usr/local/bin/python3
"""Tests for the optional-user-preference teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from example.cmd_line_handling import SetValues
from example.e30_optional_user_preference import DeliveryFormat, \
    ExampleConfig30, Palette, e30_optional_user_preference_print, \
    e30_optional_user_preference_set
from example.e30_optional_user_preference import main as e30_main
from .helpers import assert_main_round_trip_print_output
from .helpers import assert_write_command_output


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e30_set_omits_default_none_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write default configuration without None-valued members."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/optional_user_preference.cfg'
        e30_optional_user_preference_set({}, config_file)
        config = ExampleConfig30(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.author_note is None
    assert config.palette is None
    assert config.selected_palette() == Palette.ACCESSIBLE
    assert json_data == {'delivery_format': 'HTML',
                         'report_name': 'daily-status'}


def test_e30_set_keeps_explicit_optional_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write optional members when the user selected values."""
    set_values = cast(SetValues, {
        'report_name': 'weekly-summary',
        'delivery_format': DeliveryFormat.TEXT,
        'author_note': 'Reviewed by Ada',
        'palette': Palette.VIVID
    })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/optional_user_preference.cfg'
        e30_optional_user_preference_set(set_values, config_file)
        config = ExampleConfig30(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.report_name == 'weekly-summary'
    assert config.delivery_format == DeliveryFormat.TEXT
    assert config.author_note == 'Reviewed by Ada'
    assert config.palette == Palette.VIVID
    assert config.selected_palette() == Palette.VIVID
    assert json_data == {'author_note': 'Reviewed by Ada',
                         'delivery_format': 'TEXT',
                         'palette': 'VIVID',
                         'report_name': 'weekly-summary'}


def test_e30_reads_missing_optional_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Read a file where omit-None members are absent."""
    config = ExampleConfig30(
        from_json_text='{"delivery_format": "TEXT", '
                       '"report_name": "monthly"}')
    json_data = json.loads(config.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert config.author_note is None
    assert config.palette is None
    assert config.selected_palette() == Palette.ACCESSIBLE
    assert json_data == {'delivery_format': 'TEXT',
                         'report_name': 'monthly'}


def test_e30_reads_explicit_null_as_missing(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Read JSON null as None and omit it again when writing."""
    config = ExampleConfig30(
        from_json_text='{"author_note": null, '
                       '"delivery_format": "TEXT", '
                       '"palette": null, '
                       '"report_name": "monthly"}')
    json_data = json.loads(config.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert config.author_note is None
    assert config.palette is None
    assert json_data == {'delivery_format': 'TEXT',
                         'report_name': 'monthly'}


def test_e30_print_uses_effective_palette(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Print the automatic palette chosen for a missing palette setting."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/optional_user_preference.cfg'
        e30_optional_user_preference_set({}, config_file)
        _ = capsys.readouterr()
        e30_optional_user_preference_print(config_file)
        out, err = capsys.readouterr()
    assert err == ''
    assert 'Palette setting: automatic\n' in out
    assert 'Selected palette: ACCESSIBLE\n' in out


def test_e30_main_round_trip_prints_default_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip default omit-None values through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e30_main,
        'optional_user_preference.cfg',
        [],
        ['Report name: daily-status',
         'Delivery format: HTML',
         'Author note: not configured',
         'Palette setting: automatic',
         'Selected palette: ACCESSIBLE']
    )


def test_e30_main_round_trip_with_optional_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip explicit optional values through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e30_main,
        'optional_user_preference.cfg',
        ['--report-name', 'weekly-summary',
         '--delivery-format', 'text',
         '--author-note', 'Reviewed by Ada',
         '--palette', 'vivid'],
        ['Report name: weekly-summary',
         'Delivery format: TEXT',
         'Author note: Reviewed by Ada',
         'Palette setting: VIVID',
         'Selected palette: VIVID']
    )
