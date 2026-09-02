#! /usr/local/bin/python3
"""Shared helpers for the tests about leaving out ``member_name``.

The compatibility layer reads the signature of an application method once
and remembers what it found for the rest of the process, and it warns once
for each function and each class that has to be changed. A test that asserts
a warning therefore declares the class it is about inside the test function
itself, so that no earlier test can have asked about that class already.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
import warnings
from typing import Callable, Optional, TextIO, override
from config_as_json.commontypes import PathOrStr
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.validator import ValidationPlan


def deprecations(action: Callable[[], object]) -> list[str]:
    """Return the deprecation messages that one action emits.

    Args:
        action: Callable performing the action to listen to.

    Returns:
        The message of every ``DeprecationWarning`` the action emitted, in
        the order they were emitted.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        action()
    return [str(item.message) for item in caught
            if issubclass(item.category, DeprecationWarning)]


# The constructor boilerplate below, and the empty validation plan after
# it, is what every nested Config class of every test writes the same way.
# pylint: disable=duplicate-code
class PlainLeaf(Config):
    """A nested configuration written the way this version asks for."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one leaf configuration holding its default value."""
        self.kind = 'plain'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own."""
        _ = stderr_file
        return []
# pylint: enable=duplicate-code


class PlainHolder(Config):
    """A configuration holding one nested configuration in a member."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one holder of the leaf configuration."""
        self.part = PlainLeaf(stderr_file=stderr_file)
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file,
                         member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration."""
        return {'part': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                      config_type=PlainLeaf)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own."""
        _ = stderr_file
        return []


HOLDER_JSON = '{"part": {"kind": "parsed"}}'
"""JSON for one :class:`PlainHolder` with a nested leaf in it."""
