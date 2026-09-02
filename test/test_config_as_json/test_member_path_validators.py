#! /usr/local/bin/python3
"""Test that every validator reports the whole path of the member.

A validator is given the path of the member it validates, and reports that
path instead of the local attribute name. The configuration below holds the
validated member two nesting levels down, so a validator that builds a name
of its own instead of reporting the name it was given is caught.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from io import StringIO
from typing import Optional, TextIO, override
import pytest
from pytest import CaptureFixture
from config_as_json.as_dict_view_validator import AsDictViewValidator, \
    public_attrs_to_dict
from config_as_json.char_encoding import CharEncodingValidator
from config_as_json.commontypes import PathOrStr
from config_as_json.config import Config
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.csv_dialect import CsvDialectValidator
from config_as_json.dict_validators import DictForEachValidator, \
    DictKeysValidator, DictKeyValueTypesValidator, DictRule
from config_as_json.discriminated_dict_validators import DictVariant, \
    DiscriminatedDictValidator
from config_as_json.hexadecimal_number import HexadecimalNumber, \
    HexadecimalStringValidator
from config_as_json.list_element_validators import ListForEachValidator, \
    ListOfDictsKeysValidator
from config_as_json.list_ordering_validators import ListIsOrderedValidator, \
    ListKeyOrderingValidator, ListOrderingValidator
from config_as_json.list_value_validators import ListSizeValidator, \
    ListValueTypeValidator, ListValueValidator
from config_as_json.octal_number import OctalNumber, OctalStringValidator
from config_as_json.optional_validator import OptionalMemberValidator
from config_as_json.projected_validators import ProjectedMemberValidator
from config_as_json.str_validators import StrCaseChangeValidator, \
    StrCaseSpec, StrCaseValidator, StrLenValidator, StrPositionSpec, \
    StrValidator
from config_as_json.type_validators import ValueAsTypeValidator, \
    ValueTypeValidator
from config_as_json.validator import CallingMemberValidator, \
    CallingWholeConfigValidator, InvalidConfiguration, IntFloatValidator, \
    MemberValidator, MemberValidatorSequence, MemberValidationStep, \
    ValidationPlan, ValidationStep
from .check_capsys import check_capsys
from .validator_test_helpers import SingleMemberValidationConfig

PATH = 'section.thing.value'
"""The path of the validated member in the configuration below."""


class PathHolder(Config):
    """Configuration holding the object that owns the validated member."""

    def __init__(self, thing: SingleMemberValidationConfig,
                 member_name: Optional[str] = None) -> None:
        """Construct one holder of the given nested configuration."""
        self.thing = thing
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration."""
        return {'thing': ConfigNesting(
            kind=ConfigNestingKind.MEMBER,
            config_type=SingleMemberValidationConfig)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own, only the nested validation."""
        _ = stderr_file
        return []


class PathOuter(Config):
    """Top level configuration, so that a path has two dots."""

    def __init__(self, section: PathHolder,
                 member_name: Optional[str] = None) -> None:
        """Construct one top level configuration holding one holder."""
        self.section = section
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration."""
        return {'section': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                         config_type=PathHolder)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own, only the nested validation."""
        _ = stderr_file
        return []


# pylint: disable-next=too-few-public-methods
class Viewed:
    """An object that a dictionary view can be projected from."""

    def __init__(self) -> None:
        """Construct one object holding one public attribute."""
        self.cpu = 1


def _to_int(value: object) -> int:
    """Return the integer that a converted member value holds."""
    assert isinstance(value, str)
    return int(value)


def _projected_length(config: Config, member_name: str, member_value: object,
                      stderr_file: TextIO) -> object:
    """Return the length of the member value, as the projected value."""
    _ = config, member_name, stderr_file
    return len(str(member_value))


def _case_validator() -> StrCaseValidator:
    """Return one validator demanding an upper case first character."""
    return StrCaseValidator(StrPositionSpec.FIRST_IN_STRING, StrCaseSpec.UPPER,
                            StrCaseSpec.LOWER)


def _case_change_validator() -> StrCaseChangeValidator:
    """Return one validator changing the case of the first character."""
    return StrCaseChangeValidator(StrPositionSpec.FIRST_IN_STRING,
                                  StrCaseSpec.UPPER, StrCaseSpec.LOWER)


def _dict_rule() -> DictRule:
    """Return one rule limiting the value at one dictionary key."""
    return DictRule(keys=['cpu'], validators=[IntFloatValidator(1, 9, None)])


def _discriminated() -> DiscriminatedDictValidator:
    """Return one validator selecting a dictionary variant by its kind."""
    rule = DictRule(keys=['sep'],
                    validators=[StrValidator([','], ignore_case=False)])
    variant = DictVariant(mandatory_keys=['sep'], rules=[rule])
    return DiscriminatedDictValidator(discriminator_key='kind',
                                      variants={'csv': variant})


CASES: list[tuple[str, MemberValidator, object, object, str]] = [
    ('int_float', IntFloatValidator(1, 9, None), 5, 99, PATH),
    ('str', StrValidator(['csv'], ignore_case=False), 'csv', 'nope', PATH),
    ('str_len', StrLenValidator(1, 3), 'ab', 'abcd', PATH),
    ('str_case', _case_validator(), 'Abc', 'abc', PATH),
    ('str_case_change', _case_change_validator(), 'Abc', 5, PATH),
    ('value_type', ValueTypeValidator(str), 'a', 5, PATH),
    ('value_as_type',
     ValueAsTypeValidator(int, direct_types=[int],
                          convertable_types={str: _to_int}), 5, 'zz', PATH),
    ('dict_keys', DictKeysValidator(['a']), {'a': 1}, {'b': 1}, PATH),
    ('dict_for_each', DictForEachValidator([_dict_rule()]), {'cpu': 1},
     {'cpu': 99}, f'{PATH}[cpu]'),
    ('dict_key_value_types', DictKeyValueTypesValidator(str, int), {'a': 1},
     {'a': 'x'}, PATH),
    ('list_value', ListValueValidator(1, 9, None), [1], [99], PATH),
    ('list_size', ListSizeValidator(1, 2), [1], [], PATH),
    ('list_value_type', ListValueTypeValidator(int), [1], ['a'], PATH),
    ('list_is_ordered', ListIsOrderedValidator(int), [1, 2], [2, 1], PATH),
    ('list_ordering', ListOrderingValidator(int), [2, 1], ['a'], PATH),
    ('list_key_ordering',
     ListKeyOrderingValidator(element_type=str, key=len, key_type=int),
     ['a', 'bb'], [5], PATH),
    ('list_for_each',
     ListForEachValidator([StrValidator(['a'], ignore_case=False)]), ['a'],
     ['b'], f'{PATH}[0]'),
    ('list_of_dicts_keys', ListOfDictsKeysValidator(['a']), [{'a': 1}],
     [{'b': 1}], f'{PATH}[0]'),
    ('discriminated_dict', _discriminated(), {'kind': 'csv', 'sep': ','},
     {'kind': 'csv', 'sep': ';'}, f'{PATH}[sep]'),
    ('projected_member',
     ProjectedMemberValidator(projector=_projected_length,
                              validators=[IntFloatValidator(0, 5, None)]),
     'abc', 'abcdefgh', PATH),
    ('as_dict_view',
     AsDictViewValidator(non_dict_type=Viewed, rules=[_dict_rule()],
                         to_dict=public_attrs_to_dict), {'cpu': 1},
     {'cpu': 99}, f'{PATH}[cpu]'),
    ('optional_member',
     OptionalMemberValidator(StrValidator(['a'], ignore_case=False)), None,
     'b', PATH),
    ('validator_sequence',
     MemberValidatorSequence([StrValidator(['a'], ignore_case=False)]), 'a',
     'b', PATH),
    ('csv_dialect', CsvDialectValidator(), {'name': 'csv.excel'},
     {'name': 'nope'}, PATH),
    ('char_encoding', CharEncodingValidator(), 'utf-8', 'nope', PATH),
    ('hexadecimal', HexadecimalStringValidator(HexadecimalNumber.Prefix.NONE),
     'ff', 'zz', PATH),
    ('octal', OctalStringValidator(OctalNumber.Prefix.NONE), '17', '99', PATH)
]
"""One validator per case, with an accepted and a rejected value."""


def _nested_config(validator: MemberValidator, good: object) \
        -> tuple[PathOuter, SingleMemberValidationConfig]:
    """Return one configuration holding the validated member two levels in."""
    thing = SingleMemberValidationConfig(attr_name='value', member_value=good,
                                         validator=validator)
    return PathOuter(PathHolder(thing)), thing


@pytest.mark.parametrize('validator, good, bad, expected',
                         [case[1:] for case in CASES],
                         ids=[case[0] for case in CASES])
def test_validator_paths(validator: MemberValidator, good: object, bad: object,
                         expected: str, capsys: CaptureFixture[str]) -> None:
    """Test that one validator reports the whole path of the member."""
    outer, thing = _nested_config(validator, good)
    setattr(thing, 'value', bad)
    stderr_file = StringIO()
    with pytest.raises(Exception) as exc:
        outer.validate(stderr_file=stderr_file, member_name=None)
    assert expected in str(exc.value)
    assert expected in stderr_file.getvalue()
    check_capsys(capsys)


class CallingConfig(Config):
    """Configuration validated by a method that is given the member path."""

    def __init__(self, member_name: Optional[str] = None) -> None:
        """Construct one configuration with an accepted default value."""
        self.value = 'ok'
        self._method = 'check_value'
        self._answer: object = None
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         member_name=member_name)

    def check_value(self, value: object, told_name: str) -> bool:
        """Reject a value while telling what the member was called."""
        if value == 'ok':
            return True
        msg = f'Invalid configuration: {told_name} holds {value}.'
        raise InvalidConfiguration(msg)

    def answer(self, value: object) -> object:
        """Return what the test told this object to answer."""
        _ = value
        return self._answer

    def use_method(self, method: str, answer: object) -> None:
        """Make the plan call the named method, answering as told."""
        self._method = method
        self._answer = answer

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the step calling the checking method of this object."""
        _ = stderr_file
        told = None if self._method != 'check_value' else 'told_name'
        validator = CallingMemberValidator(method_name=self._method,
                                           arg_name_value='value',
                                           arg_name_member_name=told)
        return [MemberValidationStep(member_names=['value'],
                                     validator=validator)]


class CallingHolder(Config):
    """Configuration holding one method-validated nested configuration."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one holder of one method-validated configuration."""
        self.things: list[CallingConfig] = [CallingConfig(), CallingConfig()]
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration."""
        return {'things': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                        config_type=CallingConfig)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own, only the nested validation."""
        _ = stderr_file
        return []


def test_calling_validator_path(capsys: CaptureFixture[str]) -> None:
    """Test that a called method is handed the whole path of the member."""
    holder = CallingHolder()
    holder.things[1].value = 'bad'
    stderr_file = StringIO()
    with pytest.raises(InvalidConfiguration) as exc:
        holder.validate(stderr_file=stderr_file, member_name=None)
    assert 'things[1].value holds bad.' in str(exc.value)
    check_capsys(capsys)


@pytest.mark.parametrize('method, result, error, told', [
    ('missing', True, AttributeError,
     'Method missing for things[1].value not found in Config object.'),
    ('value', True, TypeError,
     'Method value for things[1].value in Config object is not callable.'),
    ('answer', False, InvalidConfiguration,
     'Method answer for things[1].value returned False.'),
    ('answer', 'maybe', TypeError,
     'Method answer for things[1].value returned str;')
])
def test_calling_method_paths(method: str, result: object,
                              error: type[Exception], told: str,
                              capsys: CaptureFixture[str]) -> None:
    """Test that a method call names the member the call was made for.

    The method is looked up on the Config object holding the member, and
    what it answers is checked. Neither diagnostic can be acted on without
    knowing which member of which nested object the call was about.
    """
    holder = CallingHolder()
    holder.things[1].use_method(method, result)
    stderr_file = StringIO()
    with pytest.raises(error) as exc:
        holder.validate(stderr_file=stderr_file, member_name=None)
    assert told in str(exc.value)
    assert told in stderr_file.getvalue()
    check_capsys(capsys)


class MissingMemberConfig(Config):
    """Configuration whose validation plan can name a missing member."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one configuration holding one member."""
        self.value = 'ok'
        self._plan_missing = False
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def use_missing_member(self) -> None:
        """Make the validation plan name a member that does not exist."""
        self._plan_missing = True

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return one step naming the member the plan is set to name."""
        _ = stderr_file
        named = 'missing' if self._plan_missing else 'value'
        return [MemberValidationStep(
            member_names=[named],
            validator=StrValidator(['ok'], ignore_case=False))]


def test_missing_member_path(capsys: CaptureFixture[str]) -> None:
    """Test that a member missing from a nested object is named by path."""
    config = MissingMemberConfig()
    config.use_missing_member()
    stderr_file = StringIO()
    with pytest.raises(AttributeError) as exc:
        config.validate(stderr_file=stderr_file, member_name='section.thing')
    told = 'Member section.thing.missing not found in Config object'
    assert told in str(exc.value)
    assert told in stderr_file.getvalue()
    check_capsys(capsys)


# pylint: disable-next=too-few-public-methods
class PathStep(ValidationStep):
    """A validation step of an application, refusing by the path it gets."""

    @override
    def apply(self, config: Config, stderr_file: TextIO = sys.stderr, *,
              member_name: Optional[str] = None) -> None:
        """Refuse a rejected value, naming the path it was given."""
        assert isinstance(config, StepConfig)
        if config.value != 'bad':
            return
        msg = f'Invalid configuration: step at {member_name} refuses.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)


class StepConfig(Config):
    """Configuration validated by one validation step of an application."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one configuration holding one accepted value."""
        self.value = 'ok'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the one application defined validation step."""
        _ = stderr_file
        return [PathStep()]


class StepHolder(Config):
    """Configuration holding the step-validated configuration in a dict."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one holder of one step-validated configuration."""
        self.parts: dict[str, StepConfig] = {'main': StepConfig()}
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration."""
        return {'parts': ConfigNesting(kind=ConfigNestingKind.DICT_VALUE,
                                       config_type=StepConfig)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own, only the nested validation."""
        _ = stderr_file
        return []


@pytest.mark.parametrize('prefix, expected', [
    (None, 'parts[main]'), ('outputs[1]', 'outputs[1].parts[main]')])
def test_validation_step_path(prefix: Optional[str], expected: str,
                              capsys: CaptureFixture[str]) -> None:
    """Test that an application validation step is given the whole path."""
    holder = StepHolder()
    holder.parts['main'].value = 'bad'
    stderr_file = StringIO()
    with pytest.raises(InvalidConfiguration) as exc:
        holder.validate(stderr_file=stderr_file, member_name=prefix)
    assert f'step at {expected} refuses.' in str(exc.value)
    assert f'step at {expected} refuses.' in stderr_file.getvalue()
    check_capsys(capsys)


@pytest.mark.parametrize('method, error, told', [
    ('missing', AttributeError,
     'Method missing at outputs[1] not found in Config object.'),
    ('value', TypeError,
     'Method value at outputs[1] in Config object is not callable.')
])
def test_whole_call_method_paths(method: str, error: type[Exception],
                                 told: str,
                                 capsys: CaptureFixture[str]) -> None:
    """Test that a whole-config method call names the object it is on."""
    config = StepConfig()
    validator = CallingWholeConfigValidator(method_name=method)
    stderr_file = StringIO()
    with pytest.raises(error) as exc:
        validator.validate(config, stderr_file, member_name='outputs[1]')
    assert told in str(exc.value)
    assert told in stderr_file.getvalue()
    check_capsys(capsys)
