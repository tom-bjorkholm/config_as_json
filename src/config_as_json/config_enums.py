#! /usr/local/bin/python3
"""Enumerations used in configuration of excel list transform."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License


from enum import Enum, auto


class FileType(Enum):
    """Is I/O file excel or CSV."""

    EXCEL = auto()
    CSV = auto()


class SplitWhere(Enum):
    """Use leftmost or rightmost separator for splitting."""

    LEFTMOST = auto()
    RIGHTMOST = auto()


class ExcelLib(Enum):
    """Use specified library for excel reading or writing."""

    OPENPYXL = auto()
    XLSXWRITER = auto()
    PYLIGHTXL = auto()


class RewriteKind(Enum):
    """Kind of write operation to apply."""

    STRIP = auto()
    REMOVECHARS = auto()
    STR_SUBSTITUTE = auto()
    REGEX_SUBSTITUTE = auto()


class CaseSensitivity(Enum):
    """Shall matching be case sensitive or not."""

    MATCH_CASE = auto()
    IGNORE_CASE = auto()


class ColumnRef(Enum):
    """Are columns referenced by number or name."""

    BY_NUMBER = auto()
    BY_NAME = auto()
