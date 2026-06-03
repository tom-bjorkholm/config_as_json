#! /usr/local/bin/python3
"""Read and write configuration of excel list transform."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License


import sys
from copy import deepcopy
from enum import Enum
from typing import Optional, Callable, TypeVar, NamedTuple, TextIO, \
    Generic, TypedDict
from csv import Dialect
from config_as_json import ReadOldConfiguration, RocfKeyRename
from config_as_json.config import Config, ParseConverter
from config_as_json.char_encoding import check_char_encoding
from config_as_json.csv_dialect import get_csv_dialect
from config_as_json.dict_validators import DictForEachValidator, DictRule
from config_as_json.discriminated_dict_validators import DictVariant, \
    DiscriminatedDictValidator
from config_as_json.list_validators import ListForEachValidator, \
    ListIsOrderedValidator, ListOfDictsKeysValidator, ListSizeValidator, \
    ListValueTypeValidator
from config_as_json.str_to_enum import string_to_enum_best_match
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.commontypes import ConfigPath
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from config_as_json.type_validators import ValueTypeValidator
from config_as_json.validator import ValidationPlan
from .config_enums import FileType, SplitWhere, \
    ExcelLib, RewriteKind, CaseSensitivity, ColumnRef


type CsvSpec = dict[str, Optional[str]]
Column = TypeVar('Column', int, str)
type SingleRule[Column] = dict[str, Optional[Column | str]]
type Rule[Column] = list[SingleRule[Column]]
type SingleRuleSplit[Column] = dict[str, Optional[Column | str | SplitWhere]]


class SingleRuleRowSplit[Column](TypedDict):
    """Sinle rule for splitting a column."""

    column: Column
    separators: list[str]
    not_separators: list[str]


type RuleSplit[Column] = list[SingleRuleSplit[Column]]
type RuleRowSplit[Column] = list[SingleRuleRowSplit[Column]]
type RuleOrder = list[str]
type RulePlace = list[int]
type RuleRemove = RulePlace
type RulePlaceOrOrder = RulePlace | RuleOrder
type SingleRuleRewrite[Column] = dict[str,
                                      Optional[Column | str |
                                               list[str] |
                                               RewriteKind |
                                               CaseSensitivity]]
type RuleRewrite[Column] = list[SingleRuleRewrite[Column]]
type SingleRuleMerge[Column] = dict[str, list[Column] | str]
type RuleMerge[Column] = list[SingleRuleMerge[Column]]
type DupCheckKeyArg[Column] = \
    SingleRule[Column] | SingleRuleMerge[Column] | SingleRuleSplit[Column]
type DupCheckKey[Column] = \
    Callable[[DupCheckKeyArg[Column]], Column | list[Column]]
type IncrCheckKey[Column] = \
    Callable[[SingleRuleMerge[Column]], Column | list[Column]]
type NoDupKeydType[Column] = \
    Rule[Column] | RuleMerge[Column] | RuleSplit[Column]


def check_unique_values(config: Config, values: list[Column], param_name: str,
                        tinfo: Column, stderr_file: TextIO) -> None:
    """Flag as error if a value occurs more than once."""
    validator = ListIsOrderedValidator(element_type=type(tinfo),
                                       is_ordered=False, unique_values=True)
    _ = validator.validate_member(config=config, member_name=param_name,
                                  member_value=values, stderr_file=stderr_file)


class ColInfo(NamedTuple, Generic[Column]):
    """Information about columns to pass to ConfigExcelListTransform init."""

    split_last: str
    insert_last: Optional[str]
    s03: RuleSplit[Column]
    s08: Rule[Column]
    col_to_use: list[Column]
    col_to_use_row: list[Column]
    tinfo: Column


class ExcelListTransformReadOldConfig(ReadOldConfiguration):
    """Normalize old excel-list-transform test configuration files."""

    def get_missing_path_values(self) -> dict[ConfigPath, object]:
        """Provide default values for optional encoding."""
        return {('in_csv_encoding',): 'utf_8_sig',
                ('out_csv_encoding',): 'utf-8',
                ('in_excel_col_name_strip',): False,
                ('in_excel_values_strip',): False,
                ('s01_split_rows',): [],
                ('s02_merge_rows',): []}

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Get names of backward compatible config parameters."""
        return [
            RocfKeyRename(old='s1_split_columns', new='s03_split_columns'),
            RocfKeyRename(old='s2_remove_columns', new='s04_remove_columns'),
            RocfKeyRename(old='s3_merge_columns', new='s05_merge_columns'),
            RocfKeyRename(old='s4_place_columns_first',
                          new='s06_place_columns_first'),
            RocfKeyRename(old='s5_rename_columns', new='s07_rename_columns'),
            RocfKeyRename(old='s6_insert_columns', new='s08_insert_columns'),
            RocfKeyRename(old='s7_rewrite_columns', new='s09_rewrite_columns'),
            RocfKeyRename(old='s8_column_order', new='s10_column_order')
        ]


