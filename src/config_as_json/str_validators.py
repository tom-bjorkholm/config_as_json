#! /usr/local/bin/python3
"""Validate strings."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from enum import Enum, auto
import sys
from typing import Callable, Optional, Sequence, TextIO, TYPE_CHECKING
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue, MemberValidator, not_one_of_allowed_values, \
    string_best_match
if TYPE_CHECKING:
    from config_as_json.config import Config


def _validate_str_value(member_name: str, member_value: object,
                        stderr_file: TextIO) -> str:
    """Validate and return one string member value."""
    if isinstance(member_value, str):
        return member_value
    msg = 'Invalid configuration: '
    msg += f'Value for {member_name} is not a string.'
    print(msg, file=stderr_file)
    raise InvalidConfiguration(msg)


def _validate_static_len_bound(value: object, parameter_name: str) -> None:
    """Validate one static string length bound or callable placeholder."""
    if value is None or callable(value):
        return
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f'{parameter_name} must be an int, None, '
                        'or a callable.')
    if value < 0:
        raise ValueError(f'{parameter_name} must be non-negative.')


def _length_bound(value: Optional[int] | Callable[[], Optional[int]],
                  parameter_name: str) -> Optional[int]:
    """Return one dynamic length bound after runtime validation."""
    if callable(value):
        bound = value()
    else:
        bound = value
    if bound is None:
        return None
    if not isinstance(bound, int) or isinstance(bound, bool):
        raise TypeError(f'{parameter_name} must be an int or None.')
    if bound < 0:
        raise ValueError(f'{parameter_name} must be non-negative.')
    return bound


def _validate_len_bounds(min_length: Optional[int],
                         max_length: Optional[int]) -> None:
    """Validate the relationship between two active length bounds."""
    if min_length is not None and max_length is not None and \
            min_length > max_length:
        raise ValueError('min_length must be less than or equal '
                         'to max_length.')


# pylint: disable-next=too-few-public-methods
class StrLenValidator(MemberValidator):
    """Validate length of a string member."""

    def __init__(self, min_length: Optional[int] | Callable[[], Optional[int]],
                 max_length: Optional[int] | Callable[[], Optional[int]]
                 ) -> None:
        """Initialize the validator.

        A validator that validates the length of a string member.
        Args:
            min_length: The minimum length of the string member.
                        If a callable is provided, it will be called
                        at validation time to get the minimum length.
                        A callable may return ``None`` to skip this bound.
            max_length: The maximum length of the string member.
                        If a callable is provided, it will be called
                        at validation time to get the maximum length.
                        A callable may return ``None`` to skip this bound.

        Raises:
            TypeError: If a static bound is not an int, None, or callable.
            ValueError: If a static bound is negative, if static bounds are
                ordered incorrectly, or if both static bounds are None.
        """
        if min_length is None and max_length is None:
            raise ValueError('At least one of min_length or max_length '
                             'must be provided.')
        _validate_static_len_bound(min_length, 'min_length')
        _validate_static_len_bound(max_length, 'max_length')
        if not callable(min_length) and not callable(max_length):
            _validate_len_bounds(min_length, max_length)
        self.min_length: Optional[int] | Callable[[], Optional[int]] = \
            min_length
        self.max_length: Optional[int] | Callable[[], Optional[int]] = \
            max_length

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate the length of a string member.

        Args:
            config: The configuration object to validate.
            member_name: The reported dotted and indexed path of the
                member to validate.
            member_value: The value of the member to validate, which is a
                string.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfiguration: The configuration is invalid.
            InvalidConfiguration: The member value is not a string.

        Returns:
            The member value unchanged if the validation passes, otherwise
            an exception is raised.
        """
        _ = config
        value = _validate_str_value(member_name, member_value, stderr_file)
        min_length = _length_bound(self.min_length, 'min_length')
        max_length = _length_bound(self.max_length, 'max_length')
        _validate_len_bounds(min_length, max_length)
        value_length = len(value)
        if min_length is not None and value_length < min_length:
            msg = 'Invalid configuration: '
            msg += f'Value for {member_name} has length {value_length} '
            msg += f'which is less than minimum {min_length}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        if max_length is not None and value_length > max_length:
            msg = 'Invalid configuration: '
            msg += f'Value for {member_name} has length {value_length} '
            msg += f'which is greater than maximum {max_length}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        return member_value


