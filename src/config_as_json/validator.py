#! /usr/local/bin/python3
"""Classes to validate a Config object or field in a Config object."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from abc import ABC, abstractmethod
from dataclasses import dataclass
import sys
from typing import Callable, Optional, Sequence, TextIO, TYPE_CHECKING, \
    TypeVar, Generic, cast
if TYPE_CHECKING:
    from config_as_json.config import Config


class InvalidConfiguration(ValueError):
    """Raised when a validation check on a configuration fails."""

    def __init__(self, message: str) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.message: str = message


def _not_one_of_allowed_values_message(
        member_name: str, member_value: object,
        allowed_values: Sequence[object], stderr_file: Optional[TextIO],
        member_index: Optional[int] = None) -> str:
    """Construct an allowed-values error message and optionally print it.

    Args:
        member_name: The name of the member that has the invalid value.
        member_value: The invalid value of the member.
        allowed_values: The allowed values for the member.
        stderr_file: The file to optionally write error messages to.
            If set to ``None`` explicitly, printing is suppressed.
        member_index: Optional index of the invalid element in a list value.

    Returns:
        A string containing the error message.
    """
    message = 'Invalid configuration: '
    message += f'Value {member_value} for {member_name} '
    if member_index is not None:
        message += f'at index {member_index} '
    message += 'is not one of the allowed values: '
    message += ', '.join(str(v) for v in allowed_values)
    if stderr_file is not None:
        print(message, file=stderr_file)
    return message


def not_one_of_allowed_values(member_name: str, member_value: object,
                              allowed_values: Sequence[object],
                              stderr_file: Optional[TextIO]) -> str:
    """Construct a message that a value is not one of the allowed values.

    If ``stderr_file`` is not ``None``, the message is written to it.

    This helper is special: passing ``stderr_file`` as ``None`` explicitly
    suppresses printing while still returning the constructed message.

    Args:
        member_name: The name of the member that has the invalid value.
        member_value: The invalid value of the member.
        allowed_values: The allowed values for the member.
        stderr_file: The file to optionally write error messages to.
            If set to ``None`` explicitly, printing is suppressed.

    Returns:
        A string containing the error message.
    """
    return _not_one_of_allowed_values_message(
        member_name=member_name, member_value=member_value,
        allowed_values=allowed_values, stderr_file=stderr_file)


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


class WholeConfigValidator(ABC):  # pylint: disable=too-few-public-methods
    """Base class for validators that validate a complete Config object."""

    def __init__(self) -> None:
        """Initialize the validator."""

    @abstractmethod
    def validate(self, config: 'Config',
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate an aspect of the entire Config object.

        The validate method must be implemented in a derived class.
        The validator shall validate the entire Config object. If the
        validation check fails, the error message shall be written to
        ``stderr_file`` before the exception is raised.
        This method may mutate the Config object directly if needed
        to normalize the configuration.

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
        msg = 'WholeConfigValidator.validate() must be implemented in a '
        msg += 'derived class.'
        print(msg, file=stderr_file)
        raise NotImplementedError(msg)


class MemberValidator(ABC):  # pylint: disable=too-few-public-methods
    """Base class for validators that validate one Config member."""

    def __init__(self) -> None:
        """Initialize the validator."""

    @abstractmethod
    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate an aspect of the Config object for one member.

        The validate_member method must be implemented in a derived class.
        It shall validate a specific member of the Config object, and
        ``member_value`` is the value of that member. If the validation check
        fails, the error message shall be written to ``stderr_file`` before
        the exception is raised.

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
            The returned value is used as the new member value, even if it is
            ``None``.
        """
        msg = 'MemberValidator.validate_member() must be implemented in a '
        msg += 'derived class.'
        print(msg, file=stderr_file)
        _ = member_value  # pylint: disable=unused-variable
        assert isinstance(member_name, str)  # pylint: disable=unused-variable
        assert config is not None  # pylint: disable=unused-variable
        raise NotImplementedError(msg)


def _validate_type_argument(value_type: object,
                            parameter_name: str) -> type[object]:
    """Validate and return one runtime type argument.

    Args:
        value_type: Value supplied as a runtime type argument.
        parameter_name: Name used in the error message.

    Returns:
        ``value_type`` after it has been proven to be a type.

    Raises:
        TypeError: ``value_type`` is not a type.
    """
    if not isinstance(value_type, type):
        raise TypeError(f'{parameter_name} must be a type.')
    return value_type


