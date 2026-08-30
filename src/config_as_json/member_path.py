#! /usr/local/bin/python3
"""Build the reported path of a value in a nested configuration.

A diagnostic naming a configuration value names the whole path from the top
level configuration down to that value, such as ``outputs[1].section.kind``.
The path is built while the configuration is traversed, on the way in. Going
into an attribute of a nested configuration object appends a dot and the
attribute name. Indexing into a list or a dict appends the index or the key
in square brackets.

The path is text for a person to read, not text for a program to parse back
into its parts. A dict key holding a dot or a square bracket therefore makes
a path that cannot be taken apart again unambiguously.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional


def member_path(member_name: Optional[str], name: str) -> str:
    """Return the path for reaching one attribute of a configuration object.

    Args:
        member_name: Path for reaching the object holding the attribute, or
            ``None`` when that object is the top level and not a member of
            anything.
        name: Local attribute name of the member on that object.

    Returns:
        The path for reaching the member, such as ``outputs[1].kind``.
    """
    return name if member_name is None else f'{member_name}.{name}'


def _indexed_path(member_name: Optional[str], index: int | str) -> str:
    """Return the path for reaching one element of a list or a dict.

    Args:
        member_name: Path for reaching the list or the dict holding the
            element, or ``None`` when that list or dict is the top level and
            not a member of anything.
        index: List index or dict key of the element.

    Returns:
        The path for reaching the element, such as ``outputs[1]`` or
        ``limits[cpu]``.
    """
    return f'{index}' if member_name is None else f'{member_name}[{index}]'
