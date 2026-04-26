#! /usr/local/bin/python3
# mypy: disable-error-code="no-untyped-def,no-untyped-call"
"""Test dict validators."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import dataclasses
import sys
from typing import Callable, Optional, TextIO
import pytest
from config_as_json.config import Config
from config_as_json.dict_validators import (DictForEachValidator,
                                            DictKeysValidator, DictRule,
                                            _inner_member_name,
                                            _validate_dict_member_value,
                                            _validate_for_each_rules,
                                            _validate_string_keys)
from config_as_json.list_validators import (ListForEachValidator,
                                            ListSizeValidator,
                                            ListValueValidator)
from config_as_json.validator import (IntFloatValidator,
                                      InvalidConfiguration,
                                      InvalidConfigurationValue,
                                      MemberValidator)
from .validator_test_helpers import (EmptyValidationConfig,
                                     SingleMemberValidationConfig,
                                     assert_validate_member_failure,
                                     assert_validate_member_ok)


Recording = list[tuple[str, str, object]]


def _replace_with_changed(value: object) -> object:
    """Transform any input into the constant string ``'changed'``."""
    _ = value
    return 'changed'


def _add_one(value: object) -> object:
    """Transform an int input by adding ``1``."""
    assert isinstance(value, int)
    return value + 1


def _add_ten(value: object) -> object:
    """Transform an int input by adding ``10``."""
    assert isinstance(value, int)
    return value + 10


# pylint: disable-next=too-few-public-methods
class _RecordingValidator(MemberValidator):
    """Recording MemberValidator used to assert call order and threading.

    Each call appends ``(label, member_name, member_value)`` to a shared
    recording list. If ``transform`` is given, the recorded value is
    transformed before being returned, so subsequent validators in the
    chain see the new value. Without ``transform``, the value is returned
    unchanged.
    """

    def __init__(
            self, label: str, recording: Recording,
            transform: Optional[Callable[[object], object]] = None) -> None:
        """Initialize the recording validator."""
        self.label: str = label
        self.recording: Recording = recording
        self.transform: Optional[Callable[[object], object]] = transform

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Record the call and optionally transform the value."""
        _ = config, stderr_file
        self.recording.append((self.label, member_name, member_value))
        if self.transform is None:
            return member_value
        return self.transform(member_value)


# ---- _validate_dict_member_value -------------------------------------------


@pytest.mark.parametrize(
    'member_value',
    [[], [1, 2], (1, 2), 'a', 1, 1.0, True, None])
