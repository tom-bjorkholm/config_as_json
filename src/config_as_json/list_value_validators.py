#! /usr/local/bin/python3
"""Implement value and size validators for list members."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from operator import lt as operator_lt
from typing import Callable, Generic, Optional, Sequence, TextIO
from config_as_json._list_validator_common import Basictype, \
    _validate_list_member_value
from config_as_json.config import Config
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue, MemberValidator, \
    _not_one_of_allowed_values_message, \
    _get_allowed_values, _values_for_type, \
    _validated_constraint_vtype, _validate_type_argument


def _validate_element_type_arg(element_type: object) -> type[object]:
    """Validate and return a list element runtime type.

    Args:
        element_type: The element type configured for a list validator.

    Returns:
        The validated element type.

    Raises:
        TypeError: If ``element_type`` is not a type.
    """
    return _validate_type_argument(element_type, 'element_type')


def _validate_list_size_bounds(min_size: int, max_size: int) -> None:
    """Validate constructor bounds for ``ListSizeValidator``.

    Args:
        min_size: Minimum allowed list size.
        max_size: Maximum allowed list size.

    Raises:
        TypeError: If one bound is not exactly an ``int``.
        ValueError: If one bound is negative or ``min_size`` exceeds
                    ``max_size``.
    """
    if isinstance(min_size, bool) or not isinstance(min_size, int):
        raise TypeError('min_size must be an int.')
    if isinstance(max_size, bool) or not isinstance(max_size, int):
        raise TypeError('max_size must be an int.')
    if min_size < 0:
        raise ValueError('min_size must be non-negative.')
    if max_size < 0:
        raise ValueError('max_size must be non-negative.')
    if min_size > max_size:
        msg = 'min_size must be less than or equal to max_size.'
        raise ValueError(msg)


def _indexed_not_allowed_message(member_name: str, member_value: object,
                                 member_index: int,
                                 allowed_values: Sequence[object],
                                 stderr_file: Optional[TextIO]) -> str:
    """Construct a message for a list element outside the allowed values.

    Construct a message that one element in a list value is not one of the
    allowed values. If ``stderr_file`` is not ``None``, the message is
    written to it.

    Args:
        member_name: The name of the member that has the invalid list value.
        member_value: The invalid element value in the list.
        member_index: The index of the invalid element in the list.
        allowed_values: The allowed values for elements in the list.
        stderr_file: The file to optionally write error messages to.
            If set to ``None`` explicitly, printing is suppressed.

    Returns:
        A string containing the error message.
    """
    return _not_one_of_allowed_values_message(member_name=member_name,
                                              member_value=member_value,
                                              allowed_values=allowed_values,
                                              stderr_file=stderr_file,
                                              member_index=member_index)


class _IndexedInvalidCfgValue(InvalidConfigurationValue):
    """Raised when a list element value is not one of the allowed values."""

    def __init__(self, member_name: str, member_value: object,
                 member_index: int, allowed_values: Sequence[object]) -> None:
        """Initialize the exception."""
        super().__init__(member_name, member_value, allowed_values)
        self.member_index: int = member_index
        self.message = _indexed_not_allowed_message(member_name, member_value,
                                                    member_index,
                                                    allowed_values, None)
        self.args = (self.message,)


# pylint: disable-next=too-few-public-methods
class ListValueValidator(MemberValidator, Generic[Basictype]):
    """Validate values in a list of basic scalar values."""

    def __init__(self, min_value: Optional[Basictype],
                 max_value: Optional[Basictype],
                 allowed_values: Optional[Sequence[Basictype] |
                                          Callable[[], Sequence[Basictype]]],
                 lt_comparator: Callable[[Basictype, Basictype], bool] =
                 operator_lt) -> None:
        """Initialize the validator.

        The validator checks that the member value is a list containing only
        values of the inferred scalar runtime type. Each element value must
        satisfy every configured constraint: lower bound, upper bound, and
        allowed-values membership.
        At least one of min_value, max_value, or allowed_values must be
        provided.

        Args:
            min_value: Minimum allowed member element value.
                       If ``None``, no minimum value is checked.
            max_value: Maximum allowed member element value.
                       If ``None``, no maximum value is checked.
            allowed_values: The only allowed values for the elements of
                            the member.
                            If ``None``, no allowed-values check is done.
                            If a callable, it is called at validation time
                            to get the allowed values.
            lt_comparator: Comparator function for the element values.
                           Defaults to the < operator.

        Raises:
            ValueError: If no constraints are provided.
            ValueError: If allowed_values is provided as an empty sequence.
            ValueError: If min_value is greater than max_value.
            TypeError: If incompatible or mixed runtime types are used.
        """
        self._lt_comparator: Callable[[Basictype, Basictype], bool] = \
            lt_comparator
        type_values = _values_for_type(min_value, max_value, allowed_values)
        self._value_type: type[Basictype] = \
            _validated_constraint_vtype(min_value, max_value, type_values,
                                        self._lt_comparator)
        self.min_value: Optional[Basictype] = min_value
        self.max_value: Optional[Basictype] = max_value
        self.allowed_values: Optional[
            Sequence[Basictype] | Callable[[], Sequence[Basictype]]] = \
            allowed_values

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one list member against elementwise constraints.

        The validator accepts only actual list values. Each element in the
        list must be an instance of the inferred constraint type and must
        satisfy every configured constraint. The custom comparator is used
        only for lower-bound and upper-bound checks. Membership in
        ``allowed_values`` uses the normal equality semantics of ``in``.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the member to validate.
            member_value: The list value to validate.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfiguration: The member is not a list or one element does
                                  not satisfy type or range constraints.
            InvalidConfigurationValue: One element is not one of the allowed
                                       values.

        Returns:
            The original list value if the validation check passes.
        """
        _ = config
        raw_list = _validate_list_member_value(member_name=member_name,
                                               member_value=member_value,
                                               stderr_file=stderr_file)
        allowed = _get_allowed_values(self.allowed_values, self._value_type)
        for member_index, raw_value in enumerate(raw_list):
            if not isinstance(raw_value, self._value_type):
                msg = 'Invalid configuration: '
                msg += f'Value {raw_value} for {member_name} '
                msg += f'at index {member_index} '
                msg += f'is not of type {self._value_type.__name__}.'
                print(msg, file=stderr_file)
                raise InvalidConfiguration(msg)
            value = raw_value
            if self.min_value is not None and \
                    self._lt_comparator(value, self.min_value):
                msg = 'Invalid configuration: '
                msg += f'Value {value} for {member_name} '
                msg += f'at index {member_index} '
                msg += f'is less than minimum {self.min_value}.'
                print(msg, file=stderr_file)
                raise InvalidConfiguration(msg)
            if self.max_value is not None and \
                    self._lt_comparator(self.max_value, value):
                msg = 'Invalid configuration: '
                msg += f'Value {value} for {member_name} '
                msg += f'at index {member_index} '
                msg += f'is greater than maximum {self.max_value}.'
                print(msg, file=stderr_file)
                raise InvalidConfiguration(msg)
            if allowed is not None and value not in allowed:
                _ = _indexed_not_allowed_message(member_name, value,
                                                 member_index, allowed,
                                                 stderr_file)
                raise _IndexedInvalidCfgValue(member_name, value, member_index,
                                              allowed)
        return member_value


