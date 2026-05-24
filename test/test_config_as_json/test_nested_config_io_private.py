#! /usr/local/bin/python3
"""Test private helpers used for nested Config JSON I/O."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

# The tests in this file intentionally exercise private functions. These
# helpers own shape combinations that normal JSON input or public validation
# catches before serialization reaches them.
# pylint: disable=protected-access

from io import StringIO
from typing import TextIO
import pytest
import config_as_json._config_nesting_io as nesting_io
from config_as_json.config import Config
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind
from .test_nested_config import AuditSection, ReportSection


def _nesting(kind: ConfigNestingKind,
             config_type: type[Config] = ReportSection) -> ConfigNesting:
    """Return one nested Config declaration for private helper tests."""
    return ConfigNesting(kind=kind, config_type=config_type)


def _by_key_nestings() -> list[ConfigNesting]:
    """Return keyed nested Config declarations for private helper tests."""
    return [
        ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                      config_type=ReportSection,
                      discriminator_key='participants'),
        ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                      config_type=AuditSection, discriminator_key='audit')
    ]


def _bad_json_data_case(
        case_name: str,
        stderr_file: TextIO) -> tuple[list[ConfigNesting], object]:
    """Return one bad nested serialization case."""
    report = ReportSection(stderr_file=stderr_file)
    audit = AuditSection(stderr_file=stderr_file)
    cases: dict[str, tuple[list[ConfigNesting], object]] = {
        'member-wrong-type': (
            [_nesting(ConfigNestingKind.MEMBER)], object()),
        'list-not-list': (
            [_nesting(ConfigNestingKind.LIST_ELEMENT)], 'not-a-list'),
        'list-wrong-item': (
            [_nesting(ConfigNestingKind.LIST_ELEMENT)], [object()]),
        'dict-not-dict': (
            [_nesting(ConfigNestingKind.DICT_VALUE)], 'not-a-dict'),
        'dict-bad-key': (
            [_nesting(ConfigNestingKind.DICT_VALUE)], {7: report}),
        'dict-wrong-value': (
            [_nesting(ConfigNestingKind.DICT_VALUE)], {'bad': object()}),
        'by-key-not-dict': (
            _by_key_nestings(), 'not-a-dict'),
        'by-key-bad-key': (
            _by_key_nestings(), {7: 'plain'}),
        'by-key-unlisted-config': (
            _by_key_nestings(), {'summary': report}),
        'by-key-wrong-type': (
            _by_key_nestings(), {'participants': audit})
    }
    return cases[case_name]


def _bad_from_json_case(case_name: str) \
        -> tuple[list[ConfigNesting], object]:
    """Return one bad nested parse case with non-JSON key types."""
    if case_name == 'dict-value':
        return [_nesting(ConfigNestingKind.DICT_VALUE)], {7: {}}
    return _by_key_nestings(), {7: {}}


def test_nested_encoder_bad_value() -> None:
    """Test that the nested JSON encoder delegates unsupported values."""
    encoder = nesting_io._NestedConfigEncoder()
    with pytest.raises(TypeError):
        encoder.default(object())


@pytest.mark.parametrize('case_name', ['dict-value', 'by-key'])
def test_nested_from_json_bad_keys(case_name: str) -> None:
    """Test JSON parse helpers with dict keys JSON cannot produce."""
    stderr_file = StringIO()
    nestings, json_data = _bad_from_json_case(case_name)
    with pytest.raises(KeyError) as exc:
        _ = nesting_io._nested_config_from_json(member_name='child',
                                                json_data=json_data,
                                                nestings=nestings,
                                                stderr_file=stderr_file)
    message = 'Nested Config member child keys must be strings'
    assert message in str(exc.value)
    assert message in stderr_file.getvalue()


@pytest.mark.parametrize('case_name, message', [
    ('member-wrong-type',
     'Nested Config member child must be ReportSection'),
    ('list-not-list', 'Nested Config member child must be a list'),
    ('list-wrong-item',
     'Nested Config member child[0] must be ReportSection'),
    ('dict-not-dict', 'Nested Config member child must be a dict'),
    ('dict-bad-key', 'Nested Config member child keys must be strings'),
    ('dict-wrong-value',
     'Nested Config member child[bad] must be ReportSection'),
    ('by-key-not-dict', 'Nested Config member child must be a dict'),
    ('by-key-bad-key', 'Nested Config member child keys must be strings'),
    ('by-key-unlisted-config',
     'Nested Config member child[summary] has no DICT_VALUE_BY_KEY'),
    ('by-key-wrong-type',
     'Nested Config member child[participants] must be ReportSection')
])
def test_nested_json_bad_shapes(case_name: str, message: str) -> None:
    """Test nested serialization helper shape and type errors."""
    stderr_file = StringIO()
    nestings, member_value = _bad_json_data_case(case_name, stderr_file)
    with pytest.raises(TypeError) as exc:
        _ = nesting_io._nested_config_json_data(member_name='child',
                                                member_value=member_value,
                                                nestings=nestings,
                                                stderr_file=stderr_file)
    assert message in str(exc.value)
    assert stderr_file.getvalue() == ''


def test_nested_json_optional_none() -> None:
    """Test optional nested serialization when the value is None."""
    stderr_file = StringIO()
    result = nesting_io._nested_config_json_data(
        member_name='child', member_value=None,
        nestings=[_nesting(ConfigNestingKind.OPTIONAL_MEMBER)],
        stderr_file=stderr_file)
    assert result is None
    assert stderr_file.getvalue() == ''
