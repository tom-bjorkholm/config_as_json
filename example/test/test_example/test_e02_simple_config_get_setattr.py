#! /usr/local/bin/python3
"""Tests for the second example program."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from tempfile import TemporaryDirectory
import pytest
import example.e02_simple_config_get_setattr as e02_module
from example.e01_simple_config import INPUT_SPECS, SimpleConfig
from example.e01_simple_config import YesNoAsk
from example.e02_simple_config_get_setattr import e02_simple_config_print
from example.e02_simple_config_get_setattr import e02_simple_config_set
from example.e02_simple_config_get_setattr import (
    get_normal_instance_attribute_names
)
from .helpers import CONFIGURED_SIMPLE_CONFIG, DEFAULT_SIMPLE_CONFIG
from .helpers import assert_simple_config_written_by_set_command


def test_get_normal_instance_attribute_names_returns_public_values() -> None:
    """Return only public non-callable instance attributes."""
    config = SimpleConfig()
    names = get_normal_instance_attribute_names(config)
    assert set(names) == {
        'name',
        'answer',
        'approximation',
        'easy',
        'confirmation'
    }
    assert all(not name.startswith('_') for name in names)
    assert 'write' not in names
    assert len(names) == 5


def test_e02_simple_config_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write a configuration file with the default values."""
    assert_simple_config_written_by_set_command(
        capsys,
        e02_simple_config_set,
        {},
        DEFAULT_SIMPLE_CONFIG
    )


def test_e02_simple_config_set_stores_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Apply overrides with setattr before writing the file."""
    assert_simple_config_written_by_set_command(
        capsys,
        e02_simple_config_set,
        {
            'name': 'configured',
            'answer': 7,
            'approximation': 2.5,
            'easy': False,
            'confirmation': YesNoAsk.NO
        },
        CONFIGURED_SIMPLE_CONFIG
    )


def test_e02_simple_config_set_rejects_invalid_key() -> None:
    """Reject overrides that are not public configuration attributes."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/simple.cfg'
        with pytest.raises(ValueError) as exc:
            e02_simple_config_set({'invalid': 'value'}, config_file)
    assert 'Invalid key: invalid' in str(exc.value)


def test_e02_simple_config_print_reads_written_file(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Read a stored configuration and print the values."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/simple.cfg'
        e02_simple_config_set(
            {
                'name': 'Ada',
                'answer': 12,
                'approximation': 2.75,
                'easy': True,
                'confirmation': YesNoAsk.YES
            },
            config_file
        )
        _ = capsys.readouterr()
        e02_simple_config_print(config_file)
    out, err = capsys.readouterr()
    assert err == ''
    lines = out.strip().splitlines()
    assert len(lines) == 6
    assert set(lines) == {
        'name: Ada',
        'answer: 12',
        'approximation: 2.75',
        'easy: True',
        'confirmation: YesNoAsk.YES',
        f'Configuration read from {config_file}'
    }


def test_main_calls_shared_command_line_helper(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Pass the expected callbacks and metadata to the shared helper."""
    received: dict[str, object] = {}

    def fake_cmd_line_handling(
            example_name: str,
            input_specs: list[object],
            set_command: object,
            print_command: object,
            args: object = None) -> None:
        """Record the values passed to cmd_line_handling."""
        received['example_name'] = example_name
        received['input_specs'] = input_specs
        received['set_command'] = set_command
        received['print_command'] = print_command
        received['args'] = args

    monkeypatch.setattr(
        e02_module,
        'cmd_line_handling',
        fake_cmd_line_handling
    )
    e02_module.main(['set', '--output', 'simple.cfg'])
    assert received == {
        'example_name': 'e02_simple_config_get_setattr',
        'input_specs': INPUT_SPECS,
        'set_command': e02_module.e02_simple_config_set,
        'print_command': e02_module.e02_simple_config_print,
        'args': ['set', '--output', 'simple.cfg']
    }
