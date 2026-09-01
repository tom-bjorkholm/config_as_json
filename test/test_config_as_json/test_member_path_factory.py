#! /usr/local/bin/python3
"""Test reported paths where something else constructs the nested object.

A nested Config object is not always constructed by the declared type. A
declared ``factory_function`` may construct it, and that factory may be one
that chooses the class by inspecting the JSON data. A ``RadixNumber`` is a
nested Config object of the package itself. All of them are given the path
of the member they are constructed for, and report it.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from io import StringIO
from typing import Optional, TextIO, override
import pytest
from pytest import CaptureFixture
from config_as_json.commontypes import PathOrStr
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_factory import config_factory_from_json, \
    JsonValueMatcher, MatchConfig, MatchConfigSeq
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.hexadecimal_number import HexadecimalNumber
from config_as_json.str_validators import StrValidator
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue, IntFloatValidator, MemberValidationStep, \
    ValidationPlan
from .check_capsys import check_capsys


class Part(Config):
    """Base of the two configuration classes that a factory chooses."""


# The two configuration classes below are the constructor boilerplate that
# every Config class selected by the config factory writes the same way,
# and the teaching example e32_config_factory writes it too.
# pylint: disable=duplicate-code
class CsvPart(Part):
    """The configuration class selected for CSV data."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one CSV part with its default values."""
        self.kind = 'csv'
        self.sep = ','
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file,
                         member_name=member_name)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the one step limiting the separator character."""
        _ = stderr_file
        validator = StrValidator([',', ';'], ignore_case=False)
        return [MemberValidationStep(member_names=['sep'],
                                     validator=validator)]


class JsonPart(Part):
    """The configuration class selected for JSON data."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one JSON part with its default values."""
        self.kind = 'json'
        self.indent = 2
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file,
                         member_name=member_name)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the one step limiting the indentation."""
        _ = stderr_file
        validator = IntFloatValidator(0, 8, None)
        return [MemberValidationStep(member_names=['indent'],
                                     validator=validator)]


# pylint: enable=duplicate-code
MATCH_PARTS: MatchConfigSeq = [
    MatchConfig(match_func=JsonValueMatcher('kind', 'csv'),
                config_class=CsvPart),
    MatchConfig(match_func=JsonValueMatcher('kind', 'json'),
                config_class=JsonPart)
]
"""The rules selecting the configuration class from the JSON data."""


# pylint: disable-next=too-few-public-methods
class PickingFactory:
    """A nested Config factory choosing the class from the JSON data."""

    def __call__(self, *, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> Config:
        """Construct the nested Config that the JSON data selects."""
        return config_factory_from_json(
            match_configs=MATCH_PARTS, auto_ch_hook=ConfigAutoChangeHook(),
            from_json_filename=from_json_filename,
            from_json_data_text=from_json_data_text, stderr_file=stderr_file,
            member_name=member_name)


class PickingParent(Config):
    """Configuration whose nested member is built by the picking factory."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one parent holding one selected part."""
        self.part: Part = CsvPart(stderr_file=stderr_file)
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration with its factory."""
        return {'part': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                      config_type=Part,
                                      factory_function=PickingFactory())}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own, only the nested validation."""
        _ = stderr_file
        return []


@pytest.mark.parametrize('prefix, expected', [
    (None, 'sep'), ('section.pick', 'section.pick.sep')])
def test_factory_function_path(prefix: Optional[str], expected: str,
                               capsys: CaptureFixture[str]) -> None:
    """Test that the config factory hands the path to the chosen class."""
    stderr_file = StringIO()
    with pytest.raises(InvalidConfigurationValue) as exc:
        _ = config_factory_from_json(
            match_configs=MATCH_PARTS, auto_ch_hook=ConfigAutoChangeHook(),
            from_json_data_text='{"kind": "csv", "sep": "|"}',
            stderr_file=stderr_file, member_name=prefix)
    assert exc.value.member_name == expected
    check_capsys(capsys)


@pytest.mark.parametrize('prefix, expected', [
    (None, 'part.indent'), ('root', 'root.part.indent')])
