#! /usr/local/bin/python3
"""Test class ConfigAutoChangeHook."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import pytest
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook


class ConfigAutoChangeHookVer(ConfigAutoChangeHook):
    """Class to test ConfigAutoChangeHook."""

    def __init__(self, old_key_ver: list[str], def_keys_ver: list[str]):
        """Construct a ConfigAutoChangeHook obejct."""
        super().__init__()
        self.num = 0
        self.old_key_ver = old_key_ver
        self.def_keys_ver = def_keys_ver

    def auto_changed(self, old_keys_handled: list[str],
                     def_vals_handled: list[str]) -> None:
        """Check call-back."""
        self.num += 1
        assert self.old_key_ver == old_keys_handled
        assert self.def_keys_ver == def_vals_handled


@pytest.mark.parametrize('okv,dkv,num',
                         [([], [], 0),
                          (['a', 'b'], ['c', 'd', 'e'], 1),
                          (['a'], [], 1),
                          (['a', 'b'], [], 1),
                          ([], ['c'], 1),
                          ([], ['c', 'd', 'e'], 1),
                          (['a', 'b'], ['c'], 1)])
def test_conf_auto_hook_ch_ok1(capsys, okv, dkv, num):
    """Test OK cases of ConfigAutoChangeHook."""
    hook = ConfigAutoChangeHookVer(old_key_ver=okv, def_keys_ver=dkv)
    for i in okv:
        hook.old_key_handled(i)
    for j in dkv:
        hook.default_value_provided(j)
    hook.all_autochanges_done()
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
def test_migrate_hook_ch_ok1(capsys, okv, dkv, msg):
    """Test OK cases of ConfigAutoChangeHook."""
    hook = MigrateCfgWarnHook()
    for i in okv:
        hook.old_key_handled(i)
    for j in dkv:
        hook.default_value_provided(j)
    hook.all_autochanges_done()
    out, err = capsys.readouterr()
    assert '' == out
    assert msg == err