def test_validate_dict_member_value_rejects_non_dict(capsys, member_value):
    """Non-dict member values must be rejected with a clear message."""
    with pytest.raises(InvalidConfiguration) as exc:
        _validate_dict_member_value('value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value for value is not a dict' in str(exc.value)
    assert out == ''
    assert 'Value for value is not a dict' in err


def test_validate_dict_member_value_returns_dict_unchanged(capsys):
    """A dict member value is returned as the same object."""
    member_value = {'a': 1, 'b': 2}
    result = _validate_dict_member_value('value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result is member_value
    assert out == ''
    assert err == ''


def test_validate_dict_member_value_accepts_empty_dict(capsys):
    """An empty dict is a valid dict member value."""
    member_value: dict[object, object] = {}
    result = _validate_dict_member_value('value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result is member_value
    assert out == ''
    assert err == ''


# ---- _validate_string_keys -------------------------------------------------


@pytest.mark.parametrize(
    'keys, exc_type, message',
    [(['a', 1, 'b'], TypeError, 'mandatory_keys[1] must be a str'),
     (['a', 'b', 2.5], TypeError, 'mandatory_keys[2] must be a str'),
     (['a', 'b', None], TypeError, 'mandatory_keys[2] must be a str'),
     (['a', 'a'], ValueError,
      "mandatory_keys[1]='a' duplicates an earlier entry"),
     (['x', 'y', 'x'], ValueError,
      "mandatory_keys[2]='x' duplicates an earlier entry")])
def test_validate_string_keys_rejects_invalid(keys, exc_type, message):
    """Non-string entries and duplicates must be rejected."""
    with pytest.raises(exc_type) as exc:
        _validate_string_keys(keys, 'mandatory_keys')
    assert message in str(exc.value)


@pytest.mark.parametrize('keys', [[], ['a'], ['a', 'b', 'c'], ('a', 'b')])
def test_validate_string_keys_accepts_valid(keys):
    """Empty and well-formed sequences are accepted."""
    _validate_string_keys(keys, 'parameter')


def test_validate_string_keys_uses_provided_parameter_name():
    """Error messages mention the parameter name passed by the caller."""
    bad_keys: list[object] = ['a', 1]
    with pytest.raises(TypeError) as exc:
        _validate_string_keys(bad_keys,  # type: ignore[arg-type]
                              'allowed_keys')
    assert 'allowed_keys[1] must be a str' in str(exc.value)


# ---- _inner_member_name ----------------------------------------------------


@pytest.mark.parametrize(
    'outer, key, expected',
    [('cfg', 'port', 'cfg[port]'),
     ('cfg.server', 'port', 'cfg.server[port]'),
     ('value[0]', 'name', 'value[0][name]'),
     ('', 'a', '[a]'),
     ('outer', '', 'outer[]')])
def test_inner_member_name(outer, key, expected):
    """The combined inner name has the documented bracket form."""
    assert _inner_member_name(outer, key) == expected


# ---- _validate_for_each_rules ----------------------------------------------


def test_validate_for_each_rules_rejects_empty():
    """Empty rules sequence must be rejected."""
    with pytest.raises(ValueError) as exc:
        _validate_for_each_rules([])
    assert 'rules must be non-empty' in str(exc.value)


@pytest.mark.parametrize('bad_entry', [object(), 'not-a-rule', 42, None])
def test_validate_for_each_rules_rejects_non_dict_rule(bad_entry):
    """Entries in rules must all be DictRule instances."""
    good = DictRule(keys=['x'], validators=[ListSizeValidator(0, 1)])
    with pytest.raises(TypeError) as exc:
        _validate_for_each_rules([good, bad_entry])
    assert 'rules[1] must be a DictRule' in str(exc.value)


def test_validate_for_each_rules_accepts_valid():
    """A non-empty sequence of DictRule instances is accepted."""
    rule = DictRule(keys=['x'], validators=[ListSizeValidator(0, 1)])
    _validate_for_each_rules([rule, rule])


# ---- DictKeysValidator: __init__ -------------------------------------------


@pytest.mark.parametrize(
    'mandatory_keys, allowed_keys, exc_type, message',
    [(['a', 1], None, TypeError, 'mandatory_keys[1] must be a str'),
     (['a', 'a'], None, ValueError,
      "mandatory_keys[1]='a' duplicates an earlier entry"),
     (['a'], ['b', 2], TypeError, 'allowed_keys[1] must be a str'),
     (['a'], ['b', 'b'], ValueError,
      "allowed_keys[1]='b' duplicates an earlier entry")])
def test_dict_keys_validator_init_rejects_invalid_arguments(
        mandatory_keys, allowed_keys, exc_type, message):
    """Test that DictKeysValidator validates its inputs in __init__."""
    with pytest.raises(exc_type) as exc:
        DictKeysValidator(mandatory_keys=mandatory_keys,
                          allowed_keys=allowed_keys)
    assert message in str(exc.value)


def test_dict_keys_validator_init_accepts_empty_mandatory_keys():
    """Empty mandatory_keys is a valid configuration."""
    validator = DictKeysValidator(mandatory_keys=[], allowed_keys=['a'])
    assert isinstance(validator.mandatory_keys, tuple)
    assert len(validator.mandatory_keys) == 0
    assert validator.allowed_keys == frozenset({'a'})


def test_dict_keys_validator_init_unions_allowed_with_mandatory():
    """allowed_keys is internally unioned with mandatory_keys."""
    validator = DictKeysValidator(
        mandatory_keys=['a', 'b'], allowed_keys=['c'])
    assert validator.mandatory_keys == ('a', 'b')
    assert validator.allowed_keys == frozenset({'a', 'b', 'c'})


def test_dict_keys_validator_init_accepts_overlap():
    """Overlap between mandatory_keys and allowed_keys is harmless."""
    validator = DictKeysValidator(
        mandatory_keys=['a'], allowed_keys=['a', 'b'])
    assert validator.allowed_keys == frozenset({'a', 'b'})


def test_dict_keys_validator_init_treats_none_allowed_as_empty():
    """allowed_keys=None means only mandatory keys are permitted."""
    validator = DictKeysValidator(mandatory_keys=['a'])
    assert validator.allowed_keys == frozenset({'a'})


# ---- DictKeysValidator: validate_member ------------------------------------


@pytest.mark.parametrize(
    'mandatory_keys, allowed_keys, member_value',
    [(['a'], None, {'a': 1}),
     (['a', 'b'], ['c'], {'a': 1, 'b': 2}),
     (['a'], ['b'], {'a': 1, 'b': 2}),
     ([], ['a'], {'a': 1}),
     ([], None, {}),
     ([], ['a'], {})])
def test_dict_keys_validator_ok(
        capsys, mandatory_keys, allowed_keys, member_value):
    """Test that DictKeysValidator passes well-formed dicts unchanged."""
    validator = DictKeysValidator(mandatory_keys=mandatory_keys,
                                  allowed_keys=allowed_keys)
    assert_validate_member_ok(capsys, validator, member_value, member_value)


def test_dict_keys_validator_returns_same_dict_object(capsys):
    """The validator returns the exact same dict object on success."""
    validator = DictKeysValidator(mandatory_keys=['a'])
    member_value = {'a': 1}
    cfg = EmptyValidationConfig()
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result is member_value
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'mandatory_keys, allowed_keys, member_value, message',
    [([], None, [1, 2], 'Value for value is not a dict'),
     (['a'], None, {}, "Mandatory key 'a' is missing from value"),
     (['a', 'b'], None, {'a': 1},
      "Mandatory key 'b' is missing from value"),
     (['a'], None, {'a': 1, 'b': 2}, "Unknown key 'b' in value"),
     (['a'], ['b'], {'a': 1, 'c': 3}, "Unknown key 'c' in value")])
def test_dict_keys_validator_rejects_invalid_member_values(
        capsys, mandatory_keys, allowed_keys, member_value, message):
    """Test that bad dicts are rejected with descriptive errors."""
    validator = DictKeysValidator(mandatory_keys=mandatory_keys,
                                  allowed_keys=allowed_keys)
    assert_validate_member_failure(
        capsys, validator, member_value, InvalidConfiguration, message)


def test_dict_keys_validator_reports_missing_before_unknown(capsys):
    """A missing mandatory key is reported before any unknown key."""
    validator = DictKeysValidator(mandatory_keys=['a'], allowed_keys=['b'])
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', {'c': 3}, sys.stderr)
    out, err = capsys.readouterr()
    assert "Mandatory key 'a' is missing" in str(exc.value)
    assert 'Unknown key' not in str(exc.value)
    assert out == ''
    assert "Mandatory key 'a' is missing" in err


def test_dict_keys_validator_reports_first_missing_in_mandatory_order(capsys):
    """Test that mandatory keys are reported in declaration order."""
    validator = DictKeysValidator(mandatory_keys=['z', 'a'])
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', {}, sys.stderr)
    out, err = capsys.readouterr()
    assert "Mandatory key 'z' is missing" in str(exc.value)
    assert "Mandatory key 'a'" not in str(exc.value)
    assert out == ''
    assert "Mandatory key 'z' is missing" in err


def test_dict_keys_validator_reports_first_unknown_in_insertion_order(capsys):
    """Unknown keys are reported in input dict insertion order."""
    validator = DictKeysValidator(mandatory_keys=['a'], allowed_keys=None)
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(
            cfg, 'value', {'a': 1, 'z': 2, 'm': 3}, sys.stderr)
    out, err = capsys.readouterr()
    assert "Unknown key 'z' in value" in str(exc.value)
    assert "Unknown key 'm'" not in str(exc.value)
    assert out == ''
    assert "Unknown key 'z' in value" in err


def test_dict_keys_validator_integration_uses_parsed_json(capsys):
    """Test that DictKeysValidator runs via the Config validation plan.

    The default value provides the expected dict keys so that Config's
    own pre-validation dict-key check accepts the JSON. The validator
    then re-checks the keys according to its own policy.
    """
    cfg = SingleMemberValidationConfig(
        'value', {'a': 0, 'b': 0}, DictKeysValidator(['a'], ['b']),
        from_json_data_text='{"value": {"a": 1, "b": 2}}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == {'a': 1, 'b': 2}
    assert out == ''
    assert err == ''


# ---- DictRule --------------------------------------------------------------


@pytest.mark.parametrize(
    'keys, validators, exc_type, message',
    [([], [ListSizeValidator(0, 1)], ValueError, 'keys must be non-empty'),
     (['a'], [], ValueError, 'validators must be non-empty'),
     (['a', 1], [ListSizeValidator(0, 1)], TypeError,
      'keys[1] must be a str'),
     (['a', 'a'], [ListSizeValidator(0, 1)], ValueError,
      "keys[1]='a' duplicates an earlier entry"),
     (['a'], [ListSizeValidator(0, 1), 'not-a-validator'], TypeError,
      'validators[1] must be a MemberValidator')])
def test_dict_rule_init_rejects_invalid_arguments(
        keys, validators, exc_type, message):
    """Test that DictRule validates its inputs through __post_init__."""
    with pytest.raises(exc_type) as exc:
        DictRule(keys=keys, validators=validators)
    assert message in str(exc.value)


def test_dict_rule_init_accepts_valid_arguments():
    """A well-formed DictRule stores its keys and validators."""
    inner = ListSizeValidator(0, 1)
    rule = DictRule(keys=['a', 'b'], validators=[inner])
    assert list(rule.keys) == ['a', 'b']
    assert list(rule.validators) == [inner]


def test_dict_rule_is_frozen():
    """Test that DictRule instances remain immutable.

    This test does NOT exist to verify that ``frozen=True`` works (that
    is library functionality already covered by Python's own tests). It
    locks in our deliberate design choice that DictRule is immutable. A
    future change that drops ``frozen=True`` (e.g. to add a method that
    mutates state) will fail this test and force the change to be
    reviewed explicitly.
    """
    rule = DictRule(keys=['a'], validators=[ListSizeValidator(0, 1)])
    with pytest.raises(dataclasses.FrozenInstanceError):
        rule.keys = ['b']  # type: ignore[misc]


# ---- DictForEachValidator: __init__ ----------------------------------------


def test_dict_for_each_validator_init_rejects_empty_rules():
    """Empty rules sequence must be rejected."""
    with pytest.raises(ValueError) as exc:
        DictForEachValidator(rules=[])
    assert 'rules must be non-empty' in str(exc.value)


@pytest.mark.parametrize('bad_entry', [object(), 'not-a-rule', 42])
def test_dict_for_each_validator_init_rejects_non_dict_rule(bad_entry):
    """Each entry in rules must be a DictRule instance."""
    good = DictRule(keys=['x'], validators=[ListSizeValidator(0, 1)])
    with pytest.raises(TypeError) as exc:
        DictForEachValidator(rules=[good, bad_entry])
    assert 'rules[1] must be a DictRule' in str(exc.value)


def test_dict_for_each_validator_init_stores_rules_as_list():
    """The constructor copies the input sequence into a list attribute."""
    rule = DictRule(keys=['x'], validators=[ListSizeValidator(0, 1)])
    validator = DictForEachValidator(rules=(rule,))
    assert isinstance(validator.rules, list)
    assert validator.rules == [rule]


# ---- DictForEachValidator: validate_member ---------------------------------


def test_dict_for_each_validator_rejects_non_dict_member(capsys):
    """The outer member value must be a dict."""
    rule = DictRule(keys=['x'], validators=[ListSizeValidator(0, 1)])
    validator = DictForEachValidator(rules=[rule])
    assert_validate_member_failure(
        capsys, validator, [1, 2], InvalidConfiguration,
        'Value for value is not a dict')


def test_dict_for_each_validator_skips_absent_rule_keys(capsys):
    """Rule keys missing from the input dict are silently skipped."""
    rule = DictRule(keys=['present', 'absent'],
                    validators=[ListSizeValidator(0, 5)])
    validator = DictForEachValidator(rules=[rule])
    cfg = EmptyValidationConfig()
    result = validator.validate_member(
        cfg, 'value', {'present': [1, 2]}, sys.stderr)
    out, err = capsys.readouterr()
    assert result == {'present': [1, 2]}
    assert out == ''
    assert err == ''


def test_dict_for_each_validator_passes_through_unmapped_keys(capsys):
    """Keys in the dict not covered by any rule are copied through."""
    rule = DictRule(keys=['ruled'], validators=[ListSizeValidator(0, 5)])
    validator = DictForEachValidator(rules=[rule])
    cfg = EmptyValidationConfig()
    member_value = {'ruled': [1], 'extra': 99, 'other': 'x'}
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result == {'ruled': [1], 'extra': 99, 'other': 'x'}
    assert out == ''
    assert err == ''


def test_dict_for_each_validator_returns_new_dict(capsys):
    """A successful validation returns a new dict object."""
    rule = DictRule(keys=['a'], validators=[ListSizeValidator(0, 5)])
    validator = DictForEachValidator(rules=[rule])
    cfg = EmptyValidationConfig()
    member_value = {'a': [1, 2]}
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result is not member_value
    assert result == member_value
    assert out == ''
    assert err == ''


def test_dict_for_each_validator_does_not_mutate_input(capsys):
    """Test that the input dict is not mutated by value transforms."""
    recording: Recording = []
    rule = DictRule(keys=['a'], validators=[_RecordingValidator(
        'x', recording, transform=_replace_with_changed)])
    validator = DictForEachValidator(rules=[rule])
    cfg = EmptyValidationConfig()
    member_value = {'a': 'original'}
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result == {'a': 'changed'}
    assert member_value == {'a': 'original'}
    assert out == ''
    assert err == ''


def test_dict_for_each_validator_preserves_input_key_order(capsys):
    """The returned dict preserves the input dict's key insertion order."""
    recording: Recording = []
    rule = DictRule(keys=['a', 'b'], validators=[
        _RecordingValidator('x', recording)])
    validator = DictForEachValidator(rules=[rule])
    cfg = EmptyValidationConfig()
    member_value = {'b': 1, 'a': 2, 'extra': 3}
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert isinstance(result, dict)
    assert list(result.keys()) == ['b', 'a', 'extra']
    assert out == ''
    assert err == ''


def test_dict_for_each_validator_order_matches_docstring(capsys):
    """The order of inner validator calls matches the class docstring example.

    Reproduces the example::

        ra = DictRule(keys=['a', 'b'], validators=[v1, v2])
        rb = DictRule(keys=['a', 'b', 'c'], validators=[v3, v4])
        v = DictForEachValidator(rules=[ra, rb])

    Verifies the documented call sequence and the inner ``member_name``
    path used at each call. The input dict also carries an extra key
    that no rule covers, to confirm such keys are ignored by the rule
    iteration but copied through to the result.
    """
    recording: Recording = []
    v1 = _RecordingValidator('v1', recording)
    v2 = _RecordingValidator('v2', recording)
    v3 = _RecordingValidator('v3', recording)
    v4 = _RecordingValidator('v4', recording)
    ra = DictRule(keys=['a', 'b'], validators=[v1, v2])
    rb = DictRule(keys=['a', 'b', 'c'], validators=[v3, v4])
    validator = DictForEachValidator(rules=[ra, rb])
    cfg = EmptyValidationConfig()
    member_value = {'a': 10, 'b': 20, 'c': 30, 'd': 40}
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    expected = [
        ('v1', 'value[a]', 10),
        ('v2', 'value[a]', 10),
        ('v1', 'value[b]', 20),
        ('v2', 'value[b]', 20),
        ('v3', 'value[a]', 10),
        ('v4', 'value[a]', 10),
        ('v3', 'value[b]', 20),
        ('v4', 'value[b]', 20),
        ('v3', 'value[c]', 30),
        ('v4', 'value[c]', 30),
    ]
    assert recording == expected
    assert result == {'a': 10, 'b': 20, 'c': 30, 'd': 40}
    assert out == ''
    assert err == ''


def test_dict_for_each_validator_skipped_key_does_not_record(capsys):
    """An absent rule key produces no validator calls for that key."""
    recording: Recording = []
    rule = DictRule(keys=['present', 'absent'],
                    validators=[_RecordingValidator('seen', recording)])
    validator = DictForEachValidator(rules=[rule])
    cfg = EmptyValidationConfig()
    validator.validate_member(cfg, 'value', {'present': 1}, sys.stderr)
    out, err = capsys.readouterr()
    assert recording == [('seen', 'value[present]', 1)]
    assert out == ''
    assert err == ''


def test_dict_for_each_validator_threads_value_within_rule(capsys):
    """Validators inside one rule see the value normalized by the previous."""
    recording: Recording = []
    plus_one = _RecordingValidator('+1', recording, transform=_add_one)
    plus_ten = _RecordingValidator('+10', recording, transform=_add_ten)
    rule = DictRule(keys=['a'], validators=[plus_one, plus_ten])
    validator = DictForEachValidator(rules=[rule])
    cfg = EmptyValidationConfig()
    result = validator.validate_member(cfg, 'value', {'a': 0}, sys.stderr)
    out, err = capsys.readouterr()
    assert recording == [
        ('+1', 'value[a]', 0),
        ('+10', 'value[a]', 1),
    ]
    assert result == {'a': 11}
    assert out == ''
    assert err == ''


def test_dict_for_each_validator_threads_value_across_rules(capsys):
    """A later rule sees the value left by earlier rules at the same key."""
    recording: Recording = []
    rule_a = DictRule(keys=['k'], validators=[_RecordingValidator(
        'first', recording, transform=_add_one)])
    rule_b = DictRule(keys=['k'], validators=[_RecordingValidator(
        'second', recording)])
    validator = DictForEachValidator(rules=[rule_a, rule_b])
    cfg = EmptyValidationConfig()
    result = validator.validate_member(cfg, 'value', {'k': 100}, sys.stderr)
    out, err = capsys.readouterr()
    assert recording == [
        ('first', 'value[k]', 100),
        ('second', 'value[k]', 101),
    ]
    assert result == {'k': 101}
    assert out == ''
    assert err == ''


def test_dict_for_each_validator_propagates_inner_failure(capsys):
    """An inner validator's InvalidConfiguration propagates with key path."""
    rule = DictRule(keys=['port'],
                    validators=[ListValueValidator(0, 10, None)])
    validator = DictForEachValidator(rules=[rule])
    assert_validate_member_failure(
        capsys, validator, {'port': [9, 11]}, InvalidConfiguration,
        'Value 11 for value[port] at index 1 is greater than maximum 10')


def test_dict_for_each_validator_propagates_inner_allowed_values_failure(
        capsys):
    """Inner validators can raise InvalidConfigurationValue."""
    rule = DictRule(keys=['code'],
                    validators=[ListValueValidator(None, None, [1, 2, 3])])
    validator = DictForEachValidator(rules=[rule])
    assert_validate_member_failure(
        capsys, validator, {'code': [1, 4]}, InvalidConfigurationValue,
        'Value 4 for value[code] at index 1 '
        'is not one of the allowed values')


def test_dict_for_each_validator_integration_uses_parsed_json(capsys):
    """Test that DictForEachValidator runs via the Config validation plan.

    The default value provides keys ``port`` and ``name`` so that
    Config's own pre-validation dict-key check accepts the JSON. The
    validator then validates the value at ``port`` and copies ``name``
    through unchanged.
    """
    rule = DictRule(keys=['port'],
                    validators=[IntFloatValidator(1, 65535, None)])
    cfg = SingleMemberValidationConfig(
        'value', {'port': 0, 'name': 'seed'},
        DictForEachValidator(rules=[rule]),
        from_json_data_text='{"value": {"port": 8080, "name": "srv"}}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == {'port': 8080, 'name': 'srv'}
    assert out == ''
    assert err == ''


# ---- Nested integration ----------------------------------------------------


def _make_list_of_dicts_validator() -> ListForEachValidator:
    """Build a validator for ``list[dict[str, list[int]]]`` configs.

    Each element must have keys ``name`` and ``ports``. ``ports`` must be a
    list of int values in the range ``[1, 65535]``. ``name`` is checked
    only for presence by ``DictKeysValidator``.
    """
    return ListForEachValidator(
        element_validators=[
            DictKeysValidator(mandatory_keys=['name', 'ports']),
            DictForEachValidator(rules=[
                DictRule(keys=['ports'],
                         validators=[ListValueValidator(1, 65535, None)])])
        ],
        element_type=dict)


def test_nested_list_of_dicts_with_lists_ok(capsys):
    """Validate ``list[dict[str, list[int]]]`` end to end via parsed JSON."""
    cfg = SingleMemberValidationConfig(
        'value', [{'name': 'seed', 'ports': [80]}],
        _make_list_of_dicts_validator(),
        from_json_data_text=(
            '{"value": ['
            '{"name": "srv1", "ports": [80, 443]},'
            '{"name": "srv2", "ports": [22]}'
            ']}'))
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == [
        {'name': 'srv1', 'ports': [80, 443]},
        {'name': 'srv2', 'ports': [22]}]
    assert out == ''
    assert err == ''


def test_nested_list_of_dicts_with_lists_inner_failure_path(capsys):
    """Errors in nested ``list[dict[str, list[int]]]`` carry the full path."""
    validator = _make_list_of_dicts_validator()
    cfg = EmptyValidationConfig()
    member_value = [
        {'name': 'srv1', 'ports': [80]},
        {'name': 'srv2', 'ports': [22, 70000]}]
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert ('Value 70000 for value[1][ports] at index 1 '
            'is greater than maximum 65535') in str(exc.value)
    assert out == ''
    assert ('Value 70000 for value[1][ports] at index 1 '
            'is greater than maximum 65535') in err


def test_nested_list_of_dicts_with_lists_unknown_key_path(capsys):
    """Unknown keys in nested dicts carry the outer list index."""
    validator = _make_list_of_dicts_validator()
    cfg = EmptyValidationConfig()
    member_value = [
        {'name': 'srv1', 'ports': [80]},
        {'name': 'srv2', 'ports': [22], 'extra': 1}]
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert "Unknown key 'extra' in value[1]" in str(exc.value)
    assert out == ''
    assert "Unknown key 'extra' in value[1]" in err


def _make_dict_of_lists_of_dicts_validator() -> DictForEachValidator:
    """Build a validator for ``dict[str, list[dict[str, int]]]`` configs.

    Top-level keys ``admin`` and ``guest`` map to lists of profile dicts.
    Each profile dict has a ``level`` int in the range ``[0, 9]``.
    """
    profile_validator = DictForEachValidator(rules=[
        DictRule(keys=['level'], validators=[IntFloatValidator(0, 9, None)])])
    list_of_profiles = ListForEachValidator(
        element_validators=[profile_validator],
        element_type=dict)
    return DictForEachValidator(rules=[
        DictRule(keys=['admin', 'guest'], validators=[list_of_profiles])])


def test_nested_dict_of_lists_of_dicts_ok(capsys):
    """Validate ``dict[str, list[dict[str, int]]]`` end to end via JSON."""
    cfg = SingleMemberValidationConfig(
        'value', {'admin': [{'level': 0}], 'guest': [{'level': 0}]},
        _make_dict_of_lists_of_dicts_validator(),
        from_json_data_text=(
            '{"value": {'
            '"admin": [{"level": 5}, {"level": 9}],'
            '"guest": [{"level": 1}]'
            '}}'))
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == {
        'admin': [{'level': 5}, {'level': 9}],
        'guest': [{'level': 1}]}
    assert out == ''
    assert err == ''


def test_nested_dict_of_lists_of_dicts_inner_failure_path(capsys):
    """Errors in nested ``dict[str, list[dict[str, int]]]`` carry full path."""
    validator = _make_dict_of_lists_of_dicts_validator()
    cfg = EmptyValidationConfig()
    member_value = {
        'admin': [{'level': 5}, {'level': 99}],
        'guest': [{'level': 1}]}
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert ('Value 99 for value[admin][1][level] '
            'is greater than maximum 9') in str(exc.value)
    assert out == ''
    assert ('Value 99 for value[admin][1][level] '
            'is greater than maximum 9') in err
