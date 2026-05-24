#! /usr/local/bin/python3
"""Classes to validate a Config object or field in a Config object."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence as SequenceABC
from dataclasses import dataclass
from operator import lt as operator_lt
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


def _validate_non_empty_str_argument(value: object,
                                     parameter_name: str) -> str:
    """Validate and return one non-empty string argument."""
    if not isinstance(value, str):
        raise TypeError(f'{parameter_name} must be a str.')
    if value == '':
        raise ValueError(f'{parameter_name} must be non-empty.')
    return value


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


type ValidationPlan = list[ValidationStep]
"""Ordered list of validation steps."""


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


IntFloat = TypeVar('IntFloat', int, float)
"""Numeric type accepted by IntFloatValidator."""


ConstraintValue = TypeVar('ConstraintValue', int, float, str, bool)
"""Value type used when validating shared constraint arguments."""


def _validated_constraint_vtype(min_value: Optional[ConstraintValue],
                                max_value: Optional[ConstraintValue],
                                allowed_values: Optional[
                                    Sequence[ConstraintValue]],
                                lt_comparator:
                                    Callable[[ConstraintValue,
                                              ConstraintValue], bool] =
                                operator_lt) -> type[ConstraintValue]:
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
    value_type: Optional[type[ConstraintValue]] = \
        type(min_value) if min_value is not None else \
        type(max_value) if max_value is not None else None
    if value_type is None and allowed_values is not None:
        assert allowed_values is not None
        value_type = _get_allowed_values_type(allowed_values)
        _ = _validate_allowed_values_sequence(allowed_values, value_type)
    assert value_type is not None  # logically impossible
    if max_value is not None and not isinstance(max_value, value_type):
        msg = 'max_value must be of type ' + value_type.__name__
        raise TypeError(msg)
    if allowed_values is not None:
        _ = _validate_allowed_values_sequence(allowed_values, value_type)
    if min_value is not None and max_value is not None:
        assert min_value is not None
        assert max_value is not None
        if lt_comparator(max_value, min_value):
            msg = 'min_value must be less than or equal to max_value.'
            raise ValueError(msg)
    return value_type


def _get_allowed_values_type(allowed_values: object) -> type[ConstraintValue]:
    """Return the type of the first value in a non-empty sequence."""
    if not isinstance(allowed_values, SequenceABC):
        raise TypeError('allowed_values must be a sequence.')
    if len(allowed_values) == 0:
        msg = 'If provided, allowed_values must be a non-empty sequence.'
        raise ValueError(msg)
    return cast(type[ConstraintValue], type(allowed_values[0]))


def _validate_allowed_values_sequence(allowed_values: object,
                                      value_type: type[ConstraintValue]) \
        -> Sequence[ConstraintValue]:
    """Validate allowed-values sequence shape and element type."""
    if not isinstance(allowed_values, SequenceABC):
        msg = 'allowed_values must be a sequence of '
        msg += value_type.__name__
        raise TypeError(msg)
    if len(allowed_values) == 0:
        msg = 'If provided, allowed_values must be a non-empty sequence.'
        raise ValueError(msg)
    if not all(isinstance(value, value_type) for value in allowed_values):
        msg = 'allowed_values must be a sequence of '
        msg += value_type.__name__
        raise TypeError(msg)
    return cast(Sequence[ConstraintValue], allowed_values)


def _values_for_type(min_value: Optional[ConstraintValue],
                     max_value: Optional[ConstraintValue],
                     allowed_values: Optional[
                         Sequence[ConstraintValue] |
                         Callable[[], Sequence[ConstraintValue]]]) \
        -> Optional[Sequence[ConstraintValue]]:
    """Return allowed values needed for constructor type inference."""
    if not callable(allowed_values):
        return allowed_values
    if min_value is None and max_value is None:
        return allowed_values()
    return None


def _get_allowed_values(allowed_values: Optional[
        Sequence[ConstraintValue] | Callable[[], Sequence[ConstraintValue]]],
                        value_type: type[ConstraintValue]) \
        -> Optional[Sequence[ConstraintValue]]:
    """Return the allowed values to use for the current validation."""
    if allowed_values is None:
        return None
    if not callable(allowed_values):
        return allowed_values
    return _validate_allowed_values_sequence(allowed_values(), value_type)


def _ensure_int_float_type(value_type: type[object]) -> None:
    """Reject unsupported runtime types for IntFloatValidator."""
    if value_type not in (int, float):
        msg = 'IntFloatValidator only supports exact int or float values.'
        raise TypeError(msg)


# pylint: disable-next=too-few-public-methods
class IntFloatValidator(MemberValidator, Generic[IntFloat]):
    """Validate one int or float member against numeric constraints."""

    def __init__(self, min_value: Optional[IntFloat],
                 max_value: Optional[IntFloat],
                 allowed_values: Optional[
                     Sequence[IntFloat] |
                     Callable[[], Sequence[IntFloat]]]) -> None:
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
                       If a callable, it is called to get the allowed values.

        Raises:
            ValueError: If no constraints are provided.
            ValueError: If allowed_values is provided as an empty sequence.
            ValueError: If min_value is greater than max_value.
            TypeError: If unsupported or mixed runtime types are used.
        """
        type_values = _values_for_type(min_value, max_value, allowed_values)
        get_value_type = _validated_constraint_vtype
        value_type = get_value_type(min_value, max_value, type_values)
        _ensure_int_float_type(value_type)
        self._value_type: type[IntFloat] = value_type
        self.min_value: Optional[IntFloat] = min_value
        self.max_value: Optional[IntFloat] = max_value
        self.allowed_values: Optional[
            Sequence[IntFloat] | Callable[[], Sequence[IntFloat]]] = \
            allowed_values

    def validate_member(self, config: 'Config', member_name: str,
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
        value = cast(IntFloat, member_value)  # type: ignore[redundant-cast]
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
        allowed_values = _get_allowed_values(self.allowed_values,
                                             self._value_type)
        if allowed_values is not None:
            if value not in allowed_values:
                _ = not_one_of_allowed_values(member_name, value,
                                              allowed_values, stderr_file)
                raise InvalidConfigurationValue(member_name, value,
                                                allowed_values)
        return value


def _copy_method_other_args(other_args: Optional[Mapping[str, object]]) \
        -> dict[str, object]:
    """Validate and copy additional keyword arguments for a method call."""
    if other_args is None:
        return {}
    if not isinstance(other_args, Mapping):
        raise TypeError('other_args must be a mapping.')
    copied: dict[str, object] = {}
    for key, value in other_args.items():
        _ = _validate_non_empty_str_argument(key, 'other_args key')
        copied[key] = value
    return copied


def _get_config_method(config: 'Config', method_name: str,
                       stderr_file: TextIO) -> Callable[..., object]:
    """Return one callable method from a Config object."""
    if not hasattr(config, method_name):
        msg = f'Method {method_name} not found in Config object.'
        print(msg, file=stderr_file)
        raise AttributeError(msg)
    method = getattr(config, method_name)
    if not callable(method):
        msg = f'Method {method_name} in Config object is not callable.'
        print(msg, file=stderr_file)
        raise TypeError(msg)
    return cast(Callable[..., object], method)


def _check_validation_only_method_result(method_name: str, result: object,
                                         stderr_file: TextIO) -> None:
    """Validate the return value from a validation-only method call."""
    if result is None or result is True:
        return
    if result is False:
        msg = 'Invalid configuration: '
        msg += f'Method {method_name} returned False.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)
    msg = f'Method {method_name} returned {type(result).__name__}; '
    msg += 'expected None, True, or False.'
    print(msg, file=stderr_file)
    raise TypeError(msg)


# pylint: disable-next=too-few-public-methods
class CallingMemberValidator(MemberValidator):
    """Validate one member by calling a method of the Config object.

    The validator calls a method of the Config object with the given arguments.
    The method must accept all arguments as keyword arguments. The method is
    expected to validate the member value. This validator is most useful when
    the configuration class is multiply derived from Config and from a class
    in a third-party library, and the class in the third-party library has
    validation logic.

    The method may indicate that the member value is invalid by raising an
    exception, or in validation-only mode by returning False. In
    validation-only mode, a return value of None or True is considered valid
    and the original member value is kept. In normalizing mode, the method is
    expected to return the validated and normalized value.
    """

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def __init__(self, method_name: str, arg_name_value: str,
                 arg_name_member_name: Optional[str] = None,
                 other_args: Optional[Mapping[str, object]] = None,
                 normalizing: bool = False) -> None:
        """Initialize the validator.

        The validator calls a method of the Config object with the given
        arguments. The method must accept all arguments as keyword arguments.

        The method may indicate that the member value is invalid by raising an
        exception, or in validation-only mode by returning False. In
        validation-only mode, a return value of None or True indicates a valid
        member value and the original member value is kept. In normalizing
        mode, the method is expected to return the validated and normalized
        value.

        Args:
            method_name: The name of the method to call on the Config object.
                         The method must accept all arguments as keyword
                         arguments.
            arg_name_value: The name of the argument to the method that
                            contains the value passed in to be validated.
            arg_name_member_name: The name of the argument to the method that
                                  contains the name of the member that is
                                  being validated. If ``None``, the member name
                                  is not passed to the method.
            other_args: Other arguments to the method. If ``None``, no other
                        arguments are passed to the method.
            normalizing: Whether the method returns a normalized member value.
                         If ``False``, the method is expected to return None
                         or True if valid, and to return False if invalid.
                         If ``True``, the method is expected to return the
                         validated and normalized value.

        Raises:
            TypeError: If one constructor argument has an invalid type.
            ValueError: If one argument name is empty or would overwrite
                another generated argument.
        """
        self.method_name: str = _validate_non_empty_str_argument(method_name,
                                                                 'method_name')
        self.arg_name_value: str = _validate_non_empty_str_argument(
            arg_name_value, 'arg_name_value')
        if arg_name_member_name is None:
            self.arg_name_member_name: Optional[str] = None
        else:
            self.arg_name_member_name = _validate_non_empty_str_argument(
                arg_name_member_name, 'arg_name_member_name')
        self.other_args: dict[str, object] = \
            _copy_method_other_args(other_args)
        generated_names = {self.arg_name_value}
        if self.arg_name_member_name is not None:
            if self.arg_name_member_name == self.arg_name_value:
                msg = 'arg_name_member_name must differ from arg_name_value.'
                raise ValueError(msg)
            generated_names.add(self.arg_name_member_name)
        for key in self.other_args:
            if key in generated_names:
                msg = 'other_args must not contain generated argument '
                msg += f'{key!r}.'
                raise ValueError(msg)
        if not isinstance(normalizing, bool):
            raise TypeError('normalizing must be a bool.')
        self.normalizing: bool = normalizing

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one member by calling a method of the Config object.

        Args:
            config: The Config object to validate.
            member_name: The name of the member to validate.
            member_value: The value of the member to validate.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfiguration: The configuration is invalid.
            InvalidConfigurationValue: The value of a configuration member is
                                       not one of the allowed values.
            Any exception raised by the method in the Config object.

        Returns:
            The original member value in validation-only mode, or the
            validated and normalized value in normalizing mode.
        """
        func = _get_config_method(config, self.method_name, stderr_file)
        kwargs: dict[str, object] = dict(self.other_args)
        kwargs[self.arg_name_value] = member_value
        if self.arg_name_member_name is not None:
            kwargs[self.arg_name_member_name] = member_name
        ret = func(**kwargs)
        if self.normalizing:
            return ret
        _check_validation_only_method_result(self.method_name, ret,
                                             stderr_file)
        return member_value


# pylint: disable-next=too-few-public-methods
class CallingWholeConfigValidator(WholeConfigValidator):
    """Validate complete Config by calling a method of the Config object.

    The validator calls a method of the Config object with the given arguments.
    The method must accept all arguments as keyword arguments. The method is
    expected to validate the configuration. This validator is most useful when
    the configuration class is multiply derived from Config and from a class
    in a third-party library, and the class in the third-party library has
    validation logic.

    The method may indicate that the configuration is invalid by raising an
    exception, or by returning False.
    The method is expected to return None or True if the configuration is
    valid.
    """

    def __init__(self, method_name: str,
                 other_args: Optional[Mapping[str, object]] = None) -> None:
        """Initialize the validator.

        The validator calls a method of the Config object with the given
        arguments. The method must accept all arguments as keyword arguments.

        The method may indicate that the configuration is invalid by raising an
        exception, or by returning False.
        A return value of None or True is indicating a valid configuration.

        The method may mutate the Config object directly if needed to
        normalize the configuration.

        Args:
            method_name: The name of the method to call on the Config object.
                         The method must accept all arguments as keyword
                         arguments.
            other_args: Other arguments to the method. If ``None``, no other
                        arguments are passed to the method.

        Raises:
            TypeError: If one constructor argument has an invalid type.
            ValueError: If one argument name is empty.
        """
        self.method_name: str = _validate_non_empty_str_argument(method_name,
                                                                 'method_name')
        self.other_args: dict[str, object] = \
            _copy_method_other_args(other_args)

    def validate(self, config: 'Config',
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate the entire Config object by calling a method in it.

        Args:
            config: The Config object to validate.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfiguration: The configuration is invalid.
            Any exception raised by the method in the Config object.
        """
        func = _get_config_method(config, self.method_name, stderr_file)
        ret: object = func(**self.other_args)
        _check_validation_only_method_result(self.method_name, ret,
                                             stderr_file)


# pylint: disable-next=too-few-public-methods
class MemberValidatorSequence(MemberValidator):
    """Validate one member by applying a sequence of validators.

    The validator applies a sequence of validators to the member value.
    The sequence is applied in order, and the output of each validator is
    passed as the input to the next validator.

    This is useful when several validators need to be applied to the
    same member value, before moving on to the next member.
    When validating several member values with ValidationPlan the natural
    order is to apply the same validator to several member values before
    moving on to the next ValidationStep that has another validator.
    MemberValidatorSequence thus has a natural order that is different from
    the order easily specified by ValidationPlan.
    """

    def __init__(self, validators: Sequence[MemberValidator]) -> None:
        """Initialize the validator.

        Args:
            validators: The sequence of validators to apply.

        Raises:
            TypeError: If ``validators`` is not a sequence or one entry is not
                a ``MemberValidator``.
            ValueError: If ``validators`` is empty.
        """
        if not isinstance(validators, SequenceABC):
            raise TypeError('validators must be a sequence.')
        if len(validators) == 0:
            raise ValueError('validators must be non-empty.')
        self.validators: list[MemberValidator] = list(validators)
        for index, validator in enumerate(self.validators):
            if not isinstance(validator, MemberValidator):
                msg = f'validators[{index}] must be a MemberValidator.'
                raise TypeError(msg)

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one member by applying a sequence of validators.

        Args:
            config: The Config object to validate.
            member_name: The name of the member to validate.
            member_value: The value of the member to validate.
            stderr_file: The file to write error messages to.
        """
        current_value = member_value
        for validator in self.validators:
            current_value = validator.validate_member(
                config=config, member_name=member_name,
                member_value=current_value, stderr_file=stderr_file)
        return current_value
