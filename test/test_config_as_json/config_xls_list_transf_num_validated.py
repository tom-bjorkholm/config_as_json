#! /usr/local/bin/python3
"""Validator-based configuration of CSV splitting by column number."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO, cast
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.list_validators import ListIsOrderedValidator
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from config_as_json.validator import ValidationPlan, MemberValidationStep
from .config_xls_list_transf_num import NumTransformRules, make_num_colinfo, \
    set_num_base_rules, sort_num_rules
from .config_excel_list_transform_validated import \
    ConfigExcelTransformValidated, increasing_merge_columns_validator
from .config_enums import ColumnRef


# pylint: disable-next=R0902,C0301,R0801,W0201
class ConfigXlsListTransfNumValidated(ConfigExcelTransformValidated[int]):
    """Validator-based configuration for excel list transform."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct validated configuration for excel list transform."""
        if auto_ch_hook is None:
            auto_ch_hook = MigrateCfgWarnHook()
        set_num_base_rules(cast(NumTransformRules, self))
        super().__init__(col_ref=ColumnRef.BY_NUMBER,
                         colinfo=make_num_colinfo(), tinfo=2,
                         from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file)

    def sort_sx_hook(self, stderr_file: TextIO = sys.stderr) -> None:
        """Sort s[0-9]_ as needed as needed (hook)."""
        _ = stderr_file
        sort_num_rules(cast(NumTransformRules, self))

    def _split_last_key(self) -> str:
        """Return the split-column key name used by this configuration."""
        return 'store_single'

    def _insert_last_key(self) -> Optional[str]:
        """Return the optional insert-column key name for this config."""
        return 'name'

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        ret = super().get_validation_plan(stderr_file=stderr_file)
        ret.extend([
            MemberValidationStep(
                member_names=['s04_remove_columns',
                              's06_place_columns_first'],
                validator=ListIsOrderedValidator(
                    int, is_ordered=False, unique_values=True)),
            MemberValidationStep(member_names=['s05_merge_columns'],
                                 validator=increasing_merge_columns_validator(
                    self._columntype))])
        return ret
