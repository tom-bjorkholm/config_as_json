#! /usr/local/bin/python3
"""Tests for the hexadecimal and octal teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
import example.e41_hex_and_octal as e41_module
from example.cmd_line_handling import SetValues
from example.e41_hex_and_octal import ExampleConfig41, e41_hex_and_octal_print
from example.e41_hex_and_octal import e41_hex_and_octal_set
from example.e41_hex_and_octal import main as e41_main
from .helpers import ExampleProgramSpec, assert_print_validator_error, \
    assert_rt_out, assert_write_command_output


E41_SPEC = ExampleProgramSpec(module=e41_module,
                              factory_name='ExampleConfig41',
                              config_factory=ExampleConfig41,
                              set_command=e41_hex_and_octal_set,
                              print_command=e41_hex_and_octal_print,
                              config_basename='hex_and_octal.cfg')

DEFAULT_JSON: dict[str, object] = {
    'report_name': 'monthly-report',
    'file_mode': {'oct_str': '0644'},
    'umask': {'oct_str': '0o022'},
    'window_colour': {'hex_str': '#204060'},
    'feature_bits': {'hex_str': '0x0000000f'}}
"""The written numbers of the default configuration, in their notations."""


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e41_set_defaults(capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default configuration in the declared notations."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/hex_and_octal.cfg'
        e41_hex_and_octal_set({}, config_file)
        config = ExampleConfig41(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert json_data == DEFAULT_JSON
    assert config.file_mode.get() == 0o644
    assert config.umask.get() == 0o022
    assert config.window_colour.get() == 0x204060
    assert config.feature_bits.get() == 0x0000000f
    assert config.owner_may_write()


def test_e41_set_notations(capsys: pytest.CaptureFixture[str]) -> None:
    """Accept any notation of a value and store the declared one."""
    set_values = cast(SetValues, {'file_mode': '0o450',
                                  'umask': '27',
                                  'window_colour': '0xff8000',
                                  'feature_bits': '#f0'})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/hex_and_octal.cfg'
        e41_hex_and_octal_set(set_values, config_file)
        config = ExampleConfig41(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert json_data == {'report_name': 'monthly-report',
                         'file_mode': {'oct_str': '0450'},
                         'umask': {'oct_str': '0o027'},
                         'window_colour': {'hex_str': '#ff8000'},
                         'feature_bits': {'hex_str': '0x000000f0'}}
    assert config.file_mode.get() == 0o450
    assert not config.owner_may_write()


def test_e41_print_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Print the written text and the integer of every value."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/hex_and_octal.cfg'
        e41_hex_and_octal_set({}, config_file)
        _ = capsys.readouterr()
        e41_hex_and_octal_print(config_file)
        out, err = capsys.readouterr()
    assert err == ''
    assert out == '\n'.join([
        f'Configuration read from {config_file}',
        'Report name: monthly-report',
        'File mode: 0644 = 420 as an integer',
        'Umask: 0o022 = 18 as an integer',
        'Window colour: #204060 = 2113632 as an integer',
        'Feature bits: 0x0000000f = 15 as an integer',
        'The owner may write the file: yes'
    ]) + '\n'


def test_e41_round_trip(capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the written numbers through the command line."""
    assert_rt_out(
        capsys, e41_main, 'hex_and_octal.cfg',
        ['--report-name', 'audit-report', '--file-mode', '600',
         '--umask', '0o077', '--window-colour', 'ffffff',
         '--feature-bits', '0x10'],
        [
            'Report name: audit-report',
            'File mode: 0600 = 384 as an integer',
            'Umask: 0o077 = 63 as an integer',
            'Window colour: #ffffff = 16777215 as an integer',
            'Feature bits: 0x00000010 = 16 as an integer',
            'The owner may write the file: yes'
        ])


@pytest.mark.parametrize('member,written,fragment', [
    ('file_mode', '0888', 'not octal digits'),
    ('umask', '0o9', 'not octal digits'),
    ('window_colour', '#gg0000', 'not hexadecimal digits'),
    ('feature_bits', '', 'is empty')])
def test_e41_bad_value(capsys: pytest.CaptureFixture[str],
                       monkeypatch: pytest.MonkeyPatch, member: str,
                       written: str, fragment: str) -> None:
    """Report a hand-edited value that is not written in its notation.

    The diagnostic names the member of the nested value, which is
    ``oct_str`` or ``hex_str``, and not the member of the configuration
    that holds the nested value.
    """
    json_data = dict(DEFAULT_JSON)
    key = 'oct_str' if member in ('file_mode', 'umask') else 'hex_str'
    json_data[member] = {key: written}
    assert_print_validator_error(capsys, monkeypatch, E41_SPEC, json_data,
                                 [key, fragment])
