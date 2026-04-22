#! /usr/local/bin/python3
"""Implement list validators for config-as-json."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from functools import cmp_to_key
from typing import Callable, Generic, Optional, Sequence, TextIO, TypeVar
from config_as_json.config import Config
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue, MemberValidator, \
    _not_one_of_allowed_values_message, \
    _validate_and_get_constraint_value_type


Basictype = TypeVar('Basictype', int, float, str, bool)
"""Basic scalar type accepted by the list validators."""


def _validate_supported_list_element_type(
        element_type: type[object]) -> None:
    """Validate that a list validator uses one supported runtime type.

    Args:
        element_type: The element type configured for a list validator.

    Raises:
        TypeError: If ``element_type`` is not exactly ``int``, ``float``,
                   ``str``, or ``bool``.
    """
    if element_type not in (int, float, str, bool):
        msg = 'element_type must be one of int, float, str, or bool.'
        raise TypeError(msg)


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


def _validate_list_member_value(member_name: str, member_value: object,
                                stderr_file: TextIO) -> list[object]:
    """Validate that one member value is a list and return it.

    Args:
        member_name: The member name used in any error message.
        member_value: The value to validate.
        stderr_file: The file to write error messages to.

    Returns:
        The validated list value.

    Raises:
        InvalidConfiguration: If ``member_value`` is not a list.
    """
    if not isinstance(member_value, list):
        msg = 'Invalid configuration: '
        msg += f'Value for {member_name} is not a list.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)
    return member_value


def _validate_typed_list_member(
        member_name: str, member_value: object, element_type: type[Basictype],
        stderr_file: TextIO) -> list[Basictype]:
    """Validate that a member is a list with elements of one runtime type.

    Args:
        member_name: The member name used in any error message.
        member_value: The value to validate.
        element_type: The required runtime type of each list element.
        stderr_file: The file to write error messages to.

    Returns:
        The validated list value with a narrow element type.

    Raises:
        InvalidConfiguration: If the member is not a list or one element has
                              the wrong runtime type.
    """
    raw_list = _validate_list_member_value(
        member_name=member_name, member_value=member_value,
        stderr_file=stderr_file)
    typed_list: list[Basictype] = []
    for member_index, raw_value in enumerate(raw_list):
        if not isinstance(raw_value, element_type):
            msg = 'Invalid configuration: '
            msg += f'Value {raw_value} for {member_name} '
            msg += f'at index {member_index} '
            msg += f'is not of type {element_type.__name__}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        typed_list.append(raw_value)
    return typed_list


def _sort_list_values(values: Sequence[Basictype],
                      lt_comparator: Callable[[Basictype, Basictype], bool],
                      reverse: bool) -> list[Basictype]:
    """Return a stably sorted list using a less-than comparator.

    Args:
        values: The values to sort.
        lt_comparator: The less-than comparator used for ordering.
        reverse: Whether to reverse the final sort order.

    Returns:
        A new sorted list.
    """
    def compare(left: Basictype, right: Basictype) -> int:
        """Compare two values for use with ``cmp_to_key``."""
        if lt_comparator(left, right):
            return -1
        if lt_comparator(right, left):
            return 1
        return 0

    return sorted(values, key=cmp_to_key(compare), reverse=reverse)


def _unique_list_values(values: Sequence[Basictype]) -> list[Basictype]:
    """Return the first occurrence of each value in the current order.

    Args:
        values: The values to deduplicate.

    Returns:
        A new list with only the first occurrence of each value kept.
    """
    return list(dict.fromkeys(values))


def _validate_list_order(
        member_name: str, values: Sequence[Basictype], is_reversed: bool,
        lt_comparator: Callable[[Basictype, Basictype], bool],
        stderr_file: TextIO) -> None:
    """Validate that adjacent values are in the requested non-strict order.

    Args:
        member_name: The member name used in any error message.
        values: The typed list values to validate.
        is_reversed: Whether descending order is required.
        lt_comparator: The less-than comparator used for ordering.
        stderr_file: The file to write error messages to.

    Raises:
        InvalidConfiguration: If the list is not in the requested order.
    """
    for member_index in range(1, len(values)):
        previous_value = values[member_index - 1]
        value = values[member_index]
        is_out_of_order = lt_comparator(previous_value, value) \
            if is_reversed else lt_comparator(value, previous_value)
        if is_out_of_order:
            msg = 'Invalid configuration: '
            msg += f'Value {value} for {member_name} '
            msg += f'at index {member_index} '
            if is_reversed:
                msg += f'is greater than previous value {previous_value}.'
            else:
                msg += f'is less than previous value {previous_value}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)


def _validate_unique_list_values(member_name: str,
                                 values: Sequence[Basictype],
                                 stderr_file: TextIO) -> None:
    """Validate that a list contains no duplicate values.

    Duplicate detection uses normal Python equality semantics rather than the
    custom ordering comparator.

    Args:
        member_name: The member name used in any error message.
        values: The typed list values to validate.
        stderr_file: The file to write error messages to.

    Raises:
        InvalidConfiguration: If a duplicate value is found.
    """
    first_indices: dict[Basictype, int] = {}
    for member_index, value in enumerate(values):
        if value in first_indices:
            msg = 'Invalid configuration: '
            msg += f'Value {value} for {member_name} '
            msg += f'at index {member_index} duplicates the value '
            msg += f'at index {first_indices[value]}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        first_indices[value] = member_index


def _indexed_not_one_of_allowed_values(
        member_name: str, member_value: object, member_index: int,
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
    return _not_one_of_allowed_values_message(
        member_name=member_name, member_value=member_value,
        allowed_values=allowed_values, stderr_file=stderr_file,
        member_index=member_index)


class _IndexedInvalidConfigurationValue(InvalidConfigurationValue):
    """Raised when a list element value is not one of the allowed values."""

    def __init__(self, member_name: str, member_value: object,
                 member_index: int,
                 allowed_values: Sequence[object]) -> None:
        """Initialize the exception."""
        super().__init__(member_name, member_value, allowed_values)
        self.member_index: int = member_index
        self.message = _indexed_not_one_of_allowed_values(
            member_name, member_value, member_index, allowed_values, None)
        self.args = (self.message,)


class ListValueValidator(  # pylint: disable=too-few-public-methods
        MemberValidator, Generic[Basictype]):
    """Validate values in a list of basic scalar values."""

    def __init__(self, min_value: Optional[Basictype],
                 max_value: Optional[Basictype],
                 allowed_values: Optional[Sequence[Basictype]],
                 lt_comparator: Callable[[Basictype, Basictype], bool] =
                 lambda x, y: x < y) -> None:
        """Initialize the validator.

        The validator checks that the member value is a list containing only
        one of the Basictype runtime types. Each element value must
        satisfy every configured constraint: lower bound, upper bound,
        and allowed-values membership.
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
            lt_comparator: Comparator function for the Basictype values.
                           Defaults to the < operator.

        Raises:
            ValueError: If no constraints are provided.
            ValueError: If allowed_values is provided as an empty sequence.
            ValueError: If min_value is greater than max_value.
            TypeError: If incompatible or mixed runtime types are used.
        """
        self._lt_comparator: Callable[[Basictype, Basictype], bool] = \
            lt_comparator
        self._value_type: type[Basictype] = \
            _validate_and_get_constraint_value_type(
                min_value=min_value, max_value=max_value,
                allowed_values=allowed_values,
                lt_comparator=self._lt_comparator)
        self.min_value: Optional[Basictype] = min_value
        self.max_value: Optional[Basictype] = max_value
        self.allowed_values: Optional[Sequence[Basictype]] = allowed_values

    def validate_member(self, config: Config,
                        member_name: str,
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
        if not isinstance(member_value, list):
            msg = 'Invalid configuration: '
            msg += f'Value for {member_name} is not a list.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        for member_index, raw_value in enumerate(member_value):
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
            if self.allowed_values is not None and \
                    value not in self.allowed_values:
                _ = _indexed_not_one_of_allowed_values(
                    member_name, value, member_index, self.allowed_values,
                    stderr_file)
                raise _IndexedInvalidConfigurationValue(
                    member_name, value, member_index, self.allowed_values)
        return member_value


class ListSizeValidator(MemberValidator):  # pylint: disable=too-few-public-methods # noqa: E501
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

    def validate_member(self, config: Config,
                        member_name: str,
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


class ListIsOrderedValidator(MemberValidator,  # pylint: disable=too-few-public-methods # noqa: E501
                             Generic[Basictype]):
    """Validate list element types, optional ordering, and uniqueness."""

    def __init__(self,  # pylint: disable=too-many-arguments, too-many-positional-arguments # noqa: E501
                 element_type: type[Basictype],
                 is_ordered: bool = True, is_reversed: bool = False,
                 unique_values: bool = False,
                 lt_comparator: Callable[[Basictype, Basictype], bool] =
                 lambda x, y: x < y) -> None:
        """Initialize the validator.

        The validator always checks that the member value is a list and that
        every element is an instance of ``element_type`` using normal
        ``isinstance`` semantics. This means, for example, that ``True`` is
        accepted when ``element_type`` is ``int``.

        If ``is_ordered`` is true, the list must be in non-strict ascending
        order by default, or in non-strict descending order when
        ``is_reversed`` is true. Equal adjacent values are therefore allowed
        unless ``unique_values`` is also true.

        If ``unique_values`` is true, duplicate detection uses normal Python
        equality semantics rather than the custom ordering comparator.

        Args:
            element_type: The type of the elements in the list. Must be a
                          one of the supported basic scalar types.
            is_ordered: Whether to validate element order.
            is_reversed: Whether ordered lists must be descending instead of
                         ascending.
            unique_values: Whether duplicate values are rejected.
            lt_comparator: Comparator function for the Basictype values.
                           Defaults to the < operator.

        Raises:
            TypeError: If ``element_type`` is unsupported.
            ValueError: If ``is_reversed`` is true while ``is_ordered`` is
                        false.
        """
        _validate_supported_list_element_type(element_type)
        if not is_ordered and is_reversed:
            msg = 'is_reversed requires is_ordered to be True.'
            raise ValueError(msg)
        self.element_type: type[Basictype] = element_type
        self.is_ordered: bool = is_ordered
        self.is_reversed: bool = is_reversed
        self.unique_values: bool = unique_values
        self.lt_comparator: Callable[[Basictype, Basictype], bool] = \
            lt_comparator

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one list member against order and uniqueness rules.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the member to validate.
            member_value: The list value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            The original list value if validation succeeds.

        Raises:
            InvalidConfiguration: If the member is not a list, an element has
                                  the wrong type, the list order is wrong, or
                                  duplicates are present when forbidden.
        """
        _ = config
        typed_values = _validate_typed_list_member(
            member_name=member_name, member_value=member_value,
            element_type=self.element_type, stderr_file=stderr_file)
        if self.is_ordered:
            _validate_list_order(
                member_name=member_name, values=typed_values,
                is_reversed=self.is_reversed,
                lt_comparator=self.lt_comparator, stderr_file=stderr_file)
        if self.unique_values:
            _validate_unique_list_values(
                member_name=member_name, values=typed_values,
                stderr_file=stderr_file)
        return member_value


