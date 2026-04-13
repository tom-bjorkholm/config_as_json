#! /usr/local/bin/python3
"""Functions to add and remove file extensions."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License


from os import path
from copy import deepcopy
from typing import Optional


def fix_file_extension(filename: str, ext_to_add: str,
                       ext_to_remove: Optional[str] = None,
                       for_reading: bool = False) -> str:
    """Add and remove file extensions as needed."""
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