class ValueTypeValidator(MemberValidator):  # pylint: disable=too-few-public-methods # noqa: E501
    """Validate that one member value has the configured runtime type."""

    def __init__(self, value_type: type[object]) -> None:
        """Initialize the validator.

        Args:
            value_type: Required runtime type for the member value.

        Raises:
            TypeError: If ``value_type`` is not a type.
        """
        self.value_type: type[object] = _validate_type_argument(
            value_type, 'value_type')

    def validate_member(self, config: 'Config',
                        member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one member's runtime type.

        The check uses normal ``isinstance`` semantics. For example,
        ``ValueTypeValidator(int)`` accepts ``True`` because ``bool`` is a
        subclass of ``int`` in Python.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the member to validate.
            member_value: The member value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            The original member value if validation succeeds.

        Raises:
            InvalidConfiguration: If ``member_value`` is not an instance of
                ``value_type``.
        """
        _ = config
        if isinstance(member_value, self.value_type):
            return member_value
        msg = 'Invalid configuration: '
        msg += f'Value for {member_name} is not of type '
        msg += f'{self.value_type.__name__}.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)


class ValidationStep(ABC):  # pylint: disable=too-few-public-methods
    """Base class for one ordered validation step."""

    @abstractmethod
    def apply(self, config: 'Config',
              stderr_file: TextIO = sys.stderr) -> None:
        """Apply the validation step to one Config object.

        Args:
            config: The Config object to validate.
            stderr_file: The file to write error messages to.

        Raises:
            NotImplementedError: A derived validation step did not implement
                this method.
        """
        assert config is not None  # pylint: disable=unused-variable
        msg = 'ValidationStep.apply() must be implemented in a derived '
        msg += 'class.'
        print(msg, file=stderr_file)
        raise NotImplementedError(msg)


@dataclass
class WholeConfigValidationStep(ValidationStep):
    """Validation step that applies one whole-config validator.

    Attributes:
        validator: Validator that receives the whole Config object.
    """

    validator: WholeConfigValidator

    def apply(self, config: 'Config',
              stderr_file: TextIO = sys.stderr) -> None:
        """Apply the whole-config validator to the Config object.

        Args:
            config: The Config object to validate.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfiguration: The supplied validator rejects the
                configuration.
            InvalidConfigurationValue: The supplied validator rejects one
                configuration value.
        """
        self.validator.validate(config=config, stderr_file=stderr_file)


@dataclass
class MemberValidationStep(ValidationStep):
    """Validation step that applies one member validator.

    Attributes:
        member_names: Config member names to validate in order.
        validator: Validator that receives each named member value.
    """

    member_names: list[str]
    validator: MemberValidator

    def apply(self, config: 'Config',
              stderr_file: TextIO = sys.stderr) -> None:
        """Apply the member validator to each named member.

        Args:
            config: The Config object to validate.
            stderr_file: The file to write error messages to.

        Raises:
            AttributeError: One member name is not present on ``config``.
            InvalidConfiguration: The supplied validator rejects the
                configuration.
            InvalidConfigurationValue: The supplied validator rejects one
                configuration value.
        """
        for member_name in self.member_names:
            if not hasattr(config, member_name):
                msg = f'Member {member_name} '
                msg += 'not found in Config object '
                msg += 'in validation of '
                msg += f'{self.validator.__class__.__name__} '
                msg += 'in Config.validate().'
                print(msg, file=stderr_file)
                raise AttributeError(msg)
            member_value = getattr(config, member_name)
            ret = self.validator.validate_member(
                config=config, member_name=member_name,
                member_value=member_value, stderr_file=stderr_file)
            setattr(config, member_name, ret)


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


class StrValidator(  # pylint: disable=too-few-public-methods
        MemberValidator):
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


IntFloat = TypeVar('IntFloat', int, float)
"""Numeric type accepted by IntFloatValidator."""


ConstraintValue = TypeVar('ConstraintValue', int, float, str, bool)
"""Value type used when validating shared constraint arguments."""


def _validate_and_get_constraint_value_type(
        min_value: Optional[ConstraintValue],
        max_value: Optional[ConstraintValue],
        allowed_values: Optional[Sequence[ConstraintValue]],
        lt_comparator: Callable[[ConstraintValue, ConstraintValue], bool] =
        lambda x, y: x < y) -> type[ConstraintValue]:
    """Validate shared constructor constraints and return their type.

    The helper validates the common constructor arguments used by validators
    that support lower bounds, upper bounds, and allowed-values membership.
    It infers one runtime type from the provided constraints and verifies
    that all provided constraint values are instances of that type.

    Args:
        min_value: Optional minimum allowed value.
        max_value: Optional maximum allowed value.
        allowed_values: Optional allowed values.
        lt_comparator: Comparator used when checking that ``min_value`` is
            not greater than ``max_value``.

    Returns:
        The inferred runtime type shared by all provided constraint values.

    Raises:
        ValueError: If no constraints are provided.
        ValueError: If ``allowed_values`` is provided as an empty sequence.
        ValueError: If ``min_value`` is greater than ``max_value``.
        TypeError: If provided constraints use incompatible runtime types.
    """
    if min_value is None and max_value is None and allowed_values is None:
        msg: str = 'At least one of min_value, max_value, '
        msg += 'or allowed_values must be provided.'
        raise ValueError(msg)
    if allowed_values is not None and not allowed_values:
        msg = 'If provided, allowed_values must be a non-empty sequence.'
        raise ValueError(msg)
    value_type: Optional[type[ConstraintValue]] = \
        type(min_value) if min_value is not None else \
        type(max_value) if max_value is not None else None
    if value_type is None and allowed_values is not None:
        assert allowed_values is not None
        value_type = type(allowed_values[0])
    assert value_type is not None  # logically impossible
    if min_value is not None and not isinstance(min_value, value_type):
        msg = 'min_value must be of type ' + value_type.__name__
        raise TypeError(msg)
    if max_value is not None and not isinstance(max_value, value_type):
        msg = 'max_value must be of type ' + value_type.__name__
        raise TypeError(msg)
    if allowed_values is not None and not all(
            isinstance(value, value_type) for value in allowed_values):
        msg = 'allowed_values must be a sequence of '
        msg += value_type.__name__
        raise TypeError(msg)
    if min_value is not None and max_value is not None:
        assert min_value is not None
        assert max_value is not None
        if lt_comparator(max_value, min_value):
            msg = 'min_value must be less than or equal to max_value.'
            raise ValueError(msg)
    return value_type


def _ensure_int_float_type(value_type: type[object]) -> None:
    """Reject unsupported runtime types for IntFloatValidator."""
    if value_type not in (int, float):
        msg = 'IntFloatValidator only supports exact int or float values.'
        raise TypeError(msg)


class IntFloatValidator(  # pylint: disable=too-few-public-methods
        MemberValidator, Generic[IntFloat]):
    """Validate one int or float member against numeric constraints."""

    def __init__(self, min_value: Optional[IntFloat],
                 max_value: Optional[IntFloat],
                 allowed_values: Optional[Sequence[IntFloat]]) -> None:
        """Initialize the validator.

        The validator checks that the member value has one runtime type,
        either ``int`` or ``float``. The value must satisfy every configured
        constraint: lower bound, upper bound, and allowed-values membership.
        At least one of min_value, max_value, or allowed_values must be
        provided.

        Args:
            min_value: Minimum allowed member value.
                       If ``None``, no minimum value is checked.
            max_value: Maximum allowed member value.
                       If ``None``, no maximum value is checked.
            allowed_values: The only allowed values for the member.
                       If ``None``, no allowed-values check is done.

        Raises:
            ValueError: If no constraints are provided.
            ValueError: If allowed_values is provided as an empty sequence.
            ValueError: If min_value is greater than max_value.
            TypeError: If unsupported or mixed runtime types are used.
        """
        value_type = _validate_and_get_constraint_value_type(
            min_value=min_value, max_value=max_value,
            allowed_values=allowed_values)
        _ensure_int_float_type(value_type)
        self._value_type: type[IntFloat] = value_type
        self.min_value: Optional[IntFloat] = min_value
        self.max_value: Optional[IntFloat] = max_value
        self.allowed_values: Optional[Sequence[IntFloat]] = allowed_values

    def validate_member(self, config: 'Config',
                        member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate the aspect of the Config object for a specific member.

        Args:
            config: The Config object to validate.
            member_name: The name of the member to validate.
            member_value: The value of the member to validate.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfiguration: The configuration is invalid.
            InvalidConfigurationValue: The value of a configuration member is
                                       not one of the allowed values.
        Returns:
            The member value if the validation check passes, otherwise
            an exception is raised.
        """
        _ = config
        if not isinstance(member_value, self._value_type):
            msg = 'Invalid configuration: '
            msg += f'Value for {member_name} is not of type '
            msg += f'{self._value_type.__name__}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        value: IntFloat = cast(IntFloat, member_value)  # type: ignore[redundant-cast] # noqa: E501
        if self.min_value is not None and value < self.min_value:
            msg = 'Invalid configuration: '
            msg += f'Value {value} for {member_name} is less than minimum '
            msg += f'{self.min_value}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        if self.max_value is not None and value > self.max_value:
            msg = 'Invalid configuration: '
            msg += f'Value {value} for {member_name} is greater than maximum '
            msg += f'{self.max_value}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        if self.allowed_values is not None and \
                value not in self.allowed_values:
            _ = not_one_of_allowed_values(member_name, value,
                                          self.allowed_values, stderr_file)
            raise InvalidConfigurationValue(member_name, value,
                                            self.allowed_values)
        return value


type ValidationPlan = list[ValidationStep]
"""Ordered list of validation steps."""
