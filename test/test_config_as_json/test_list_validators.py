#! /usr/local/bin/python3
# mypy: disable-error-code="no-untyped-def,no-untyped-call"
"""Test list validators."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from typing import Any, Sequence, cast
import pytest
from config_as_json.list_validators import ListForEachValidator, \
    ListIsOrderedValidator, ListOrderingValidator, ListSizeValidator, \
    ListOfDictsKeysValidator, ListValueTypeValidator, ListValueValidator
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue
from .validator_test_helpers import EmptyValidationConfig, \
    SingleMemberValidationConfig, assert_validate_member_failure, \
    assert_validate_member_ok


def casefold_lt(left: str, right: str) -> bool:
    """Compare two strings case-insensitively."""
    return left.casefold() < right.casefold()


def _assert_allowed_values_fail(capsys, values, exc_type, message) -> None:
    """Assert failure from one validation-time allowed-values result."""
    def current_allowed_values():
        """Return the parameterized allowed-values sequence."""
        return values

    validator = ListValueValidator(1, 5, cast(Any, current_allowed_values))
    cfg = EmptyValidationConfig()
    with pytest.raises(exc_type) as exc:
        validator.validate_member(cfg, 'value', [2], sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert message in str(exc.value)


@pytest.mark.parametrize(
    'min_value, max_value, allowed_values, exc_type, message',
    [(None, None, None, ValueError,
      'At least one of min_value, max_value, or allowed_values'),
     (None, None, [], ValueError, 'allowed_values must be a non-empty'),
     (3, 2, None, ValueError,
      'min_value must be less than or equal to max_value'),
     (1, 2.0, None, TypeError, 'max_value must be of type int'),
     (None, 2.0, [1.0, 2], TypeError,
      'allowed_values must be a sequence of float'),
     (None, None, lambda: [], ValueError,
      'allowed_values must be a non-empty'),
     (None, None, lambda: [1, 2.0], TypeError,
      'allowed_values must be a sequence of int')])
def test_list_value_validator_init_rejects_invalid_constraints(
        min_value, max_value, allowed_values, exc_type, message):
    """Test ListValueValidator constructor validation."""
    with pytest.raises(exc_type) as exc:
        ListValueValidator(min_value=min_value, max_value=max_value,
                           allowed_values=allowed_values)
    assert message in str(exc.value)


def test_list_value_validator_init_uses_custom_comparator():
    """Test that ListValueValidator uses the custom comparator in __init__."""
    with pytest.raises(ValueError) as exc:
        ListValueValidator(min_value='beta', max_value='Alpha',
                           allowed_values=None, lt_comparator=casefold_lt)
    assert 'min_value must be less than or equal to max_value' in \
        str(exc.value)


@pytest.mark.parametrize('validator, member_value, expected', [
    (ListValueValidator(1, 5, None), [1, 3, 5], [1, 3, 5]),
    (ListValueValidator(1, 5, None), [], []),
    (ListValueValidator(None, 1.5, [0.5, 1.5]), [0.5, 1.5], [0.5, 1.5]),
    (ListValueValidator(None, None, lambda: [2, 4]), [2, 4], [2, 4]),
    (ListValueValidator(None, None, lambda: ['json', 'html']),
     ['json'], ['json']),
    (ListValueValidator('alpha', 'gamma', None, lt_comparator=casefold_lt),
     ['Alpha', 'beta'], ['Alpha', 'beta']),
    (ListValueValidator(False, True, [False, True]),
     [False, True], [False, True]),
    (ListValueValidator(1, 5, None), [True, 2], [True, 2])])
def test_list_value_validator_ok(capsys, validator, member_value, expected):
    """Test OK cases of ListValueValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


