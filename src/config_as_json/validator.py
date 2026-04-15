#! /usr/local/bin/python3
"""Classes to validate a Config object or field in a Config object."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from typing import Callable, NamedTuple, Optional, Sequence, TextIO, \
    TYPE_CHECKING
if TYPE_CHECKING:
    from config_as_json.config import Config


class InvalidConfiguration(ValueError):
    """Raised when a validation check on a configuration fails."""

    def __init__(self, message: str) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.message: str = message


def not_one_of_allowed_values(member_name: str, member_value: object,
                              allowed_values: Sequence[object],
                              stderr_file: Optional[TextIO]) -> str:
    """Construct a message that a value is not one of the allowed values.

    Construct a message that a value is not one of the allowed values.
    If ``stderr_file`` is not ``None``, the message is written to it.

    This helper is special: passing ``stderr_file`` as ``None`` explicitly
    suppresses printing while still returning the constructed message.

    Args:
        member_name: The name of the member that has the invalid value.
        member_value: The invalid value of the member,
        allowed_values: The allowed values for the member.
        stderr_file: The file to optionally write error messages to.
            If set to ``None`` explicitly, printing is suppressed.

    Returns:
        A string containing the error message.
    """
    message = 'Invalid configuration: '
    message += f'Value {member_value} for {member_name} '
    message += 'is not one of the allowed values: '
    message += ', '.join(str(v) for v in allowed_values)
    if stderr_file is not None:
        print(message, file=stderr_file)
    return message


class InvalidConfigurationValue(InvalidConfiguration):
    """Raised when a configuration value is not one of the allowed values."""

    def __init__(self, member_name: str, member_value: object,
                 allowed_values: Sequence[object]) -> None:
        """Initialize the exception."""
        self.member_name: str = member_name
        self.member_value: object = member_value
        self.allowed_values: list[object] = list(allowed_values)
        super().__init__(not_one_of_allowed_values(member_name, member_value,
                                                   allowed_values, None))


class Validator:
    """Base class for validating an aspect of a Config object."""

    def __init__(self) -> None:
        """Initialize the validator."""

    def validate(self, config: 'Config',
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate the aspect of the entire Config object.

        The validate method must be implemented in a derived class, if used
        for validating the entire Config object.

        The validator shall validate the entire Config object.
        If the validation check fails, the error message shall be written to
        ``stderr_file`` before the exception is raised.

        Raises:
            InvalidConfiguration: The configuration is invalid.
            InvalidConfigurationValue: The value of a configuration member is
                                        not one of the allowed values.

        Args:
            config: The Config object to validate.
            stderr_file: The file to write error messages to.

        Returns:
            None if the validation check passes, otherwise the exception
            is raised.
        """
        assert config is not None  # pylint: disable=unused-variable
        msg = 'Validator.validate() must be implemented in a derived class.'
        print(msg, file=stderr_file)
        raise NotImplementedError(msg)

    def validate_member(self, config: 'Config',
                        member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate the aspect of the Config object for a specific member.

        The validate_member method must be implemented in a derived class, if
        used for validating a specific member of the Config object.

        It shall validate a specific member of the Config object, and
        ``member_value`` is the value of that member.
        If the validation check fails, the error message shall be written to
        ``stderr_file`` before the exception is raised.

        Raises:
            InvalidConfiguration: The configuration is invalid.
            InvalidConfigurationValue: The value of a configuration member is
                                      not one of the allowed values.

        Args:
            config: The complete Config object (might be needed if the
                    validator needs to access other members of the Config
                    object).
            member_name: The name of the member to validate.
            member_value: The value of the member to validate.
            stderr_file: The file to write error messages to.

        Returns:
            A normalized value if the validation check passes,
            otherwise the exception is raised. This returned value will be
            used as the value of the member in the Config object.
            Return the original value if you only validate and do not want
            to change the value of the member in the Config object.
            Notice: The returned value is used as the new member value, even if
            it is ``None``.
        """
        msg = 'Validator.validate_member() must be implemented in a ' + \
            'derived class.'
        print(msg, file=stderr_file)
        _ = member_value  # pylint: disable=unused-variable
        assert isinstance(member_name, str)  # pylint: disable=unused-variable
        assert config is not None  # pylint: disable=unused-variable
        raise NotImplementedError(msg)


def string_best_match(value: str, allowed_values: Sequence[str],
                      member_name: str,
                      stderr_file: TextIO = sys.stderr) -> str:
    """Return the best match for a string value from a list of allowed values.

    The helper first accepts a direct match among ``value`` and a few common
    case variants. If that fails, it accepts a unique prefix match ignoring
    case.

    Args:
        value: The value to match.
        allowed_values: The allowed values to match against.
        member_name: The name of the member to validate used in any
                     error message.
        stderr_file: The file to write error messages to.

    Returns:
        The best match for the value from the allowed values.

    Raises:
       InvalidConfiguration: The value is not a string.
       InvalidConfigurationValue: The value is not one of the allowed values.
    """
    if not isinstance(value, str):
        msg = 'Invalid configuration: ' + \
            f'Value for {member_name} is not a string.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)
    for variant in (value, value.capitalize(), value.lower(), value.upper()):
        if variant in allowed_values:
            return variant
    num_match: int = 0
    match: Optional[str] = None
    for i in allowed_values:
        if i.lower()[0:len(value)] == value.lower():
            num_match += 1
            match = i
    if num_match == 1 and match is not None:
        assert match is not None
        assert isinstance(match, str)
        return match
    msg = not_one_of_allowed_values(member_name, value, allowed_values,
                                    stderr_file)
    raise InvalidConfigurationValue(member_name, value, allowed_values)


class StrValidator(Validator):
    """Validator for simple case of string value member of a Config object."""

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

    def validate_member(self, config: 'Config',
                        member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate the aspect of the Config object for a specific str member.

        Raises:
            InvalidConfiguration: The configuration is invalid.
            InvalidConfigurationValue: The value of a configuration member is
                                       not one of the allowed values.

        Args:
            config: The Config object to validate.
            member_name: The name of the member to validate.
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
        if not isinstance(member_value, str):
            msg = 'Invalid configuration: ' + \
                f'Value for {member_name} is not a string.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        assert isinstance(member_value, str)
        allowed_values = self.allowed_values() if \
            callable(self.allowed_values) \
            else self.allowed_values
        cmp_value = member_value
        if self.ignore_case:
            cmp_value = member_value.lower()
        for allowed_value in allowed_values:
            if (self.ignore_case and cmp_value == allowed_value.lower()) or \
                    cmp_value == allowed_value:
                if self.normalize:
                    return allowed_value
                return member_value
        if self.best_match:
            return string_best_match(member_value, allowed_values,
                                     member_name, stderr_file)
        msg = not_one_of_allowed_values(member_name, member_value,
                                        allowed_values, stderr_file)
        raise InvalidConfigurationValue(member_name, member_value,
                                        allowed_values)

    def validate(self, config: 'Config',
                 stderr_file: TextIO = sys.stderr) -> None:
        """Cannot validate complete Config object with this validator."""
        msg = 'Cannot validate complete Config object with a StrValidator.'
        assert config is not None
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)


class Validation(NamedTuple):
    """Instruction for validation.

    One Validation object describes one aspect of validation of the
    Config object. This may be applied to either the entire Config object
    or to one or several members of the Config object.
    """

    member_names: Optional[list[str]]
    """The names of the members to validate with this validator.

    If ``None``, the validator shall validate the entire Config object.
    Otherwise, it shall validate the members with the given names.
    When validating a specific member, the validator is passed the
    member name and value, in addition to the complete Config object.
    """

    validator: Validator
    """The validator to use for the validation.

    The ``validate_member`` method of the validator is called once for each
    member name to validate (with the member name and value, in addition to
    the complete Config object).
    If ``member_names`` is ``None``, the ``validate`` method is called once
    for the entire Config object.
    """


type ValidationList = list[Validation]
"""List of validation instructions."""
