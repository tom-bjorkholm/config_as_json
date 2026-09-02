#! /usr/local/bin/python3
"""A deep nested configuration recording every path handed to it.

Every level of the tree nests one child in each of the five
``ConfigNestingKind`` values, so the tree holds every nesting kind inside
every other nesting kind. Each object records the path it was given itself,
and the path its own plain member was given, through validators that accept
every value and only record.

A Config constructor has to build its declared defaults before it parses
anything, and those placeholder objects validate themselves while they are
built. They are built with :data:`DEFAULTS` as their path, and the recorder
drops what they record, so that a test sees only the traversal it started.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from typing import Optional, TextIO, override
from config_as_json.commontypes import PathOrStr
from config_as_json.config import Config
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.validator import MemberValidationStep, MemberValidator, \
    ValidationPlan, WholeConfigValidationStep, WholeConfigValidator

DEFAULTS = '#defaults'
"""Path given to the placeholder objects that a constructor builds."""


def _is_placeholder(path: Optional[str]) -> bool:
    """Return whether a path is inside a placeholder default object."""
    return path is not None and path.startswith(DEFAULTS)


class PathRecorder:
    """Collect the paths that one traversal hands out.

    ``configs`` holds one entry per validated Config object, which is
    ``None`` for the object the traversal was started on. ``members`` holds
    one entry per validated plain member.
    """

    def __init__(self) -> None:
        """Start with nothing recorded."""
        self.configs: list[Optional[str]] = []
        self.members: list[str] = []

    def clear(self) -> None:
        """Forget everything recorded so far."""
        self.configs.clear()
        self.members.clear()

    def add_config(self, path: Optional[str]) -> None:
        """Record the path of one validated Config object."""
        if not _is_placeholder(path):
            self.configs.append(path)

    def add_member(self, path: str) -> None:
        """Record the path of one validated plain member."""
        if not _is_placeholder(path):
            self.members.append(path)


RECORDER = PathRecorder()
"""The recorder that the whole tree reports to."""


# pylint: disable-next=too-few-public-methods
class RecordMember(MemberValidator):
    """Record the path of one member, and accept every value."""

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Record the path and return the value unchanged."""
        _ = config, stderr_file
        RECORDER.add_member(member_name)
        return member_value


# pylint: disable-next=too-few-public-methods
class RecordWhole(WholeConfigValidator):
    """Record the path of one Config object, and accept it."""

    def validate(self, config: Config, stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Record the path of the Config object being validated."""
        _ = config, stderr_file
        RECORDER.add_config(member_name)


def _recording_plan(member: str) -> ValidationPlan:
    """Return the recording steps for one member and for the object."""
    return [MemberValidationStep(member_names=[member],
                                 validator=RecordMember()),
            WholeConfigValidationStep(validator=RecordWhole())]


class RecLeaf(Config):
    """Innermost recording configuration, holding one plain member."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one leaf with its default value."""
        self.value = 'leaf'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the recording steps of this leaf."""
        _ = stderr_file
        return _recording_plan('value')


class RecNest(Config):
    """Recording configuration nesting one child in every nesting kind.

    The class of the children is ``_child_type``, which every derived class
    sets. That is what makes one class describe every level of the tree.
    """

    _child_type: type[Config]

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one level holding one placeholder child per kind."""
        self.name = 'plain'
        self.leaf: Config = self._new_child(stderr_file)
        self.spare: Optional[Config] = self._new_child(stderr_file)
        self.leaves: list[Config] = [self._new_child(stderr_file)]
        self.by_name: dict[str, Config] = {'main':
                                           self._new_child(stderr_file)}
        self.mixed: dict[str, object] = {
            'picked': self._new_child(stderr_file), 'plain_value': 3}
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @classmethod
    def _new_child(cls, stderr_file: TextIO) -> Config:
        """Return one placeholder child that a parse replaces."""
        return cls._child_type(from_json_data_text=None,
                               from_json_filename=None,
                               stderr_file=stderr_file, member_name=DEFAULTS)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return one nested Config declaration per nesting kind."""
        child = self._child_type
        by_key = ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                               config_type=child, discriminator_key='picked')
        return {'leaf': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                      config_type=child),
                'spare': ConfigNesting(kind=ConfigNestingKind.OPTIONAL_MEMBER,
                                       config_type=child),
                'leaves': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                        config_type=child),
                'by_name': ConfigNesting(kind=ConfigNestingKind.DICT_VALUE,
                                         config_type=child),
                'mixed': [by_key]}

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return the optional member that is left out while it is None."""
        return ['spare']

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the recording steps of this level."""
        _ = stderr_file
        return _recording_plan('name')


class RecBranch(RecNest):
    """Middle level of the recording tree, nesting recording leaves."""

    _child_type = RecLeaf


class RecTop(RecNest):
    """Top level of the recording tree, nesting recording branches."""

    _child_type = RecBranch


CONFIG_PATHS: list[Optional[str]] = [
    None,
    'leaf', 'leaf.leaf', 'leaf.spare', 'leaf.leaves[0]',
    'leaf.by_name[main]', 'leaf.mixed[picked]',
    'spare', 'spare.leaf', 'spare.spare', 'spare.leaves[0]',
    'spare.by_name[main]', 'spare.mixed[picked]',
    'leaves[0]', 'leaves[0].leaf', 'leaves[0].spare', 'leaves[0].leaves[0]',
    'leaves[0].by_name[main]', 'leaves[0].mixed[picked]',
    'by_name[main]', 'by_name[main].leaf', 'by_name[main].spare',
    'by_name[main].leaves[0]', 'by_name[main].by_name[main]',
    'by_name[main].mixed[picked]',
    'mixed[picked]', 'mixed[picked].leaf', 'mixed[picked].spare',
    'mixed[picked].leaves[0]', 'mixed[picked].by_name[main]',
    'mixed[picked].mixed[picked]']
"""The path of every Config object in the tree, top level first."""

MEMBER_PATHS: list[str] = [
    'name',
    'leaf.name', 'leaf.leaf.value', 'leaf.spare.value',
    'leaf.leaves[0].value', 'leaf.by_name[main].value',
    'leaf.mixed[picked].value',
    'spare.name', 'spare.leaf.value', 'spare.spare.value',
    'spare.leaves[0].value', 'spare.by_name[main].value',
    'spare.mixed[picked].value',
    'leaves[0].name', 'leaves[0].leaf.value', 'leaves[0].spare.value',
    'leaves[0].leaves[0].value', 'leaves[0].by_name[main].value',
    'leaves[0].mixed[picked].value',
    'by_name[main].name', 'by_name[main].leaf.value',
    'by_name[main].spare.value', 'by_name[main].leaves[0].value',
    'by_name[main].by_name[main].value', 'by_name[main].mixed[picked].value',
    'mixed[picked].name', 'mixed[picked].leaf.value',
    'mixed[picked].spare.value', 'mixed[picked].leaves[0].value',
    'mixed[picked].by_name[main].value', 'mixed[picked].mixed[picked].value']
"""The path of every plain member in the tree, top level first."""


def leaf_data() -> dict[str, object]:
    """Return the JSON data of one recording leaf."""
    return {'value': 'leaf'}


def nest_data(child: dict[str, object]) -> dict[str, object]:
    """Return the JSON data of one level nesting the given child data."""
    return {'name': 'plain', 'leaf': child, 'spare': child,
            'leaves': [child], 'by_name': {'main': child},
            'mixed': {'picked': child, 'plain_value': 3}}


def tree_text() -> str:
    """Return the JSON text of the whole recording tree."""
    return json.dumps(nest_data(nest_data(leaf_data())))
