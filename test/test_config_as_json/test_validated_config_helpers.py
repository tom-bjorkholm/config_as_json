#! /usr/local/bin/python3
# mypy: disable-error-code=no-untyped-def
"""Test validator-based helper configurations beside the legacy ones."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from io import StringIO
import pytest
from config_as_json.assert_dict_equal import assert_dict_equal
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from .config_xls_list_transf_name import ConfigXlsListTransfName
from .config_xls_list_transf_name_validated import \
    ConfigXlsListTransfNameValidated
from .config_xls_list_transf_num import ConfigXlsListTransfNum
from .config_xls_list_transf_num_validated import \
    ConfigXlsListTransfNumValidated


def assert_cfg_equal(left, right) -> None:
    """Assert equality of two config objects except for hook identity."""
    assert_dict_equal(left.__dict__, right.__dict__, ['_hook_cfg_autochange'],
                      stderr_file=sys.stderr)


def test_validated_name_cfg_matches_legacy_default(capsys):
    """Test validated helper config against legacy default config."""
    refcfg = ConfigXlsListTransfName()
    cfg = ConfigXlsListTransfNameValidated()
    out, err = capsys.readouterr()
    assert_cfg_equal(refcfg, cfg)
    assert out == ''
    assert err == ''


def test_validated_num_cfg_matches_legacy_default(capsys):
    """Test validated helper config against legacy default config."""
    refcfg = ConfigXlsListTransfNum()
    cfg = ConfigXlsListTransfNumValidated()
    out, err = capsys.readouterr()
    assert_cfg_equal(refcfg, cfg)
    assert out == ''
    assert err == ''


def test_validated_name_cfg_matches_legacy_compat_file(capsys):
    """Test validated name config against legacy parsing of compat file."""
    filename = 'test/test_config_as_json/bak_compat_0_7_13_name.cfg'
    refcfg = ConfigXlsListTransfName(
        from_json_filename=filename, auto_ch_hook=ConfigAutoChangeHook())
    cfg = ConfigXlsListTransfNameValidated(
        from_json_filename=filename, auto_ch_hook=ConfigAutoChangeHook())
    out, err = capsys.readouterr()
    assert_cfg_equal(refcfg, cfg)
    assert out == ''
    assert err == ''


def test_validated_num_cfg_matches_legacy_compat_file(capsys):
    """Test validated number config against legacy parsing of compat file."""
    filename = 'test/test_config_as_json/bak_compat_0_7_13_number.cfg'
    refcfg = ConfigXlsListTransfNum(
        from_json_filename=filename, auto_ch_hook=ConfigAutoChangeHook())
    cfg = ConfigXlsListTransfNumValidated(
        from_json_filename=filename, auto_ch_hook=ConfigAutoChangeHook())
    out, err = capsys.readouterr()
    assert_cfg_equal(refcfg, cfg)
    assert out == ''
    assert err == ''


def test_legacy_name_cfg_uses_supplied_stderr_file(capsys):
    """Test legacy helper diagnostics with an explicitly supplied stream."""
    template = ConfigXlsListTransfName()
    template.s07_rename_columns[0]['column'] = 'last name'
    stderr_file = StringIO()
    with pytest.raises(SystemExit):
        _ = ConfigXlsListTransfName(
            from_json_data_text=template.as_json_string(
                stderr_file=stderr_file),
            stderr_file=stderr_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert 'Duplicates not allowed in s07_rename_columns.' in \
        stderr_file.getvalue()


def test_validated_name_cfg_uses_supplied_stderr_file(capsys):
    """Test validated helper diagnostics with an explicitly supplied stream."""
    template = ConfigXlsListTransfNameValidated()
    template.s07_rename_columns[0]['extra'] = 'boom'
    stderr_file = StringIO()
    with pytest.raises(SystemExit):
        _ = ConfigXlsListTransfNameValidated(
            from_json_data_text=template.as_json_string(
                stderr_file=stderr_file),
            stderr_file=stderr_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert 'Found non-allowed key "extra"' in stderr_file.getvalue()
