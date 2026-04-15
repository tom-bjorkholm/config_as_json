#! /usr/local/bin/python3
"""Validator-based configuration for excel list transform tests."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from copy import deepcopy
from typing import Generic, Optional, TextIO, cast
from config_as_json.config import BackwardCompatible, Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_enums import ColumnRef
from config_as_json.commontypes import JsonType
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from config_as_json.validator import Validation, ValidationList, Validator
from .config_excel_list_transform import ColInfo, Column, Rule, RuleMerge, \
    RuleSplit, \
    ConfigExcelListTransform as LegacyConfigExcelListTransform


class ConfigMethodValidator(Validator):
    """Call one no-argument validation method on the Config object."""

    def __init__(self, method_name: str) -> None:
        """Store the method name to call during validation."""
        self._method_name = method_name

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate by calling the named method on the Config object."""
        _ = stderr_file
        method = getattr(config, self._method_name)
        assert callable(method)
        method()


class CharEncodingValidator(Validator):
    """Validate that one string member names a recognized encoding."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one encoding member and return it unchanged."""
        _ = member_name
        assert isinstance(config, Config)
        assert isinstance(member_value, str)
        config.check_char_encoding(member_value, stderr_file=stderr_file)
        return member_value


class NoDuplicateItemsValidator(Validator):
    """Validate that one list member contains no duplicates."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one list member and return it unchanged."""
        _ = config
        assert isinstance(member_value, list)
        checked_value = cast(list[str] | list[int], member_value)
        Config.check_no_duplicates(checked_value, member_name, stderr_file)
        return member_value


class NoDuplicateSingleColumnsValidator(Validator, Generic[Column]):
    """Validate that one single-column rule list uses each column once."""

    def __init__(self, column_type: type[Column]) -> None:
        """Store the column type used by the rule list."""
        self._column_type: type[Column]
        self._column_type = column_type

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one single-column rule list and return it unchanged."""
        _ = config
        sample = self._column_type()
        checked_value = cast(Rule[Column] | RuleSplit[Column], member_value)
        cols = LegacyConfigExcelListTransform.get_cols_single(
            checked_value, sample)
        Config.check_no_duplicates(cols, member_name, stderr_file)
        return member_value


class IncreasingMultiColumnsValidator(Validator, Generic[Column]):
    """Validate that one merge-column rule list stays in increasing order."""

    def __init__(self, column_type: type[Column]) -> None:
        """Store the column type used by the merge rules."""
        self._column_type: type[Column]
        self._column_type = column_type

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one merge-column rule list and return it unchanged."""
        _ = config
        sample = self._column_type()
        checked_value = cast(RuleMerge[Column], member_value)
        cols = LegacyConfigExcelListTransform.get_cols_multi(
            checked_value, sample)
        seen: Optional[Column] = None
        for col in cols:
            if seen is not None and seen >= col:
                msg = f'Increasing order needed in {member_name}'
                print(msg, file=stderr_file)
                raise KeyError(msg)
            seen = col
        return member_value


# pylint: disable=too-many-arguments,too-many-positional-arguments
def copy_common_state_from_legacy(config: Config, col_ref: ColumnRef,
                                  colinfo: ColInfo[Column], tinfo: Column,
                                  auto_ch_hook: ConfigAutoChangeHook,
                                  stderr_file: TextIO) -> None:
    """Copy the common default state from the legacy helper config."""
    template = LegacyConfigExcelListTransform(
        col_ref=col_ref, colinfo=deepcopy(colinfo), tinfo=tinfo,
        from_json_data_text=None, from_json_filename=None,
        auto_ch_hook=auto_ch_hook, stderr_file=stderr_file)
    for name, value in vars(template).items():
        if not name.startswith('_') or name == '_columntype':
            setattr(config, name, deepcopy(value))
# pylint: enable=too-many-arguments,too-many-positional-arguments