# pylint: disable-next=too-few-public-methods
class ListSizeValidator(MemberValidator):
    """Validate that a list length stays within mandatory size bounds."""

    def __init__(self, min_size: int, max_size: int) -> None:
        """Initialize the validator.

        The validator accepts only actual list values. The list length must be
        between ``min_size`` and ``max_size``, inclusive.

        Args:
            min_size: Minimum allowed size of the list.
            max_size: Maximum allowed size of the list.

        Raises:
            TypeError: If one bound is not exactly an ``int``.
            ValueError: If one bound is negative or ``min_size`` exceeds
                        ``max_size``.
        """
        _validate_list_size_bounds(min_size=min_size, max_size=max_size)
        self.min_size: int = min_size
        self.max_size: int = max_size

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one list member against the configured size bounds.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the member to validate.
            member_value: The list value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            The original list value if validation succeeds.

        Raises:
            InvalidConfiguration: If the member is not a list or its size is
                                  outside the allowed range.
        """
        _ = config
        validated_value = _validate_list_member_value(
            member_name=member_name, member_value=member_value,
            stderr_file=stderr_file)
        if len(validated_value) < self.min_size:
            msg = 'Invalid configuration: '
            msg += f'Value for {member_name} is list with size '
            msg += f'{len(validated_value)} which is less than minimum '
            msg += f'{self.min_size}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        if len(validated_value) > self.max_size:
            msg = 'Invalid configuration: '
            msg += f'Value for {member_name} is list with size '
            msg += f'{len(validated_value)} which is greater than maximum '
            msg += f'{self.max_size}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        return member_value


# pylint: disable-next=too-few-public-methods
class ListValueTypeValidator(MemberValidator):
    """Validate that a member is a list with one element runtime type."""

    def __init__(self, element_type: type[object]) -> None:
        """Initialize the validator.

        Args:
            element_type: Required runtime type for each list element.

        Raises:
            TypeError: If ``element_type`` is not a type.
        """
        self.element_type: type[object] = \
            _validate_element_type_arg(element_type)

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one list member's element types.

        The element checks use normal ``isinstance`` semantics. For example,
        ``ListValueTypeValidator(int)`` accepts ``True`` because ``bool`` is
        a subclass of ``int`` in Python.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the member to validate.
            member_value: The list value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            The original list value if validation succeeds.

        Raises:
            InvalidConfiguration: If the member is not a list or one element
                is not an instance of ``element_type``.
        """
        _ = config
        raw_list = _validate_list_member_value(member_name=member_name,
                                               member_value=member_value,
                                               stderr_file=stderr_file)
        for member_index, raw_value in enumerate(raw_list):
            if not isinstance(raw_value, self.element_type):
                msg = 'Invalid configuration: '
                msg += f'Value {raw_value} for {member_name} '
                msg += f'at index {member_index} '
                msg += f'is not of type {self.element_type.__name__}.'
                print(msg, file=stderr_file)
                raise InvalidConfiguration(msg)
        return member_value
