#! /usr/local/bin/python3
"""Test one application-defined notation built on RadixNumber."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
from enum import Enum
import sys
import pytest
from config_as_json.radix_number import RadixNumber, RadixSpec, RadixValidator
from config_as_json.config import Config
from config_as_json.config_nesting import NestedConfigs, ConfigNesting, \
    ConfigNestingKind
from config_as_json.commontypes import PathOrStr
from config_as_json.validator import InvalidConfiguration, ValidationPlan
from config_as_json.type_validators import InvalidConfigurationType
from .check_capsys import check_capsys


_BIN_SPEC = RadixSpec(radix=2, digit_chars='01', format_letter='b',
                      member_name='bin_str', adjective='binary', article='a')
"""One notation that this package does not predefine."""


class BinaryStringValidator(RadixValidator['BinaryNumber.Prefix']):
    """A validator for a binary string configuration value."""

    _SPEC = _BIN_SPEC


class BinaryNumber(RadixNumber['BinaryNumber.Prefix']):
    """A configuration value that should format as a binary number."""

    bin_str: str
    """The binary string, and the only member stored in JSON."""

    class Prefix(Enum):
        """The prefix to use when formatting the binary number."""

        NONE = ''
        """No prefix."""

        ZERO_B = '0b'
        """The prefix '0b', the notation of Python."""

    _SPEC = _BIN_SPEC
    _no_prefix = Prefix.NONE
    _validator_class = BinaryStringValidator


flags_factory = BinaryNumber.factory(BinaryNumber.Prefix.ZERO_B, 8, 0b101)
"""Say the format of the one member of the test configuration."""


class BinaryConfig(Config):
    """A configuration with one binary number value."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Initialize the BinaryConfig configuration."""
        made = flags_factory(member_name=None)
        assert isinstance(made, BinaryNumber)
        self.flags: BinaryNumber = made
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=None, stderr_file=stderr_file,
                         member_name=member_name)

    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for this configuration."""
        return {'flags': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                       config_type=BinaryNumber,
                                       factory_function=flags_factory)}

    def get_validation_plan(self, stderr_file: TextIO = sys.stderr) \
            -> ValidationPlan:
        """Return the validation plan for this configuration."""
        _ = stderr_file
        return []


@pytest.mark.parametrize('value,expected,number', [
    (0, '0b00000000', 0), (0b1011, '0b00001011', 11), ('0b0', '0b00000000', 0),
    ('0B11', '0b00000011', 3), ('  1111  ', '0b00001111', 15)])
def test_notation(value: int | str, expected: str, number: int,
                  capsys: pytest.CaptureFixture[str]) -> None:
    """An application-defined notation writes and reads its own digits."""
    written = BinaryNumber(value=value, prefix=BinaryNumber.Prefix.ZERO_B,
                           digits=8)
    assert written.bin_str == expected
    assert written.get() == number
    assert BinaryNumber.strip_prefix(expected) == expected[2:]
    check_capsys(capsys)


def test_json_round_trip(capsys: pytest.CaptureFixture[str]) -> None:
    """The declared notation survives a parse and normalizes what it reads."""
    config = BinaryConfig(stderr_file=sys.stderr)
    assert config.flags.bin_str == '0b00000101'
    parsed = BinaryConfig(from_json_data_text='{"flags": {"bin_str": "11"}}',
                          stderr_file=sys.stderr)
    assert parsed.flags.bin_str == '0b00000011'
    assert parsed.flags.get() == 3
    assert parsed.flags.digits == 8
    assert '0b00000011' in parsed.as_json_string(stderr_file=sys.stderr,
                                                 member_name=None)
    check_capsys(capsys)


@pytest.mark.parametrize('value,error,message', [
    ('2', InvalidConfiguration, 'not binary digits'),
    ('0b', InvalidConfiguration, 'Binary string for flags is empty'),
    (-1, InvalidConfiguration, 'is negative'),
    (None, InvalidConfigurationType, 'not a binary string or a number')])
def test_diagnostics(value: object, error: type[Exception], message: str,
                     capsys: pytest.CaptureFixture[str]) -> None:
    """The notation names itself in the diagnostics of a refused value."""
    validator = BinaryStringValidator(prefix=BinaryNumber.Prefix.NONE)
    config = BinaryConfig(stderr_file=sys.stderr)
    with pytest.raises(error) as raised:
        validator.validate_member(config, 'flags', value, sys.stderr)
    assert message in str(raised.value)
    check_capsys(capsys, in_err=message)