class ConfigExcelListTransformValidated(Config, Generic[Column]):  # pylint: disable=too-many-instance-attributes, line-too-long, duplicate-code # noqa: E501
    """Validator-based test configuration for excel list transform."""

    _columntype: type[Column]
    s03_split_columns: RuleSplit[Column]
    s05_merge_columns: RuleMerge[Column]
    s07_rename_columns: Rule[Column]
    s08_insert_columns: Rule[Column]

    def __init__(self, *, col_ref: ColumnRef,  # pylint: disable=too-many-arguments # noqa: E501
                 colinfo: ColInfo[Column], tinfo: Column,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: Optional[TextIO] = None) -> None:
        """Construct configuration for excel list transform."""
        if stderr_file is None:
            stderr_file = sys.stderr
        if auto_ch_hook is None:
            auto_ch_hook = MigrateCfgWarnHook(stderr_file=stderr_file)
        copy_common_state_from_legacy(self, col_ref, colinfo, tinfo,
                                      auto_ch_hook, stderr_file)
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook,
                         stderr_file=stderr_file)

    def sort_sx_hook(self) -> None:
        """Sort s[0-9]_ as needed (hook)."""

    def _split_last_key(self) -> str:
        """Return the split-column key name used by this configuration."""
        msg = '_split_last_key() must be implemented in a derived class.'
        raise NotImplementedError(msg)

    def _insert_last_key(self) -> Optional[str]:
        """Return the optional insert-column key name for this config."""
        msg = '_insert_last_key() must be implemented in a derived class.'
        raise NotImplementedError(msg)

    def _validate_array_configs(self) -> None:
        """Validate the keyword sets used by the configuration arrays."""
        legacy_self = cast(LegacyConfigExcelListTransform[Column], self)
        LegacyConfigExcelListTransform.check_array_configs(
            legacy_self, split_last=self._split_last_key(),
            insert_last=self._insert_last_key())

    def _validate_rewrite_configs(self) -> None:
        """Validate the rewrite-column configuration."""
        legacy_self = cast(LegacyConfigExcelListTransform[Column], self)
        LegacyConfigExcelListTransform.check_rewrite_configs(
            legacy_self, coltype=self._columntype)

    def _validate_split_row_cfg(self) -> None:
        """Validate the split-row configuration."""
        legacy_self = cast(LegacyConfigExcelListTransform[Column], self)
        LegacyConfigExcelListTransform.check_split_row_cfg(legacy_self)

    def _validate_merge_row_cfg(self) -> None:
        """Validate the merge-row configuration."""
        legacy_self = cast(LegacyConfigExcelListTransform[Column], self)
        LegacyConfigExcelListTransform.check_merge_row_cfg(legacy_self)

    def get_validation_list(self) -> ValidationList:
        """Get validation list for use when validating the Config object."""
        return [
            Validation(member_names=None,
                       validator=ConfigMethodValidator('sort_sx_hook')),
            Validation(member_names=None,
                       validator=ConfigMethodValidator(
                           '_validate_array_configs')),
            Validation(member_names=['in_csv_encoding', 'out_csv_encoding'],
                       validator=CharEncodingValidator()),
            Validation(member_names=['s03_split_columns',
                                     's07_rename_columns',
                                     's08_insert_columns'],
                       validator=NoDuplicateSingleColumnsValidator(
                           self._columntype)),
            Validation(member_names=None,
                       validator=ConfigMethodValidator(
                           '_validate_rewrite_configs')),
            Validation(member_names=None,
                       validator=ConfigMethodValidator(
                           '_validate_split_row_cfg')),
            Validation(member_names=None,
                       validator=ConfigMethodValidator(
                           '_validate_merge_row_cfg'))]

    get_out_csv_dialect = LegacyConfigExcelListTransform.get_out_csv_dialect
    get_in_csv_dialect = LegacyConfigExcelListTransform.get_in_csv_dialect
    check_sep_not_sep = staticmethod(
        LegacyConfigExcelListTransform.check_sep_not_sep)
    get_converter_dict = staticmethod(
        LegacyConfigExcelListTransform.get_converter_dict)
    parse_converters = LegacyConfigExcelListTransform.parse_converters

    def _def_vals_for_optional(self) -> dict[str, JsonType]:
        """Provide default values for optional encoding."""
        legacy_self = cast(LegacyConfigExcelListTransform[Column], self)
        # pylint: disable=protected-access
        return LegacyConfigExcelListTransform._def_vals_for_optional(
            legacy_self)

    def _backward_compatible(self) -> list[BackwardCompatible]:
        """Get names of backward compatible config parameters."""
        legacy_self = cast(LegacyConfigExcelListTransform[Column], self)
        # pylint: disable=protected-access
        return LegacyConfigExcelListTransform._backward_compatible(
            legacy_self)