def test_nested_factory_path(prefix: Optional[str], expected: str,
                             capsys: CaptureFixture[str]) -> None:
    """Test that a nested member built by a factory reports its path."""
    stderr_file = StringIO()
    text = '{"part": {"kind": "json", "indent": 99}}'
    with pytest.raises(InvalidConfiguration) as exc:
        _ = PickingParent(from_json_data_text=text, stderr_file=stderr_file,
                          member_name=prefix)
    assert f'Value 99 for {expected} is greater' in str(exc.value)
    assert f'Value 99 for {expected} is greater' in stderr_file.getvalue()
    check_capsys(capsys)


COLOR_FACTORY = HexadecimalNumber.factory(HexadecimalNumber.Prefix.HASH, 6, 0)
"""Say the format that every colour of the palette below is written in."""


def _color(stderr_file: TextIO) -> HexadecimalNumber:
    """Return one colour written in the format of the palette."""
    made = COLOR_FACTORY(stderr_file=stderr_file, member_name=None)
    assert isinstance(made, HexadecimalNumber)
    return made


class Palette(Config):
    """Configuration holding a list of written hexadecimal numbers."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one palette holding two default colours."""
        self.colors: list[HexadecimalNumber] = [_color(stderr_file),
                                                _color(stderr_file)]
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration with its factory."""
        return {'colors': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                        config_type=HexadecimalNumber,
                                        factory_function=COLOR_FACTORY)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own, only the nested validation."""
        _ = stderr_file
        return []


@pytest.mark.parametrize('prefix, expected', [
    (None, 'colors[1].hex_str'), ('theme', 'theme.colors[1].hex_str')])
def test_radix_number_path(prefix: Optional[str], expected: str,
                           capsys: CaptureFixture[str]) -> None:
    """Test that a written number of the package reports its whole path."""
    palette = Palette()
    palette.colors[1].hex_str = 'zz'
    stderr_file = StringIO()
    with pytest.raises(InvalidConfiguration) as exc:
        palette.validate(stderr_file=stderr_file, member_name=prefix)
    assert expected in str(exc.value)
    assert expected in stderr_file.getvalue()
    check_capsys(capsys)


def test_radix_parse_path(capsys: CaptureFixture[str]) -> None:
    """Test that parsing a written number names it by its whole path."""
    stderr_file = StringIO()
    text = '{"colors": [{"hex_str": "#000000"}, {"hex_str": "zz"}]}'
    with pytest.raises(InvalidConfiguration) as exc:
        _ = Palette(from_json_data_text=text, stderr_file=stderr_file,
                    member_name='theme')
    assert 'theme.colors[1].hex_str' in str(exc.value)
    check_capsys(capsys)


def test_radix_read_local_name(capsys: CaptureFixture[str]) -> None:
    """Test that reading a value outside a validation names it locally.

    A read of the value is not part of any traversal, so there is no path to
    report and the local name of the written member is what a diagnostic
    calls it.
    """
    palette = Palette()
    palette.colors[1].hex_str = 'zz'
    with pytest.raises(InvalidConfiguration) as exc:
        _ = palette.colors[1].get()
    assert 'for hex_str' in str(exc.value)
    check_capsys(capsys)


@pytest.mark.parametrize('prefix, expected', [
    (None, 'No matching config class found\n'),
    ('section.pick', 'No matching config class found for section.pick\n')
])
def test_factory_no_match_path(prefix: Optional[str], expected: str,
                               capsys: CaptureFixture[str]) -> None:
    """Test that a factory matching nothing names the member it was for."""
    stderr_file = StringIO()
    with pytest.raises(SystemExit):
        _ = config_factory_from_json(match_configs=MATCH_PARTS,
                                     auto_ch_hook=ConfigAutoChangeHook(),
                                     from_json_data_text='{"kind": "xml"}',
                                     stderr_file=stderr_file,
                                     member_name=prefix)
    assert expected in stderr_file.getvalue()
    check_capsys(capsys)
