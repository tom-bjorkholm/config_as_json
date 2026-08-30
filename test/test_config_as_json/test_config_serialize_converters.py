#! /usr/local/bin/python3
"""Test integration of :meth:`Config.serialize_converters` with JSON output.

These tests exercise :class:`Config` subclasses that override
``serialize_converters()`` to convert rich Python values (most notably
``IntEnum`` members) into JSON-compatible data during ``as_json_string()``.
The matching read-back paths use ``parse_converters()`` so the tests can
also confirm round-tripping is consistent.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code

import json
import sys
from enum import Enum
from typing import Optional, TextIO, override
import pytest
from config_as_json.commontypes import JsonType, PathOrStr
from config_as_json.config import Config, ParseConverter
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.json_write_hooks import SerializeConverter, \
    SerializeConverters, SerializeSelectorError
from config_as_json.validator import ValidationPlan
from .write_hook_test_helpers import Priority, Severity, to_enum_name


# ----------------------------------------------------------------------
# IntEnum round-trip via explicit converter
# ----------------------------------------------------------------------


class PriorityCfg(Config):
    """Config that uses :class:`Priority` directly as a member value."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the test configuration with default priorities."""
        self.task = 'review'
        self.priority = Priority.MEDIUM
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Skip validation in this focused write-side hook test."""
        _ = stderr_file
        return []

    @override
    def serialize_converters(self) -> SerializeConverters:
        """Convert Priority members to their name before JSON write."""
        return {'priority': SerializeConverter(value_type=Enum,
                                               func=to_enum_name, args={})}

    @override
    def parse_converters(self) -> Optional[dict[str, ParseConverter]]:
        """Parse the name string back into the Priority member."""
        return {'priority': self.get_converter_dict(Priority)}


def test_intenum_serialized_as_name() -> None:
    """A subclass converter turns IntEnum into its name in JSON output."""
    cfg = PriorityCfg()
    cfg.priority = Priority.HIGH
    text = cfg.as_json_string(stderr_file=sys.stderr, member_name=None)
    payload = json.loads(text)
    assert payload == {'task': 'review', 'priority': 'HIGH'}


def test_intenum_round_trips() -> None:
    """Writing and reading back recovers the IntEnum member."""
    cfg = PriorityCfg()
    cfg.priority = Priority.LOW
    text = cfg.as_json_string(stderr_file=sys.stderr, member_name=None)
    cfg2 = PriorityCfg(from_json_data_text=text)
    assert cfg2.priority is Priority.LOW
    assert cfg2.task == cfg.task


# ----------------------------------------------------------------------
# Enum fallback still works without override
# ----------------------------------------------------------------------


class SeverityCfg(Config):
    """Config that exercises the built-in Enum fallback (no converter)."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the configuration with a default severity."""
        self.label = 'incident'
        self.severity = Severity.LOW
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Skip validation in this test configuration."""
        _ = stderr_file
        return []

    @override
    def parse_converters(self) -> Optional[dict[str, ParseConverter]]:
        """Convert the severity name back into the enum member."""
        return {'severity': self.get_converter_dict(Severity)}


def test_plain_enum_fallback() -> None:
    """Without an explicit converter the Enum fallback writes the name."""
    cfg = SeverityCfg()
    cfg.severity = Severity.HIGH
    text = cfg.as_json_string(stderr_file=sys.stderr, member_name=None)
    payload = json.loads(text)
    assert payload == {'label': 'incident', 'severity': 'HIGH'}


# ----------------------------------------------------------------------
# Nested Config: parent converter must not reach into child data
# ----------------------------------------------------------------------


class ChildSection(Config):
    """Nested Config that owns its own ``severity`` member.

    The child does not declare an explicit converter, so the built-in
    fallback turns its ``Severity`` member into the symbolic name.
    """

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the child section with a default severity."""
        self.severity = Severity.LOW
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Skip validation in this test configuration."""
        _ = stderr_file
        return []

    @override
    def parse_converters(self) -> Optional[dict[str, ParseConverter]]:
        """Convert the severity name back into the enum member."""
        return {'severity': self.get_converter_dict(Severity)}


def _scream(value: object, *, path_text: str, stderr_file: TextIO,
            **_extra: object) -> JsonType:
    """Uppercase a string. Used to detect boundary-crossing leaks."""
    _ = path_text, stderr_file
    assert isinstance(value, str)
    return value.upper()


class ParentWithChild(Config):
    """Parent Config with a single nested child and a recursive converter."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the configuration with a default child section."""
        self.label = 'parent'
        self.parent_note = 'hello'
        self.section = ChildSection(stderr_file=stderr_file)
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Declare the ``section`` member as a single nested Config."""
        return {'section': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                         config_type=ChildSection)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Skip validation in this test configuration."""
        _ = stderr_file
        return []

    @override
    def serialize_converters(self) -> SerializeConverters:
        """Use a recursive selector that intentionally also names ``label``."""
        return {'parent_note': SerializeConverter(value_type=str, func=_scream,
                                                  args={})}


