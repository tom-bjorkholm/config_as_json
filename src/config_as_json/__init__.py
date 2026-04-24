#! /usr/local/bin/python3
"""Define application configuration classes that serialize to JSON.

The package centers on :class:`config_as_json.config.Config`. Applications
derive their own configuration classes, declare supported settings as
instance attributes, and use the library to read, validate, migrate, and
write JSON configuration files.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License


from config_as_json.config import Config, BackwardCompatible, ConfigBadJson, \
    ParseConverter
from config_as_json.commontypes import JsonType, PathOrStr
from config_as_json.config_factory import config_factory_from_json, \
    MatchConfig, MatchConfigSeq, JsonValueMatcher
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from config_as_json.migrate_cfg import migrate_cfg
from config_as_json.validator import ValidationPlan, ValidationStep, \
    WholeConfigValidationStep, MemberValidationStep, WholeConfigValidator, \
    MemberValidator, StrValidator, IntFloatValidator, string_best_match, \
    InvalidConfiguration, InvalidConfigurationValue
from config_as_json.list_validators import ListValueValidator, \
    ListSizeValidator, ListIsOrderedValidator, ListOrderingValidator, \
    ListForEachValidator
from config_as_json.str_to_enum import string_to_enum_best_match
from config_as_json.assert_dict_equal import assert_dict_equal


__all__ = ['Config',
           'BackwardCompatible',
           'ConfigBadJson',
           'JsonType',
           'PathOrStr',
           'ParseConverter',
           'ConfigAutoChangeHook',
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
           'StrValidator',
           'IntFloatValidator',
           'string_best_match',
           'string_to_enum_best_match',
           'InvalidConfiguration',
           'InvalidConfigurationValue',
           'ListValueValidator',
           'ListSizeValidator',
           'ListIsOrderedValidator',
           'ListOrderingValidator',
           'ListForEachValidator',
           'assert_dict_equal']