@pytest.mark.parametrize(
    'validator, member_value, exc_type, message',
    [(ListValueValidator(1, 5, None), (1, 2), InvalidConfiguration,
      'Value for value is not a list'),
     (ListValueValidator(False, True, None), [1], InvalidConfiguration,
      'Value 1 for value at index 0 is not of type bool'),
     (ListValueValidator(2, None, None), [2, 1], InvalidConfiguration,
      'Value 1 for value at index 1 is less than minimum 2'),
     (ListValueValidator(None, 3, None), [2, 4], InvalidConfiguration,
      'Value 4 for value at index 1 is greater than maximum 3'),
     (ListValueValidator(1, 5, [2, 3]), [2, 4],
      InvalidConfigurationValue,
      'Value 4 for value at index 1 is not one of the allowed values')])
def test_list_value_validator_rejects_invalid_member_values(
        capsys, validator, member_value, exc_type, message):
    """Test ListValueValidator failures for type and value constraints."""
    assert_validate_member_failure(
        capsys, validator, member_value, exc_type, message)


def test_list_value_validator_uses_custom_comparator_for_member_values(
        capsys):
    """Test that ListValueValidator uses the custom comparator at runtime."""
    validator = ListValueValidator(min_value='bravo', max_value='delta',
                                   allowed_values=None,
                                   lt_comparator=casefold_lt)
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', ['Echo'], sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value Echo for value at index 0 is greater than maximum delta' \
        in str(exc.value)
    assert out == ''
    assert 'Value Echo for value at index 0 is greater than maximum delta' \
        in err


def test_list_value_validator_requires_allowed_value_to_be_in_range(capsys):
    """Test that allowed values do not bypass range validation in lists."""
    validator = ListValueValidator(1, 5, [6])
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', [6], sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value 6 for value at index 0 is greater than maximum 5' in \
        str(exc.value)
    assert out == ''
    assert 'Value 6 for value at index 0 is greater than maximum 5' in err


def test_list_value_validator_callable_infers_type_when_needed(capsys):
    """A callable supplies the element type when bounds do not."""
    calls: list[int] = []

    def current_allowed_values() -> Sequence[int]:
        """Return allowed values and record the call."""
        calls.append(len(calls))
        return [2, 3]

    validator = ListValueValidator(None, None, current_allowed_values)
    assert calls == [0]
    assert_validate_member_ok(capsys, validator, [2, 3], [2, 3])
    assert calls == [0, 1]


def test_list_value_validator_callable_uses_bounds_type_first(capsys):
    """Bounds provide the element type without calling allowed_values."""
    calls: list[str] = []

    def current_allowed_values() -> Sequence[int]:
        """Return allowed values and record the call."""
        calls.append('validate')
        return [2, 3]

    validator = ListValueValidator(1, 5, current_allowed_values)
    assert not calls
    assert_validate_member_ok(capsys, validator, [2, 3], [2, 3])
    assert calls == ['validate']


def test_list_value_validator_callable_values_are_dynamic(capsys):
    """Every validation uses the callable's current allowed values."""
    allowed_values = [2, 3]

    def current_allowed_values() -> Sequence[int]:
        """Return the current allowed-values list."""
        return allowed_values

    validator = ListValueValidator(None, None, current_allowed_values)
    assert_validate_member_ok(capsys, validator, [2, 3], [2, 3])
    allowed_values = [4, 5]
    message = 'Value 2 for value at index 0 is not one of the allowed values'
    assert_validate_member_failure(capsys, validator, [2],
                                   InvalidConfigurationValue, message)
    assert_validate_member_ok(capsys, validator, [4, 5], [4, 5])


def test_list_value_validator_callable_is_called_once_per_member(capsys):
    """One validate_member call uses one allowed-values snapshot."""
    calls: list[int] = []

    def current_allowed_values() -> Sequence[int]:
        """Return allowed values and record the call."""
        calls.append(len(calls))
        return [1, 2, 3]

    validator = ListValueValidator(None, None, current_allowed_values)
    assert calls == [0]
    assert_validate_member_ok(capsys, validator, [1, 2, 3], [1, 2, 3])
    assert calls == [0, 1]


