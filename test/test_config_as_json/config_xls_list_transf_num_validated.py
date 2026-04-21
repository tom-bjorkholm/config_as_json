#! /usr/local/bin/python3
"""Validator-based configuration of CSV splitting by column number."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from config_as_json.validator import Validation, ValidationList
from .config_excel_list_transform import ColInfo, RulePlace, RuleRemove
from .config_xls_list_transf_num import get_column, get_merge_first_column
from .config_excel_list_transform_validated import \
    ConfigExcelListTransformValidated, IncreasingMultiColumnsValidator, \
    NoDuplicateItemsValidator
from .config_enums import ColumnRef, SplitWhere


class ConfigXlsListTransfNumValidated(  # pylint: disable=too-many-instance-attributes, line-too-long, duplicate-code, attribute-defined-outside-init # noqa: E501
        ConfigExcelListTransformValidated[int]):
    """Validator-based configuration for excel list transform."""

    def __init__(self,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for excel list transform."""
        if auto_ch_hook is None:
            auto_ch_hook = MigrateCfgWarnHook()
        self.s04_remove_columns: RuleRemove = [1, 2, 3]
        self.s06_place_columns_first: RulePlace = [7, 3, 6]
        col_to_use = [15, 16, 1, 2, 5, 5, 5, 5, 5, 6]
        col_to_use_row = [7, 1, 2]
        colinfo = ColInfo[int](split_last='store_single',
                               insert_last='name',
                               s03=[{'column': 15, 'separator': ' ',
                                     'where': SplitWhere.RIGHTMOST,
                                     'store_single':
                                     SplitWhere.LEFTMOST}],
                               s08=[{'column': 1, 'name': 'Division',
                                     'value': None},
                                    {'column': 7, 'name': 'Other',
                                     'value': 'some text'}],
                               col_to_use=col_to_use,
                               col_to_use_row=col_to_use_row, tinfo=2)
        super().__init__(col_ref=ColumnRef.BY_NUMBER,
                         colinfo=colinfo, tinfo=2,
                         from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook,
                         stderr_file=stderr_file)

    def sort_sx_hook(self, stderr_file: TextIO = sys.stderr) -> None:
        """Sort s[0-9]_ as needed as needed (hook)."""
        self.s03_split_columns = sorted(self.s03_split_columns, key=get_column)
        self.s04_remove_columns = sorted(self.s04_remove_columns)
        self.s05_merge_columns = sorted(self.s05_merge_columns,
                                        key=get_merge_first_column)
        self.s07_rename_columns = sorted(self.s07_rename_columns,
                                         key=get_column)
        self.s08_insert_columns = sorted(self.s08_insert_columns,
                                         key=get_column)

    def _split_last_key(self) -> str:
        """Return the split-column key name used by this configuration."""
        return 'store_single'

    def _insert_last_key(self) -> Optional[str]:
        """Return the optional insert-column key name for this config."""
        return 'name'

    def get_validation_list(self, stderr_file: TextIO) -> ValidationList:
        """Get validation list for use when validating the Config object."""
        ret = super().get_validation_list(stderr_file=stderr_file)
        ret.extend([
            Validation(member_names=['s04_remove_columns',
                                     's06_place_columns_first'],
                       validator=NoDuplicateItemsValidator()),
            Validation(member_names=['s05_merge_columns'],
                       validator=IncreasingMultiColumnsValidator(
                           self._columntype))])
        return ret
