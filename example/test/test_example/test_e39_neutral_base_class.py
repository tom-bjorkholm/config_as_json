#! /usr/local/bin/python3
"""Tests for the e39 neutral-base-class teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from example.cmd_line_handling import SetValues
from example.e39_neutral_base_class import MyConfigEager, MySubA, MySubB, \
    NConfigEager, e39_neutral_base_class_print, e39_neutral_base_class_set
from example.e39_neutral_base_class import main as e39_main
from .helpers import assert_rt_out, assert_write_command_output


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e39_default_wraps(capsys: pytest.CaptureFixture[str]) -> None:
    """Default bridge construction wraps neutral nested defaults."""
    config = MyConfigEager()
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert config.c1 == 'example'
    assert isinstance(config.suba, MySubA)
    assert config.suba.a1param == 'aa'
    assert isinstance(config.subb, MySubB)
    assert config.subb.b1param is False
    assert config.subb.b3param == 1


def test_e39_neutral_overrides(capsys: pytest.CaptureFixture[str]) -> None:
    """A supplied neutral instance carries its values into the bridge."""
    neutral = NConfigEager(c1='hello', b1p=True, b3p=4)
    config = MyConfigEager(neutral=neutral)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert config.c1 == 'hello'
    assert isinstance(config.suba, MySubA)
    assert isinstance(config.subb, MySubB)
    assert config.subb.b1param is True
    assert config.subb.b3param == 4


def test_e39_set_writes_overrides(capsys: pytest.CaptureFixture[str]) -> None:
    """The set command writes the values from a supplied neutral."""
    set_values = cast(SetValues, {'c1': 'hello', 'b1p': True, 'b3p': 4})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/neutral_base_class.cfg'
        e39_neutral_base_class_set(set_values, config_file)
        config = MyConfigEager(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.c1 == 'hello'
    assert isinstance(config.subb, MySubB)
    assert config.subb.b1param is True
    assert config.subb.b3param == 4
    assert json_data == {
        'c1': 'hello',
        'suba': {'a1param': 'aa', 'a2param': 4, 'a3param': None},
        'subb': {'b1param': True, 'b2param': 'bbb', 'b3param': 4}
    }


def test_e39_print_default(capsys: pytest.CaptureFixture[str]) -> None:
    """The print command shows the wrapped values from a default file."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/neutral_base_class.cfg'
        e39_neutral_base_class_set({}, config_file)
        _ = capsys.readouterr()
        e39_neutral_base_class_print(config_file)
        out, err = capsys.readouterr()
    assert err == ''
    assert out == '\n'.join([
        f'Configuration read from {config_file}',
        'c1: example',
        'suba.a1param: aa',
        'suba.a2param: 4',
        'suba.a3param: None',
        'subb.b1param: False',
        'subb.b2param: bbb',
        'subb.b3param: 1'
    ]) + '\n'


def test_e39_main_round_trip(capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip neutral-bridge configuration through the command line."""
    assert_rt_out(capsys, e39_main, 'neutral_base_class.cfg',
                  ['--c1', 'hello', '--b1p', 'true', '--b3p', '4'],
                  ['c1: hello',
                   'suba.a1param: aa',
                   'suba.a2param: 4',
                   'suba.a3param: None',
                   'subb.b1param: True',
                   'subb.b2param: bbb',
                   'subb.b3param: 4'])


def test_e39_json_roundtrip(capsys: pytest.CaptureFixture[str]) -> None:
    """Reading back JSON gives bridge-typed nested members."""
    neutral = NConfigEager(c1='roundtrip', b1p=True, b3p=7)
    config = MyConfigEager(neutral=neutral)
    json_text = config.as_json_string(stderr_file=sys.stderr)
    again = MyConfigEager(from_json_data_text=json_text)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert isinstance(again.suba, MySubA)
    assert isinstance(again.subb, MySubB)
    assert again.subb.b3param == 7
