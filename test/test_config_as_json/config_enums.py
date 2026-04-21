#! /usr/local/bin/python3
"""Enumerations used in the test suite."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License


from enum import Enum, auto


class FileType(Enum):
    """Identify whether a file is handled as Excel or CSV data."""

    EXCEL = auto()
    CSV = auto()


class SplitWhere(Enum):
    """Choose whether splitting uses the leftmost or rightmost separator."""

    LEFTMOST = auto()
    RIGHTMOST = auto()


class ExcelLib(Enum):
    """Select which Excel library should perform I/O operations."""

    OPENPYXL = auto()
    XLSXWRITER = auto()
    PYLIGHTXL = auto()


class RewriteKind(Enum):
    """Describe which text-rewrite operation should be applied."""

    STRIP = auto()
    REMOVECHARS = auto()
    STR_SUBSTITUTE = auto()
    REGEX_SUBSTITUTE = auto()


class CaseSensitivity(Enum):
    """Control whether string matching respects case differences."""

    MATCH_CASE = auto()
    IGNORE_CASE = auto()


class ColumnRef(Enum):
    """Describe whether columns are referenced by number or by name."""

    BY_NUMBER = auto()
    BY_NAME = auto()
