#! /usr/local/bin/python3
"""Implement ordering validators for list members."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from functools import cmp_to_key
from operator import lt as operator_lt
from typing import Callable, Generic, Optional, Sequence, TextIO
from config_as_json._list_validator_common import Basictype, Elementtype, \
    _validate_basic_list_type, _validate_list_member_value
from config_as_json.config import Config
from config_as_json.validator import InvalidConfiguration, MemberValidator, \
    _validate_type_argument


class InvalidListKeyType(InvalidConfiguration):
    """Raised when a key-ordering validator receives a key of wrong type."""

    def __init__(self, member_name: str, member_index: int, key_value: object,
                 key_type: type[object]) -> None:
        """Initialize the exception."""
        self.member_name: str = member_name
        self.member_index: int = member_index
        self.key_value: object = key_value
        self.key_type: type[object] = key_type
        msg = 'Invalid configuration: '
        msg += f'Key value {key_value} for {member_name} '
        msg += f'at index {member_index} '
        msg += f'is not of type {key_type.__name__}.'
        super().__init__(msg)


def _validate_list_element_type(element_type: type[object]) -> None:
    """Validate that a list validator uses one supported runtime type.

    Args:
        element_type: The element type configured for a list validator.

    Raises:
        TypeError: If ``element_type`` is not exactly ``int``, ``float``,
                   ``str``, or ``bool``.
    """
    _validate_basic_list_type(element_type, 'element_type')


def _validate_list_key_type(key_type: type[object]) -> None:
    """Validate that a key-ordering validator uses a supported key type.

    Args:
        key_type: The key type configured for a list validator.

    Raises:
        TypeError: If ``key_type`` is not exactly ``int``, ``float``,
                   ``str``, or ``bool``.
    """
    _validate_basic_list_type(key_type, 'key_type')


def _validate_typed_list_member(member_name: str, member_value: object,
                                element_type: type[Basictype],
                                stderr_file: TextIO) -> list[Basictype]:
    """Validate that a member is a list with elements of one runtime type.

    Args:
        member_name: The reported path of the member, used in any
            error message.
        member_value: The value to validate.
        element_type: The required runtime type of each list element.
        stderr_file: The file to write error messages to.

    Returns:
        The validated list value with a narrow element type.

    Raises:
        InvalidConfiguration: If the member is not a list or one element has
                              the wrong runtime type.
    """
    raw_list = _validate_list_member_value(member_name=member_name,
                                           member_value=member_value,
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


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def _validate_keyed_list_member(
        member_name: str, member_value: object,
        element_type: type[Elementtype], key: Callable[[Elementtype],
                                                       Basictype],
        key_type: type[Basictype], stderr_file: TextIO
        ) -> list[tuple[Elementtype, Basictype]]:
    """Validate one list and return each element with its projected key.

    Args:
        member_name: The reported path of the member, used in any
            error message.
        member_value: The value to validate.
        element_type: The required runtime type of each list element.
        key: Callable that computes the ordering key for one element.
        key_type: The required runtime type of each projected key.
        stderr_file: The file to write error messages to.

    Returns:
        A list of ``(element, key)`` pairs.

    Raises:
        InvalidConfiguration: If the member is not a list or one element has
                              the wrong runtime type.
        InvalidListKeyType: If one projected key has the wrong runtime type.
    """
    raw_list = _validate_list_member_value(member_name=member_name,
                                           member_value=member_value,
                                           stderr_file=stderr_file)
    keyed_list: list[tuple[Elementtype, Basictype]] = []
    for member_index, raw_value in enumerate(raw_list):
        if not isinstance(raw_value, element_type):
            msg = 'Invalid configuration: '
            msg += f'Value {raw_value} for {member_name} '
            msg += f'at index {member_index} '
            msg += f'is not of type {element_type.__name__}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        key_value = key(raw_value)
        if not isinstance(key_value, key_type):
            exc = InvalidListKeyType(member_name=member_name,
                                     member_index=member_index,
                                     key_value=key_value, key_type=key_type)
            print(exc.message, file=stderr_file)
            raise exc
        keyed_list.append((raw_value, key_value))
    return keyed_list


def _compare_values(left: Basictype, right: Basictype,
                    lt_comparator: Callable[[Basictype, Basictype], bool]
                    ) -> int:
    """Compare two values using a less-than comparator."""
    if lt_comparator(left, right):
        return -1
    if lt_comparator(right, left):
        return 1
    return 0


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
        return _compare_values(left, right, lt_comparator)

    return sorted(values, key=cmp_to_key(compare), reverse=reverse)


def _sort_keyed_list_values(
        values: Sequence[tuple[Elementtype, Basictype]],
        lt_comparator: Callable[[Basictype, Basictype], bool],
        reverse: bool) -> list[tuple[Elementtype, Basictype]]:
    """Return a stably sorted list using each element's projected key.

    Args:
        values: The ``(element, key)`` pairs to sort.
        lt_comparator: The less-than comparator used for keys.
        reverse: Whether to reverse the final sort order.

    Returns:
        A new sorted list of ``(element, key)`` pairs.
    """
    def compare(left: tuple[Elementtype, Basictype],
                right: tuple[Elementtype, Basictype]) -> int:
        """Compare two keyed elements for use with ``cmp_to_key``."""
        return _compare_values(left[1], right[1], lt_comparator)

    return sorted(values, key=cmp_to_key(compare), reverse=reverse)


def _unique_list_values(values: Sequence[Basictype]) -> list[Basictype]:
    """Return the first occurrence of each value in the current order.

    Args:
        values: The values to deduplicate.

    Returns:
        A new list with only the first occurrence of each value kept.
    """
    return list(dict.fromkeys(values))


def _unique_keyed_list_values(values: Sequence[
        tuple[Elementtype, Basictype]]) \
        -> list[tuple[Elementtype, Basictype]]:
    """Return the first element for each key in the current order.

    Args:
        values: The ``(element, key)`` pairs to deduplicate.

    Returns:
        A new list of ``(element, key)`` pairs with unique keys.
    """
    result: list[tuple[Elementtype, Basictype]] = []
    seen_keys: set[Basictype] = set()
    for element, key_value in values:
        if key_value not in seen_keys:
            seen_keys.add(key_value)
            result.append((element, key_value))
    return result


def _validate_list_order(member_name: str, values: Sequence[Basictype],
                         is_reversed: bool,
                         lt_comparator: Callable[[Basictype, Basictype], bool],
                         stderr_file: TextIO) -> None:
    """Validate that adjacent values are in the requested non-strict order.

    Args:
        member_name: The reported path of the member, used in any
            error message.
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