@pytest.mark.parametrize('values, exc_type, message', [
    ([], ValueError, 'allowed_values must be a non-empty'),
    ([1.0], TypeError, 'allowed_values must be a sequence of int')])
def test_list_value_validator_rejects_dynamic_values(capsys, values,
                                                     exc_type, message):
    """Dynamic allowed values must stay non-empty and type-compatible."""
    _assert_allowed_values_fail(capsys, values, exc_type, message)


def test_list_value_validator_integration_uses_parsed_json(capsys):
    """Test ListValueValidator integration through Config.validate()."""
    cfg = SingleMemberValidationConfig(
        'value', [2], ListValueValidator(1, 5, [2, 3]),
        from_json_data_text='{"value": [2, 3]}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == [2, 3]
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'min_size, max_size, exc_type, message',
    [(True, 1, TypeError, 'min_size must be an int'),
     (0, False, TypeError, 'max_size must be an int'),
     (-1, 0, ValueError, 'min_size must be non-negative'),
     (0, -1, ValueError, 'max_size must be non-negative'),
     (3, 2, ValueError, 'min_size must be less than or equal to max_size')])
def test_list_size_validator_init_rejects_invalid_bounds(
        min_size, max_size, exc_type, message):
    """Test ListSizeValidator constructor validation."""
    with pytest.raises(exc_type) as exc:
        ListSizeValidator(min_size=min_size, max_size=max_size)
    assert message in str(exc.value)


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(ListSizeValidator(0, 0), [], []),
     (ListSizeValidator(1, 3), ['a', 'b'], ['a', 'b'])])
def test_list_size_validator_ok(capsys, validator, member_value, expected):
    """Test OK cases of ListSizeValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


@pytest.mark.parametrize(
    'validator, member_value, message',
    [(ListSizeValidator(0, 2), ('a',), 'Value for value is not a list'),
     (ListSizeValidator(1, 3), [], 'size 0 which is less than minimum 1'),
     (ListSizeValidator(0, 1), [1, 2],
      'size 2 which is greater than maximum 1')])
def test_list_size_validator_rejects_invalid_member_values(
        capsys, validator, member_value, message):
    """Test ListSizeValidator failures."""
    assert_validate_member_failure(
        capsys, validator, member_value, InvalidConfiguration, message)


def test_list_size_validator_integration_uses_parsed_json(capsys):
    """Test ListSizeValidator integration through Config.validate()."""
    cfg = SingleMemberValidationConfig(
        'value', [1], ListSizeValidator(1, 3),
        from_json_data_text='{"value": [1, 2]}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == [1, 2]
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'bad_element_type',
    [None, 'str', [str]])
def test_list_value_type_validator_init_rejects_non_type(bad_element_type):
    """Test ListValueTypeValidator constructor validation."""
    with pytest.raises(TypeError) as exc:
        ListValueTypeValidator(bad_element_type)
    assert 'element_type must be a type' in str(exc.value)


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(ListValueTypeValidator(str), [], []),
     (ListValueTypeValidator(str), ['alpha', 'beta'], ['alpha', 'beta']),
     (ListValueTypeValidator(int), [True, 2], [True, 2]),
     (ListValueTypeValidator(list), [[1], [2, 3]], [[1], [2, 3]])])
def test_list_value_type_validator_ok(
        capsys, validator, member_value, expected):
    """Test OK cases of ListValueTypeValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


@pytest.mark.parametrize(
    'validator, member_value, message',
    [(ListValueTypeValidator(str), ('alpha',),
      'Value for value is not a list'),
     (ListValueTypeValidator(str), ['alpha', 2],
      'Value 2 for value at index 1 is not of type str'),
     (ListValueTypeValidator(bool), [False, 1],
      'Value 1 for value at index 1 is not of type bool')])
def test_list_value_type_validator_rejects_invalid_member_values(
        capsys, validator, member_value, message):
    """Test ListValueTypeValidator failures."""
    assert_validate_member_failure(
        capsys, validator, member_value, InvalidConfiguration, message)


def test_list_value_type_validator_integration_uses_parsed_json(capsys):
    """Test ListValueTypeValidator integration through Config.validate()."""
    cfg = SingleMemberValidationConfig(
        'value', ['alpha'], ListValueTypeValidator(str),
        from_json_data_text='{"value": ["beta", "gamma"]}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == ['beta', 'gamma']
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'element_type, is_ordered, is_reversed, exc_type, message',
    [([], True, False, TypeError,
      'element_type must be one of int, float, str, or bool'),
     (int, False, True, ValueError,
      'is_reversed requires is_ordered to be True')])
def test_list_is_ordered_validator_init_rejects_invalid_arguments(
        element_type, is_ordered, is_reversed, exc_type, message):
    """Test ListIsOrderedValidator constructor validation."""
    with pytest.raises(exc_type) as exc:
        ListIsOrderedValidator(
            element_type=element_type, is_ordered=is_ordered,
            is_reversed=is_reversed)
    assert message in str(exc.value)


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(ListIsOrderedValidator(int), [], []),
     (ListIsOrderedValidator(int), [1, 1, 2], [1, 1, 2]),
     (ListIsOrderedValidator(int, is_reversed=True), [3, 3, 1], [3, 3, 1]),
     (ListIsOrderedValidator(int, is_ordered=False, unique_values=True),
      [3, 1, 2], [3, 1, 2]),
     (ListIsOrderedValidator(int), [True, 2], [True, 2]),
     (ListIsOrderedValidator(str, lt_comparator=casefold_lt),
      ['Alpha', 'beta'], ['Alpha', 'beta'])])
def test_list_is_ordered_validator_ok(
        capsys, validator, member_value, expected):
    """Test OK cases of ListIsOrderedValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


@pytest.mark.parametrize(
    'validator, member_value, message',
    [(ListIsOrderedValidator(int), (1, 2), 'Value for value is not a list'),
     (ListIsOrderedValidator(bool), [1],
      'Value 1 for value at index 0 is not of type bool'),
     (ListIsOrderedValidator(int), [2, 1],
      'Value 1 for value at index 1 is less than previous value 2'),
     (ListIsOrderedValidator(int, is_reversed=True), [2, 3],
      'Value 3 for value at index 1 is greater than previous value 2'),
     (ListIsOrderedValidator(int, is_ordered=False, unique_values=True),
      [2, 1, 2], 'Value 2 for value at index 2 duplicates the value'),
     (ListIsOrderedValidator(str, lt_comparator=casefold_lt),
      ['bravo', 'Alpha'],
      'Value Alpha for value at index 1 is less than previous value bravo')])
def test_list_is_ordered_validator_rejects_invalid_member_values(
        capsys, validator, member_value, message):
    """Test ListIsOrderedValidator failures."""
    assert_validate_member_failure(
        capsys, validator, member_value, InvalidConfiguration, message)


def test_list_is_ordered_validator_integration_uses_parsed_json(capsys):
    """Test ListIsOrderedValidator integration through Config.validate()."""
    cfg = SingleMemberValidationConfig(
        'value', [1], ListIsOrderedValidator(int, unique_values=True),
        from_json_data_text='{"value": [1, 2, 3]}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == [1, 2, 3]
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'element_type, message',
    [([], 'element_type must be one of int, float, str, or bool')])
def test_list_ordering_validator_init_rejects_invalid_arguments(
        element_type, message):
    """Test ListOrderingValidator constructor validation."""
    with pytest.raises(TypeError) as exc:
        ListOrderingValidator(element_type=element_type)
    assert message in str(exc.value)


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(ListOrderingValidator(int), [3, 1, 2], [1, 2, 3]),
     (ListOrderingValidator(int, reverse=True), [3, 1, 2], [3, 2, 1]),
     (ListOrderingValidator(int, order=False, reverse=True),
      [1, 2, 3], [3, 2, 1]),
     (ListOrderingValidator(int, order=False, keep_only_unique=True),
      [3, 1, 3, 2, 1], [3, 1, 2]),
     (ListOrderingValidator(
         int, order=False, reverse=True, keep_only_unique=True),
      [3, 1, 3, 2, 1], [1, 2, 3]),
     (ListOrderingValidator(str, lt_comparator=casefold_lt),
      ['Bravo', 'alpha', 'charlie'], ['alpha', 'Bravo', 'charlie']),
     (ListOrderingValidator(
         str, keep_only_unique=True, lt_comparator=casefold_lt),
      ['alpha', 'Alpha'], ['alpha', 'Alpha']),
     (ListOrderingValidator(int, order=False), [True, 2], [True, 2])])
def test_list_ordering_validator_ok(capsys, validator, member_value, expected):
    """Test OK cases of ListOrderingValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