# pylint: disable-next=too-many-instance-attributes,line-too-long
class ConfigExcelListTransform(Config, Generic[Column]):
    """Class with configuration for excel list transform."""

    # pylint: disable-next=too-many-arguments
    def __init__(self, *, col_ref: ColumnRef, colinfo: ColInfo[Column],
                 tinfo: Column, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for excel list transform."""
        if auto_ch_hook is None:
            auto_ch_hook = MigrateCfgWarnHook()
        assert isinstance(colinfo.tinfo, type(tinfo))
        self._columntype: type[Column] = type(tinfo)
        self.column_ref: ColumnRef = col_ref
        col2use = deepcopy(colinfo.col_to_use)  # dont destroying caller's arg
        col2userow = deepcopy(colinfo.col_to_use_row)
        self.max_column_read: int = 20
        self.out_csv_dialect: CsvSpec = {'name': 'csv.excel',
                                         'delimiter': ',', 'quoting': None,
                                         'quotechar': '"',
                                         'lineterminator': None,
                                         'escapechar': None}
        self.in_csv_dialect: CsvSpec = {'name': 'csv.excel',
                                        'delimiter': ',', 'quoting': None,
                                        'quotechar': '"',
                                        'lineterminator': None,
                                        'escapechar': None}
        self.in_csv_encoding = 'utf_8_sig'
        self.out_csv_encoding = 'utf-8'
        self.in_type: FileType = FileType.EXCEL
        self.in_excel_col_name_strip = True
        self.in_excel_values_strip = False
        self.in_excel_library: ExcelLib = ExcelLib.PYLIGHTXL
        self.out_excel_library: ExcelLib = ExcelLib.PYLIGHTXL
        self.out_type: FileType = FileType.EXCEL
        self.s01_split_rows: RuleRowSplit[Column] = \
            [{'column': col2userow.pop(0),
              'separators': [' ', '+'],
              'not_separators': ['\\ ', '\\+', ' + ']}]
        self.s02_merge_rows: RuleMerge[Column] = \
            [{'columns': [col2userow.pop(0), col2userow.pop(0)],
              'separator': ' + '}]
        self.s03_split_columns: RuleSplit[Column] = colinfo.s03
        self.s05_merge_columns: RuleMerge[Column] = \
            [{'columns': [col2use.pop(0), col2use.pop(0)],
              'separator': ' '}]
        self.s07_rename_columns: Rule[Column] = \
            [{'column': col2use.pop(0), 'name': 'First Name'},
             {'column': col2use.pop(0), 'name': 'Last Name'}]
        self.s08_insert_columns: Rule[Column] = colinfo.s08
        self.s09_rewrite_columns: RuleRewrite[Column] = \
            [{'column': col2use.pop(0),
              'kind': RewriteKind.STRIP, 'chars': '',
              'case': CaseSensitivity.IGNORE_CASE},
             {'column': col2use.pop(0), 'kind': RewriteKind.REMOVECHARS,
              'chars': [' ', '-'], 'case': CaseSensitivity.MATCH_CASE},
             {'column': col2use.pop(0),
              'kind': RewriteKind.REGEX_SUBSTITUTE,
              'from': '^07', 'to': '+467',
              'case': CaseSensitivity.MATCH_CASE},
             {'column': col2use.pop(0),
              'kind': RewriteKind.REGEX_SUBSTITUTE,
              'from': '^+4607', 'to': '+467',
              'case': CaseSensitivity.MATCH_CASE},
             {'column': col2use.pop(0),
              'kind': RewriteKind.REGEX_SUBSTITUTE,
              'from': '^467', 'to': '+467',
              'case': CaseSensitivity.MATCH_CASE},
             {'column': col2use.pop(0), 'kind': RewriteKind.STR_SUBSTITUTE,
              'from': 'donald', 'to': 'duck',
              'case': CaseSensitivity.IGNORE_CASE}]
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file)
        self.check_array_configs(split_last=colinfo.split_last,
                                 insert_last=colinfo.insert_last,
                                 stderr_file=stderr_file)
        self.sort_sx_hook()
        self._check_no_duplicate_single(self.s03_split_columns,
                                        's03_split_columns', colinfo.tinfo,
                                        stderr_file=stderr_file)
        self._check_no_duplicate_single(self.s07_rename_columns,
                                        's07_rename_columns', colinfo.tinfo,
                                        stderr_file=stderr_file)
        self._check_no_duplicate_single(self.s08_insert_columns,
                                        's08_insert_columns', colinfo.tinfo,
                                        stderr_file=stderr_file)
        self.check_rewrite_configs(coltype=type(colinfo.tinfo),
                                   stderr_file=stderr_file)
        check_char_encoding(self.in_csv_encoding, stderr_file=stderr_file)
        check_char_encoding(self.out_csv_encoding, stderr_file=stderr_file)
        self.check_split_row_cfg(stderr_file=stderr_file)
        self.check_merge_row_cfg(stderr_file=stderr_file)

    def get_out_csv_dialect(self, stderr_file: TextIO) -> Dialect:
        """Get CSV dialect for output file.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        assert self.out_csv_dialect['name'] is not None
        return get_csv_dialect(
            name=self.out_csv_dialect['name'],
            delimiter=self.out_csv_dialect['delimiter'],
            quoting=self.out_csv_dialect['quoting'],
            quotechar=self.out_csv_dialect['quotechar'],
            lineterminator=self.out_csv_dialect['lineterminator'],
            escapechar=self.out_csv_dialect['escapechar'],
            stderr_file=stderr_file)

    def get_in_csv_dialect(self, stderr_file: TextIO) -> Dialect:
        """Get CSV dialect for input file from Portfolio.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        assert self.in_csv_dialect['name'] is not None
        return get_csv_dialect(
            name=self.in_csv_dialect['name'],
            delimiter=self.in_csv_dialect['delimiter'],
            quoting=self.in_csv_dialect['quoting'],
            quotechar=self.in_csv_dialect['quotechar'],
            lineterminator=self.in_csv_dialect['lineterminator'],
            escapechar=self.in_csv_dialect['escapechar'],
            stderr_file=stderr_file)

    def sort_sx_hook(self) -> None:
        """Sort s[0-9]_ as needed (hook)."""

    def _get_read_old_configuration(self) -> ReadOldConfiguration:
        """Return the object that normalizes old test config files."""
        return ExcelListTransformReadOldConfig()

    @staticmethod
    def get_cols_single(rule: Rule[Column] | RuleSplit[Column] |
                        RuleRewrite[Column], tinfo: Column) -> list[Column]:
        """Get list of columns for modification rule."""
        cols: list[Column] = []
        for row in rule:
            rowcol = row['column']
            assert isinstance(rowcol, type(tinfo))
            cols.append(rowcol)
        return cols

    @staticmethod
    def get_cols_multi(rule: RuleMerge[Column], tinfo: Column) -> list[Column]:
        """Get list of columns for merge rule."""
        cols: list[Column] = []
        for row in rule:
            rowcols = row['columns']
            for singlecol in rowcols:
                assert isinstance(singlecol, type(tinfo))
                cols.append(singlecol)
        return cols

    def _check_no_duplicate_values(self, values: list[Column], param_name: str,
                                   tinfo: Column, stderr_file: TextIO) -> None:
        """Flag as error if a value occurs more than once."""
        check_unique_values(self, values, param_name, tinfo, stderr_file)

    def _check_no_duplicate_single(self,
                                   rule: Rule[Column] | RuleSplit[Column],
                                   param_name: str, tinfo: Column,
                                   stderr_file: TextIO) -> None:
        """Flag as error if column is refered to multiple times.

        Args:
            rule: Rule list whose ``column`` values must be unique.
            param_name: Configuration parameter name used in diagnostics.
            tinfo: Sample value used to identify the column type.
            stderr_file: Stream used for user-facing diagnostics.
        """
        cols: list[Column] = ConfigExcelListTransform.get_cols_single(rule,
                                                                      tinfo)
        self._check_no_duplicate_values(cols, param_name, tinfo, stderr_file)

    def _check_no_duplicate_multi(self, rule: RuleMerge[Column],
                                  param_name: str, tinfo: Column,
                                  stderr_file: TextIO) -> None:
        """Flag as error if column is refered to multiple times.

        Args:
            rule: Rule list whose merged columns must be unique.
            param_name: Configuration parameter name used in diagnostics.
            tinfo: Sample value used to identify the column type.
            stderr_file: Stream used for user-facing diagnostics.
        """
        cols: list[Column] = ConfigExcelListTransform.get_cols_multi(rule,
                                                                     tinfo)
        self._check_no_duplicate_values(cols, param_name, tinfo, stderr_file)

    @staticmethod
    def _check_increasing_multi(rule: RuleMerge[Column], param_name: str,
                                tinfo: Column, stderr_file: TextIO) -> None:
        """Flag as error if order is not increasing.

        Args:
            rule: Rule list whose merged columns must stay in order.
            param_name: Configuration parameter name used in diagnostics.
            tinfo: Sample value used to identify the column type.
            stderr_file: Stream used for user-facing diagnostics.
        """
        cols: list[Column] = ConfigExcelListTransform.get_cols_multi(rule,
                                                                     tinfo)
        seen: Optional[Column] = None
        for col in cols:
            assert isinstance(col, (int, str))
            if seen is not None and seen >= col:
                msg: str = f'Increasing order needed in {param_name}'
                print(msg, file=stderr_file)
                raise KeyError(msg)
            seen = col

    @staticmethod
    def get_converter_dict(enum_type: type[Enum]) -> ParseConverter:
        """Get dict for converting to given enum_type."""
        return ParseConverter(result_type=enum_type,
                              func=string_to_enum_best_match,
                              args={'num_type': enum_type})

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Get converters for use when parsing JSON.

        Overriding in derived class.
        Return None if no conversions.
        Return dict of dict for use in json decoder hook.
        Structure of return value shall be:
        {key: {'result type': res_type, 'func': function,
        'args': {arg_name: arg_value}}}.
        """
        return {'in_type': self.get_converter_dict(FileType),
                'out_type': self.get_converter_dict(FileType),
                'in_excel_library': self.get_converter_dict(ExcelLib),
                'out_excel_library': self.get_converter_dict(ExcelLib),
                'where': self.get_converter_dict(SplitWhere),
                'store_single': self.get_converter_dict(SplitWhere),
                'kind': self.get_converter_dict(RewriteKind),
                'case': self.get_converter_dict(CaseSensitivity),
                'column_ref': self.get_converter_dict(ColumnRef)}

    def check_array_configs(self, split_last: str, insert_last: Optional[str],
                            stderr_file: TextIO) -> None:
        """Check that keywords in configuration arrays are OK.

        Args:
            split_last: Final allowed key in split-column rules.
            insert_last: Optional extra allowed key in insert-column rules.
            stderr_file: Stream used for user-facing diagnostics.
        """
        split_col_keys = ['column', 'separator', 'where', split_last]
        _ = ListOfDictsKeysValidator(split_col_keys).validate_member(
            self, 's03_split_columns', self.s03_split_columns, stderr_file)
        merge_col_keys = ['columns', 'separator']
        _ = ListOfDictsKeysValidator(merge_col_keys).validate_member(
            self, 's05_merge_columns', self.s05_merge_columns, stderr_file)
        rename_col_keys = ['column', 'name']
        _ = ListOfDictsKeysValidator(rename_col_keys).validate_member(
            self, 's07_rename_columns', self.s07_rename_columns, stderr_file)
        insert_col_keys = ['column', 'value']
        if insert_last is not None:
            assert insert_last is not None  # keep mypy happy
            insert_col_keys.append(insert_last)
        _ = ListOfDictsKeysValidator(insert_col_keys).validate_member(
            self, 's08_insert_columns', self.s08_insert_columns, stderr_file)

    def check_rewrite_configs(self, coltype: type,
                              stderr_file: TextIO) -> None:
        """Check the rewrite column configuration.

        Args:
            coltype: Expected runtime type for the configured columns.
            stderr_file: Stream used for user-facing diagnostics.
        """
        column_rule = DictRule(keys=['column'],
                               validators=[ValueTypeValidator(coltype)])
        chars_str_rule = DictRule(keys=['chars'],
                                  validators=[ValueTypeValidator(str)])
        chars_list_rule = DictRule(keys=['chars'],
                                   validators=[ValueTypeValidator(list)])
        case_rule = DictRule(keys=['case'],
                             validators=[ValueTypeValidator(CaseSensitivity)])
        from_to_rule = DictRule(keys=['from', 'to'],
                                validators=[ValueTypeValidator(str)])
        variants: dict[object, DictVariant] = {
            RewriteKind.STRIP: DictVariant(
                mandatory_keys=['column', 'chars', 'case'],
                allowed_keys=['from', 'to'],
                rules=[column_rule, chars_str_rule, case_rule]),
            RewriteKind.REMOVECHARS: DictVariant(
                mandatory_keys=['column', 'chars', 'case'],
                allowed_keys=['from', 'to'],
                rules=[column_rule, chars_list_rule, case_rule]),
            RewriteKind.REGEX_SUBSTITUTE: DictVariant(
                mandatory_keys=['column', 'from', 'to', 'case'],
                allowed_keys=['chars'],
                rules=[column_rule, from_to_rule, case_rule]),
            RewriteKind.STR_SUBSTITUTE: DictVariant(
                mandatory_keys=['column', 'from', 'to', 'case'],
                allowed_keys=['chars'],
                rules=[column_rule, from_to_rule, case_rule])
        }
        rewrite_validator = ListForEachValidator(
            element_validators=[DiscriminatedDictValidator(
                discriminator_key='kind', variants=variants,
                discriminator_validator=ValueTypeValidator(RewriteKind))],
            element_type=dict)
        _ = rewrite_validator.validate_member(self, 's09_rewrite_columns',
                                              self.s09_rewrite_columns,
                                              stderr_file)

    @staticmethod
    def check_sep_not_sep(separators: list[str], not_separators: list[str],
                          stderr_file: TextIO) -> None:
        """Check relationship between separators and not separators.

        Args:
            separators: Accepted separators in the split rule.
            not_separators: Escaped strings that must not trigger a split.
            stderr_file: Stream used for user-facing diagnostics.
        """
        for notsep in not_separators:
            if notsep in separators:
                print('Error in s01_split_rows:\n' +
                      'Cannot have same string as both separator and ' +
                      f'not separator: {notsep}', file=stderr_file)
                sys.exit(1)
            found: bool = False
            for sep in separators:
                if sep in notsep:
                    found = True
                    break
            if not found:
                print('Error in s01_split_rows:\n' +
                      f'Not separator "{notsep}" does not affect ' +
                      'any separator.', file=stderr_file)
                sys.exit(1)

    def check_split_row_cfg(self, stderr_file: TextIO) -> None:
        """Check the split row configuration.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        keys = ['column', 'separators', 'not_separators']
        keys_validator = ListOfDictsKeysValidator(keys)
        _ = keys_validator.validate_member(self, 's01_split_rows',
                                           self.s01_split_rows, stderr_file)
        split_rows_validator = ListForEachValidator(
            element_validators=[DictForEachValidator(rules=[
                DictRule(keys=['column'],
                         validators=[ValueTypeValidator(self._columntype)]),
                DictRule(keys=['separators'],
                         validators=[ListSizeValidator(1, sys.maxsize),
                                     ListValueTypeValidator(str)]),
                DictRule(keys=['not_separators'],
                         validators=[ListSizeValidator(0, sys.maxsize),
                                     ListValueTypeValidator(str)])
            ])], element_type=dict)
        _ = split_rows_validator.validate_member(self, 's01_split_rows',
                                                 self.s01_split_rows,
                                                 stderr_file)
        for elem in self.s01_split_rows:
            sep = elem['separators']
            assert isinstance(sep, list)
            nosep = elem['not_separators']
            assert isinstance(nosep, list)
            self.check_sep_not_sep(separators=sep, not_separators=nosep,
                                   stderr_file=stderr_file)

    def check_merge_row_cfg(self, stderr_file: TextIO) -> None:
        """Check the merge rows configuration.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        keys = ['columns', 'separator']
        keys_validator = ListOfDictsKeysValidator(keys)
        _ = keys_validator.validate_member(self, 's02_merge_rows',
                                           self.s02_merge_rows, stderr_file)
        merge_rows_validator = ListForEachValidator(
            element_validators=[DictForEachValidator(rules=[
                DictRule(keys=['columns'],
                         validators=[
                             ListSizeValidator(1, sys.maxsize),
                             ListValueTypeValidator(self._columntype)]),
                DictRule(keys=['separator'],
                         validators=[ValueTypeValidator(str)])
            ])], element_type=dict)
        _ = merge_rows_validator.validate_member(self, 's02_merge_rows',
                                                 self.s02_merge_rows,
                                                 stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []
