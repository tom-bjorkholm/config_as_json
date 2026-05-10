#! /usr/local/bin/python3
"""Test validators for relations between list-like values."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Any, Optional, TextIO, cast
import pytest
from config_as_json.config import Config
from config_as_json.list_relation_validator import ListRelationKind, \
    ListRelationValidator
from config_as_json.validator import InvalidConfiguration, ValidationPlan, \
    WholeConfigValidationStep, WholeConfigValidator


class RelationConfig(Config):
    """Config class used to test list relation validators."""

    def __init__(self, validator: Optional[WholeConfigValidator] = None,
                 from_json_data_text: Optional[str] = None) -> None:
        """Construct a small config object with relation values."""
        self._validator = validator
        self._unchecked_dicts: list[str] = ['handlers']
        self.a: object = ['api', 'admin']
        self.b: object = ['admin', 'api']
        self.handlers: dict[str, str] = {'api': 'api_handler',
                                         'admin': 'admin_handler'}
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=sys.stderr)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return [] if self._validator is None else [
            WholeConfigValidationStep(validator=self._validator)]


# pylint: disable-next=too-few-public-methods
class _RecordingProjector:
    """Whole-config projector that records the context it received."""

    def __init__(self, projected_value: object) -> None:
        """Store the value returned by the projector."""
        self.projected_value: object = projected_value
        self.calls: list[tuple[Config, TextIO]] = []

    def __call__(self, config: Config, stderr_file: TextIO) -> object:
        """Record one projector call and return the stored value."""
        self.calls.append((config, stderr_file))
        return self.projected_value


def make_config(a_value: object, b_value: object) -> RelationConfig:
    """Return a config object with customized relation values."""
    config = RelationConfig()
    config.a = a_value
    config.b = b_value
    return config


def handler_names_projector(config: Config, stderr_file: TextIO) -> object:
    """Project the configured handler keys as a tuple."""
    _ = stderr_file
    relation_config = cast(RelationConfig, config)
    return tuple(relation_config.handlers.keys())


def case_insensitive_eq(left: object, right: object) -> bool:
    """Compare strings case-insensitively and other values normally."""
    if isinstance(left, str) and isinstance(right, str):
        return left.lower() == right.lower()
    return left == right


def assert_relation_ok(capsys: pytest.CaptureFixture[str],
                       validator: ListRelationValidator,
                       config: RelationConfig) -> None:
    """Assert that one relation validation succeeds silently."""
    validator.validate(config, sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


def assert_relation_failure(capsys: pytest.CaptureFixture[str],
                            validator: ListRelationValidator,
                            config: RelationConfig, exc_type: type[Exception],
                            message: str) -> None:
    """Assert that one relation validation fails with diagnostics."""
    with pytest.raises(exc_type) as exc:
        validator.validate(config, sys.stderr)
    captured = capsys.readouterr()
    assert captured.out == ''
    assert message in captured.err
    assert message in str(exc.value)


@pytest.mark.parametrize(
    'kwargs, exc_type, message',
    [({'kind': object(), 'member_a_name': 'a', 'member_b_name': 'b'},
      TypeError, 'kind must be a ListRelationKind'),
     ({'kind': ListRelationKind.EQUAL, 'member_a_name': object(),
       'member_b_name': 'b'}, TypeError, 'member_a_name must be a str'),
     ({'kind': ListRelationKind.EQUAL, 'member_a_name': '',
       'member_b_name': 'b'}, ValueError,
      'member_a_name must be non-empty'),
     ({'kind': ListRelationKind.EQUAL, 'member_a_name': 'a',
       'member_b_name': object()}, TypeError, 'member_b_name must be a str'),
     ({'kind': ListRelationKind.EQUAL, 'member_a_name': 'a',
       'member_b_name': ''}, ValueError,
      'member_b_name must be non-empty'),
     ({'kind': ListRelationKind.EQUAL, 'member_a_name': 'a',
       'member_b_name': 'b', 'a_projector': object()}, TypeError,
      'a_projector must be None or callable'),
     ({'kind': ListRelationKind.EQUAL, 'member_a_name': 'a',
       'member_b_name': 'b', 'b_projector': object()}, TypeError,
      'b_projector must be None or callable'),
     ({'kind': ListRelationKind.EQUAL, 'member_a_name': 'a',
       'member_b_name': 'b', 'eq_comparator': object()}, TypeError,
      'eq_comparator must be callable'),
     ({'kind': ListRelationKind.EQUAL, 'member_a_name': 'a',
       'member_b_name': 'b', 'lt_comparator': object()}, TypeError,
      'lt_comparator must be callable')])
def test_list_rel_rejects_bad_init(
        kwargs: dict[str, object], exc_type: type[Exception],
        message: str) -> None:
    """Test constructor validation."""
    with pytest.raises(exc_type, match=message):
        ListRelationValidator(**cast(Any, kwargs))


def test_list_rel_stores_args() -> None:
    """Test that constructor arguments are exposed on the validator."""
    a_projector = _RecordingProjector(['a'])
    b_projector = _RecordingProjector(['b'])
    validator = ListRelationValidator(
        kind=ListRelationKind.SET_EQUAL, member_a_name='left',
        member_b_name='right', a_projector=a_projector,
        b_projector=b_projector, eq_comparator=case_insensitive_eq)
    assert validator.kind == ListRelationKind.SET_EQUAL
    assert validator.member_a_name == 'left'
    assert validator.member_b_name == 'right'
    assert validator.a_projector is a_projector
    assert validator.b_projector is b_projector
    assert validator.eq_comparator is case_insensitive_eq
    assert callable(validator.lt_comparator)


@pytest.mark.parametrize(
    'kind, a_value, b_value',
    [(ListRelationKind.EQUAL, ['api', 'admin'], ('api', 'admin')),
     (ListRelationKind.MULTISET_EQUAL, ['a', 'a', 'b'], ('b', 'a', 'a')),
     (ListRelationKind.SET_EQUAL, ['a', 'a'], ('a',)),
     (ListRelationKind.SUBSET, ['a', 'a'], ('a', 'b')),
     (ListRelationKind.DISJOINT, ['a', 'a'], ('b', 'b')),
     (ListRelationKind.MULTISET_EQUAL, [[1], [2]], ([2], [1]))])
def test_list_rel_accepts_valid(
        capsys: pytest.CaptureFixture[str], kind: ListRelationKind,
        a_value: object, b_value: object) -> None:
    """Accept each relation kind, including tuple and unhashable values."""
    validator = ListRelationValidator(kind=kind, member_a_name='a',
                                      member_b_name='b')
    assert_relation_ok(capsys, validator, make_config(a_value, b_value))


@pytest.mark.parametrize(
    'kind, a_value, b_value',
    [(ListRelationKind.EQUAL, ['admin', 'api'], ['api', 'admin']),
     (ListRelationKind.EQUAL, ['api'], ['api', 'admin']),
     (ListRelationKind.MULTISET_EQUAL, ['a', 'b'], ['a', 'a', 'b']),
     (ListRelationKind.SET_EQUAL, ['a'], ['a', 'b']),
     (ListRelationKind.SUBSET, ['c'], ['a', 'b']),
     (ListRelationKind.DISJOINT, ['a'], ['b', 'a'])])
def test_list_rel_rejects_invalid(
        capsys: pytest.CaptureFixture[str], kind: ListRelationKind,
        a_value: object, b_value: object) -> None:
    """Reject every relation kind when the relation does not hold."""
    validator = ListRelationValidator(kind=kind, member_a_name='a',
                                      member_b_name='b')
    assert_relation_failure(capsys, validator, make_config(a_value, b_value),
                            InvalidConfiguration,
                            f'Relation {kind.name} does not hold')


def test_list_rel_custom_eq(capsys: pytest.CaptureFixture[str]) -> None:
    """Use the supplied equality comparator for element matching."""
    validator = ListRelationValidator(
        kind=ListRelationKind.SET_EQUAL, member_a_name='a', member_b_name='b',
        eq_comparator=case_insensitive_eq)
    assert_relation_ok(capsys, validator, make_config(['API'], ['api']))


def test_list_rel_uses_projectors(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate relation values returned from whole-config projectors."""
    a_projector = _RecordingProjector(('api', 'admin'))
    b_projector = _RecordingProjector(['admin', 'api'])
    validator = ListRelationValidator(
        kind=ListRelationKind.MULTISET_EQUAL, member_a_name='route_names',
        member_b_name='handler_names', a_projector=a_projector,
        b_projector=b_projector)
    config = RelationConfig()
    assert_relation_ok(capsys, validator, config)
    assert a_projector.calls == [(config, sys.stderr)]
    assert b_projector.calls == [(config, sys.stderr)]


