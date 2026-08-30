#! /usr/local/bin/python3
"""Test the HexadecimalNumber configuration value."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO, cast
from pathlib import Path
import sys
import pytest
from config_as_json.hexadecimal_number import HexadecimalNumber, \
    HexadecimalStringValidator
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_nesting import NestedConfigs, ConfigNesting, \
    ConfigNestingKind
from config_as_json.commontypes import PathOrStr
from config_as_json.validator import InvalidConfiguration, ValidationPlan
from config_as_json.type_validators import InvalidConfigurationType
from .check_capsys import check_capsys
from .validator_test_helpers import assert_validate_member_ok, \
    assert_validate_member_failure


Prefix = HexadecimalNumber.Prefix


class TkColour(HexadecimalNumber):
    """A colour value written the way Tk expects to be given one.

    The format is said by the class itself, which is one of the two ways of
    keeping it when the base class rebuilds the member from parsed JSON.
    """

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 value: Optional[int | str] = None) -> None:
        """Initialize one Tk colour value."""
        super().__init__(from_json_data_text, from_json_filename, auto_ch_hook,
                         stderr_file, value=value, prefix=Prefix.HASH,
                         digits=6)


mask_factory = HexadecimalNumber.factory(Prefix.ZERO_X, 8, 0x0f)
"""Say the format of one member once, for its default and for every parse."""


def _new_mask(json_text: Optional[str] = None) -> HexadecimalNumber:
    """Return one bit mask value constructed by the shared factory.

    The factory answers with the declared ``Config`` type of the protocol, so
    the test says here once what kind of object it really constructs.
    """
    made = mask_factory(from_json_data_text=json_text)
    assert isinstance(made, HexadecimalNumber)
    return made


class TwoHexConfig(Config):
    """A configuration with two hexadecimal number values."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the TwoHexConfig configuration value.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.pycolor: HexadecimalNumber = TkColour(value=0x102030)
        self.ccolor: HexadecimalNumber = _new_mask()
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=None, stderr_file=stderr_file)

    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for this configuration."""
        subclassed = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                   config_type=TkColour)
        by_factory = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                   config_type=HexadecimalNumber,
                                   factory_function=mask_factory)
        return {'pycolor': subclassed, 'ccolor': by_factory}

    def get_validation_plan(self, stderr_file: TextIO = sys.stderr) \
            -> ValidationPlan:
        """Return the validation plan for this configuration."""
        _ = stderr_file
        return []


def _written_and_read(config: TwoHexConfig, tmp_path: Path) -> TwoHexConfig:
    """Write one configuration to file and read it back into a new object."""
    fname = str(tmp_path / 'test_config.cfg')
    config.write(to_json_filename=fname, stderr_file=sys.stderr)
    return TwoHexConfig(from_json_filename=fname, stderr_file=sys.stderr)


def test_default_value(capsys: pytest.CaptureFixture[str]) -> None:
    """A value constructed without arguments is zero without a prefix."""
    number = HexadecimalNumber()
    assert number.hex_str == '0'
    assert number.get() == 0
    assert number.prefix == Prefix.NONE
    assert number.digits == 0
    check_capsys(capsys)


@pytest.mark.parametrize('prefix,digits,value,expected', [
    (Prefix.NONE, 0, 0, '0'),
    (Prefix.NONE, 0, 255, 'ff'),
    (Prefix.NONE, 4, 255, '00ff'),
    (Prefix.ZERO_X, 0, 255, '0xff'),
    (Prefix.ZERO_X, 8, 255, '0x000000ff'),
    (Prefix.HASH, 6, 0, '#000000'),
    (Prefix.HASH, 6, 0x00ff00, '#00ff00'),
    (Prefix.HASH, 6, 0xffffff, '#ffffff'),
    (Prefix.HASH, 2, 0xabcdef, '#abcdef'),
    (Prefix.HASH, 6, '0x00FF00', '#00ff00'),
    (Prefix.NONE, 0, ' #1F ', '1f'),
    (Prefix.ZERO_X, 0, '0X1f', '0x1f'),
    (Prefix.ZERO_X, 0, '1f', '0x1f'),
    (Prefix.HASH, 0, '000f', '#f')])
def test_formatting(prefix: HexadecimalNumber.Prefix, digits: int,
                    value: int | str, expected: str,
                    capsys: pytest.CaptureFixture[str]) -> None:
    """Values are written with the declared prefix and digit count."""
    from_init = HexadecimalNumber(value=value, prefix=prefix, digits=digits)
    assert from_init.hex_str == expected
    from_set = HexadecimalNumber(prefix=prefix, digits=digits)
    from_set.set(value)
    assert from_set.hex_str == expected
    assert from_set.get() == from_init.get()
    check_capsys(capsys)


@pytest.mark.parametrize('text,expected', [
    ('0', 0), ('ff', 255), ('FF', 255), ('0xff', 255), ('0XFF', 255),
    ('#ff', 255), ('  #ff  ', 255), ('000000ff', 255), ('#0', 0),
    ('0x0', 0), ('7fffffffffffffff', 2**63 - 1)])
def test_reading_notations(text: str, expected: int,
                           capsys: pytest.CaptureFixture[str]) -> None:
    """Any of the notations is accepted whatever prefix is declared."""
    number = HexadecimalNumber(value=text, prefix=Prefix.HASH)
    assert number.get() == expected
    check_capsys(capsys)


@pytest.mark.parametrize('value', [-1, -255, -(2**64)])
def test_negative_value(value: int,
                        capsys: pytest.CaptureFixture[str]) -> None:
    """A negative integer is refused, as hexadecimal text cannot hold one."""
    with pytest.raises(InvalidConfiguration):
        HexadecimalNumber(value=value)
    number = HexadecimalNumber()
    with pytest.raises(InvalidConfiguration):
        number.set(value)
    assert number.hex_str == '0'
    check_capsys(capsys)


@pytest.mark.parametrize('value', [
    '', '   ', '#', '0x', '0X', 'gg', '#12g', '-5', '#-5', '0x 5', '1.5',
    'ff ff', '0xff\n\nff'])
def test_bad_hex_string(value: str,
                        capsys: pytest.CaptureFixture[str]) -> None:
    """A string that does not hold a hexadecimal number is refused."""
    with pytest.raises(InvalidConfiguration):
        HexadecimalNumber(value=value)
    check_capsys(capsys)


@pytest.mark.parametrize('value', [1.5, True, False, [255], {'a': 1},
                                   (1, 2), b'ff'])
def test_bad_value_type(value: object,
                        capsys: pytest.CaptureFixture[str]) -> None:
    """A value that is neither an integer nor a string is refused."""
    number = HexadecimalNumber()
    with pytest.raises(InvalidConfiguration):
        number.set(cast(int, value))
    check_capsys(capsys)


@pytest.mark.parametrize('digits', [-1, -8])
def test_negative_digits(digits: int,
                         capsys: pytest.CaptureFixture[str]) -> None:
    """A negative digit count is a declaration error in the application."""
    with pytest.raises(ValueError):
        HexadecimalNumber(digits=digits)
    with pytest.raises(ValueError):
        HexadecimalStringValidator(prefix=Prefix.NONE, digits=digits)
    with pytest.raises(ValueError):
        HexadecimalNumber.factory(prefix=Prefix.NONE, digits=digits)
    check_capsys(capsys)


def test_get_after_assign(capsys: pytest.CaptureFixture[str]) -> None:
    """Assigning the public member is seen by the next read of the value."""
    number = HexadecimalNumber(value=1, prefix=Prefix.HASH, digits=6)
    assert number.get() == 1
    number.hex_str = '0x00ff00'
    assert number.get() == 0x00ff00
    number.hex_str = ' 7 '
    assert number.get() == 7
    number.set(2)
    assert number.get() == 2
    assert number.hex_str == '#000002'
    check_capsys(capsys)


def test_get_after_bad_assign(capsys: pytest.CaptureFixture[str]) -> None:
    """Assigning text that is not hexadecimal is reported when read."""
    number = HexadecimalNumber(value=1)
    number.hex_str = 'not hex'
    with pytest.raises(InvalidConfiguration):
        number.get()
    check_capsys(capsys)


def test_json_round_trip(tmp_path: Path,
                         capsys: pytest.CaptureFixture[str]) -> None:
    """Writing and reading back keeps the declared notation of each member."""
    config = TwoHexConfig(stderr_file=sys.stderr)
    config.pycolor.set(5)
    config.ccolor.set(10)
    assert config.pycolor.hex_str == '#000005'
    assert config.ccolor.hex_str == '0x0000000a'
    text = config.as_json_string(stderr_file=sys.stderr, member_name=None)
    assert '#000005' in text
    assert '0x0000000a' in text
    other = _written_and_read(config, tmp_path)
    assert other.pycolor.hex_str == '#000005'
    assert other.ccolor.hex_str == '0x0000000a'
    assert other.pycolor.get() == 5
    assert other.ccolor.get() == 10
    check_capsys(capsys)


def test_read_keeps_format(tmp_path: Path,
                           capsys: pytest.CaptureFixture[str]) -> None:
    """A member read from file is rebuilt with the declared format."""
    other = _written_and_read(TwoHexConfig(stderr_file=sys.stderr), tmp_path)
    assert other.pycolor.prefix == Prefix.HASH
    assert other.pycolor.digits == 6
    assert other.ccolor.prefix == Prefix.ZERO_X
    assert other.ccolor.digits == 8
    other.pycolor.set(0xff)
    assert other.pycolor.hex_str == '#0000ff'
    check_capsys(capsys)


@pytest.mark.parametrize('written,expected_py,expected_c', [
    ('"0x10"', '#000010', '0x00000010'),
    ('"#10"', '#000010', '0x00000010'),
    ('"10"', '#000010', '0x00000010'),
    ('"  0X0000000010  "', '#000010', '0x00000010'),
    ('"AB"', '#0000ab', '0x000000ab'),
    ('16', '#000010', '0x00000010'),
    ('0', '#000000', '0x00000000')])
def test_json_normalizes(written: str, expected_py: str, expected_c: str,
                         capsys: pytest.CaptureFixture[str]) -> None:
    """A hand-edited file is normalized to the notation declared for it."""
    text = f'{{"pycolor": {{"hex_str": {written}}}, ' \
           f'"ccolor": {{"hex_str": {written}}}}}'
    config = TwoHexConfig(from_json_data_text=text, stderr_file=sys.stderr)
    assert config.pycolor.hex_str == expected_py
    assert config.ccolor.hex_str == expected_c
    assert config.pycolor.get() == config.ccolor.get()
    check_capsys(capsys)


def test_cache_after_parse(capsys: pytest.CaptureFixture[str]) -> None:
    """Parsing builds the cached integer, so no read has to rebuild it."""
    text = '{"pycolor": {"hex_str": "0x1234"}, "ccolor": {"hex_str": 66}}'
    config = TwoHexConfig(from_json_data_text=text, stderr_file=sys.stderr)
    assert config.pycolor.hex_str == '#001234'
    assert config.pycolor.get() == 0x1234
    assert config.ccolor.get() == 66
    check_capsys(capsys)


@pytest.mark.parametrize('written,in_err', [
    ('"zz"', 'not hexadecimal digits'),
    ('""', 'is empty'),
    ('"  "', 'is empty'),
    ('"-1"', 'not hexadecimal digits'),
    ('-1', 'is negative'),
    ('true', 'is a bool'),
    ('null', 'not a hexadecimal string or a number'),
    ('1.5', 'not a hexadecimal string or a number'),
    ('[1]', 'not a hexadecimal string or a number')])
def test_json_bad_value(written: str, in_err: str,
                        capsys: pytest.CaptureFixture[str]) -> None:
    """A JSON value that is not a hexadecimal number is refused and told."""
    text = f'{{"pycolor": {{"hex_str": {written}}}, ' \
           '"ccolor": {"hex_str": "0"}}'
    with pytest.raises(InvalidConfiguration):
        TwoHexConfig(from_json_data_text=text, stderr_file=sys.stderr)
    check_capsys(capsys, in_err=in_err)


def test_factory_format(capsys: pytest.CaptureFixture[str]) -> None:
    """The factory says the format for the default and for every parse."""
    made = _new_mask()
    assert made.hex_str == '0x0000000f'
    assert made.get() == 0x0f
    parsed = _new_mask('{"hex_str": "#ff"}')
    assert parsed.hex_str == '0x000000ff'
    assert parsed.prefix == Prefix.ZERO_X
    assert parsed.digits == 8
    check_capsys(capsys)


@pytest.mark.parametrize('value,expected', [
    ('0xff', 'ff'), ('0XFF', 'FF'), ('#ff', 'ff'), ('ff', 'ff'),
    ('', ''), ('0', '0'), ('#', ''), ('0x', ''), ('x0', 'x0'),
    ('##1', '#1'), ('0x0xff', '0xff')])
def test_strip_prefix(value: str, expected: str) -> None:
    """Any recognized prefix is removed, whatever prefix is declared."""
    assert HexadecimalNumber.strip_prefix(value) == expected


@pytest.mark.parametrize('value,expected', [
    ('ff', '#0000ff'), ('0xFF', '#0000ff'), ('  #00ff00  ', '#00ff00'),
    (255, '#0000ff'), (0, '#000000')])
def test_validator_ok(capsys: pytest.CaptureFixture[str], value: object,
                      expected: str) -> None:
    """The validator normalizes accepted values to the declared notation."""
    validator = HexadecimalStringValidator(prefix=Prefix.HASH, digits=6)
    assert_validate_member_ok(capsys, validator, value, expected)


@pytest.mark.parametrize('value,error,message', [
    ('zz', InvalidConfiguration, 'not hexadecimal digits'),
    ('', InvalidConfiguration, 'is empty'),
    (-1, InvalidConfiguration, 'is negative'),
    (True, InvalidConfiguration, 'is a bool'),
    (None, InvalidConfigurationType, 'not a hexadecimal string or a number'),
    (1.5, InvalidConfigurationType, 'not a hexadecimal string or a number')])
def test_validator_failure(capsys: pytest.CaptureFixture[str], value: object,
                           error: type[Exception], message: str) -> None:
    """The validator refuses and reports what a value is refused for."""
    validator = HexadecimalStringValidator(prefix=Prefix.NONE)
    assert_validate_member_failure(capsys, validator, value, error, message)
