#! /usr/local/bin/python3
"""Validator-based configuration of CSV splitting by column name."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.list_validators import ListIsOrderedValidator
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from config_as_json.validator import ValidationPlan, MemberValidationStep
from .config_excel_list_transform_validated import \
    ConfigExcelTransformValidated
from .config_enums import ColumnRef
from .config_xls_list_transf_name import NAME_COLUMN_ORDER, make_name_colinfo


# pylint: disable-next=R0902,C0301,R0801
class ConfigXlsListTransfNameValidated(ConfigExcelTransformValidated[str]):
    """Validator-based configuration for excel list transform."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for excel list transform."""
        if auto_ch_hook is None:
            auto_ch_hook = MigrateCfgWarnHook()
        self.s10_column_order: list[str] = list(NAME_COLUMN_ORDER)
        super().__init__(col_ref=ColumnRef.BY_NAME,
                         colinfo=make_name_colinfo(), tinfo='a',
                         from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file)

    def _split_last_key(self) -> str:
        """Return the split-column key name used by this configuration."""
        return 'right_name'

    def _insert_last_key(self) -> Optional[str]:
        """Return the optional insert-column key name for this config."""
        return None

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        ret = super().get_validation_plan(stderr_file=stderr_file)
        ret.append(MemberValidationStep(member_names=['s10_column_order'],
                                        validator=ListIsOrderedValidator(
                str, is_ordered=False, unique_values=True)))
        return ret
