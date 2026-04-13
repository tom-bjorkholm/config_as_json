#! /usr/local/bin/python3
# mypy: disable-error-code=no-untyped-def
"""Test factory selection and configuration migration helpers."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from tempfile import TemporaryDirectory
import sys
import pytest
from config_as_json.assert_dict_equal import assert_dict_equal
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_enums import FileType
from config_as_json.config_factory import config_factory_from_json, \
    JsonValueMatcher, MatchConfig, MatchConfigSeq
from config_as_json.migrate_cfg import migrate_cfg
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from .config_xls_list_transf_name import ConfigXlsListTransfName
from .config_xls_list_transf_num import ConfigXlsListTransfNum


def _match_configs() -> MatchConfigSeq:
    """Return matchers for the two copied compatibility configurations."""
    return [
        MatchConfig(match_func=JsonValueMatcher('column_ref', 'BY_NAME'),
                    config_class=ConfigXlsListTransfName),
        MatchConfig(match_func=JsonValueMatcher('column_ref', 'BY_NUMBER'),
                    config_class=ConfigXlsListTransfNum)
    ]


def _config_from_file(filename: str,
                      auto_ch_hook: ConfigAutoChangeHook) -> \
        ConfigXlsListTransfName | ConfigXlsListTransfNum:
    """Create one of the copied test configurations from a file."""
    cfg = config_factory_from_json(match_configs=_match_configs(),
                                   auto_ch_hook=auto_ch_hook,
                                   from_json_filename=filename,
                                   stderr_file=sys.stderr)
    assert isinstance(cfg, (ConfigXlsListTransfName, ConfigXlsListTransfNum))
    return cfg


def test_config_factory_from_json_name_cfg(capsys):
    """Select the name-based configuration class from legacy JSON."""
    cfg = _config_from_file(
        'test/test_config_as_json/bak_compat_0_7_13_name.cfg',
        MigrateCfgWarnHook())
    out, err = capsys.readouterr()
    assert isinstance(cfg, ConfigXlsListTransfName)
    assert cfg.column_ref.name == 'BY_NAME'
    assert err == MigrateCfgWarnHook.migrate_warn_msg()
    assert out == ''


def test_config_factory_from_json_number_cfg(capsys):
    """Select the number-based configuration class from legacy JSON."""
    cfg = _config_from_file(
        'test/test_config_as_json/bak_compat_0_7_13_number.cfg',
        MigrateCfgWarnHook())
    out, err = capsys.readouterr()
    assert isinstance(cfg, ConfigXlsListTransfNum)
    assert cfg.column_ref.name == 'BY_NUMBER'
    assert err == MigrateCfgWarnHook.migrate_warn_msg()
    assert out == ''


def test_config_factory_from_json_nok_no_match(capsys):
    """Fail cleanly when no registered configuration matches the JSON."""
    with pytest.raises(SystemExit):
        config_factory_from_json(
            match_configs=_match_configs(),
            auto_ch_hook=ConfigAutoChangeHook(),
            from_json_data_text='{"column_ref": "UNKNOWN"}',
            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'No matching config class found' in err


def test_config_factory_from_json_nok_missing_input(capsys):
    """Fail cleanly when no JSON input source was supplied."""
    with pytest.raises(RuntimeError):
        config_factory_from_json(match_configs=_match_configs(),
                                 auto_ch_hook=ConfigAutoChangeHook(),
                                 stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Either JSON text or JSON file needed' in err


def test_migrate_cfg_name(capsys):
    """Migrate the name-based legacy configuration file."""
    refcfg = ConfigXlsListTransfName()
    refcfg.out_type = FileType.CSV
    refcfg.in_csv_dialect['name'] = 'csv.unix_dialect'
    refcfg.s01_split_rows = []
    refcfg.s02_merge_rows = []
    refcfg.s03_split_columns[0]['right_name'] = 'Family Name'
    refcfg.s08_insert_columns[1]['column'] = 'Something Else'
    infilename = 'test/test_config_as_json/bak_compat_0_7_13_name.cfg'
    with TemporaryDirectory() as dirname:
        outfilename = dirname + '/a.cfg'
        res = migrate_cfg(infile=infilename, outfile=outfilename,
                          match_configs=_match_configs(),
                          stderr_file=sys.stderr)
        cfg = _config_from_file(outfilename, ConfigAutoChangeHook())
    out, err = capsys.readouterr()
    assert_dict_equal(refcfg.__dict__, cfg.__dict__, ['_hook_cfg_autochange'],
                      stderr_file=sys.stderr)
    assert cfg.s03_split_columns[0]['right_name'] == 'Family Name'
    assert cfg.s08_insert_columns[1]['column'] == 'Something Else'
    assert out == ''
    assert err == ''
    assert res == 0


def test_migrate_cfg_number(capsys):
    """Migrate the number-based legacy configuration file."""
    refcfg = ConfigXlsListTransfNum()
    refcfg.out_type = FileType.CSV
    refcfg.in_csv_dialect['name'] = 'csv.unix_dialect'
    refcfg.s01_split_rows = []
    refcfg.s02_merge_rows = []
    refcfg.s07_rename_columns[1]['name'] = 'Family Name'
    refcfg.s08_insert_columns[1]['name'] = 'Something else'
    infilename = 'test/test_config_as_json/bak_compat_0_7_13_number.cfg'
    with TemporaryDirectory() as dirname:
        outfilename = dirname + '/a.cfg'
        res = migrate_cfg(infile=infilename, outfile=outfilename,
                          match_configs=_match_configs(),
                          stderr_file=sys.stderr)
        cfg = _config_from_file(outfilename, ConfigAutoChangeHook())
    out, err = capsys.readouterr()
    assert_dict_equal(refcfg.__dict__, cfg.__dict__, ['_hook_cfg_autochange'],
                      stderr_file=sys.stderr)
    assert cfg.s07_rename_columns[1]['name'] == 'Family Name'
    assert cfg.s08_insert_columns[1]['name'] == 'Something else'
    assert out == ''
    assert err == ''
    assert res == 0


def test_migrate_cfg_nok_missing_input(capsys):
    """Report a missing input file when migrating configuration."""
    with TemporaryDirectory() as dirname:
        infilename = dirname + '/a.cfg'
        outfilename = dirname + '/b.cfg'
        with pytest.raises(SystemExit):
            migrate_cfg(infile=infilename, outfile=outfilename,
                        match_configs=_match_configs(),
                        stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Cannot find input configuration file' in err


def test_migrate_cfg_nok_existing_output(capsys):
    """Refuse to overwrite an existing migration output file."""
    cfg = ConfigXlsListTransfNum()
    with TemporaryDirectory() as dirname:
        infilename = dirname + '/a.cfg'
        outfilename = dirname + '/b.cfg'
        cfg.write(to_json_filename=infilename)
        cfg.write(to_json_filename=outfilename)
        with pytest.raises(SystemExit):
            migrate_cfg(infile=infilename, outfile=outfilename,
                        match_configs=_match_configs(),
                        stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Output configuration file' in err
    assert 'already exists.' in err
    assert 'Cowardly refusing to overwrite existing configuration file' in err
