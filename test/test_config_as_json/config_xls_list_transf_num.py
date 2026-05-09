#! /usr/local/bin/python3
"""Read and write configuration of CSV splitting."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License


import sys
from typing import Optional, Protocol, TextIO
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from .config_excel_list_transform import \
    ConfigExcelListTransform, Rule, RuleMerge, RulePlace, RuleRemove, \
    RuleSplit, SingleRuleMerge, SingleRuleSplit, SingleRule, ColInfo, \
    check_unique_values
from .config_enums import SplitWhere, ColumnRef


NUM_REMOVE_COLUMNS = [1, 2, 3]
NUM_PLACE_COLUMNS_FIRST = [7, 3, 6]


# pylint: disable-next=too-few-public-methods
class NumTransformRules(Protocol):
    """Number-based transform fixture rules."""

    s03_split_columns: RuleSplit[int]
    s04_remove_columns: RuleRemove
    s05_merge_columns: RuleMerge[int]
    s06_place_columns_first: RulePlace
    s07_rename_columns: Rule[int]
    s08_insert_columns: Rule[int]


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


def make_num_colinfo() -> ColInfo[int]:
    """Build column info for the number-based transform fixture."""
    cols = [15, 16, 1, 2, 5, 5, 5, 5, 5, 6]
    row_cols = [7, 1, 2]
    return ColInfo[int](split_last='store_single', insert_last='name',
                        s03=[{'column': 15, 'separator': ' ',
                              'where': SplitWhere.RIGHTMOST,
                              'store_single': SplitWhere.LEFTMOST}],
                        s08=[{'column': 1, 'name': 'Division',
                              'value': None},
                             {'column': 7, 'name': 'Other',
                              'value': 'some text'}],
                        col_to_use=cols, col_to_use_row=row_cols, tinfo=2)


def set_num_base_rules(config: NumTransformRules) -> None:
    """Set base list rules for the number-based transform fixture."""
    config.s04_remove_columns = list(NUM_REMOVE_COLUMNS)
    config.s06_place_columns_first = list(NUM_PLACE_COLUMNS_FIRST)


def sort_num_rules(config: NumTransformRules) -> None:
    """Sort number-based list transform rules."""
    config.s03_split_columns = sorted(config.s03_split_columns, key=get_column)
    config.s04_remove_columns = sorted(config.s04_remove_columns)
    config.s05_merge_columns = sorted(config.s05_merge_columns,
                                      key=get_merge_first_column)
    config.s07_rename_columns = sorted(config.s07_rename_columns,
                                       key=get_column)
    config.s08_insert_columns = sorted(config.s08_insert_columns,
                                       key=get_column)


# pylint: disable-next=R0902,C0301,R0801
class ConfigXlsListTransfNum(ConfigExcelListTransform[int]):
    """Class with configuration for excel list transform."""

    s04_remove_columns: RuleRemove
    s06_place_columns_first: RulePlace

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for excel list transform."""
        if auto_ch_hook is None:
            auto_ch_hook = MigrateCfgWarnHook()
        set_num_base_rules(self)
        colinfo = make_num_colinfo()
        super().__init__(col_ref=ColumnRef.BY_NUMBER, colinfo=colinfo, tinfo=2,
                         from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file)
        check_unique_values(self, self.s04_remove_columns,
                            's04_remove_columns', 1, stderr_file)
        self._check_increasing_multi(self.s05_merge_columns,
                                     's05_merge_columns', 2,
                                     stderr_file=stderr_file)
        check_unique_values(self, self.s06_place_columns_first,
                            's06_place_columns_first', 1, stderr_file)

    def sort_sx_hook(self) -> None:
        """Sort s[0-9]_ as needed as needed (hook)."""
        sort_num_rules(self)
