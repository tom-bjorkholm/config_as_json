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
from .config_excel_list_transform import ColInfo
from .config_excel_list_transform_validated import \
    ConfigExcelListTransformValidated
from .config_enums import ColumnRef, SplitWhere


class ConfigXlsListTransfNameValidated(  # pylint: disable=too-many-instance-attributes, line-too-long, duplicate-code # noqa: E501
        ConfigExcelListTransformValidated[str]):
    """Validator-based configuration for excel list transform."""

    def __init__(self,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for excel list transform."""
        if auto_ch_hook is None:
            auto_ch_hook = MigrateCfgWarnHook()
        col_to_use = ['street', 'street number', 'name', 'last name',
                      'Phone', 'Phone', 'Phone', 'Phone', 'Phone',
                      'Last Name']
        col_to_use_row = ['Club Name', 'name', 'last name']
        colinfo = ColInfo[str](split_last='right_name', insert_last=None,
                               s03=[{'column': 'name',
                                     'separator': ' ',
                                     'where': SplitWhere.RIGHTMOST,
                                     'right_name': 'last name'}],
                               s08=[{'column': 'Division', 'value': None},
                                    {'column': 'Other',
                                     'value': 'some text'}],
                               col_to_use=col_to_use,
                               col_to_use_row=col_to_use_row, tinfo='a')
        self.s10_column_order: list[str] = [
            'Class', 'Division', 'Nationality', 'Sail Number', 'Boat Name',
            'First Name', 'Last Name', 'Club Name', 'Email', 'Phone',
            'WhatsApp']
        super().__init__(col_ref=ColumnRef.BY_NAME,
                         colinfo=colinfo, tinfo='a',
                         from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook,
                         stderr_file=stderr_file)

    def _split_last_key(self) -> str:
        """Return the split-column key name used by this configuration."""
        return 'right_name'

    def _insert_last_key(self) -> Optional[str]:
        """Return the optional insert-column key name for this config."""
        return None

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        ret = super().get_validation_plan(stderr_file=stderr_file)
        ret.append(MemberValidationStep(
            member_names=['s10_column_order'],
            validator=ListIsOrderedValidator(
                str, is_ordered=False, unique_values=True)))
        return ret
