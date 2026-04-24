#! /usr/local/bin/python3
# mypy: disable-error-code="no-untyped-def,no-untyped-call"
"""Test list validators."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
import pytest
from config_as_json.list_validators import ListForEachValidator, \
    ListIsOrderedValidator, ListOrderingValidator, ListSizeValidator, \
    ListValueValidator
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue
from .validator_test_helpers import EmptyValidationConfig, \
    SingleMemberValidationConfig, assert_validate_member_failure, \
    assert_validate_member_ok


def casefold_lt(left: str, right: str) -> bool:
    """Compare two strings case-insensitively."""
    return left.casefold() < right.casefold()


@pytest.mark.parametrize(
    'min_value, max_value, allowed_values, exc_type, message',
    [(None, None, None, ValueError,
      'At least one of min_value, max_value, or allowed_values'),
     (None, None, [], ValueError, 'allowed_values must be a non-empty'),
     (3, 2, None, ValueError,
      'min_value must be less than or equal to max_value'),
     (1, 2.0, None, TypeError, 'max_value must be of type int'),
     (None, 2.0, [1.0, 2], TypeError,
      'allowed_values must be a sequence of float')])
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


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(ListValueValidator(1, 5, None), [1, 3, 5], [1, 3, 5]),
     (ListValueValidator(1, 5, None), [], []),
     (ListValueValidator(None, 1.5, [0.5, 1.5]), [0.5, 1.5], [0.5, 1.5]),
     (ListValueValidator('alpha', 'gamma', None,
                         lt_comparator=casefold_lt),
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
