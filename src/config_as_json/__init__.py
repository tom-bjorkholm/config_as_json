#! /usr/local/bin/python3
"""Define application configuration classes that serialize to JSON.

The package centers on :class:`config_as_json.config.Config`. Applications
derive their own configuration classes, declare supported settings as
instance attributes, and use the library to read, validate, migrate, and
write JSON configuration files.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License


from config_as_json.config import Config, RocfKeyRename, ConfigBadJson, \
    ParseConverter
from config_as_json.commontypes import JsonType, PathOrStr
from config_as_json.config_factory import config_factory_from_json, \
    MatchConfig, MatchConfigSeq, JsonValueMatcher
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.csv_dialect import CsvDialectConfig, \
    CsvDialectValidator, get_csv_dialect
from config_as_json.char_encoding import check_char_encoding, \
    CharEncodingValidator, valid_char_encoding
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from config_as_json.migrate_cfg import migrate_cfg
from config_as_json.optional_validator import OptionalMemberValidator
from config_as_json.validator import ValidationPlan, ValidationStep, \
    WholeConfigValidationStep, MemberValidationStep, WholeConfigValidator, \
    MemberValidator, ValueTypeValidator, StrValidator, IntFloatValidator, \
    CallingMemberValidator, CallingWholeConfigValidator, \
    MemberValidatorSequence, string_best_match, InvalidConfiguration, \
    InvalidConfigurationValue
from config_as_json.list_validators import ListValueValidator, \
    ListSizeValidator, ListIsOrderedValidator, ListOrderingValidator, \
    ListValueTypeValidator, ListForEachValidator, ListOfDictsKeysValidator
from config_as_json.dict_validators import DictKeysValidator, DictRule, \
    DictForEachValidator, accept_all_keys
from config_as_json.discriminated_dict_validators import DictVariant, \
    DiscriminatedDictValidator
from config_as_json.projected_validators import ProjectedMemberValidator
from config_as_json.as_dict_view_validator import AsDictViewValidator, \
    public_attrs_to_dict
from config_as_json.str_to_enum import string_to_enum_best_match
from config_as_json.assert_dict_equal import assert_dict_equal


__all__ = ['Config',
           'RocfKeyRename',
           'ConfigBadJson',
           'JsonType',
           'PathOrStr',
           'ParseConverter',
           'ConfigAutoChangeHook',
           'CsvDialectConfig',
           'CsvDialectValidator',
           'get_csv_dialect',
           'check_char_encoding',
           'CharEncodingValidator',
           'valid_char_encoding',
           'MigrateCfgWarnHook',
           'migrate_cfg',
           'config_factory_from_json',
           'MatchConfig',
           'MatchConfigSeq',
           'JsonValueMatcher',
           'ValidationPlan',
           'ValidationStep',
           'WholeConfigValidationStep',
           'MemberValidationStep',
           'WholeConfigValidator',
           'MemberValidator',
           'ValueTypeValidator',
           'StrValidator',
           'IntFloatValidator',
           'CallingMemberValidator',
           'CallingWholeConfigValidator',
           'MemberValidatorSequence',
           'OptionalMemberValidator',
           'string_best_match',
           'string_to_enum_best_match',
           'InvalidConfiguration',
           'InvalidConfigurationValue',
           'ListValueValidator',
           'ListSizeValidator',
           'ListIsOrderedValidator',
           'ListOrderingValidator',
           'ListValueTypeValidator',
           'ListForEachValidator',
           'ListOfDictsKeysValidator',
           'DictKeysValidator',
           'DictRule',
           'DictForEachValidator',
           'accept_all_keys',
           'DictVariant',
           'DiscriminatedDictValidator',
           'ProjectedMemberValidator',
           'AsDictViewValidator',
           'public_attrs_to_dict',
           'assert_dict_equal']
