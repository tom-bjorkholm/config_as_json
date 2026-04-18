#! /usr/local/bin/python3
"""Implement list validators for config-as-json."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from typing import Callable, Generic, Optional, Sequence, TextIO, TypeVar
from config_as_json.config import Config
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue, Validator, \
    _not_one_of_allowed_values_message, \
    _validate_and_get_constraint_value_type


Basictype = TypeVar('Basictype', int, float, str, bool)
"""Basic scalar type accepted by the list validators."""


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


class ListValueValidator(Validator, Generic[Basictype]):
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

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Raise an exception of incorrect usage.

        Raises:
            RuntimeError: If the validator is used to validate the entire
                          Config object.
        """
        _ = config
        msg = 'ListValueValidator cannot be used to validate the '
        msg += 'entire Config object.'
        print(msg, file=stderr_file)
        raise RuntimeError(msg)


class ListSizeValidator(Validator):
    """Validate the size of a list."""

    def __init__(self, min_size: int, max_size: int) -> None:
        """Initialize the validator.

        Args:
            min_size: Minimum allowed size of the list.
            max_size: Maximum allowed size of the list.
        """
        self.min_size: int = min_size
        self.max_size: int = max_size

    def validate_member(self, config: Config,
                        member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate the size of a list."""
        _ = config
        if not isinstance(member_value, list):
            msg = 'Invalid configuration: '
            msg += f'Value for {member_name} is not a list.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        if len(member_value) < self.min_size:
            msg = 'Invalid configuration: '
            msg += f'Value for {member_name} is list with size '
            msg += f'{len(member_value)} which is less than minimum '
            msg += f'{self.min_size}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        if len(member_value) > self.max_size:
            msg = 'Invalid configuration: '
            msg += f'Value for {member_name} is list with size '
            msg += f'{len(member_value)} which is greater than maximum '
            msg += f'{self.max_size}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        return member_value

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Raise an exception of incorrect usage.

        Raises:
            RuntimeError: If the validator is used to validate the entire
                          Config object.
        """
        _ = config
        msg = 'ListSizeValidator cannot be used to validate the '
        msg += 'entire Config object.'
        print(msg, file=stderr_file)
        raise RuntimeError(msg)


class ListIsOrderedValidator(Validator, Generic[Basictype]):
    """Validate that a list is ordered or only has unique values."""

    def __init__(self,  # pylint: disable=too-many-arguments, too-many-positional-arguments # noqa: E501
                 element_type: type[Basictype],
                 is_ordered: bool = True, is_reversed: bool = False,
                 unique_values: bool = False,
                 lt_comparator: Callable[[Basictype, Basictype], bool] =
                 lambda x, y: x < y) -> None:
        """Initialize the validator.
        
        Initializes a validator that checks that a list is ordered
        or only has unique values. Additionally it always checks that all
        list elements are of the correct type. If is_ordered is True, the
        list is checked to be ordered. If is_reversed is True, the list is
        checked to be reversed. If unique_values is True, the list is
        checked to only have unique values.

        Args:
            element_type: The type of the elements in the list. Must be a
                          one of the Basictype types.
            is_ordered: Check whether the list is ordered.
            is_reversed: If True, when checking the order, check that each
                         element is less than or equal to the previous element.
                         If False, when checking the order, check that each
                         element is greater than or equal to the previous
                         element.
            unique_values: Check whether the list only has unique values.
            lt_comparator: Comparator function for the Basictype values.
                           Defaults to the < operator.
        """
        self.element_type: type[Basictype] = element_type
        self.is_ordered: bool = is_ordered
        self.is_reversed: bool = is_reversed
        self.unique_values: bool = unique_values
        self.lt_comparator: Callable[[Basictype, Basictype], bool] = \
            lt_comparator


class ListOrderingValidator(Validator, Generic[Basictype]):
    """Validator that reorders a list."""

    def __init__(self,  # pylint: disable=too-many-arguments, too-many-positional-arguments # noqa: E501
                 element_type: type[Basictype],
                 order: bool = True, reverse: bool = False,
                 keep_only_unique: bool = False,
                 lt_comparator: Callable[[Basictype, Basictype], bool] =
                 lambda x, y: x < y) -> None:
        """Initialize the validator.

        Initializes a validator that reorders a list.
        Additionally it always checks that all list elements are of the correct
        type.

        Args:
            element_type: The type of the elements in the list. Must be a
                          one of the Basictype types.
            order: If True, the list is reordered to be ordered.
            reverse: If True, and order is True, the list is reordered
                     so that each element is less than or equal to the
                     previous element.
                     If False, and order is True, the list is reordered
                     so that each element is greater than or equal
                     to the previous element.
                     If True, and order is False, the list is reordered
                     so that the list is reversed (compared to the order
                     of the original list).
            keep_only_unique: If True, the list is reordered to only have
                              unique values.
            lt_comparator: Comparator function for the Basictype values.
                           Defaults to the < operator.
        """
        self.element_type: type[Basictype] = element_type
        self.order: bool = order
        self.reverse: bool = reverse
        self.keep_only_unique: bool = keep_only_unique
        self.lt_comparator: Callable[[Basictype, Basictype], bool] = \
            lt_comparator
