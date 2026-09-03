#! /usr/local/bin/python3
"""Collect shared helpers for list validators."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from typing import TextIO, TypeVar
from config_as_json.validator import InvalidConfiguration


Basictype = TypeVar('Basictype', int, float, str, bool)
"""Basic scalar type accepted by the list validators."""


Elementtype = TypeVar('Elementtype')
"""Element type accepted by key-based list ordering validators."""


def _validate_basic_list_type(value_type: type[object],
                              parameter_name: str) -> None:
    """Validate that a list validator uses one supported scalar type.

    Args:
        value_type: The configured scalar type.
        parameter_name: The constructor argument name used in error messages.

    Raises:
        TypeError: If ``value_type`` is not exactly ``int``, ``float``,
                   ``str``, or ``bool``.
    """
    if value_type not in (int, float, str, bool):
        msg = f'{parameter_name} must be one of int, float, str, or bool.'
        raise TypeError(msg)


def _validate_list_member_value(member_name: str, member_value: object,
                                stderr_file: TextIO) -> list[object]:
    """Validate that one member value is a list and return it.

    Args:
        member_name: The reported path of the member, used in any
            error message.
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
