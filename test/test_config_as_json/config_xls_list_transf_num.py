#! /usr/local/bin/python3
"""Read and write configuration of CSV splitting."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License


import sys
from typing import Optional, TextIO
from config_as_json.config_enums import SplitWhere, ColumnRef
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from .config_excel_list_transform import \
    ConfigExcelListTransform, RulePlace, RuleRemove, \
    SingleRuleMerge, SingleRuleSplit, SingleRule, ColInfo


def get_column(rule:  SingleRuleSplit[int] | SingleRule[int]) -> int:
    """Get column of rule."""
    ret = rule['column']
    assert isinstance(ret, int)
    return ret


def get_merge_first_column(rule: SingleRuleMerge[int]) -> int:
    """Get column of rule."""
    cols = rule['columns']
    ret = cols[0]
    assert isinstance(ret, int)
    return ret


class ConfigXlsListTransfNum(ConfigExcelListTransform[int]):  # pylint: disable=too-many-instance-attributes, line-too-long # noqa: E501
    """Class with configuration for excel list transform."""

    def __init__(self,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: Optional[TextIO] = None) -> None:
        """Construct configuration for excel list transform."""
        if stderr_file is None:
            stderr_file = sys.stderr
        if auto_ch_hook is None:
            auto_ch_hook = MigrateCfgWarnHook(stderr_file=stderr_file)
        self.s04_remove_columns: RuleRemove = [1, 2, 3]
        self.s06_place_columns_first: RulePlace = [7, 3, 6]
        col_to_use = [15, 16, 1, 2, 5, 5, 5, 5, 5, 6]
        col_to_use_row = [7, 1, 2]
        colinfo: ColInfo[int] = \
            ColInfo[int](split_last='store_single', insert_last='name',
                         s03=[{'column': 15, 'separator': ' ',
                               'where': SplitWhere.RIGHTMOST,
                               'store_single': SplitWhere.LEFTMOST}],
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
        self.check_no_duplicates(self.s04_remove_columns,
                                 's04_remove_columns',
                                 stderr_file=self._stderr_file)
        self._check_increasing_multi(self.s05_merge_columns,
                                     's05_merge_columns', 2,
                                     stderr_file=self._stderr_file)
        self.check_no_duplicates(self.s06_place_columns_first,
                                 's06_place_columns_first',
                                 stderr_file=self._stderr_file)

    def sort_sx_hook(self) -> None:
        """Sort s[0-9]_ as needed as needed (hook)."""
        self.s03_split_columns = sorted(self.s03_split_columns, key=get_column)
        self.s04_remove_columns = sorted(self.s04_remove_columns)
        self.s05_merge_columns = sorted(self.s05_merge_columns,
                                        key=get_merge_first_column)
        self.s07_rename_columns = sorted(self.s07_rename_columns,
                                         key=get_column)
        self.s08_insert_columns = sorted(self.s08_insert_columns,
                                         key=get_column)
