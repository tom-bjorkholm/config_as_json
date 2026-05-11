#! /usr/local/bin/python3
"""Test validators for relations between list-like values."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from collections.abc import Callable
from typing import Any, Optional, TextIO, cast
import pytest
from config_as_json.config import Config
from config_as_json.list_relation_validator import ListRelationKind, \
    ListRelationValidator, _contains_equal, _is_disjoint, \
    _is_distinct_subset, _is_multiset_equal
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


def standard_eq(left: object, right: object) -> bool:
    """Compare values using normal Python equality."""
    return left == right


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


def relation_holds_for_kind(kind: ListRelationKind, values_a: list[object],
                            values_b: list[object], eq_comparator: Callable[
                                [object, object], bool]) -> bool:
    """Return relation result from the protected relation dispatcher."""
    validator = ListRelationValidator(
        kind=kind, member_a_name='a', member_b_name='b',
        eq_comparator=eq_comparator)
    # pylint: disable-next=protected-access
    return validator._relation_holds(values_a, values_b)


@pytest.mark.parametrize(
    'values, value, eq_comparator, expected',
    [pytest.param([], 'api', standard_eq, False, id='empty-list'),
     pytest.param(['api'], 'api', standard_eq, True, id='first-item'),
     pytest.param(['api', 'admin'], 'admin', standard_eq, True,
                  id='later-item'),
     pytest.param(['api'], 'admin', standard_eq, False, id='missing-item'),
     pytest.param(['api', 'api'], 'api', standard_eq, True,
                  id='duplicate-match'),
     pytest.param([[1], [2]], [2], standard_eq, True, id='unhashable-match'),
     pytest.param([[1]], [2], standard_eq, False, id='unhashable-missing'),
     pytest.param(['API'], 'api', case_insensitive_eq, True,
                  id='custom-equality-match'),
     pytest.param(['API'], 'admin', case_insensitive_eq, False,
                  id='custom-equality-missing')])
def test_contains_equal(values: list[object], value: object,
                        eq_comparator: Callable[[object, object], bool],
                        expected: bool) -> None:
    """Test protected containment checks with edge-case list values."""
    assert _contains_equal(values, value, eq_comparator) is expected


@pytest.mark.parametrize(
    'values_a, values_b, eq_comparator, expected',
    [pytest.param([], [], standard_eq, True, id='empty-is-subset-of-empty'),
     pytest.param([], ['api'], standard_eq, True,
                  id='empty-is-subset-of-nonempty'),
     pytest.param(['api'], [], standard_eq, False,
                  id='nonempty-is-not-subset-of-empty'),
     pytest.param(['api'], ['api'], standard_eq, True, id='same-single-value'),
     pytest.param(['admin', 'api'], ['api', 'admin'], standard_eq, True,
                  id='order-ignored'),
     pytest.param(['api'], ['api', 'admin'], standard_eq, True,
                  id='extra-values-in-superset'),
     pytest.param(['metrics'], ['api', 'admin'], standard_eq, False,
                  id='missing-distinct-value'),
     pytest.param(['api', 'api'], ['api'], standard_eq, True,
                  id='duplicates-in-subset-ignored'),
     pytest.param(['api'], ['api', 'api'], standard_eq, True,
                  id='duplicates-in-superset-ok'),
     pytest.param(['api', 'api', 'admin'], ['api'], standard_eq, False,
                  id='missing-one-distinct-value'),
     pytest.param([[1], [1]], [[1]], standard_eq, True,
                  id='unhashable-duplicates-ignored'),
     pytest.param([[1], [2]], [[2], [1]], standard_eq, True,
                  id='unhashable-order-ignored'),
     pytest.param([[1], [2]], [[1]], standard_eq, False,
                  id='unhashable-missing-value'),
     pytest.param(['API', 'api'], ['api'], case_insensitive_eq, True,
                  id='custom-equality-duplicates-ignored'),
     pytest.param(['API', 'admin'], ['api'], case_insensitive_eq, False,
                  id='custom-equality-missing-value')])
def test_is_distinct_subset(values_a: list[object], values_b: list[object],
                            eq_comparator: Callable[[object, object], bool],
                            expected: bool) -> None:
    """Test protected distinct-subset checks with duplicates and empties."""
    assert _is_distinct_subset(values_a, values_b, eq_comparator) is expected


@pytest.mark.parametrize(
    'values_a, values_b, eq_comparator, expected',
    [pytest.param([], [], standard_eq, True, id='empty-multisets'),
     pytest.param(['api'], ['api'], standard_eq, True, id='same-single-value'),
     pytest.param(['api', 'admin'], ['admin', 'api'], standard_eq, True,
                  id='order-ignored'),
     pytest.param(['api', 'api', 'admin'], ['api', 'admin', 'api'],
                  standard_eq, True, id='duplicate-counts-match'),
     pytest.param(['api', 'api'], ['api', 'admin'], standard_eq, False,
                  id='same-length-duplicate-count-mismatch'),
     pytest.param(['api'], ['api', 'api'], standard_eq, False,
                  id='length-mismatch'),
     pytest.param(['api', 'admin'], ['api', 'metrics'], standard_eq, False,
                  id='same-length-different-value'),
     pytest.param([[1], [2]], [[2], [1]], standard_eq, True,
                  id='unhashable-order-ignored'),
     pytest.param([[1], [1]], [[1], [2]], standard_eq, False,
                  id='unhashable-count-mismatch'),
     pytest.param(['API', 'a'], ['api', 'A'], case_insensitive_eq, True,
                  id='custom-equality-match'),
     pytest.param(['API', 'api'], ['api', 'admin'], case_insensitive_eq, False,
                  id='custom-equality-count-mismatch')])
def test_is_multiset_equal(values_a: list[object], values_b: list[object],
                           eq_comparator: Callable[[object, object], bool],
                           expected: bool) -> None:
    """Test protected multiset equality checks with order and counts."""
    assert _is_multiset_equal(values_a, values_b, eq_comparator) is expected


@pytest.mark.parametrize(
    'values_a, values_b, eq_comparator, expected',
    [pytest.param([], [], standard_eq, True, id='two-empty-lists'),
     pytest.param([], ['api'], standard_eq, True, id='empty-left'),
     pytest.param(['api'], [], standard_eq, True, id='empty-right'),
     pytest.param(['api'], ['admin'], standard_eq, True, id='no-overlap'),
     pytest.param(['api'], ['admin', 'api'], standard_eq, False,
                  id='one-shared-value'),
     pytest.param(['api', 'api'], ['admin', 'api'], standard_eq, False,
                  id='duplicate-left-overlap'),
     pytest.param(['api'], ['admin', 'api', 'api'], standard_eq, False,
                  id='duplicate-right-overlap'),
     pytest.param([[1]], [[2]], standard_eq, True, id='unhashable-no-overlap'),
     pytest.param([[1]], [[2], [1]], standard_eq, False,
                  id='unhashable-overlap'),
     pytest.param(['API'], ['api'], case_insensitive_eq, False,
                  id='custom-equality-overlap'),
     pytest.param(['API'], ['admin'], case_insensitive_eq, True,
                  id='custom-equality-no-overlap')])
def test_is_disjoint(values_a: list[object], values_b: list[object],
                     eq_comparator: Callable[[object, object], bool],
                     expected: bool) -> None:
    """Test protected disjoint checks with empty lists and duplicates."""
    assert _is_disjoint(values_a, values_b, eq_comparator) is expected


@pytest.mark.parametrize(
    'kind, values_a, values_b, eq_comparator, expected',
    [pytest.param(ListRelationKind.EQUAL, [], [], standard_eq, True,
                  id='equal-empty'),
     pytest.param(ListRelationKind.EQUAL, ['api'], ['api'], standard_eq, True,
                  id='equal-same-order'),
     pytest.param(ListRelationKind.EQUAL, ['admin', 'api'], ['api', 'admin'],
                  standard_eq, False, id='equal-order-matters'),
     pytest.param(ListRelationKind.EQUAL, ['api'], ['api', 'admin'],
                  standard_eq, False, id='equal-length-matters'),
     pytest.param(ListRelationKind.EQUAL, [[1]], [[1]], standard_eq, True,
                  id='equal-unhashable-values'),
     pytest.param(ListRelationKind.EQUAL, ['API'], ['api'],
                  case_insensitive_eq, True, id='equal-custom-equality'),
     pytest.param(ListRelationKind.MULTISET_EQUAL, [], [], standard_eq, True,
                  id='multiset-empty'),
     pytest.param(ListRelationKind.MULTISET_EQUAL, ['api', 'admin'],
                  ['admin', 'api'], standard_eq, True,
                  id='multiset-order-ignored'),
     pytest.param(ListRelationKind.MULTISET_EQUAL, ['api', 'api'],
                  ['api', 'admin'], standard_eq, False,
                  id='multiset-counts-matter'),
     pytest.param(ListRelationKind.MULTISET_EQUAL, ['api'], ['api', 'api'],
                  standard_eq, False, id='multiset-length-matters'),
     pytest.param(ListRelationKind.MULTISET_EQUAL, [[1], [2]], [[2], [1]],
                  standard_eq, True, id='multiset-unhashable-values'),
     pytest.param(ListRelationKind.MULTISET_EQUAL, ['API', 'admin'],
                  ['api', 'ADMIN'], case_insensitive_eq, True,
                  id='multiset-custom-equality'),
     pytest.param(ListRelationKind.SET_EQUAL, [], [], standard_eq, True,
                  id='set-empty'),
     pytest.param(ListRelationKind.SET_EQUAL, ['api', 'api'], ['api'],
                  standard_eq, True, id='set-duplicates-ignored'),
     pytest.param(ListRelationKind.SET_EQUAL, ['admin', 'api'],
                  ['api', 'admin'], standard_eq, True, id='set-order-ignored'),
     pytest.param(ListRelationKind.SET_EQUAL, ['api'], ['api', 'admin'],
                  standard_eq, False, id='set-missing-value'),
     pytest.param(ListRelationKind.SET_EQUAL, [[1], [1]], [[1]], standard_eq,
                  True, id='set-unhashable-values'),
     pytest.param(ListRelationKind.SET_EQUAL, ['API'], ['api'],
                  case_insensitive_eq, True, id='set-custom-equality'),
     pytest.param(ListRelationKind.SUBSET, [], ['api'], standard_eq, True,
                  id='subset-empty-left'),
     pytest.param(ListRelationKind.SUBSET, ['api', 'api'], ['api'],
                  standard_eq, True, id='subset-duplicates-ignored'),
     pytest.param(ListRelationKind.SUBSET, ['api'], ['admin', 'api'],
                  standard_eq, True, id='subset-extra-right-values-ok'),
     pytest.param(ListRelationKind.SUBSET, ['api', 'admin'], ['api'],
                  standard_eq, False, id='subset-missing-right-value'),
     pytest.param(ListRelationKind.SUBSET, [[1]], [[2], [1]], standard_eq,
                  True, id='subset-unhashable-values'),
     pytest.param(ListRelationKind.SUBSET, ['API'], ['api'],
                  case_insensitive_eq, True, id='subset-custom-equality'),
     pytest.param(ListRelationKind.DISJOINT, [], [], standard_eq, True,
                  id='disjoint-empty'),
     pytest.param(ListRelationKind.DISJOINT, ['api'], ['admin'], standard_eq,
                  True, id='disjoint-no-overlap'),
     pytest.param(ListRelationKind.DISJOINT, ['api'], ['admin', 'api'],
                  standard_eq, False, id='disjoint-shared-value'),
     pytest.param(ListRelationKind.DISJOINT, ['api', 'api'], ['api'],
                  standard_eq, False, id='disjoint-duplicates-overlap'),
     pytest.param(ListRelationKind.DISJOINT, [[1]], [[2]], standard_eq, True,
                  id='disjoint-unhashable-no-overlap'),
     pytest.param(ListRelationKind.DISJOINT, ['API'], ['api'],
                  case_insensitive_eq, False,
                  id='disjoint-custom-equality-overlap')])
def test_list_rel_relation_holds(
        kind: ListRelationKind, values_a: list[object], values_b: list[object],
        eq_comparator: Callable[[object, object], bool],
        expected: bool) -> None:
    """Test protected relation dispatch for every relation kind."""
    assert relation_holds_for_kind(
        kind, values_a, values_b, eq_comparator) is expected


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
