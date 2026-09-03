#! /usr/local/bin/python3
"""Implement type validators for configuration data."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from functools import partial
from typing import Callable, Generic, Optional, TextIO, TypeVar, TYPE_CHECKING
from typing import cast
from config_as_json.validator import InvalidConfiguration, MemberValidator, \
    _validate_type_argument
if TYPE_CHECKING:
    from config_as_json.config import Config


def _validate_type_spec(type_spec: object, parameter_name: str,
                        allow_empty: bool) -> tuple[type[object], ...]:
    """Validate a type or list of types and return it as a tuple.

    Args:
        type_spec: Constructor argument to validate.
        parameter_name: Name used in error messages.
        allow_empty: Whether an empty list is accepted.

    Returns:
        The validated runtime types as a tuple.

    Raises:
        TypeError: If ``type_spec`` is not a type or list of types.
        ValueError: If ``type_spec`` is an empty list and empty is rejected.
    """
    if isinstance(type_spec, type):
        return (type_spec,)
    if not isinstance(type_spec, list):
        msg = f'{parameter_name} must be a type or a list of types.'
        raise TypeError(msg)
    if len(type_spec) == 0 and not allow_empty:
        raise ValueError(f'{parameter_name} must be non-empty.')
    return tuple(
        _validate_type_argument(value_type, f'{parameter_name}[{index}]')
        for index, value_type in enumerate(type_spec))


def _copy_type_spec(value_types: tuple[type[object], ...]) \
        -> type[object] | list[type[object]]:
    """Return the public representation for one validated type spec.

    Args:
        value_types: Validated type tuple.

    Returns:
        The only type directly, or a list when there are several types.
    """
    if len(value_types) == 1:
        return value_types[0]
    return list(value_types)


def _format_type_names(value_types: tuple[type[object], ...]) -> str:
    """Return a short human-readable list of runtime type names.

    Args:
        value_types: Runtime types to include in the text.

    Returns:
        A comma-separated list with ``or`` before the last type.
    """
    names = [value_type.__name__ for value_type in value_types]
    if len(names) == 1:
        return names[0]
    return ', '.join(names[:-1]) + ' or ' + names[-1]


def _matches_type_spec(member_value: object,
                       value_types: tuple[type[object], ...],
                       strict: bool) -> bool:
    """Return whether ``member_value`` matches the configured types.

    Args:
        member_value: Value to check.
        value_types: Runtime types to check against.
        strict: Whether exact type matching should be used.

    Returns:
        ``True`` when the value matches one of the runtime types.
    """
    if strict:
        return type(member_value) in value_types
    return isinstance(member_value, value_types)


def _validate_strict(strict: bool) -> None:
    """Validate the strict-mode constructor argument.

    Args:
        strict: Value supplied as the strict-mode flag.

    Raises:
        TypeError: If ``strict`` is not a ``bool``.
    """
    if not isinstance(strict, bool):
        raise TypeError('strict must be a bool.')


def _validate_allowed_denied(allowed: tuple[type[object], ...],
                             denied: tuple[type[object], ...],
                             strict: bool) -> None:
    """Reject allowed types that are completely denied.

    Args:
        allowed: Accepted runtime types.
        denied: Runtime types that are rejected after the allowed check.
        strict: Whether exact type matching should be used.

    Raises:
        ValueError: If one allowed type can never pass the denied check.
    """
    for allowed_type in allowed:
        for denied_type in denied:
            if _type_is_denied(allowed_type, denied_type, strict):
                msg = f'value_type {allowed_type.__name__} is denied by '
                msg += f'not_allowed_type {denied_type.__name__}.'
                raise ValueError(msg)


def _type_is_denied(allowed_type: type[object], denied_type: type[object],
                    strict: bool) -> bool:
    """Return whether one allowed type is rejected by one denied type.

    Args:
        allowed_type: Candidate allowed type.
        denied_type: Candidate denied type.
        strict: Whether exact type matching should be used.

    Returns:
        ``True`` when the constructor arguments contradict each other.
    """
    if strict:
        return allowed_type is denied_type
    return issubclass(allowed_type, denied_type)


def _raise_type_error(member_name: str, member_value: object,
                      value_types: tuple[type[object], ...],
                      stderr_file: TextIO) -> None:
    """Print and raise an invalid-type error for one member value.

    Args:
        member_name: The reported path of the member being validated.
        member_value: Invalid member value.
        value_types: Runtime types accepted by the validator.
        stderr_file: Stream used for diagnostics.

    Raises:
        InvalidConfigurationType: Always.
    """
    _ = member_value
    msg = 'Invalid configuration: '
    msg += f'Value for {member_name} is not of type '
    msg += f'{_format_type_names(value_types)}.'
    print(msg, file=stderr_file)
    raise InvalidConfigurationType(msg)


def _raise_denied_error(member_name: str, member_value: object,
                        denied_types: tuple[type[object], ...],
                        stderr_file: TextIO) -> None:
    """Print and raise an error for one explicitly denied type.

    Args:
        member_name: The reported path of the member being validated.
        member_value: Invalid member value.
        denied_types: Runtime types rejected by the validator.
        stderr_file: Stream used for diagnostics.

    Raises:
        InvalidConfigurationType: Always.
    """
    _ = member_value
    msg = 'Invalid configuration: '
    msg += f'Value for {member_name} must not be of type '
    msg += f'{_format_type_names(denied_types)}.'
    print(msg, file=stderr_file)
    raise InvalidConfigurationType(msg)


def _matching_type(member_value: object,
                   value_types: tuple[type[object], ...]) \
        -> Optional[type[object]]:
    """Return the closest matching type for ``member_value``.

    Args:
        member_value: Value to match against the candidate types.
        value_types: Candidate runtime types.

    Returns:
        The candidate type nearest to the value type, or ``None``.
    """
    matches = [value_type for value_type in value_types
               if isinstance(member_value, value_type)]
    if len(matches) == 0:
        return None
    member_type = type(member_value)
    return min(matches, key=partial(_type_rank, member_type))


def _type_rank(member_type: type[object], value_type: type[object]) -> int:
    """Return how close ``value_type`` is in ``member_type``'s MRO.

    Args:
        member_type: Runtime type of the value being converted.
        value_type: Candidate base type.

    Returns:
        Lower numbers mean a more specific match.
    """
    if value_type in member_type.__mro__:
        return member_type.__mro__.index(value_type)
    return len(member_type.__mro__)


T = TypeVar('T', bound=object)


def _validate_convert_map(
        convertable_types: Optional[dict[type[object], Callable[[object], T]]]
        ) -> dict[type[object], Callable[[object], T]]:
    """Validate conversion functions keyed by runtime type.

    Args:
        convertable_types: Optional conversion mapping.

    Returns:
        A shallow copy of the validated conversion mapping.

    Raises:
        TypeError: If the mapping, keys, or values are invalid.
    """
    if convertable_types is None:
        return {}
    if not isinstance(convertable_types, dict):
        raise TypeError('convertable_types must be a dict.')
    result: dict[type[object], Callable[[object], T]] = {}
    for key, conversion in convertable_types.items():
        value_type = _validate_type_argument(key, 'convertable_types key')
        if not callable(conversion):
            msg = f'convertable_types[{value_type.__name__}] '
            msg += 'must be callable.'
            raise TypeError(msg)
        result[value_type] = conversion
    return result


def _validate_no_overlap(direct_types: tuple[type[object], ...],
                         convertable_types: dict[type[object],
                                                 Callable[[object], T]]) \
                                                     -> None:
    """Reject exact type overlap between direct and callable conversion.

    Args:
        direct_types: Types converted with the target constructor.
        convertable_types: Types converted with custom callables.

    Raises:
        ValueError: If a type is present in both conversion sets.
    """
    for direct_type in direct_types:
        if direct_type in convertable_types:
            msg = f'{direct_type.__name__} is both a direct type and '
            msg += 'a convertable type.'
            raise ValueError(msg)


def _raise_conversion_error(member_name: str, member_value: object,
                            target_type: type[object], stderr_file: TextIO,
                            cause: Exception) -> None:
    """Print and raise an error when conversion fails.

    Args:
        member_name: The reported path of the member being validated.
        member_value: Member value that could not be converted.
        target_type: Runtime type the value should convert to.
        stderr_file: Stream used for diagnostics.
        cause: Exception raised by the conversion.

    Raises:
        InvalidConfigurationType: Always.
    """
    _ = member_value
    msg = 'Invalid configuration: '
    msg += f'Value for {member_name} could not be converted to '
    msg += f'{target_type.__name__}.'
    print(msg, file=stderr_file)
    raise InvalidConfigurationType(msg) from cause


def _validate_converted_value(member_name: str, converted_value: object,
                              target_type: type[object],
                              stderr_file: TextIO) -> None:
    """Validate that a conversion returned the target runtime type.

    Args:
        member_name: The reported path of the member being validated.
        converted_value: Result returned from the conversion.
        target_type: Required runtime type after conversion.
        stderr_file: Stream used for diagnostics.

    Raises:
        InvalidConfigurationType: If the result has the wrong type.
    """
    if isinstance(converted_value, target_type):
        return
    msg = 'Invalid configuration: '
    msg += f'Conversion for {member_name} returned '
    msg += f'{type(converted_value).__name__} instead of '
    msg += f'{target_type.__name__}.'
    print(msg, file=stderr_file)
    raise InvalidConfigurationType(msg)


class InvalidConfigurationType(InvalidConfiguration):
    """Raised when a member value has an invalid runtime type."""


# pylint: disable-next=too-few-public-methods
class ValueTypeValidator(MemberValidator):
    """Validate that one member value has the configured runtime type.

    The validator accepts either one runtime type or a list of runtime types.
    Normal mode uses ``isinstance`` semantics, so subclasses are accepted.
    Strict mode uses exact ``type(value)`` matching. Optional denied types
    are checked with the same strictness as the allowed types.
    """

    def __init__(self, value_type: type[object] | list[type[object]],
                 not_allowed_type: Optional[
                     type[object] | list[type[object]]] = None,
                 strict: bool = False) -> None:
        """Initialize the validator.

        Args:
            value_type: Required runtime type or types for the member value.
            not_allowed_type: Optional runtime types that are not allowed.
            strict: Whether to require exact runtime type matches.

        Raises:
            TypeError: If a type specification is invalid.
            TypeError: If ``strict`` is not a boolean.
            ValueError: If ``value_type`` is an empty list.
            ValueError: If allowed and denied types contradict each other.
        """
        _validate_strict(strict)
        self._value_types = _validate_type_spec(value_type, 'value_type',
                                                allow_empty=False)
        if not_allowed_type is None:
            self._not_allowed_types: tuple[type[object], ...] = ()
        else:
            self._not_allowed_types = _validate_type_spec(not_allowed_type,
                                                          'not_allowed_type',
                                                          allow_empty=True)
        _validate_allowed_denied(self._value_types, self._not_allowed_types,
                                 strict)
        self.value_type: type[object] | list[type[object]] = \
            _copy_type_spec(self._value_types)
        self.not_allowed_type: Optional[type[object] | list[type[object]]] = \
            None if not_allowed_type is None else \
            _copy_type_spec(self._not_allowed_types)
        self.strict: bool = strict

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one member's runtime type.

        Args:
            config: The Config object that owns the member.
            member_name: The reported dotted and indexed path of the
                member to validate.
            member_value: The member value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            The original member value if validation succeeds.

        Raises:
            InvalidConfigurationType: If ``member_value`` does not match the
                allowed types, or if it matches a denied type.
        """
        _ = config
        if not _matches_type_spec(member_value, self._value_types,
                                  self.strict):
            _raise_type_error(member_name, member_value, self._value_types,
                              stderr_file)
        if self._not_allowed_types and _matches_type_spec(
                member_value, self._not_allowed_types, self.strict):
            _raise_denied_error(member_name, member_value,
                                self._not_allowed_types, stderr_file)
        return member_value


