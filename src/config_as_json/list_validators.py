#! /usr/local/bin/python3
"""Implement the list validators for config-as-json."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License


from typing import TypeVar


Basictype = TypeVar('Basictype', int, float, str, bool)
"""Basic scalar type accepted by the list validators."""