@pytest.mark.parametrize(
    'validator, member_value, message',
    [(ListOrderingValidator(int), (1, 2), 'Value for value is not a list'),
     (ListOrderingValidator(bool), [1],
      'Value 1 for value at index 0 is not of type bool')])
def test_list_ordering_validator_rejects_invalid_member_values(
        capsys, validator, member_value, message):
    """Test ListOrderingValidator failures."""
    assert_validate_member_failure(
        capsys, validator, member_value, InvalidConfiguration, message)


def test_list_ordering_validator_integration_uses_parsed_json(capsys):
    """Test ListOrderingValidator integration through Config.validate()."""
    cfg = SingleMemberValidationConfig(
        'value', [3], ListOrderingValidator(int, keep_only_unique=True),
        from_json_data_text='{"value": [3, 1, 3, 2]}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == [1, 2, 3]
    assert out == ''
    assert err == ''


def test_list_for_each_validator_init_rejects_empty_element_validators():
    """Empty element_validators must be rejected."""
    with pytest.raises(ValueError) as exc:
        ListForEachValidator(element_validators=[])
    assert 'element_validators must be non-empty' in str(exc.value)


@pytest.mark.parametrize(
    'bad_entry',
    [object(), 'not-a-validator', 42])
def test_list_for_each_validator_init_rejects_non_validator_entry(bad_entry):
    """Entries in element_validators must be MemberValidator instances."""
    good = ListSizeValidator(0, 10)
    with pytest.raises(TypeError) as exc:
        ListForEachValidator(element_validators=[good, bad_entry])
    assert 'element_validators[1] must be a MemberValidator' in str(exc.value)


@pytest.mark.parametrize(
    'bad_element_type',
    ['int', 0, [list]])
def test_list_for_each_validator_init_rejects_non_type_element_type(
        bad_element_type):
    """element_type must be a type when it is not None."""
    with pytest.raises(TypeError) as exc:
        ListForEachValidator(
            element_validators=[ListSizeValidator(0, 10)],
            element_type=bad_element_type)
    assert 'element_type must be a type or None' in str(exc.value)


def test_list_for_each_validator_rejects_non_list_member_value(capsys):
    """The outer member value must be a list."""
    validator = ListForEachValidator(
        element_validators=[ListSizeValidator(0, 10)],
        element_type=list)
    assert_validate_member_failure(
        capsys, validator, (1, 2), InvalidConfiguration,
        'Value for value is not a list')


def test_list_for_each_validator_rejects_element_with_wrong_type(capsys):
    """Elements must match element_type when it is configured."""
    validator = ListForEachValidator(
        element_validators=[ListSizeValidator(0, 10)],
        element_type=list)
    assert_validate_member_failure(
        capsys, validator, [[1, 2], 3], InvalidConfiguration,
        'Value at value[1] has type int; expected list')


def test_list_for_each_validator_skips_type_check_when_element_type_none(
        capsys):
    """Passing element_type=None leaves type checks to inner validators."""
    validator = ListForEachValidator(
        element_validators=[ListSizeValidator(min_size=2, max_size=2)])
    member_value = [[1, 2], [3, 4]]
    cfg = EmptyValidationConfig()
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result == [[1, 2], [3, 4]]
    assert out == ''
    assert err == ''


def test_list_for_each_validator_accepts_empty_outer_list(capsys):
    """An empty outer list is accepted because there are no elements."""
    validator = ListForEachValidator(
        element_validators=[ListSizeValidator(2, 2)],
        element_type=list)
    assert_validate_member_ok(capsys, validator, [], [])


def test_list_for_each_validator_chains_normalized_value(capsys):
    """Each inner validator sees the value returned by the previous one."""
    sort_inner = ListOrderingValidator(int)
    check_sorted = ListIsOrderedValidator(int)
    validator = ListForEachValidator(
        element_validators=[sort_inner, check_sorted],
        element_type=list)
    member_value = [[3, 1, 2], [5, 4]]
    cfg = EmptyValidationConfig()
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result == [[1, 2, 3], [4, 5]]
    assert out == ''
    assert err == ''


def test_list_for_each_validator_returns_new_list_without_mutating_input(
        capsys):
    """The caller's list must not be mutated in place."""
    validator = ListForEachValidator(
        element_validators=[ListOrderingValidator(int)],
        element_type=list)
    inner_original = [2, 1]
    member_value = [inner_original]
    cfg = EmptyValidationConfig()
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result == [[1, 2]]
    assert result is not member_value
    assert member_value == [[2, 1]]
    assert inner_original == [2, 1]
    assert out == ''
    assert err == ''


def test_list_for_each_validator_propagates_inner_failure(capsys):
    """An inner validator's exception must propagate to the caller."""
    validator = ListForEachValidator(
        element_validators=[ListValueValidator(0, 10, None)],
        element_type=list)
    assert_validate_member_failure(
        capsys, validator, [[0, 1], [9, 11]], InvalidConfiguration,
        'Value 11 for value[1] at index 1 is greater than maximum 10')


def test_list_for_each_validator_propagates_inner_allowed_values_failure(
        capsys):
    """Inner validators can raise InvalidConfigurationValue."""
    validator = ListForEachValidator(
        element_validators=[ListValueValidator(None, None, [1, 2, 3])],
        element_type=list)
    assert_validate_member_failure(
        capsys, validator, [[1, 2], [3, 4]], InvalidConfigurationValue,
        'Value 4 for value[1] at index 1 is not one of the allowed values')


def test_list_for_each_validator_integration_uses_parsed_json(capsys):
    """Test ListForEachValidator integration through Config.validate()."""
    per_row = ListForEachValidator(
        element_validators=[ListValueValidator(0, 9, None)],
        element_type=list)
    cfg = SingleMemberValidationConfig(
        'value', [[0]], per_row,
        from_json_data_text='{"value": [[1, 2], [3, 4]]}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == [[1, 2], [3, 4]]
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'mandatory_keys, allowed_keys, exc_type, message',
    [(['name', 3], None, TypeError,
      'mandatory_keys[1] must be a str'),
     (['name', 'name'], None, ValueError,
      "mandatory_keys[1]='name' duplicates an earlier entry"),
     (['name'], ['enabled', object()], TypeError,
      'allowed_keys[1] must be a str'),
     (['name'], ['enabled', 'enabled'], ValueError,
      "allowed_keys[1]='enabled' duplicates an earlier entry")])
def test_list_of_dicts_keys_validator_init_rejects_invalid_keys(
        mandatory_keys, allowed_keys, exc_type, message):
    """Test ListOfDictsKeysValidator constructor validation."""
    with pytest.raises(exc_type) as exc:
        ListOfDictsKeysValidator(mandatory_keys=mandatory_keys,
                                 allowed_keys=allowed_keys)
    assert message in str(exc.value)


def test_list_of_dicts_keys_validator_init_rejects_non_bool_extra_policy():
    """allow_extra_dict_keys must be a bool."""
    with pytest.raises(TypeError) as exc:
        ListOfDictsKeysValidator(
            mandatory_keys=['name'],
            allow_extra_dict_keys=cast(Any, 'yes'))
    assert 'allow_extra_dict_keys must be a bool' in str(exc.value)


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(ListOfDictsKeysValidator(['name']), [], []),
     (ListOfDictsKeysValidator(['name']), [{'name': 'extract'}],
      [{'name': 'extract'}]),
     (ListOfDictsKeysValidator(['name'], ['enabled']),
      [{'name': 'extract'}, {'name': 'load', 'enabled': True}],
      [{'name': 'extract'}, {'name': 'load', 'enabled': True}]),
     (ListOfDictsKeysValidator([], ['name']),
      [{'name': 'optional'}, {}], [{'name': 'optional'}, {}])])
