#! /usr/local/bin/python3
"""Test class ConfigAutoChangeHook."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from typing import TextIO
from io import StringIO
import sys
import pytest
from pytest import CaptureFixture
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook


class ConfigAutoChangeHookVer(ConfigAutoChangeHook):
    """Class to test ConfigAutoChangeHook."""

    def __init__(self, old_key_ver: list[str],
                 rocf_val_keys_ver: list[str]) -> None:
        """Construct a ConfigAutoChangeHook object."""
        super().__init__()
        self.num = 0
        self.old_key_ver = old_key_ver
        self._rocf_val_keys_ver = rocf_val_keys_ver

    def auto_changed(self, old_keys_handled: list[str],
                     rocf_vals_handled: list[str],
                     stderr_file: TextIO) -> None:
        """Check call-back."""
        _ = stderr_file  # pylint: disable=unused-variable
        self.num += 1
        assert self.old_key_ver == old_keys_handled
        assert self._rocf_val_keys_ver == rocf_vals_handled


def test_hook_records_moved_paths(capsys: CaptureFixture[str]) -> None:
    """Test that moved paths trigger the backward-compatible callback."""
    hook = ConfigAutoChangeHookVer(old_key_ver=[], rocf_val_keys_ver=[])
    hook.old_path_moved('old.value', 'new.value')
    hook.all_autochanges_done(stderr_file=sys.stderr)
    assert hook.num == 1
    assert hook.old_paths_moved == [('old.value', 'new.value')]
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('okv,dkv,num',
                         [([], [], 0),
                          (['a', 'b'], ['c', 'd', 'e'], 1),
                          (['a'], [], 1),
                          (['a', 'b'], [], 1),
                          ([], ['c'], 1),
                          ([], ['c', 'd', 'e'], 1),
                          (['a', 'b'], ['c'], 1)])
def test_conf_auto_hook_ch_ok1(capsys: CaptureFixture[str], okv: list[str],
                               dkv: list[str], num: int) -> None:
    """Test OK cases of ConfigAutoChangeHook."""
    hook = ConfigAutoChangeHookVer(old_key_ver=okv, rocf_val_keys_ver=dkv)
    for i in okv:
        hook.old_key_handled(i)
    for j in dkv:
        hook.rocf_missing_value_provided(j)
    hook.all_autochanges_done(stderr_file=sys.stderr)
    assert hook.num == num
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('okv,dkv,msg',
                         [([], [], ''),
                          (['a', 'b'], ['c', 'd', 'e'],
                           MigrateCfgWarnHook.migrate_warn_msg()),
                          (['a'], [],
                           MigrateCfgWarnHook.migrate_warn_msg()),
                          (['a', 'b'], [],
                           MigrateCfgWarnHook.migrate_warn_msg()),
                          ([], ['c'],
                           MigrateCfgWarnHook.migrate_warn_msg()),
                          ([], ['c', 'd', 'e'],
                           MigrateCfgWarnHook.migrate_warn_msg()),
                          (['a', 'b'], ['c'],
                           MigrateCfgWarnHook.migrate_warn_msg())])
def test_migrate_hook_ch_ok1(capsys: CaptureFixture[str], okv: list[str],
                             dkv: list[str], msg: str) -> None:
    """Test OK cases of ConfigAutoChangeHook."""
    hook = MigrateCfgWarnHook()
    for i in okv:
        hook.old_key_handled(i)
    for j in dkv:
        hook.rocf_missing_value_provided(j)
    hook.all_autochanges_done(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert msg == err


def test_migrate_hook_call_stderr(capsys: CaptureFixture[str]) -> None:
    """Test that the warning stream is chosen when the hook is called."""
    hook = MigrateCfgWarnHook()
    hook.rocf_missing_value_provided('alpha')
    stderr_file = StringIO()
    hook.all_autochanges_done(stderr_file=stderr_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert stderr_file.getvalue() == MigrateCfgWarnHook.migrate_warn_msg()