def _validate_unique_list_values(member_name: str, values: Sequence[Basictype],
                                 stderr_file: TextIO) -> None:
    """Validate that a list contains no duplicate values.

    Duplicate detection uses normal Python equality semantics rather than the
    custom ordering comparator.

    Args:
        member_name: The reported path of the member, used in any
            error message.
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


# pylint: disable-next=too-few-public-methods
class ListIsOrderedValidator(MemberValidator, Generic[Basictype]):
    """Validate list element types, optional ordering, and uniqueness."""

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def __init__(self, element_type: type[Basictype], is_ordered: bool = True,
                 is_reversed: bool = False, unique_values: bool = False,
                 lt_comparator: Callable[[Basictype, Basictype], bool] =
                 operator_lt) -> None:
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
            element_type: The type of the elements in the list. Must be one
                          of the supported basic scalar types.
            is_ordered: Whether to validate element order.
            is_reversed: Whether ordered lists must be descending instead of
                         ascending.
            unique_values: Whether duplicate values are rejected.
            lt_comparator: Comparator function for the element values.
                           Defaults to the < operator.

        Raises:
            TypeError: If ``element_type`` is unsupported.
            ValueError: If ``is_reversed`` is true while ``is_ordered`` is
                        false.
        """
        _validate_list_element_type(element_type)
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
            member_name: The reported dotted and indexed path of the
                member to validate.
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
            _validate_list_order(member_name=member_name, values=typed_values,
                                 is_reversed=self.is_reversed,
                                 lt_comparator=self.lt_comparator,
                                 stderr_file=stderr_file)
        if self.unique_values:
            _validate_unique_list_values(member_name=member_name,
                                         values=typed_values,
                                         stderr_file=stderr_file)
        return member_value