class ListOrderingValidator(MemberValidator,  # pylint: disable=too-few-public-methods # noqa: E501
                            Generic[Basictype]):
    """Normalize one list by ordering, reversing, and deduplicating it."""

    def __init__(self,  # pylint: disable=too-many-arguments, too-many-positional-arguments # noqa: E501
                 element_type: type[Basictype],
                 order: bool = True, reverse: bool = False,
                 keep_only_unique: bool = False,
                 lt_comparator: Callable[[Basictype, Basictype], bool] =
                 lambda x, y: x < y) -> None:
        """Initialize the validator.

        The validator always checks that the member value is a list and that
        every element is an instance of ``element_type`` using normal
        ``isinstance`` semantics. This means, for example, that ``True`` is
        accepted when ``element_type`` is ``int``.

        If ``order`` is true, the list is stably sorted with
        ``lt_comparator``. If ``reverse`` is also true, the sorted result is
        descending.

        If ``order`` is false and ``reverse`` is true, the original list order
        is reversed first.

        If ``keep_only_unique`` is true, duplicate removal happens after any
        ordering or reversing. Duplicate removal is stable in the current
        order, so the first occurrence in the current order is kept and later
        equal values are removed. Duplicate detection uses normal Python
        equality semantics rather than the custom ordering comparator.

        Args:
            element_type: The type of the elements in the list. Must be a
                          one of the supported basic scalar types.
            order: Whether to sort the list.
            reverse: Whether to reverse the sort order, or to reverse the
                     original list when ``order`` is false.
            keep_only_unique: Whether to remove later duplicate values after
                              ordering or reversing.
            lt_comparator: Comparator function for the Basictype values.
                           Defaults to the < operator.

        Raises:
            TypeError: If ``element_type`` is unsupported.
        """
        _validate_supported_list_element_type(element_type)
        self.element_type: type[Basictype] = element_type
        self.order: bool = order
        self.reverse: bool = reverse
        self.keep_only_unique: bool = keep_only_unique
        self.lt_comparator: Callable[[Basictype, Basictype], bool] = \
            lt_comparator

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate and normalize one list member.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the member to validate.
            member_value: The list value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            A reordered or deduplicated list. If no normalization is
            configured, the original list value is returned unchanged.

        Raises:
            InvalidConfiguration: If the member is not a list or one element
                                  has the wrong runtime type.
        """
        _ = config
        typed_values = _validate_typed_list_member(
            member_name=member_name, member_value=member_value,
            element_type=self.element_type, stderr_file=stderr_file)
        if not self.order and not self.reverse and \
                not self.keep_only_unique:
            return member_value
        if self.order:
            result = _sort_list_values(
                values=typed_values, lt_comparator=self.lt_comparator,
                reverse=self.reverse)
        else:
            result = list(typed_values)
            if self.reverse:
                result.reverse()
        if self.keep_only_unique:
            result = _unique_list_values(result)
        return result