class StrCaseSpec(Enum):
    """Specification for string case."""

    LOWER = auto()
    """Character(s) in the position shall be lowercase."""

    UPPER = auto()
    """Character(s) in the position shall be uppercase."""

    ORIGINAL = auto()
    """Character(s) in the position shall be original case.

    When converting this means no conversion is performed.
    When validating/checking this means any case is allowed.
    """


class StrPositionSpec(Enum):
    """Specification for string position."""

    FIRST_IN_STRING = auto()
    """First character in the string."""

    FIRST_IN_WORD = auto()
    """First character in every word.

    This is the first non-whitespace character in the string, and the first
    non-whitespace character after a whitespace character.
    """

    FIRST_IN_SENTENCE = auto()
    """First character in every sentence.

    This is the first non-whitespace character in the string, and the first
    non-whitespace character after a period, exclamation mark, or question
    mark.
    """

    EVERY_CHARACTER = auto()
    """Every character in the string."""


def _validate_case_args(special_position: StrPositionSpec,
                        special_position_case: StrCaseSpec,
                        other_position_case: StrCaseSpec) -> None:
    """Validate constructor arguments for string case validators."""
    if not isinstance(special_position, StrPositionSpec):
        raise TypeError('special_position must be a StrPositionSpec.')
    if not isinstance(special_position_case, StrCaseSpec):
        raise TypeError('special_position_case must be a StrCaseSpec.')
    if not isinstance(other_position_case, StrCaseSpec):
        raise TypeError('other_position_case must be a StrCaseSpec.')


def _word_position_flags(value: str) -> list[bool]:
    """Return flags for first non-whitespace characters in words."""
    result: list[bool] = []
    previous_whitespace = True
    for character in value:
        result.append(not character.isspace() and previous_whitespace)
        previous_whitespace = character.isspace()
    return result


def _sentence_position_flags(value: str) -> list[bool]:
    """Return flags for first non-whitespace characters in sentences."""
    result: list[bool] = []
    sentence_start = True
    for character in value:
        if character.isspace():
            result.append(False)
            continue
        result.append(sentence_start)
        sentence_start = character in '.?!'
    return result


def _position_flags(value: str,
                    special_position: StrPositionSpec) -> list[bool]:
    """Return flags for the positions selected by one position spec."""
    if special_position == StrPositionSpec.FIRST_IN_STRING:
        return [index == 0 for index, _ in enumerate(value)]
    if special_position == StrPositionSpec.FIRST_IN_WORD:
        return _word_position_flags(value)
    if special_position == StrPositionSpec.FIRST_IN_SENTENCE:
        return _sentence_position_flags(value)
    if special_position == StrPositionSpec.EVERY_CHARACTER:
        return [True for _ in value]
    raise AssertionError('Unhandled StrPositionSpec.')


def _case_spec_for_flag(is_special: bool, special_position_case: StrCaseSpec,
                        other_position_case: StrCaseSpec) -> StrCaseSpec:
    """Return the case specification for one position flag."""
    if is_special:
        return special_position_case
    return other_position_case


def _is_case_match(character: str, case_spec: StrCaseSpec) -> bool:
    """Return whether one character matches one case specification."""
    if case_spec == StrCaseSpec.ORIGINAL:
        return True
    if case_spec == StrCaseSpec.LOWER:
        return character == character.lower()
    if case_spec == StrCaseSpec.UPPER:
        return character == character.upper()
    raise AssertionError('Unhandled StrCaseSpec.')