def test_parent_converter_bounded() -> None:
    """A parent converter on a key that also exists in a child is bounded.

    The child's ``severity`` member is serialized by the child's own
    machinery, so the parent's recursive converter never touches it.
    """
    cfg = ParentWithChild()
    cfg.parent_note = 'quiet'
    cfg.section.severity = Severity.HIGH
    text = cfg.as_json_string(stderr_file=sys.stderr, member_name=None)
    payload = json.loads(text)
    assert payload == {'label': 'parent',
                       'parent_note': 'QUIET',
                       'section': {'severity': 'HIGH'}}


# ----------------------------------------------------------------------
# Nested Config: parent converter targeting child subtree is rejected
# ----------------------------------------------------------------------


class ParentTargetingChild(ParentWithChild):
    """Parent that wrongly declares a path inside the nested child."""

    @override
    def serialize_converters(self) -> SerializeConverters:
        """Declare a path selector reaching into the nested child."""
        return {('section', 'severity'): SerializeConverter(value_type=str,
                                                            func=_scream,
                                                            args={})}


def test_parent_path_rejected() -> None:
    """A parent path-selector aimed at child data raises at write time."""
    cfg = ParentTargetingChild()
    with pytest.raises(SerializeSelectorError, match='child-owned'):
        _ = cfg.as_json_string(stderr_file=sys.stderr, member_name=None)


# ----------------------------------------------------------------------
# Nested Config: LIST_ELEMENT child ownership
# ----------------------------------------------------------------------


class ReportEntry(Config):
    """List-element child Config with its own enum member."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a report entry with default values."""
        self.kind = 'summary'
        self.priority = Priority.MEDIUM
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Skip validation in this test configuration."""
        _ = stderr_file
        return []

    @override
    def serialize_converters(self) -> SerializeConverters:
        """Convert the report's priority IntEnum to its name."""
        return {'priority': SerializeConverter(value_type=Enum,
                                               func=to_enum_name, args={})}

    @override
    def parse_converters(self) -> Optional[dict[str, ParseConverter]]:
        """Convert the priority name back into the enum member."""
        return {'priority': self.get_converter_dict(Priority)}


class ReportListConfig(Config):
    """Parent Config containing a list of ``ReportEntry`` children."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the parent with one report entry by default."""
        self.title = 'monthly'
        self.reports: list[ReportEntry] = [ReportEntry(
            stderr_file=stderr_file)]
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Declare ``reports`` as a list of nested ReportEntry objects."""
        return {'reports': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                         config_type=ReportEntry)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Skip validation in this test configuration."""
        _ = stderr_file
        return []


def test_list_children_serialize() -> None:
    """Each list-element child applies its own converters independently."""
    cfg = ReportListConfig()
    cfg.reports = [ReportEntry(), ReportEntry()]
    cfg.reports[0].priority = Priority.LOW
    cfg.reports[1].priority = Priority.HIGH
    text = cfg.as_json_string(stderr_file=sys.stderr, member_name=None)
    payload = json.loads(text)
    assert payload == {
        'title': 'monthly',
        'reports': [{'kind': 'summary', 'priority': 'LOW'},
                    {'kind': 'summary', 'priority': 'HIGH'}]}


def test_parent_into_list_rejected() -> None:
    """A parent path selector cannot reach into list-child data."""

    class WrongParent(ReportListConfig):
        """Parent that declares a path inside the LIST_ELEMENT child."""

        @override
        def serialize_converters(self) -> SerializeConverters:
            """Declare a path selector reaching into a list child."""
            return {('reports', '[', 'priority'): SerializeConverter(
                value_type=Enum, func=to_enum_name, args={})}

    cfg = WrongParent()
    with pytest.raises(SerializeSelectorError, match='child-owned'):
        _ = cfg.as_json_string(stderr_file=sys.stderr, member_name=None)
