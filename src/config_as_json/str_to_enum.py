#! /usr/local/bin/python3
"""Functions to fuzzy parse string into enum."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License


from enum import Enum
from typing import TypeVar, Optional

SomeEnum = TypeVar('SomeEnum', bound=Enum)


def string_to_enum_best_match(inp: str, num_type: type[SomeEnum]) -> SomeEnum:
    """Find the enum that is the best match for string.

    Parameters:
    inp: the string that should match an enum value
    num_type: the enumeration class to find enum values in
    """
    assert isinstance(inp, str), 'string_to_enum_best_match called ' + \
        f'with {type(inp).__name__} not str as expected.'
    for variant in (inp, inp.capitalize(), inp.lower(), inp.upper()):
        try:
            return num_type[variant]
        except KeyError:
            pass
    num_match: int = 0
    match: Optional[SomeEnum] = None
    for i in num_type:
        if i.name.upper()[0:len(inp)] == inp.upper():
            num_match += 1
            match = i
    if num_match == 1 and match is not None:
        assert match is not None
        assert isinstance(match, num_type)
        return match
    errstr = inp + ' is not one of: ' + ', '.join([e.name for e in num_type])
    raise KeyError(errstr)
