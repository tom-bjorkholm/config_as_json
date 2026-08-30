#! /usr/local/bin/python3
"""Validator-based configuration for excel list transform tests."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from collections.abc import Callable
from copy import deepcopy
from typing import Generic, Optional, TextIO, cast
from config_as_json import ReadOldConfiguration
from config_as_json.char_encoding import CharEncodingValidator
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.csv_dialect import CsvDialectValidator
from config_as_json.list_element_validators import ListOfDictsKeysValidator
from config_as_json.list_ordering_validators import ListIsOrderedValidator
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from config_as_json.projected_validators import ProjectedMemberValidator
from config_as_json.validator import ValidationPlan, \
    WholeConfigValidationStep, MemberValidationStep, \
    WholeConfigValidator
from .config_excel_list_transform import ColInfo, Column, Rule, RuleMerge, \
    RuleSplit, \
    ConfigExcelListTransform as LegacyConfigExcelListTransform
from .config_enums import ColumnRef


# pylint: disable-next=too-few-public-methods
class ConfigMethodValidator(WholeConfigValidator):
    """Call one validation method on the Config object."""

    def __init__(self, method_name: str) -> None:
        """Store the method name to call during validation."""
        self._method_name = method_name

    def validate(self, config: Config, stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str]) -> None:
        """Validate by calling the named method on the Config object.

        Args:
            config: Config object whose method should be called.
            stderr_file: Stream passed through to the named method.
            member_name: Path for reaching ``config`` from the top level of
                the validation, or ``None`` when it is the top level.
        """
        _ = member_name
        method = getattr(config, self._method_name)
        assert callable(method)
        method(stderr_file=stderr_file)


def single_rule_columns_projector(column_type: type[Column]) -> Callable[
        [Config, str, object, TextIO], object]:
    """Build a projector from single-column rules to column values."""
    def project_single_rule_columns(config: Config, member_name: str,
                                    member_value: object,
                                    stderr_file: TextIO) -> object:
        """Project one single-column rule list to its column values."""
        _ = config, member_name, stderr_file
        sample = column_type()
        checked_value = cast(Rule[Column] | RuleSplit[Column], member_value)
        return LegacyConfigExcelListTransform.get_cols_single(checked_value,
                                                              sample)

    return project_single_rule_columns


def merge_rule_columns_projector(column_type: type[Column]) -> Callable[
        [Config, str, object, TextIO], object]:
    """Build a projector from merge rules to flattened column values."""
    def project_merge_rule_columns(config: Config, member_name: str,
                                   member_value: object,
                                   stderr_file: TextIO) -> object:
        """Project one merge rule list to its flattened column values."""
        _ = config, member_name, stderr_file
        sample = column_type()
        checked_value = cast(RuleMerge[Column], member_value)
        return LegacyConfigExcelListTransform.get_cols_multi(checked_value,
                                                             sample)

    return project_merge_rule_columns


def unique_single_columns_validator(
        column_type: type[Column]) -> ProjectedMemberValidator:
    """Build a validator for unique columns in single-column rules."""
    return ProjectedMemberValidator(
        projector=single_rule_columns_projector(column_type),
        validators=[
            ListIsOrderedValidator(element_type=column_type, is_ordered=False,
                                   unique_values=True)])


def increasing_merge_columns_validator(
        column_type: type[Column]) -> ProjectedMemberValidator:
    """Build a validator for increasing columns in merge-column rules."""
    return ProjectedMemberValidator(
        projector=merge_rule_columns_projector(column_type),
        validators=[
            ListIsOrderedValidator(element_type=column_type,
                                   unique_values=True)])


# pylint: disable=too-many-arguments,too-many-positional-arguments
def copy_common_state_from_legacy(config: Config, col_ref: ColumnRef,
                                  colinfo: ColInfo[Column], tinfo: Column,
                                  auto_ch_hook: ConfigAutoChangeHook,
                                  stderr_file: TextIO) -> None:
    """Copy the common default state from the legacy helper config."""
    template = LegacyConfigExcelListTransform(col_ref=col_ref,
                                              colinfo=deepcopy(colinfo),
                                              tinfo=tinfo,
                                              from_json_data_text=None,
                                              from_json_filename=None,
                                              auto_ch_hook=auto_ch_hook,
                                              stderr_file=stderr_file)
    for name, value in vars(template).items():
        if not name.startswith('_') or name == '_columntype':
            setattr(config, name, deepcopy(value))


# pylint: enable=too-many-arguments,too-many-positional-arguments


# pylint: disable-next=R0902,C0301,R0801
class ConfigExcelTransformValidated(Config, Generic[Column]):
    """Validator-based test configuration for excel list transform."""

    _columntype: type[Column]
    s03_split_columns: RuleSplit[Column]
    s05_merge_columns: RuleMerge[Column]
    s07_rename_columns: Rule[Column]
    s08_insert_columns: Rule[Column]

    # pylint: disable-next=too-many-arguments
    def __init__(self, *, col_ref: ColumnRef, colinfo: ColInfo[Column],
                 tinfo: Column, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for excel list transform."""
        if auto_ch_hook is None:
            auto_ch_hook = MigrateCfgWarnHook()
        copy_common_state_from_legacy(self, col_ref, colinfo, tinfo,
                                      auto_ch_hook, stderr_file)
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file)

    def sort_sx_hook(self, stderr_file: TextIO) -> None:
        """Sort s[0-9]_ as needed (hook)."""

    def _split_last_key(self) -> str:
        """Return the split-column key name used by this configuration."""
        msg = '_split_last_key() must be implemented in a derived class.'
        raise NotImplementedError(msg)

    def _insert_last_key(self) -> Optional[str]:
        """Return the optional insert-column key name for this config."""
        insert_last_key: Optional[str] = None
        return insert_last_key

    def _validate_rewrite_configs(self, stderr_file: TextIO) -> None:
        """Validate the rewrite-column configuration.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        legacy_self = cast(LegacyConfigExcelListTransform[Column], self)
        LegacyConfigExcelListTransform.check_rewrite_configs(
            legacy_self, coltype=self._columntype, stderr_file=stderr_file)

    def _validate_split_row_cfg(self, stderr_file: TextIO) -> None:
        """Validate the split-row configuration.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        legacy_self = cast(LegacyConfigExcelListTransform[Column], self)
        LegacyConfigExcelListTransform.check_split_row_cfg(
            legacy_self, stderr_file=stderr_file)

    def _validate_merge_row_cfg(self, stderr_file: TextIO) -> None:
        """Validate the merge-row configuration.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        legacy_self = cast(LegacyConfigExcelListTransform[Column], self)
        LegacyConfigExcelListTransform.check_merge_row_cfg(
            legacy_self, stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        insert_last = self._insert_last_key()
        insert_allowed_keys = None if insert_last is None else [insert_last]
        return [
            WholeConfigValidationStep(
                validator=ConfigMethodValidator('sort_sx_hook')),
            MemberValidationStep(member_names=['s03_split_columns'],
                                 validator=ListOfDictsKeysValidator([
                                     'column', 'separator', 'where',
                                     self._split_last_key()
                                 ])),
            MemberValidationStep(
                member_names=['s05_merge_columns'],
                validator=ListOfDictsKeysValidator(['columns', 'separator'])),
            MemberValidationStep(member_names=['s07_rename_columns'],
                                 validator=ListOfDictsKeysValidator(
                                     ['column', 'name'])),
            MemberValidationStep(
                member_names=['s08_insert_columns'],
                validator=ListOfDictsKeysValidator(['column', 'value'],
                                                   insert_allowed_keys)),
            MemberValidationStep(
                member_names=['in_csv_encoding', 'out_csv_encoding'],
                validator=CharEncodingValidator()),
            MemberValidationStep(
                member_names=['in_csv_dialect', 'out_csv_dialect'],
                validator=CsvDialectValidator()),
            MemberValidationStep(
                member_names=[
                    's03_split_columns', 's07_rename_columns',
                    's08_insert_columns'
                ],
                validator=unique_single_columns_validator(self._columntype)),
            WholeConfigValidationStep(
                validator=ConfigMethodValidator('_validate_rewrite_configs')),
            WholeConfigValidationStep(
                validator=ConfigMethodValidator('_validate_split_row_cfg')),
            WholeConfigValidationStep(
                validator=ConfigMethodValidator('_validate_merge_row_cfg'))
        ]

    get_out_csv_dialect = LegacyConfigExcelListTransform.get_out_csv_dialect
    get_in_csv_dialect = LegacyConfigExcelListTransform.get_in_csv_dialect
    check_sep_not_sep = staticmethod(
        LegacyConfigExcelListTransform.check_sep_not_sep)
    get_converter_dict = staticmethod(
        LegacyConfigExcelListTransform.get_converter_dict)
    parse_converters = LegacyConfigExcelListTransform.parse_converters

    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the object that normalizes old test config files."""
        legacy_self = cast(LegacyConfigExcelListTransform[Column], self)
        # pylint: disable=protected-access
        return LegacyConfigExcelListTransform._get_read_old_config(legacy_self)