# pylint: disable-next=too-few-public-methods
class ValueAsTypeValidator(ValueTypeValidator, Generic[T]):
    """Normalize one member value to the configured runtime type.

    Values already matching ``value_type`` are returned unchanged. Other
    accepted values are converted either by calling ``value_type(value)`` for
    direct types, or by a custom conversion function for convertable types.
    """

    def __init__(self, value_type: type[T],
                 direct_types: Optional[
                     type[object] | list[type[object]]] = None,
                 convertable_types: Optional[
                     dict[type[object], Callable[[object], T]]] = None
                 ) -> None:
        """Initialize the validator.

        Args:
            value_type: Runtime type to normalize the member value to.
            direct_types: Runtime types converted with ``value_type(value)``.
            convertable_types: Runtime types converted with custom callables.

        Raises:
            TypeError: If any constructor argument has an invalid shape.
            ValueError: If one type is both direct and convertable.
        """
        target_type = _validate_type_argument(value_type, 'value_type')
        super().__init__(target_type)
        if direct_types is None:
            self._direct_types: tuple[type[object], ...] = ()
        else:
            self._direct_types = _validate_type_spec(direct_types,
                                                     'direct_types',
                                                     allow_empty=True)
        self._convertable_types = _validate_convert_map(convertable_types)
        _validate_no_overlap(self._direct_types, self._convertable_types)
        self._target_type: type[T] = value_type
        self.direct_types: Optional[type[object] | list[type[object]]] = \
            None if direct_types is None else \
            _copy_type_spec(self._direct_types)
        self.convertable_types: dict[type[object], Callable[[object], T]] = \
            dict(self._convertable_types)

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Normalize the member value to the configured runtime type.

        If both a direct type and a convertable type match, the type closest
        to ``type(member_value)`` in the MRO decides which conversion path is
        used.

        Args:
            config: The Config object that owns the member.
            member_name: The reported dotted and indexed path of the
                member to validate.
            member_value: The member value to validate.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfigurationType: If the value is not accepted, if
                conversion fails, or if conversion returns the wrong type.

        Returns:
            The original or normalized member value if validation succeeds.
        """
        _ = config
        if isinstance(member_value, self._target_type):
            return member_value
        direct_type = _matching_type(member_value, self._direct_types)
        conv_type = _matching_type(member_value,
                                   tuple(self._convertable_types.keys()))
        if direct_type is None and conv_type is None:
            allowed_types = self._conversion_input_types()
            _raise_type_error(member_name, member_value, allowed_types,
                              stderr_file)
        if self._use_direct(member_value, direct_type, conv_type):
            return self._convert_direct(member_name, member_value, stderr_file)
        assert conv_type is not None
        return self._convert_with_func(member_name, member_value, conv_type,
                                       stderr_file)

    def _conversion_input_types(self) -> tuple[type[object], ...]:
        """Return all accepted input types for diagnostics.

        Returns:
            Target, direct, and convertable runtime types in check order.
        """
        return (self._target_type, *self._direct_types,
                *self._convertable_types.keys())

    def _use_direct(self, member_value: object,
                    direct_type: Optional[type[object]],
                    conv_type: Optional[type[object]]) -> bool:
        """Return whether direct constructor conversion should be used.

        Args:
            member_value: Value being converted.
            direct_type: Matching direct type, if any.
            conv_type: Matching callable-conversion type, if any.

        Returns:
            ``True`` when the direct constructor path should be used.
        """
        if direct_type is None:
            return False
        if conv_type is None:
            return True
        member_type = type(member_value)
        direct_rank = _type_rank(member_type, direct_type)
        conv_rank = _type_rank(member_type, conv_type)
        return direct_rank <= conv_rank

    def _convert_direct(self, member_name: str, member_value: object,
                        stderr_file: TextIO) -> T:
        """Convert a value with the target type constructor.

        Args:
            member_name: The reported path of the member being validated.
            member_value: Value to convert.
            stderr_file: Stream used for diagnostics.

        Returns:
            Converted value.

        Raises:
            InvalidConfigurationType: If conversion fails or returns a
                value with the wrong runtime type.
        """
        try:
            constructor = cast(Callable[[object], T], self._target_type)
            converted_value = constructor(member_value)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _raise_conversion_error(member_name, member_value,
                                    self._target_type, stderr_file, exc)
        _validate_converted_value(member_name, converted_value,
                                  self._target_type, stderr_file)
        return converted_value

    def _convert_with_func(self, member_name: str, member_value: object,
                           conv_type: type[object], stderr_file: TextIO) -> T:
        """Convert a value with a configured conversion function.

        Args:
            member_name: The reported path of the member being validated.
            member_value: Value to convert.
            conv_type: Matching key in ``convertable_types``.
            stderr_file: Stream used for diagnostics.

        Returns:
            Converted value.

        Raises:
            InvalidConfigurationType: If conversion fails or returns a
                value with the wrong runtime type.
        """
        conversion = self._convertable_types[conv_type]
        try:
            converted_value = conversion(member_value)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _raise_conversion_error(member_name, member_value,
                                    self._target_type, stderr_file, exc)
        _validate_converted_value(member_name, converted_value,
                                  self._target_type, stderr_file)
        return converted_value
