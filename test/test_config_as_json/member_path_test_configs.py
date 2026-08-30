#! /usr/local/bin/python3
"""Nested Config classes for testing reported member paths.

The classes nest one ``Leaf`` in every ``ConfigNestingKind``, so that one
reported path exists per kind, and they nest two levels deep so that a
reported path has more than one dot.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO, override
from config_as_json.config import Config
from config_as_json.commontypes import PathOrStr
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.dict_validators import DictForEachValidator, DictRule
from config_as_json.list_element_validators import ListForEachValidator
from config_as_json.list_relation_validator import ListRelationKind, \
    ListRelationValidator
from config_as_json.member_path import member_path
from config_as_json.projected_validators import ProjectedWholeConfigValidator
from config_as_json.read_old_configuration import ReadOldConfiguration, \
    RocfKeyRename
from config_as_json.str_validators import StrValidator
from config_as_json.validator import CallingWholeConfigValidator, \
    InvalidConfiguration, IntFloatValidator, MemberValidationStep, \
    ValidationPlan, WholeConfigValidationStep, WholeConfigValidator

ALLOWED_KINDS = ['csv', 'json', 'legacy']
"""Values that the ``kind`` member of a ``Leaf`` accepts."""

ALLOWED_TAGS = ['plain', 'wide', 'bad']
"""Values that an element of the ``tags`` member of a ``Leaf`` accepts."""


# pylint: disable-next=too-few-public-methods
class LeafWholeCheck(WholeConfigValidator):
    """Warn about a legacy kind, and reject a leaf holding a bad tag.

    The warning is printed without raising, which is the diagnostic that
    only a path travelling down the traversal can name.
    """

    def validate(self, config: Config, stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str]) -> None:
        """Warn about a legacy kind and reject a bad tag."""
        assert isinstance(config, Leaf)
        if config.kind == 'legacy':
            told = member_path(member_name, 'kind')
            print(f'Warning: {told} still uses a legacy format',
                  file=stderr_file)
        if 'bad' in config.tags:
            msg = 'Invalid configuration: '
            msg += f'{member_path(member_name, "tags")} holds a bad tag.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)


# pylint: disable-next=too-few-public-methods
class LeafReadOldConfig(ReadOldConfiguration):
    """Describe how an older leaf configuration file is normalized."""

    @override
    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return the old key name mapped to the current key name."""
        return [RocfKeyRename(old='old_kind', new='kind')]


class Leaf(Config):
    """Innermost nested configuration holding one validated value each."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one leaf configuration with its default values."""
        self.kind = 'csv'
        self.tags: list[str] = ['plain']
        self.limits: dict[str, int] = {'cpu': 1}
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the rules that read an older leaf configuration file."""
        return LeafReadOldConfig()

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return one member validator per member and one whole check."""
        _ = stderr_file
        kind_step = MemberValidationStep(
            member_names=['kind'],
            validator=StrValidator(ALLOWED_KINDS, ignore_case=False))
        tags_step = MemberValidationStep(
            member_names=['tags'],
            validator=ListForEachValidator(element_validators=[
                StrValidator(ALLOWED_TAGS, ignore_case=False)]))
        limits_step = MemberValidationStep(
            member_names=['limits'],
            validator=DictForEachValidator(rules=[
                DictRule(keys=['cpu'],
                         validators=[IntFloatValidator(1, 9, None)])]))
        return [kind_step, tags_step, limits_step,
                WholeConfigValidationStep(validator=LeafWholeCheck())]


class Middle(Config):
    """Configuration nesting one ``Leaf`` in every nesting kind."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one middle configuration with its default values."""
        self.leaf = Leaf(stderr_file=stderr_file)
        self.spare: Optional[Leaf] = None
        self.leaves: list[Leaf] = [Leaf(stderr_file=stderr_file)]
        self.by_name: dict[str, Leaf] = {'main': Leaf(stderr_file=stderr_file)}
        self.mixed: dict[str, object] = {'picked': Leaf(
            stderr_file=stderr_file), 'plain_value': 3}
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return one nested Config declaration per nesting kind."""
        return {
            'leaf': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                  config_type=Leaf),
            'spare': ConfigNesting(kind=ConfigNestingKind.OPTIONAL_MEMBER,
                                   config_type=Leaf),
            'leaves': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                    config_type=Leaf),
            'by_name': ConfigNesting(kind=ConfigNestingKind.DICT_VALUE,
                                     config_type=Leaf),
            'mixed': [ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                                    config_type=Leaf,
                                    discriminator_key='picked')]
        }

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return the optional member omitted while its value is None."""
        return ['spare']

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own, only the nested validations."""
        _ = stderr_file
        return []


class Top(Config):
    """Configuration holding one ``Middle``, so paths have two dots."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one top configuration with its default values."""
        self.section = Middle(stderr_file=stderr_file)
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration."""
        return {'section': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                         config_type=Middle)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own, only the nested validations."""
        _ = stderr_file
        return []


class DottedKeys(Config):
    """Configuration whose dict keys hold a dot, making paths ambiguous."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one configuration keyed by names holding a dot."""
        self.by_name: dict[str, Leaf] = {
            'a.b': Leaf(stderr_file=stderr_file)}
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration."""
        return {'by_name': ConfigNesting(kind=ConfigNestingKind.DICT_VALUE,
                                         config_type=Leaf)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own, only the nested validations."""
        _ = stderr_file
        return []


def total_size(config: Config, stderr_file: TextIO) -> object:
    """Return the sum of the configured sizes of one ``BuiltIn``."""
    _ = stderr_file
    assert isinstance(config, BuiltIn)
    return sum(config.sizes)


class BuiltIn(Config):
    """Nested configuration checked by the built-in whole-config validators."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one configuration with its default values."""
        self.sizes: list[int] = [1]
        self.pool: list[int] = [1, 3]
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def check_pool(self) -> bool:
        """Return whether the pool of allowed sizes has any value at all."""
        return len(self.pool) > 0

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return one step per built-in whole-config validator."""
        _ = stderr_file
        projected = ProjectedWholeConfigValidator(
            projector=total_size, pseudo_member_name='total_size',
            validators=[IntFloatValidator(0, 5, None)])
        relation = ListRelationValidator(ListRelationKind.SUBSET, 'sizes',
                                         'pool')
        calling = CallingWholeConfigValidator(method_name='check_pool')
        return [WholeConfigValidationStep(validator=projected),
                WholeConfigValidationStep(validator=relation),
                WholeConfigValidationStep(validator=calling)]


class BuiltInTop(Config):
    """Configuration holding one ``BuiltIn`` as a nested member."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct one configuration holding one ``BuiltIn``."""
        self.built_in = BuiltIn(stderr_file=stderr_file)
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration."""
        return {'built_in': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                          config_type=BuiltIn)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation of its own, only the nested validations."""
        _ = stderr_file
        return []
