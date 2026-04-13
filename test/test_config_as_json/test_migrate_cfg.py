#! /usr/local/bin/python3
"""Test migrate_cfg."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License

from tempfile import TemporaryDirectory
import pytest
from config_as_json.migrate_cfg import migrate_cfg
from config_as_json.migrate_cfg_warn_hook import MigrateCfgWarnHook
from config_as_json.config_enums import FileType
from config_as_json.assert_dict_equal import assert_dict_equal
from config_as_json.config_factory import config_factory_from_json


def test_migrate_cfg1(capsys):
    """Test migration of 0.7.13 config file."""
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
        _ = config_factory_from_json(from_json_filename=infilename)
        _, err = capsys.readouterr()
        assert err == MigrateCfgWarnHook.migrate_warn_msg()
        res = migrate_cfg(infile=infilename, outfile=outfilename)
        cfg = config_factory_from_json(from_json_filename=outfilename)
        out, err = capsys.readouterr()
        assert_dict_equal(refcfg.__dict__, cfg.__dict__,
                          ['_hook_cfg_autochange'])
        assert cfg.s03_split_columns[0]['right_name'] == 'Family Name'
        assert cfg.s08_insert_columns[1]['column'] == 'Something Else'
        assert '' == out
        assert '' == err
        assert res == 0


def test_migrate_cfg2(capsys):
    """Test migration of 0.7.13 config file."""
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
        _ = config_factory_from_json(from_json_filename=infilename)
        _, err = capsys.readouterr()
        assert err == MigrateCfgWarnHook.migrate_warn_msg()
        res = migrate_cfg(infile=infilename, outfile=outfilename)
        cfg = config_factory_from_json(from_json_filename=outfilename)
        out, err = capsys.readouterr()
        assert_dict_equal(refcfg.__dict__, cfg.__dict__,
                          ['_hook_cfg_autochange'])
        assert cfg.s07_rename_columns[1]['name'] == 'Family Name'
        assert cfg.s08_insert_columns[1]['name'] == 'Something else'
        assert '' == out
        assert '' == err
        assert res == 0


def test_migrate_cfg_nok1(capsys):
    """Test not OK case 1 of migrate_cfg."""
    with TemporaryDirectory() as dirname:
        infilename = dirname + '/a.cfg'
        outfilename = dirname + '/b.cfg'
        with pytest.raises(SystemExit):
            _ = migrate_cfg(infile=infilename, outfile=outfilename)
    out, err = capsys.readouterr()
    assert '' == out
    assert 'Cannot find input configuration file' in err


def test_migrate_cfg_nok2(capsys):
    """Test not OK case 2 of migrate_cfg."""
    cfg = ConfigXlsListTransfNum()
    with TemporaryDirectory() as dirname:
        infilename = dirname + '/a.cfg'
        outfilename = dirname + '/b.cfg'
        cfg.write(to_json_filename=infilename)
        cfg.write(to_json_filename=outfilename)
        with pytest.raises(SystemExit):
            _ = migrate_cfg(infile=infilename, outfile=outfilename)
    out, err = capsys.readouterr()
    assert '' == out
    assert 'Output configuration file' in err
    assert 'already exists.' in err
    assert 'Cowardly refusing to overwrite existing configuration file' in err


@pytest.mark.parametrize('ipar', ['-i', '--input'])
@pytest.mark.parametrize('opar', ['-o', '--output'])
def test_migrate_cmd1(capsys, ipar, opar):
    """Test migration of 0.7.13 config file."""
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
        args = ['migrate-cfg', ipar, infilename, opar, outfilename]
        transform_cmd(arguments=args)
        cfg = config_factory_from_json(from_json_filename=outfilename)
        out, err = capsys.readouterr()
        assert_dict_equal(refcfg.__dict__, cfg.__dict__,
                          ['_hook_cfg_autochange'])
        assert cfg.s03_split_columns[0]['right_name'] == 'Family Name'
        assert cfg.s08_insert_columns[1]['column'] == 'Something Else'
        assert '' == out
        assert '' == err


@pytest.mark.parametrize('ipar', ['-i', '--input'])
@pytest.mark.parametrize('opar', ['-o', '--output'])
def test_migrate_cmd2(capsys, ipar, opar):
    """Test migration of 0.7.13 config file."""
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
        args = ['migrate-cfg', ipar, infilename, opar, outfilename]
        transform_cmd(arguments=args)
        cfg = config_factory_from_json(from_json_filename=outfilename)
        out, err = capsys.readouterr()
        assert_dict_equal(refcfg.__dict__, cfg.__dict__,
                          ['_hook_cfg_autochange'])
        assert cfg.s07_rename_columns[1]['name'] == 'Family Name'
        assert cfg.s08_insert_columns[1]['name'] == 'Something else'
        assert '' == out
        assert '' == err


@pytest.mark.parametrize('ipar', ['-i', '--input'])
@pytest.mark.parametrize('opar', ['-o', '--output'])
def test_migrate_cmd_nok1(capsys, ipar, opar):
    """Test not OK case 1 of migrate_cmd."""
    with TemporaryDirectory() as dirname:
        infilename = dirname + '/a.cfg'
        outfilename = dirname + '/b.cfg'
        with pytest.raises(SystemExit):
            args = ['migrate-cfg', ipar, infilename, opar, outfilename]
            transform_cmd(arguments=args)
    out, err = capsys.readouterr()
    assert '' == out
    assert 'Cannot find input configuration file' in err


@pytest.mark.parametrize('ipar', ['-i', '--input'])
@pytest.mark.parametrize('opar', ['-o', '--output'])
def test_migrate_cmd_nok2(capsys, ipar, opar):
    """Test not OK case 2 of migrate_cmd."""
    cfg = ConfigXlsListTransfNum()
    with TemporaryDirectory() as dirname:
        infilename = dirname + '/a.cfg'
        outfilename = dirname + '/b.cfg'
        cfg.write(to_json_filename=infilename)
        cfg.write(to_json_filename=outfilename)
        with pytest.raises(SystemExit):
            args = ['migrate-cfg', ipar, infilename, opar, outfilename]
            transform_cmd(arguments=args)
    out, err = capsys.readouterr()
    assert '' == out
    assert 'Output configuration file' in err
    assert 'already exists.' in err
    assert 'Cowardly refusing to overwrite existing configuration file' in err


def test_migrate_cmd_help1(capsys):
    """Test help including migrate-cfg."""
    with pytest.raises(SystemExit):
        transform_cmd(['-h'])
    out, err = capsys.readouterr()
    assert '' == err
    assert ',migrate-cfg}' in out
    assert '  migrate-cfg  ' in out
    assert 'Migrate configuration file format from older format' in out
    assert 'newest format.' in out


def test_migrate_cmd_help2(capsys):
    """Test help for migrate-cfg."""
    with pytest.raises(SystemExit):
        transform_cmd(['migrate-cfg', '-h'])
    out, err = capsys.readouterr()
    assert '' == err
    assert 'Migrate configuration file format from older format' in out
    assert 'newest format.' in out
    assert 'can be read by the next version of the command' in out


@pytest.mark.parametrize('ipar', ['-i', '--input'])
@pytest.mark.parametrize('opar', ['-o', '--output'])
@pytest.mark.parametrize('ival', ['ab', 'cd'])
@pytest.mark.parametrize('oval', ['ef', 'gh'])
def test_migrate_cmd3(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                      monkeypatch, ipar, opar, ival, oval):
    """Test command line calling migrate_cfg."""
    def migrate_mock(infile: str, outfile: str) -> int:
        """Mock of migrate_cfg."""
        migrate_mock.num_calls += 1
        assert infile == ival
        assert outfile == oval

    migrate_mock.num_calls = 0
    to_mock = 'config_as_json.transform_cmd.migrate_cfg'
    monkeypatch.setattr(to_mock, migrate_mock)
    args = ['migrate-cfg', ipar, ival, opar, oval]
    transform_cmd(arguments=args)
    out, err = capsys.readouterr()
    assert 1 == migrate_mock.num_calls
    assert '' == out
    assert '' == err
