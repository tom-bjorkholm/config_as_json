#! /usr/local/bin/python3
"""Normalize filenames by removing or appending configured extensions."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License


from os import path
from copy import deepcopy
from typing import Optional


def fix_file_extension(filename: str, ext_to_add: str,
                       ext_to_remove: Optional[str] = None,
                       for_reading: bool = False) -> str:
    """Return ``filename`` with the desired extension normalization applied.

    Args:
        filename: Path text to normalize.
        ext_to_add: Extension that should be present in the returned value.
        ext_to_remove: Optional extension that should be stripped before
            ``ext_to_add`` is applied.
        for_reading: If ``True`` and ``filename`` already exists as written,
            return it unchanged.

    Returns:
        The normalized filename.
    """
    ret = deepcopy(filename)
    low = ret.lower()
    if for_reading and path.exists(path=ret):
        return ret
    if ext_to_remove is not None:
        extlowrem = ext_to_remove.lower()
        extlen = len(ext_to_remove)
        if low[-extlen:] == extlowrem:
            ret = ret[:-extlen]
    extlowadd = ext_to_add.lower()
    extlen = len(ext_to_add)
    if low[-extlen:] != extlowadd:
        ret = ret + ext_to_add
    return ret
