#! /usr/local/bin/python3
"""Test validator-based helper configurations beside the legacy ones."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
import json
from io import StringIO
import pytest
from pytest import CaptureFixture
from config_as_json.assert_dict_equal import assert_dict_equal
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.commontypes import JsonType
from config_as_json.validator import InvalidConfiguration
from .config_xls_list_transf_name import ConfigXlsListTransfName
from .config_xls_list_transf_name_validated import \
    ConfigXlsListTransfNameValidated
from .config_xls_list_transf_num import ConfigXlsListTransfNum
from .config_xls_list_transf_num_validated import \
    ConfigXlsListTransfNumValidated


def assert_cfg_equal(left: Config, right: Config) -> None:
    """Assert equality of two config objects except for hook identity."""
    assert_dict_equal(left.__dict__, right.__dict__, ['_hook_cfg_autochange'],
                      stderr_file=sys.stderr)


def test_name_cfg_default(capsys: CaptureFixture[str]) -> None:
    """Test validated helper config against legacy default config."""
    refcfg = ConfigXlsListTransfName()
    cfg = ConfigXlsListTransfNameValidated()
    out, err = capsys.readouterr()
    assert_cfg_equal(refcfg, cfg)
    assert out == ''
    assert err == ''


def test_num_cfg_default(capsys: CaptureFixture[str]) -> None:
    """Test validated helper config against legacy default config."""
    refcfg = ConfigXlsListTransfNum()
    cfg = ConfigXlsListTransfNumValidated()
    out, err = capsys.readouterr()
    assert_cfg_equal(refcfg, cfg)
    assert out == ''
    assert err == ''


def test_name_cfg_compat_file(capsys: CaptureFixture[str]) -> None:
    """Test validated name config against legacy parsing of compat file."""
    filename = 'test/test_config_as_json/bak_compat_0_7_13_name.cfg'
    refcfg = ConfigXlsListTransfName(from_json_filename=filename,
                                     auto_ch_hook=ConfigAutoChangeHook())
    cfg = ConfigXlsListTransfNameValidated(from_json_filename=filename,
                                           auto_ch_hook=ConfigAutoChangeHook())
    out, err = capsys.readouterr()
    assert_cfg_equal(refcfg, cfg)
    assert out == ''
    assert err == ''


def test_num_cfg_compat_file(capsys: CaptureFixture[str]) -> None:
    """Test validated number config against legacy parsing of compat file."""
    filename = 'test/test_config_as_json/bak_compat_0_7_13_number.cfg'
    refcfg = ConfigXlsListTransfNum(from_json_filename=filename,
                                    auto_ch_hook=ConfigAutoChangeHook())
    cfg = ConfigXlsListTransfNumValidated(from_json_filename=filename,
                                          auto_ch_hook=ConfigAutoChangeHook())
    out, err = capsys.readouterr()
    assert_cfg_equal(refcfg, cfg)
    assert out == ''
    assert err == ''


def test_legacy_name_stderr(capsys: CaptureFixture[str]) -> None:
    """Test legacy helper diagnostics with an explicitly supplied stream."""
    template = ConfigXlsListTransfName()
    template.s07_rename_columns[0]['column'] = 'last name'
    stderr_file = StringIO()
    with pytest.raises(InvalidConfiguration):
        json_text = template.as_json_string(stderr_file=stderr_file,
                                            member_name=None)
        _ = ConfigXlsListTransfName(from_json_data_text=json_text,
                                    stderr_file=stderr_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert 'Value last name for s07_rename_columns at index 1 ' in \
        stderr_file.getvalue()
    assert 'duplicates the value at index 0' in \
        stderr_file.getvalue()


def test_validated_name_stderr(capsys: CaptureFixture[str]) -> None:
    """Test validated helper diagnostics with an explicitly supplied stream."""
    template = ConfigXlsListTransfNameValidated()
    template.s07_rename_columns[0]['extra'] = 'boom'
    stderr_file = StringIO()
    with pytest.raises(InvalidConfiguration):
        json_text = template.as_json_string(stderr_file=stderr_file,
                                            member_name=None)
        _ = ConfigXlsListTransfNameValidated(from_json_data_text=json_text,
                                             stderr_file=stderr_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert "Unknown key 'extra' in s07_rename_columns[0]" in \
        stderr_file.getvalue()


def test_name_cfg_duplicate_columns(capsys: CaptureFixture[str]) -> None:
    """Test validated helper catches duplicate single-column rules."""
    template = ConfigXlsListTransfNameValidated()
    stderr_file = StringIO()
    json_data: JsonType = json.loads(template.as_json_string(
        stderr_file=stderr_file, member_name=None))
    assert isinstance(json_data, dict)
    rename_columns = json_data['s07_rename_columns']
    assert isinstance(rename_columns, list)
    first_column = rename_columns[0]
    assert isinstance(first_column, dict)
    first_column['column'] = 'last name'
    with pytest.raises(InvalidConfiguration):
        _ = ConfigXlsListTransfNameValidated(
            from_json_data_text=json.dumps(json_data), stderr_file=stderr_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert 's07_rename_columns' in stderr_file.getvalue()
    assert 'duplicates the value at index 0' in stderr_file.getvalue()


def test_num_cfg_decreasing_merge(capsys: CaptureFixture[str]) -> None:
    """Test validated helper catches decreasing merge-column rules."""
    template = ConfigXlsListTransfNumValidated()
    stderr_file = StringIO()
    json_data: JsonType = json.loads(template.as_json_string(
        stderr_file=stderr_file, member_name=None))
    assert isinstance(json_data, dict)
    merge_columns = json_data['s05_merge_columns']
    assert isinstance(merge_columns, list)
    first_column = merge_columns[0]
    assert isinstance(first_column, dict)
    first_column['columns'] = [2, 1]
    with pytest.raises(InvalidConfiguration):
        _ = ConfigXlsListTransfNumValidated(
            from_json_data_text=json.dumps(json_data), stderr_file=stderr_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert 's05_merge_columns' in stderr_file.getvalue()
    assert 'less than previous value 2' in stderr_file.getvalue()
