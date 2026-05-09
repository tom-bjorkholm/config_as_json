#! /usr/local/bin/python3
# mypy: disable-error-code=no-untyped-def
"""Test factory selection and configuration migration helpers."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from tempfile import TemporaryDirectory
from typing import Any, Callable, TextIO, cast
import sys
import pytest
from config_as_json.assert_dict_equal import assert_dict_equal
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_factory import config_factory_from_json, \
    JsonValueMatcher, MatchConfig, MatchConfigSeq
from config_as_json.migrate_cfg import migrate_cfg
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from .config_xls_list_transf_name import ConfigXlsListTransfName
from .config_xls_list_transf_num import ConfigXlsListTransfNum
from .config_enums import FileType


def _match_configs() -> MatchConfigSeq:
    """Return matchers for the two copied compatibility configurations."""
    return [
        MatchConfig(match_func=JsonValueMatcher('column_ref', 'BY_NAME'),
                    config_class=ConfigXlsListTransfName),
        MatchConfig(match_func=JsonValueMatcher('column_ref', 'BY_NUMBER'),
                    config_class=ConfigXlsListTransfNum)
    ]


def _config_from_file(filename: str, auto_ch_hook: ConfigAutoChangeHook,
                      stderr_file: TextIO) -> \
        ConfigXlsListTransfName | ConfigXlsListTransfNum:
    """Create one of the copied test configurations from a file."""
    cfg = config_factory_from_json(match_configs=_match_configs(),
                                   auto_ch_hook=auto_ch_hook,
                                   from_json_filename=filename,
                                   stderr_file=stderr_file)
    assert isinstance(cfg, (ConfigXlsListTransfName, ConfigXlsListTransfNum))
    return cfg


def _expected_name_cfg() -> ConfigXlsListTransfName:
    """Return the expected current name-based configuration."""
    refcfg = ConfigXlsListTransfName()
    refcfg.out_type = FileType.CSV
    refcfg.in_csv_dialect['name'] = 'csv.unix_dialect'
    refcfg.s01_split_rows = []
    refcfg.s02_merge_rows = []
    refcfg.s03_split_columns[0]['right_name'] = 'Family Name'
    refcfg.s08_insert_columns[1]['column'] = 'Something Else'
    return refcfg


def _expected_number_cfg() -> ConfigXlsListTransfNum:
    """Return the expected current number-based configuration."""
    refcfg = ConfigXlsListTransfNum()
    refcfg.out_type = FileType.CSV
    refcfg.in_csv_dialect['name'] = 'csv.unix_dialect'
    refcfg.s01_split_rows = []
    refcfg.s02_merge_rows = []
    refcfg.s07_rename_columns[1]['name'] = 'Family Name'
    refcfg.s08_insert_columns[1]['name'] = 'Something else'
    return refcfg


def _assert_name_cfg(filename: str) -> None:
    """Assert that a file contains the migrated name-based configuration."""
    refcfg = _expected_name_cfg()
    cfg = _config_from_file(filename, ConfigAutoChangeHook(),
                            stderr_file=sys.stderr)
    assert_dict_equal(refcfg.__dict__, cfg.__dict__, ['_hook_cfg_autochange'],
                      stderr_file=sys.stderr)
    assert cfg.s03_split_columns[0]['right_name'] == 'Family Name'
    assert cfg.s08_insert_columns[1]['column'] == 'Something Else'


def _assert_number_cfg(filename: str) -> None:
    """Assert that a file contains the migrated number-based configuration."""
    refcfg = _expected_number_cfg()
    cfg = _config_from_file(filename, ConfigAutoChangeHook(),
                            stderr_file=sys.stderr)
    assert_dict_equal(refcfg.__dict__, cfg.__dict__, ['_hook_cfg_autochange'],
                      stderr_file=sys.stderr)
    assert cfg.s07_rename_columns[1]['name'] == 'Family Name'
    assert cfg.s08_insert_columns[1]['name'] == 'Something else'


def _migrate_and_assert(infilename: str,
                        config_class: type[Config] | MatchConfigSeq,
                        check_config_func: Callable[[str], None]) -> int:
    """Migrate one file to a temporary path and check the result."""
    with TemporaryDirectory() as dirname:
        outfilename = dirname + '/a.cfg'
        res = migrate_cfg(infile=infilename, outfile=outfilename,
                          config_class=config_class, stderr_file=sys.stderr)
        check_config_func(outfilename)
    return res


def test_config_factory_from_json_name_cfg(capsys):
    """Select the name-based configuration class from legacy JSON."""
    cfg = _config_from_file(
        'test/test_config_as_json/bak_compat_0_7_13_name.cfg',
        MigrateCfgWarnHook(), stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert isinstance(cfg, ConfigXlsListTransfName)
    assert cfg.column_ref.name == 'BY_NAME'
    assert err == MigrateCfgWarnHook.migrate_warn_msg()
    assert out == ''


def test_config_factory_from_json_number_cfg(capsys):
    """Select the number-based configuration class from legacy JSON."""
    cfg = _config_from_file(
        'test/test_config_as_json/bak_compat_0_7_13_number.cfg',
        MigrateCfgWarnHook(), stderr_file=sys.stderr)
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


def test_config_factory_from_json_nok_both_inputs(capsys):
    """Fail cleanly when both JSON input sources were supplied."""
    with pytest.raises(RuntimeError):
        config_factory_from_json(match_configs=_match_configs(),
                                 auto_ch_hook=ConfigAutoChangeHook(),
                                 from_json_filename='unused.cfg',
                                 from_json_data_text='{}',
                                 stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Both cannot be given' in err


def test_json_value_matcher_returns_false_for_missing_key(capsys):
    """Return False when the distinguishing key is missing."""
    matcher = JsonValueMatcher('column_ref', 'BY_NAME')
    ret = matcher('{"other_key": "BY_NAME"}', sys.stderr)
    out, err = capsys.readouterr()
    assert ret is False
    assert out == ''
    assert err == ''


def test_json_value_matcher_compares_non_string_values(capsys):
    """Compare non-string JSON values with ordinary equality."""
    matcher = JsonValueMatcher('version', 2)
    ret = matcher('{"version": 2}', sys.stderr)
    out, err = capsys.readouterr()
    assert ret is True
    assert out == ''
    assert err == ''


def test_json_value_matcher_rejects_invalid_json(capsys):
    """Stop with a helpful message for malformed JSON text."""
    matcher = JsonValueMatcher('column_ref', 'BY_NAME')
    with pytest.raises(SystemExit):
        matcher('{"column_ref": ', sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Configuration JSON cannot be decoded.' in err


def test_json_value_matcher_rejects_invalid_utf8_bytes(capsys):
    """Stop with a helpful message for invalid UTF-8 byte input."""
    matcher = JsonValueMatcher('column_ref', 'BY_NAME')
    with pytest.raises(SystemExit):
        matcher(cast(Any, b'\xff'), sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Invalid UTF-8 in configuration data.' in err
    assert 'decode byte 0xff in position 0' in err


def test_json_value_matcher_rejects_non_dict_top_level(capsys):
    """Stop with a helpful message for non-dictionary top-level JSON."""
    matcher = JsonValueMatcher('column_ref', 'BY_NAME')
    with pytest.raises(SystemExit):
        matcher('["BY_NAME"]', sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Top level not dict' in err


def test_migrate_cfg_single_name(capsys):
    """Migrate a name-based legacy file using one known config class."""
    infilename = 'test/test_config_as_json/bak_compat_0_7_13_name.cfg'
    res = _migrate_and_assert(infilename, ConfigXlsListTransfName,
                              _assert_name_cfg)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert res == 0


def test_migrate_cfg_single_number(capsys):
    """Migrate a number-based legacy file using one known config class."""
    infilename = 'test/test_config_as_json/bak_compat_0_7_13_number.cfg'
    res = _migrate_and_assert(infilename, ConfigXlsListTransfNum,
                              _assert_number_cfg)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert res == 0


def test_migrate_cfg_multiple_name(capsys):
    """Migrate a name-based legacy file chosen from several config classes."""
    infilename = 'test/test_config_as_json/bak_compat_0_7_13_name.cfg'
    res = _migrate_and_assert(infilename, _match_configs(), _assert_name_cfg)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert res == 0


def test_migrate_cfg_multiple_number(capsys):
    """Migrate a number-based legacy file using several config classes."""
    infilename = 'test/test_config_as_json/bak_compat_0_7_13_number.cfg'
    res = _migrate_and_assert(infilename, _match_configs(), _assert_number_cfg)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert res == 0


def test_migrate_cfg_multiple_nok_no_match(capsys):
    """Report a factory selection failure during migration."""
    with TemporaryDirectory() as dirname:
        infilename = dirname + '/a.cfg'
        outfilename = dirname + '/b.cfg'
        with open(infilename, mode='w', encoding='UTF-8') as file:
            file.write('{"column_ref": "UNKNOWN"}')
        with pytest.raises(SystemExit):
            migrate_cfg(infile=infilename, outfile=outfilename,
                        config_class=_match_configs(), stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'No matching config class found' in err


@pytest.mark.parametrize(
    ('config_class', 'msg'),
    [(cast(Any, []), 'empty MatchConfig'),
     (cast(Any,
           [('not a matcher', ConfigXlsListTransfName)]), 'non-MatchConfig'),
     (cast(Any, 'not a matcher'), 'Config subclass'),
     (cast(Any, ConfigAutoChangeHook), 'Config subclass')])
def test_migrate_cfg_nok_invalid_config_class(config_class, msg, capsys):
    """Reject invalid configuration selector arguments."""
    infilename = 'test/test_config_as_json/bak_compat_0_7_13_name.cfg'
    with TemporaryDirectory() as dirname:
        outfilename = dirname + '/b.cfg'
        with pytest.raises(TypeError, match=msg):
            migrate_cfg(infile=infilename, outfile=outfilename,
                        config_class=config_class, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


def test_migrate_cfg_nok_missing_input(capsys):
    """Report a missing input file when migrating configuration."""
    with TemporaryDirectory() as dirname:
        infilename = dirname + '/a.cfg'
        outfilename = dirname + '/b.cfg'
        with pytest.raises(SystemExit):
            migrate_cfg(infile=infilename, outfile=outfilename,
                        config_class=_match_configs(), stderr_file=sys.stderr)
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
                        config_class=_match_configs(), stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Output configuration file' in err
    assert 'already exists.' in err
    assert 'Cowardly refusing to overwrite existing configuration file' in err