# pylint: disable-next=too-few-public-methods
class ListOrderingValidator(MemberValidator, Generic[Basictype]):
    """Normalize one list by ordering, reversing, and deduplicating it."""

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def __init__(self, element_type: type[Basictype], order: bool = True,
                 reverse: bool = False, keep_only_unique: bool = False,
                 lt_comparator: Callable[[Basictype, Basictype], bool] =
                 operator_lt) -> None:
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
            element_type: The type of the elements in the list. Must be one
                          of the supported basic scalar types.
            order: Whether to sort the list.
            reverse: Whether to reverse the sort order, or to reverse the
                     original list when ``order`` is false.
            keep_only_unique: Whether to remove later duplicate values after
                              ordering or reversing.
            lt_comparator: Comparator function for the element values.
                           Defaults to the < operator.

        Raises:
            TypeError: If ``element_type`` is unsupported.
        """
        _validate_list_element_type(element_type)
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
            member_name: The reported dotted and indexed path of the
                member to validate.
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
            result = _sort_list_values(values=typed_values,
                                       lt_comparator=self.lt_comparator,
                                       reverse=self.reverse)
        else:
            result = list(typed_values)
            if self.reverse:
                result.reverse()
        if self.keep_only_unique:
            result = _unique_list_values(result)
        return result


# pylint: disable-next=too-few-public-methods
class ListKeyOrderingValidator(MemberValidator,
                               Generic[Elementtype, Basictype]):
    """Normalize one list by ordering complex elements through scalar keys.

    Use this validator when your configuration stores a list of complex
    elements, such as dictionaries, and your application wants that list
    normalized by one scalar value from each element.

    The member value must be a list. Every element must be an instance of
    ``element_type`` according to normal ``isinstance`` semantics. The
    validator calls ``key`` once for every element, validates that the
    returned key is an instance of ``key_type``, and then orders or
    deduplicates the original elements through those keys. The supported key
    types are the same basic scalar types accepted by
    ``ListOrderingValidator``: ``int``, ``float``, ``str``, and ``bool``.

    Your ``key`` callable owns the application-specific projection from one
    complex element to one scalar key. If the callable raises an exception,
    this validator does not catch or wrap it. Validate the element shape
    before this validator, or make the callable raise the exception you want
    application code to see.

    Ordering and duplicate removal are based on the projected keys, but the
    returned normalized list contains the original elements. If
    ``keep_only_unique`` is true, later elements whose projected key is equal
    to a key already kept are removed. Duplicate-key detection uses normal
    Python equality semantics for the keys rather than ``lt_comparator``.
    """

    # pylint: disable-next=too-many-arguments
    def __init__(self, *, element_type: type[Elementtype],
                 key: Callable[[Elementtype], Basictype],
                 key_type: type[Basictype], order: bool = True,
                 reverse: bool = False, keep_only_unique: bool = False,
                 lt_comparator: Callable[[Basictype, Basictype], bool] =
                 operator_lt) -> None:
        """Initialize the key-ordering validator.

        Args:
            element_type: Runtime type required for each original list
                          element. For example, use ``dict`` for a list of
                          dictionaries.
            key: Callable that computes the scalar ordering key for one
                 element. Exceptions raised by this callable propagate
                 unchanged.
            key_type: Runtime type required for the keys returned by
                      ``key``. Must be one of ``int``, ``float``, ``str``, or
                      ``bool``.
            order: Whether to sort the list by projected key.
            reverse: Whether to reverse the sort order, or to reverse the
                     original list when ``order`` is false.
            keep_only_unique: Whether to remove later elements with duplicate
                              projected keys after ordering or reversing.
            lt_comparator: Comparator function for the projected keys.
                           Defaults to the < operator.

        Raises:
            TypeError: If ``element_type`` is not a type, if ``key`` is not
                       callable, or if ``key_type`` is unsupported.
        """
        _validate_type_argument(element_type, 'element_type')
        if not callable(key):
            raise TypeError('key must be callable.')
        _validate_list_key_type(key_type)
        self.element_type: type[Elementtype] = element_type
        self.key: Callable[[Elementtype], Basictype] = key
        self.key_type: type[Basictype] = key_type
        self.order: bool = order
        self.reverse: bool = reverse
        self.keep_only_unique: bool = keep_only_unique
        self.lt_comparator: Callable[[Basictype, Basictype], bool] = \
            lt_comparator

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate and normalize one list member by projected key.

        Args:
            config: The Config object that owns the member.
            member_name: The reported dotted and indexed path of the
                member to validate.
            member_value: The list value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            A reordered or key-deduplicated list containing the original
            elements. If no normalization is configured, the original list
            value is returned unchanged.

        Raises:
            InvalidConfiguration: If the member is not a list or one element
                                  has the wrong runtime type.
            InvalidListKeyType: If ``key`` returns a value whose runtime type
                                is not accepted by ``key_type``.
        """
        _ = config
        keyed_values = _validate_keyed_list_member(
            member_name=member_name, member_value=member_value,
            element_type=self.element_type, key=self.key,
            key_type=self.key_type, stderr_file=stderr_file)
        if not self.order and not self.reverse and \
                not self.keep_only_unique:
            return member_value
        if self.order:
            result = _sort_keyed_list_values(values=keyed_values,
                                             lt_comparator=self.lt_comparator,
                                             reverse=self.reverse)
        else:
            result = list(keyed_values)
            if self.reverse:
                result.reverse()
        if self.keep_only_unique:
            result = _unique_keyed_list_values(result)
        return [element for element, _ in result]