def test_list_rel_mixes_projector(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate one stored member against one projected sequence."""
    validator = ListRelationValidator(
        kind=ListRelationKind.SET_EQUAL, member_a_name='a',
        member_b_name='handler_names', b_projector=handler_names_projector)
    assert_relation_ok(capsys, validator, RelationConfig())


def test_list_rel_missing_member(capsys: pytest.CaptureFixture[str]) -> None:
    """Raise ``KeyError`` when an unprojected member is missing."""
    validator = ListRelationValidator(kind=ListRelationKind.EQUAL,
                                      member_a_name='missing',
                                      member_b_name='b')
    assert_relation_failure(capsys, validator, RelationConfig(), KeyError,
                            'Member missing not found')


@pytest.mark.parametrize('bad_value', ['text', b'text', bytearray(b'text'), 1])
def test_list_rel_rejects_bad_values(capsys: pytest.CaptureFixture[str],
                                     bad_value: object) -> None:
    """Reject scalar and binary values instead of treating them as lists."""
    validator = ListRelationValidator(kind=ListRelationKind.EQUAL,
                                      member_a_name='a', member_b_name='b')
    assert_relation_failure(capsys, validator, make_config(bad_value, []),
                            TypeError, 'must be a sequence')


def test_list_rel_rejects_proj_str(capsys: pytest.CaptureFixture[str]) -> None:
    """Reject a string returned from a projector."""
    validator = ListRelationValidator(
        kind=ListRelationKind.EQUAL, member_a_name='projected',
        member_b_name='b', a_projector=_RecordingProjector('text'))
    assert_relation_failure(capsys, validator, RelationConfig(), TypeError,
                            'must be a sequence')


def test_list_rel_accepts_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate a list relation through ``Config.validate()``."""
    validator = ListRelationValidator(
        kind=ListRelationKind.SET_EQUAL, member_a_name='a',
        member_b_name='handler_names', b_projector=handler_names_projector)
    config = RelationConfig(
        validator=validator,
        from_json_data_text='{"a": ["api", "admin"], "b": [], '
        '"handlers": {"api": "api_handler", "admin": "admin_handler"}}')
    out, err = capsys.readouterr()
    assert config.a == ['api', 'admin']
    assert config.handlers == {'api': 'api_handler',
                               'admin': 'admin_handler'}
    assert out == ''
    assert err == ''


def test_list_rel_rejects_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Reject an invalid relation while parsing a config."""
    validator = ListRelationValidator(
        kind=ListRelationKind.SET_EQUAL, member_a_name='a',
        member_b_name='handler_names', b_projector=handler_names_projector)
    with pytest.raises(InvalidConfiguration) as exc:
        RelationConfig(
            validator=validator,
            from_json_data_text='{"a": ["api"], "b": [], '
            '"handlers": {"api": "api_handler", '
            '"admin": "admin_handler"}}')
    out, err = capsys.readouterr()
    assert 'Relation SET_EQUAL does not hold' in str(exc.value)
    assert out == ''
    assert 'Relation SET_EQUAL does not hold' in err
