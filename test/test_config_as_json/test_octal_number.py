#! /usr/local/bin/python3
"""Test the OctalNumber configuration value."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO, cast
from pathlib import Path
import sys
import pytest
from config_as_json.octal_number import OctalNumber, OctalStringValidator
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


Prefix = OctalNumber.Prefix


class FileMode(OctalNumber):
    """A file mode written the way the chmod documentation writes one.

    The format is said by the class itself, which is one of the two ways of
    keeping it when the base class rebuilds the member from parsed JSON.
    """

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 value: Optional[int | str] = None) -> None:
        """Initialize one file mode value."""
        super().__init__(from_json_data_text, from_json_filename, auto_ch_hook,
                         stderr_file, value=value, prefix=Prefix.ZERO,
                         digits=3)


umask_factory = OctalNumber.factory(Prefix.ZERO_O, 3, 0o22)
"""Say the format of one member once, for its default and for every parse."""


def _new_umask(json_text: Optional[str] = None) -> OctalNumber:
    """Return one umask value constructed by the shared factory.

    The factory answers with the declared ``Config`` type of the protocol, so
    the test says here once what kind of object it really constructs.
    """
    made = umask_factory(from_json_data_text=json_text)
    assert isinstance(made, OctalNumber)
    return made


class TwoOctConfig(Config):
    """A configuration with two octal number values."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the TwoOctConfig configuration value.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.mode: OctalNumber = FileMode(value=0o644)
        self.umask: OctalNumber = _new_umask()
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=None, stderr_file=stderr_file)

    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for this configuration."""
        subclassed = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                   config_type=FileMode)
        by_factory = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                   config_type=OctalNumber,
                                   factory_function=umask_factory)
        return {'mode': subclassed, 'umask': by_factory}

    def get_validation_plan(self, stderr_file: TextIO = sys.stderr) \
            -> ValidationPlan:
        """Return the validation plan for this configuration."""
        _ = stderr_file
        return []


def _written_and_read(config: TwoOctConfig, tmp_path: Path) -> TwoOctConfig:
    """Write one configuration to file and read it back into a new object."""
    fname = str(tmp_path / 'test_config.cfg')
    config.write(to_json_filename=fname, stderr_file=sys.stderr)
    return TwoOctConfig(from_json_filename=fname, stderr_file=sys.stderr)


def test_default_value(capsys: pytest.CaptureFixture[str]) -> None:
    """A value constructed without arguments is zero without a prefix."""
    number = OctalNumber()
    assert number.oct_str == '0'
    assert number.get() == 0
    assert number.prefix == Prefix.NONE
    assert number.digits == 0
    check_capsys(capsys)


@pytest.mark.parametrize('prefix,digits,value,expected', [
    (Prefix.NONE, 0, 0, '0'),
    (Prefix.NONE, 0, 0o777, '777'),
    (Prefix.NONE, 4, 0o17, '0017'),
    (Prefix.ZERO_O, 0, 0o17, '0o17'),
    (Prefix.ZERO_O, 3, 0o22, '0o022'),
    (Prefix.ZERO, 3, 0o755, '0755'),
    (Prefix.ZERO, 3, 0, '0000'),
    (Prefix.ZERO, 4, 0o4644, '04644'),
    (Prefix.ZERO, 1, 0o755, '0755'),
    (Prefix.ZERO, 3, '0o644', '0644'),
    (Prefix.NONE, 0, ' 0o17 ', '17'),
    (Prefix.ZERO_O, 0, '0O17', '0o17'),
    (Prefix.ZERO_O, 0, '17', '0o17'),
    (Prefix.ZERO, 0, '0017', '017')])
def test_formatting(prefix: OctalNumber.Prefix, digits: int, value: int | str,
                    expected: str, capsys: pytest.CaptureFixture[str]) -> None:
    """Values are written with the declared prefix and digit count."""
    from_init = OctalNumber(value=value, prefix=prefix, digits=digits)
    assert from_init.oct_str == expected
    from_set = OctalNumber(prefix=prefix, digits=digits)
    from_set.set(value)
    assert from_set.oct_str == expected
    assert from_set.get() == from_init.get()
    check_capsys(capsys)


def test_zero_prefix_padding(capsys: pytest.CaptureFixture[str]) -> None:
    """The leading zero is written even when no digit count is declared."""
    number = OctalNumber(value=0, prefix=Prefix.ZERO)
    assert number.oct_str == '00'
    assert number.get() == 0
    number.set(0o7)
    assert number.oct_str == '07'
    assert OctalNumber(value='00', prefix=Prefix.ZERO).get() == 0
    check_capsys(capsys)


@pytest.mark.parametrize('text,expected', [
    ('0', 0), ('7', 7), ('17', 15), ('755', 0o755), ('0755', 0o755),
    ('0o755', 0o755), ('0O755', 0o755), ('  0o755  ', 0o755), ('00', 0),
    ('0o0', 0), ('000000755', 0o755), ('777777777777777777777', 8**21 - 1)])
def test_reading_notations(text: str, expected: int,
                           capsys: pytest.CaptureFixture[str]) -> None:
    """Any of the notations is accepted whatever prefix is declared."""
    number = OctalNumber(value=text, prefix=Prefix.ZERO)
    assert number.get() == expected
    check_capsys(capsys)


def test_file_mode_bits(capsys: pytest.CaptureFixture[str]) -> None:
    """A file mode is written as text and used as the integer chmod wants."""
    mode = FileMode(value='0750')
    assert mode.oct_str == '0750'
    assert mode.get() == 0o750
    assert mode.get() & 0o700 == 0o700
    assert mode.get() & 0o007 == 0
    check_capsys(capsys)


@pytest.mark.parametrize('value', [-1, -8, -(2**64)])
def test_negative_value(value: int,
                        capsys: pytest.CaptureFixture[str]) -> None:
    """A negative integer is refused, as octal text cannot hold one."""
    with pytest.raises(InvalidConfiguration):
        OctalNumber(value=value)
    number = OctalNumber()
    with pytest.raises(InvalidConfiguration):
        number.set(value)
    assert number.oct_str == '0'
    check_capsys(capsys)


@pytest.mark.parametrize('value', [
    '', '   ', '0o', '0O', '8', '9', '18', '0o8', '0x1f', 'ff', '-5', '0o-5',
    '0o 5', '1.5', '1_0', '75 5', '0o75\n\n5'])
def test_bad_octal_string(value: str,
                          capsys: pytest.CaptureFixture[str]) -> None:
    """A string that does not hold an octal number is refused."""
    with pytest.raises(InvalidConfiguration):
        OctalNumber(value=value)
    check_capsys(capsys)


@pytest.mark.parametrize('value', [1.5, True, False, [8], {'a': 1},
                                   (1, 2), b'17'])
def test_bad_value_type(value: object,
                        capsys: pytest.CaptureFixture[str]) -> None:
    """A value that is neither an integer nor a string is refused."""
    number = OctalNumber()
    with pytest.raises(InvalidConfiguration):
        number.set(cast(int, value))
    check_capsys(capsys)


@pytest.mark.parametrize('digits', [-1, -3])
def test_negative_digits(digits: int,
                         capsys: pytest.CaptureFixture[str]) -> None:
    """A negative digit count is a declaration error in the application."""
    with pytest.raises(ValueError):
        OctalNumber(digits=digits)
    with pytest.raises(ValueError):
        OctalStringValidator(prefix=Prefix.NONE, digits=digits)
    with pytest.raises(ValueError):
        OctalNumber.factory(prefix=Prefix.NONE, digits=digits)
    check_capsys(capsys)


def test_get_after_assign(capsys: pytest.CaptureFixture[str]) -> None:
    """Assigning the public member is seen by the next read of the value."""
    number = OctalNumber(value=1, prefix=Prefix.ZERO, digits=3)
    assert number.get() == 1
    number.oct_str = '0o644'
    assert number.get() == 0o644
    number.oct_str = ' 7 '
    assert number.get() == 7
    number.set(2)
    assert number.get() == 2
    assert number.oct_str == '0002'
    check_capsys(capsys)


def test_get_bad_assign(capsys: pytest.CaptureFixture[str]) -> None:
    """Assigning text that is not octal is reported when read."""
    number = OctalNumber(value=1)
    number.oct_str = 'not octal'
    with pytest.raises(InvalidConfiguration):
        number.get()
    check_capsys(capsys)


def test_json_round_trip(tmp_path: Path,
                         capsys: pytest.CaptureFixture[str]) -> None:
    """Writing and reading back keeps the declared notation of each member."""
    config = TwoOctConfig(stderr_file=sys.stderr)
    config.mode.set(0o755)
    config.umask.set(0o27)
    assert config.mode.oct_str == '0755'
    assert config.umask.oct_str == '0o027'
    text = config.as_json_string(stderr_file=sys.stderr)
    assert '0755' in text
    assert '0o027' in text
    other = _written_and_read(config, tmp_path)
    assert other.mode.oct_str == '0755'
    assert other.umask.oct_str == '0o027'
    assert other.mode.get() == 0o755
    assert other.umask.get() == 0o27
    check_capsys(capsys)


def test_read_keeps_format(tmp_path: Path,
                           capsys: pytest.CaptureFixture[str]) -> None:
    """A member read from file is rebuilt with the declared format."""
    other = _written_and_read(TwoOctConfig(stderr_file=sys.stderr), tmp_path)
    assert other.mode.prefix == Prefix.ZERO
    assert other.mode.digits == 3
    assert other.umask.prefix == Prefix.ZERO_O
    assert other.umask.digits == 3
    other.mode.set(0o7)
    assert other.mode.oct_str == '0007'
    check_capsys(capsys)


@pytest.mark.parametrize('written,expected_mode,expected_umask', [
    ('"0o17"', '0017', '0o017'),
    ('"017"', '0017', '0o017'),
    ('"17"', '0017', '0o017'),
    ('"  0O0000017  "', '0017', '0o017'),
    ('"7"', '0007', '0o007'),
    (15, '0017', '0o017'),
    (0, '0000', '0o000')])
def test_json_normalizes(written: str | int, expected_mode: str,
                         expected_umask: str,
                         capsys: pytest.CaptureFixture[str]) -> None:
    """A hand-edited file is normalized to the notation declared for it."""
    text = f'{{"mode": {{"oct_str": {written}}}, ' \
           f'"umask": {{"oct_str": {written}}}}}'
    config = TwoOctConfig(from_json_data_text=text, stderr_file=sys.stderr)
    assert config.mode.oct_str == expected_mode
    assert config.umask.oct_str == expected_umask
    assert config.mode.get() == config.umask.get()
    check_capsys(capsys)


def test_cache_after_parse(capsys: pytest.CaptureFixture[str]) -> None:
    """Parsing builds the cached integer, so no read has to rebuild it."""
    text = '{"mode": {"oct_str": "0o644"}, "umask": {"oct_str": 18}}'
    config = TwoOctConfig(from_json_data_text=text, stderr_file=sys.stderr)
    assert config.mode.oct_str == '0644'
    assert config.mode.get() == 0o644
    assert config.umask.get() == 0o22
    check_capsys(capsys)


@pytest.mark.parametrize('written,in_err', [
    ('"8"', 'not octal digits'),
    ('"0x1f"', 'not octal digits'),
    ('""', 'is empty'),
    ('"  "', 'is empty'),
    ('"0o"', 'is empty'),
    ('"-1"', 'not octal digits'),
    ('-1', 'is negative'),
    ('true', 'is a bool'),
    ('null', 'not an octal string or a number'),
    ('1.5', 'not an octal string or a number'),
    ('[1]', 'not an octal string or a number')])
def test_json_bad_value(written: str, in_err: str,
                        capsys: pytest.CaptureFixture[str]) -> None:
    """A JSON value that is not an octal number is refused and told."""
    text = f'{{"mode": {{"oct_str": {written}}}, ' \
           '"umask": {"oct_str": "0"}}'
    with pytest.raises(InvalidConfiguration):
        TwoOctConfig(from_json_data_text=text, stderr_file=sys.stderr)
    check_capsys(capsys, in_err=in_err)


def test_factory_format(capsys: pytest.CaptureFixture[str]) -> None:
    """The factory says the format for the default and for every parse."""
    made = _new_umask()
    assert made.oct_str == '0o022'
    assert made.get() == 0o22
    parsed = _new_umask('{"oct_str": "0755"}')
    assert parsed.oct_str == '0o755'
    assert parsed.prefix == Prefix.ZERO_O
    assert parsed.digits == 3
    check_capsys(capsys)


@pytest.mark.parametrize('value,expected', [
    ('0o17', '17'), ('0O17', '17'), ('17', '17'), ('0755', '0755'),
    ('0', '0'), ('', ''), ('0o', ''), ('o0', 'o0'), ('0o0o17', '0o17')])
def test_strip_prefix(value: str, expected: str) -> None:
    """The '0o' prefix is removed, and a leading zero is kept as a digit."""
    assert OctalNumber.strip_prefix(value) == expected


@pytest.mark.parametrize('value,expected', [
    ('17', '0017'), ('0o17', '0017'), ('  0755  ', '0755'),
    (0o17, '0017'), (0, '0000')])
def test_validator_ok(capsys: pytest.CaptureFixture[str], value: object,
                      expected: str) -> None:
    """The validator normalizes accepted values to the declared notation."""
    validator = OctalStringValidator(prefix=Prefix.ZERO, digits=3)
    assert_validate_member_ok(capsys, validator, value, expected)


@pytest.mark.parametrize('value,error,message', [
    ('8', InvalidConfiguration, 'not octal digits'),
    ('', InvalidConfiguration, 'is empty'),
    (-1, InvalidConfiguration, 'is negative'),
    (True, InvalidConfiguration, 'is a bool'),
    (None, InvalidConfigurationType, 'not an octal string or a number'),
    (1.5, InvalidConfigurationType, 'not an octal string or a number')])
def test_validator_failure(capsys: pytest.CaptureFixture[str], value: object,
                           error: type[Exception], message: str) -> None:
    """The validator refuses and reports what a value is refused for."""
    validator = OctalStringValidator(prefix=Prefix.NONE)
    assert_validate_member_failure(capsys, validator, value, error, message)