def test_list_of_dicts_keys_validator_ok(
        capsys, validator, member_value, expected):
    """Test OK cases of ListOfDictsKeysValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


def test_list_of_dicts_keys_validator_accepts_extra_keys_when_allowed(
        capsys):
    """Open per-dict policy allows extra keys in list elements."""
    validator = ListOfDictsKeysValidator(
        mandatory_keys=['name'], allow_extra_dict_keys=True)
    member_value = [{'name': 'extract', 'runtime_seconds': 12}]
    assert_validate_member_ok(capsys, validator, member_value, member_value)


def test_list_of_dicts_keys_validator_open_policy_requires_mandatory(
        capsys):
    """Open per-dict policy still rejects missing mandatory keys."""
    validator = ListOfDictsKeysValidator(
        mandatory_keys=['name'], allow_extra_dict_keys=True)
    assert_validate_member_failure(
        capsys, validator, [{'runtime_seconds': 12}],
        InvalidConfiguration, "Mandatory key 'name' is missing from value[0]")


@pytest.mark.parametrize(
    'member_value, message',
    [({'name': 'extract'}, 'Value for value is not a list'),
     ([{'name': 'extract'}, ['name', 'load']],
      'Value at value[1] has type list; expected dict'),
     ([{'name': 'extract'}, {'enabled': True}],
      "Mandatory key 'name' is missing from value[1]"),
     ([{'name': 'extract', 'extra': 'boom'}],
      "Unknown key 'extra' in value[0]")])
def test_list_of_dicts_keys_validator_rejects_invalid_member_values(
        capsys, member_value, message):
    """Test ListOfDictsKeysValidator failures."""
    validator = ListOfDictsKeysValidator(['name'], ['enabled'])
    assert_validate_member_failure(
        capsys, validator, member_value, InvalidConfiguration, message)


def test_list_of_dicts_keys_validator_returns_new_outer_list(capsys):
    """Test ListOfDictsKeysValidator delegates through ListForEachValidator."""
    member_value = [{'name': 'extract'}]
    cfg = EmptyValidationConfig()
    validator = ListOfDictsKeysValidator(['name'])
    result = validator.validate_member(cfg, 'value', member_value,
                                       sys.stderr)
    out, err = capsys.readouterr()
    assert result == member_value
    assert result is not member_value
    assert out == ''
    assert err == ''


def test_list_of_dicts_keys_validator_integration_uses_parsed_json(capsys):
    """Test ListOfDictsKeysValidator integration through Config.validate()."""
    validator = ListOfDictsKeysValidator(['name'], ['enabled'])
    cfg = SingleMemberValidationConfig(
        'value', [{'name': 'extract'}], validator,
        from_json_data_text='{"value": [{"name": "load", "enabled": true}]}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == [{'name': 'load', 'enabled': True}]
    assert out == ''
    assert err == ''
