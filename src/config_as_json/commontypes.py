#! /usr/local/bin/python3
"""Common type definitions used for type hints."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License


from typing import Optional, cast, Sequence, Mapping, TypeVar, \
    Any
from datetime import datetime
# imports needed by mypy, but not by python:
from typing import Union, List, Dict  # pylint: disable=unused-import,ungrouped-imports # noqa: E501


# types used to describe input and output data
type Value = Optional[str | int | float | datetime]
type NumRow = list[Value]
type NumRowSeq = Sequence[Value]
type NameRow = dict[str, Value]
Row = TypeVar('Row', NumRow, NameRow)
type NameRowMap = Mapping[str, Value]
type NumData = list[NumRow]
type NumDataSeq = list[NumRowSeq]
type NameData = list[NameRow]
type NameDataMap = Sequence[NameRowMap]
type Data[Row] = list[Row]
DataCov = TypeVar('DataCov', NumDataSeq, NameDataMap)

type JsonType = \
    'Union[None, int, str, bool, List[JsonType], Dict[str, JsonType]]'

# helper functions


def num_row_to_str_list(row: NumRowSeq) -> list[str]:
    """Convert NumRow to list of str."""
    ret: list[str] = []
    for i in row:
        if isinstance(i, str):
            ret.append(i)
        elif i is None:
            raise TypeError('Found None when expecting str.')
        else:
            ret.append(str(i))
    return ret


def str_list_to_num_row(row: list[str]) -> NumRow:
    """Convert list of str to NumRow."""
    return cast(NumRow, row)


T = TypeVar('T')


def get_checked_type(value: Optional[Any], istype: type[T]) -> T:
    """Get value narrowed to be of type istype."""
    assert value is not None
    assert isinstance(value, istype)
    return value