def _case_spec_text(case_spec: StrCaseSpec) -> str:
    """Return a human-readable name for one case specification."""
    if case_spec == StrCaseSpec.LOWER:
        return 'lowercase'
    if case_spec == StrCaseSpec.UPPER:
        return 'uppercase'
    if case_spec == StrCaseSpec.ORIGINAL:
        return 'original case'
    raise AssertionError('Unhandled StrCaseSpec.')


def _raise_case_error(member_name: str, character: str, index: int,
                      case_spec: StrCaseSpec, stderr_file: TextIO) -> None:
    """Raise a validation error for one incorrectly cased character."""
    msg = 'Invalid configuration: '
    msg += f'Character {character!r} for {member_name} '
    msg += f'at index {index} is not {_case_spec_text(case_spec)}.'
    print(msg, file=stderr_file)
    raise InvalidConfiguration(msg)


def _change_case(character: str, case_spec: StrCaseSpec) -> str:
    """Return one character converted according to a case specification."""
    if case_spec == StrCaseSpec.ORIGINAL:
        return character
    if case_spec == StrCaseSpec.LOWER:
        return character.lower()
    if case_spec == StrCaseSpec.UPPER:
        return character.upper()
    raise AssertionError('Unhandled StrCaseSpec.')


# pylint: disable-next=too-few-public-methods
class StrCaseValidator(MemberValidator):
    """Validate (upper/lower) case of a string member."""

    def __init__(self, special_position: StrPositionSpec,
                 special_position_case: StrCaseSpec,
                 other_position_case: StrCaseSpec) -> None:
        """Initialize the validator.

        A validator that validates the (upper/lower) case of a string member.
        Args:
            special_position: The position of the special characters.
                              To what position(s) in the string shall
                              the special_position_case apply?
            special_position_case: The case of the special characters.
                              The case that the character(s) in the special
                              position(s) (as specified by special_position)
                              shall have.
            other_position_case: The case of the other characters.
                              The case that the character(s) in the other
                              position(s) (that is every position not matching
                              the special_position) shall have.

        Raises:
            TypeError: If one argument is not the expected enum type.
        """
        _validate_case_args(special_position, special_position_case,
                            other_position_case)
        self.special_position: StrPositionSpec = special_position
        self.special_position_case: StrCaseSpec = special_position_case
        self.other_position_case: StrCaseSpec = other_position_case

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate the (upper/lower) case of a string member.

        The validation is performed by checking the case of the characters in
        the special position(s) and the other position(s).
        Args:
            config: The configuration object to validate.
            member_name: The reported dotted and indexed path of the
                member to validate.
            member_value: The value of the member to validate, which is a
                string.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfiguration: The configuration is invalid. One or more
                characters in the string do not match the case specification.
            InvalidConfiguration: The member value is not a string.

        Returns:
            The member value unchanged if the validation passes, otherwise
            an exception is raised.
        """
        _ = config
        value = _validate_str_value(member_name, member_value, stderr_file)
        flags = _position_flags(value, self.special_position)
        for index, character in enumerate(value):
            case_spec = _case_spec_for_flag(flags[index],
                                            self.special_position_case,
                                            self.other_position_case)
            if not _is_case_match(character, case_spec):
                _raise_case_error(member_name, character, index, case_spec,
                                  stderr_file)
        return member_value


# pylint: disable-next=too-few-public-methods
class StrCaseChangeValidator(MemberValidator):
    """Change the (upper/lower) case of a string member."""

    def __init__(self, special_position: StrPositionSpec,
                 special_position_case: StrCaseSpec,
                 other_position_case: StrCaseSpec) -> None:
        """Initialize the validator.

        A validator that changes the (upper/lower) case of a string member.
        Args:
            special_position: The position of the special characters.
                              To what position(s) in the string shall
                              the special_position_case apply?
            special_position_case: The case of the special characters.
                              The case that the character(s) in the special
                              position(s) (as specified by special_position)
                              shall be changed to.
            other_position_case: The case of the other characters.
                              The case that the character(s) in the other
                              position(s) (that is every position not matching
                              the special_position) shall be changed to.

        Raises:
            TypeError: If one argument is not the expected enum type.
        """
        _validate_case_args(special_position, special_position_case,
                            other_position_case)
        self.special_position: StrPositionSpec = special_position
        self.special_position_case: StrCaseSpec = special_position_case
        self.other_position_case: StrCaseSpec = other_position_case

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Change the (upper/lower) case of a string member.

        The change is performed by converting the case of the characters in
        the special position(s) and the other position(s).
        Args:
            config: The configuration object to validate.
            member_name: The reported dotted and indexed path of the
                member to validate.
            member_value: The value of the member to validate, which is a
                string.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfiguration: The member value is not a string.

        Returns:
            The member value changed to the new case if the validation passes,
            otherwise an exception is raised.
        """
        _ = config
        value = _validate_str_value(member_name, member_value, stderr_file)
        flags = _position_flags(value, self.special_position)
        result: list[str] = []
        for index, character in enumerate(value):
            case_spec = _case_spec_for_flag(flags[index],
                                            self.special_position_case,
                                            self.other_position_case)
            result.append(_change_case(character, case_spec))
        return ''.join(result)


# pylint: disable-next=too-few-public-methods
class StrValidator(MemberValidator):
    """Validate one string member against allowed string values."""

    def __init__(self,
                 allowed_values: Sequence[str] | Callable[[], Sequence[str]],
                 ignore_case: bool, best_match: bool = False,
                 normalize: bool = False) -> None:
        """Initialize the validator.

        Args:
            allowed_values: The allowed values for the string member.
            ignore_case: Whether to ignore case when validating the
                         string member.
            best_match: Whether to return the best match for the string
                        member if the value is not one of the allowed values.
                        The best match includes a unique prefix match ignoring
                        case. In this case, the returned value from
                        validate_member will be the best match (or an
                        exception if no best match is found).
            normalize: Whether to normalize the string member to one of the
                       allowed values.
        """
        self.allowed_values: Sequence[str] | Callable[[], Sequence[str]] = \
            allowed_values
        self.ignore_case: bool = ignore_case
        self.best_match: bool = best_match
        self.normalize: bool = normalize

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate the aspect of the Config object for a specific str member.

        Raises:
            InvalidConfiguration: The configuration is invalid.
            InvalidConfigurationValue: The value of a configuration member is
                                       not one of the allowed values.

        Args:
            config: The Config object to validate.
            member_name: The reported dotted and indexed path of the
                member to validate.
            member_value: The value of the member to validate.
            stderr_file: The file to write error messages to.

        Returns:
            A normalized value if the validation check passes, otherwise
            an exception is raised.
            Returns the original value when only validated and does not want
            to change the value of the member in the Config object.
            When ``best_match`` is used, the returned value is the matched
            entry from ``allowed_values``. This can normalize the member value
            even when ``normalize`` is ``False``.
        """
        _ = config
        value = _validate_str_value(member_name, member_value, stderr_file)
        allowed_values = self.allowed_values() if \
            callable(self.allowed_values) \
            else self.allowed_values
        cmp_value = value
        if self.ignore_case:
            cmp_value = value.lower()
        for allowed_value in allowed_values:
            if (self.ignore_case and cmp_value == allowed_value.lower()) or \
                    cmp_value == allowed_value:
                if self.normalize:
                    return allowed_value
                return member_value
        if self.best_match:
            return string_best_match(value, allowed_values, member_name,
                                     stderr_file)
        _ = not_one_of_allowed_values(member_name, value, allowed_values,
                                      stderr_file)
        raise InvalidConfigurationValue(member_name, value, allowed_values)
