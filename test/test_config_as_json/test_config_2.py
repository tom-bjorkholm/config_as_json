#! /usr/local/bin/python3
# mypy: disable-error-code="no-untyped-def,no-untyped-call"
"""Test the Config class (part 2 of tests)."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code

from typing import Any, Optional, cast, TextIO  # pylint: disable=unused-import,ungrouped-imports # noqa: E501
from copy import deepcopy
from enum import Enum, auto
import json
import sys
import pytest
from config_as_json.config import Config, RocfKeyRename, ParseConverter
from config_as_json.commontypes import JsonType
from config_as_json.validator import ValidationPlan


@pytest.mark.parametrize('enc, is_ok',
                         [('utf-8', True),
                          ('abc123', False)])
def test_cfg_valid_chr_enc_ok(capsys, enc, is_ok):
    """Test OK cases of valid_char_encoding."""
    ret = Config.valid_char_encoding(enc)
    out, err = capsys.readouterr()
    assert ret == is_ok
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('enc',
                         [8, True])
def test_cfg_valid_chr_enc_nok(capsys, enc):
    """Test not OK cases of valid_char_encoding."""
    with pytest.raises(Exception) as exc:
        _ = Config.valid_char_encoding(enc)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert 'must be str' in str(exc)


@pytest.mark.parametrize('enc',
                         ['utf-8', 'iso8859-1'])
def test_cfg_check_chr_enc_ok(capsys, enc):
    """Test OK cases of check_char_encoding."""
    Config.check_char_encoding(enc, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('enc',
                         ['utf-88', 'abc123'])
def test_cfg_check_chr_enc_nok(capsys, enc):
    """Test not OK cases of check_char_encoding."""
    with pytest.raises(SystemExit):
        Config.check_char_encoding(enc, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert f'{enc} is not a recognized encoding' in err


class AbcConfig(Config):
    """Class to test defualt values."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.ab = 'a1b2'
        self.cd = 'c3d4'
        self.ef = 'e5f6'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def _rocf_values_for_missing_json_keys(self) -> dict[str, JsonType]:
        """Return default values for optional parameters."""
        return {'cd': 'cd99', 'ef': 'ef99'}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


class OptionalOutputMode(Enum):
    """Output modes used by omit-None tests."""

    FAST = auto()
    CAREFUL = auto()


class OmitNoneConfig(Config):
    """Class to test omit-when-None configuration values."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a config object with true optional members."""
        self.required_name = 'default'
        self.optional_text: Optional[str] = None
        self.optional_mode: Optional[OptionalOutputMode] = None
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def _omit_none_from_json(self) -> list[str]:
        """Return the keys omitted while their value is None."""
        return ['optional_text', 'optional_mode']

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return converters for enum-valued test members."""
        return {'optional_mode': self.get_converter_dict(OptionalOutputMode)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


class OmitNoneUnknownMemberConfig(OmitNoneConfig):
    """Class with an invalid omit-None member name."""

    def _omit_none_from_json(self) -> list[str]:
        """Return an invalid omit-None member name."""
        return ['missing_member']


class OmitNoneNonNoneDefaultConfig(Config):
    """Class with an invalid omit-None default value."""

    def __init__(self, stderr_file: TextIO = sys.stderr) -> None:
        """Construct an invalid config object for omit-None tests."""
        self.required_name = 'default'
        self.optional_text: Optional[str] = 'must fail'
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def _omit_none_from_json(self) -> list[str]:
        """Return a key whose constructor default is not None."""
        return ['optional_text']

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


def test_cfg_abc_dump_ok(capsys):
    """Test dump of default constructed AbcConfig."""
    abc = AbcConfig(stderr_file=sys.stderr)
    jstext = abc.as_json_string(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    jstext = jstext.replace('\n', ' ')
    for _ in range(10):
        jstext = jstext.replace('  ', ' ')
    assert jstext == '{ "ab": "a1b2", "cd": "c3d4", "ef": "e5f6" }'


def test_omit_none_config_omits_default_none_values(capsys):
    """Test that default None members are omitted from JSON."""
    cfg = OmitNoneConfig(stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert json_data == {'required_name': 'default'}


def test_omit_none_config_accepts_missing_values(capsys):
    """Test that missing omit-None members remain None."""
    cfg = OmitNoneConfig(from_json_data_text='{"required_name": "read"}',
                         stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.required_name == 'read'
    assert cfg.optional_text is None
    assert cfg.optional_mode is None
    assert json_data == {'required_name': 'read'}


def test_omit_none_config_accepts_explicit_null(capsys):
    """Test that explicit JSON null is treated like a missing value."""
    cfg = OmitNoneConfig(
        from_json_data_text='{"required_name": "read", '
                            '"optional_text": null, '
                            '"optional_mode": null}',
        stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.optional_text is None
    assert cfg.optional_mode is None
    assert json_data == {'required_name': 'read'}


def test_omit_none_config_keeps_explicit_values(capsys):
    """Test that explicit optional values are read, converted, and written."""
    cfg = OmitNoneConfig(
        from_json_data_text='{"required_name": "read", '
                            '"optional_text": "note", '
                            '"optional_mode": "FAST"}',
        stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.optional_text == 'note'
    assert cfg.optional_mode == OptionalOutputMode.FAST
    assert json_data == {'optional_mode': 'FAST',
                         'optional_text': 'note',
                         'required_name': 'read'}


def test_omit_none_config_still_requires_normal_members(capsys):
    """Test that omit-None handling does not hide missing required keys."""
    with pytest.raises(KeyError):
        _ = OmitNoneConfig(from_json_data_text='{"optional_text": "note"}',
                           stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert 'No value for required_name in JSON data' in err


def test_omit_none_config_rejects_unknown_member(capsys):
    """Test that omit-None member names must exist."""
    with pytest.raises(KeyError) as exc:
        _ = OmitNoneUnknownMemberConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert '_omit_none_from_json() returned unknown key missing_member' in \
        str(exc.value)


def test_omit_none_config_rejects_non_none_default(capsys):
    """Test that omit-None members must default to None."""
    with pytest.raises(ValueError) as exc:
        _ = OmitNoneNonNoneDefaultConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert '_omit_none_from_json() key optional_text must default to None' in \
        str(exc.value)


@pytest.mark.parametrize('jstext, aval, cval, fval',
                         [('{ "ab": "a1b2", "cd": "c3d4", "ef": "e5f6" }',
                           'a1b2', 'c3d4', 'e5f6'),
                          ('{ "ab": "donald", "cd": "duck", "ef": "mouse" }',
                           'donald', 'duck', 'mouse'),
                          ('{ "ab": "aaa", "cd": "mickey" }',
                           'aaa', 'mickey', 'ef99'),
                          ('{ "ab": "donald", "ef": "duck" }',
                           'donald', 'cd99', 'duck'),
                          ('{ "ab": "duck"}',
                           'duck', 'cd99', 'ef99')])
def test_cfg_rocf_val_json_ok(capsys, jstext, aval, cval, fval):
    """Test construction of cfg from json with default values."""
    abc = AbcConfig(from_json_data_text=jstext, from_json_filename=None)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert abc.ab == aval
    assert abc.cd == cval
    assert abc.ef == fval


@pytest.mark.parametrize('jstext',
                         ['{ "cd": "c3d4", "ef": "e5f6" }',
                          '{ "cd": "duck", "ef": "mouse" }',
                          '{ "cd": "mickey" }',
                          '{ "ef": "duck" }', '{}'])
def test_cfg_rocf_val_json_nok(capsys, jstext):
    """Test construction of cfg from json with default values."""
    with pytest.raises(KeyError):
        _ = AbcConfig(from_json_data_text=jstext, from_json_filename=None,
                      stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert 'No value for ab in' in err


@pytest.mark.parametrize('ind, outd, ren, errtxt',
                         [({'foo': 12, 'bar': 'data'},
                           {'foo': 12, 'bar': 'data'},
                           RocfKeyRename(old='star', new='sun'), ''),
                          ({'foo': 12, 'bar': 'data'},
                           {'sun': 12, 'bar': 'data'},
                           RocfKeyRename(old='foo', new='sun'), ''),
                          ({'foo': 12, 'bar': 'data'},
                           {'foo': 12, 'sun': 'data'},
                           RocfKeyRename(old='bar', new='sun'), ''),
                          ({'foo': 12, 'bar': 'data'},
                           {'foo': 12},
                           RocfKeyRename(old='bar', new='foo'),
                           'Inconsistent configuration:\n' +
                           'Both new config parameter foo and old bar ' +
                           'present.\nIgnoring old parameter bar\n'),
                          ({'foo': {'a': 'b', 'bar': 'c'}, 'bar': 'data'},
                           {'foo': {'a': 'b', 'sun': 'c'}, 'sun': 'data'},
                           RocfKeyRename(old='bar', new='sun'), ''),
                          ({'foo': {'a': 'b', 'foo': 'c'}, 'bar': 'data'},
                           {'sun': {'a': 'b', 'sun': 'c'}, 'bar': 'data'},
                           RocfKeyRename(old='foo', new='sun'), ''),
                          ({'foo': {'foo': 'b', 'bar': 'c'}, 'bar': 'data'},
                           {'sun': {'sun': 'b', 'bar': 'c'}, 'bar': 'data'},
                           RocfKeyRename(old='foo', new='sun'), ''),
                          ({'a': [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], 'b': 5},
                           {'c': [{'c': 1, 'b': 2}, {'c': 3, 'b': 4}], 'b': 5},
                           RocfKeyRename(old='a', new='c'), '')])
def test_bw_compat_single1(capsys, ind, outd, ren, errtxt):
    """Test Config._bwcompat_single for case 1."""
    data = deepcopy(ind)
    Config._rocf_rename_json_key_in_dict(rename=ren,  # pylint: disable=protected-access # noqa: E501
                                         json_data=data,
                                         stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert err == errtxt
    assert data == outd


@pytest.mark.parametrize('ren',
                         [RocfKeyRename(old=cast(Any, None), new='sun'),
                          RocfKeyRename(old='foo', new=cast(Any, None)),
                          RocfKeyRename(old='foo', new='foo')])
def test_bw_compat_single2(capsys, ren):
    """Test Config._bwcompat_single for not OK case."""
    with pytest.raises(AssertionError):
        Config._rocf_rename_json_key_in_dict(rename=ren,  # pylint: disable=protected-access # noqa: E501
                                             json_data={'a': 'b'},
                                             stderr_file=sys.stderr)
    out, _ = capsys.readouterr()
    assert '' == out


@pytest.mark.parametrize('ind,outd,ren,errtxt',
                         [([{'a': 2, 'b': 'c'},
                            {'a': 4, 'b': 'd'}],
                           [{'e': 2, 'b': 'c'},
                            {'e': 4, 'b': 'd'}],
                           RocfKeyRename(old='a', new='e'), ''),
                          ([{'foo': 12, 'bar': 'data'},
                            {'fff': 14, 'bar': 'other'}],
                           [{'foo': 12}, {'fff': 14, 'foo': 'other'}],
                           RocfKeyRename(old='bar', new='foo'),
                           'Inconsistent configuration:\n' +
                           'Both new config parameter foo and old bar ' +
                           'present.\nIgnoring old parameter bar\n'),
                          ([[{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]],
                           [[{'a': 1, 'c': 2}, {'a': 3, 'c': 4}]],
                           RocfKeyRename(old='b', new='c'), '')])
def test_bwcompat_single_lst1(capsys, ind, outd, ren, errtxt):
    """Test Config._bwcompat_single_lst for case 1."""
    data = deepcopy(ind)
    Config._rocf_rename_json_key_in_list(rename=ren,  # pylint: disable=protected-access # noqa: E501
                                         json_data=data,
                                         stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert err == errtxt
    assert data == outd


class DummyCfg(Config):
    """Dummy Config for testing only."""

    def __init__(self, stderr_file: TextIO = sys.stderr) -> None:
        """Create a DummyCfg object."""
        self.aa = 'text'
        super().__init__(from_json_data_text='{ "aa": "text" }',
                         from_json_filename=None,
                         stderr_file=stderr_file)

    def _rocf_get_json_key_renames(self) -> list[RocfKeyRename]:
        return [
            RocfKeyRename(old='a', new='x'),
            RocfKeyRename(old='b', new='y'),
            RocfKeyRename(old='c', new='z')
        ]

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


@pytest.mark.parametrize('ind,outd,errtxt',
                         [({'p': [{'a': 2, 'b': 'c'}, {'a': 4, 'b': 'd'}]},
                           {'p': [{'x': 2, 'y': 'c'}, {'x': 4, 'y': 'd'}]},
                           '')])
def test_rename_backward_compatible(capsys, ind, outd, errtxt):
    """Test Config._rename_backward_compatible."""
    data = deepcopy(ind)
    cfg = DummyCfg(stderr_file=sys.stderr)
    cfg._rocf_rename_json_keys(  # pylint: disable=protected-access # noqa: E501
                                    json_data=data, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert err == errtxt
    assert data == outd


@pytest.mark.parametrize('par, inp, key, opt, vtype, mls',
                         [('parr', [{'bar': 3, 'foo': 2},
                                    {'bar': 'b', 'foo': 3}],
                           'foo', False, int, 1),
                          ('par2', [{'bar': 'b', 'foo': 2},
                                    {'bar': 'b', 'foo': 3}],
                           'bar', False, str, 2),
                          ('par3', [{'bar': 'b', 'foo': 2},
                                    {'bar': 'b', 'foo': 3}],
                           'foobar', True, str, 0)])
def test_check_list_dict_ok(capsys,  # pylint: disable=too-many-arguments, too-many-positional-arguments # noqa: E501
                            par, inp, key, opt, vtype, mls):
    """Test OK cases of Config.check_lst_dict."""
    Config.check_lst_dict(paramname=par, inp=inp, key=key,
                          key_optional=opt, valtype=vtype,
                          min_size_list=mls, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('par, inp, key, opt, vtype, mls, msgs',
                         [('parr', {'bar': 3, 'foo': 2},
                           'foo', False, int, 0,
                           ['Error in parameter parr.',
                            'Expected list but found dict',
                            "{'bar': 3, 'foo': 2}"]),
                          ('par2', ['bar', 'b', 'foo', '2'],
                           'bar', False, int, 0,
                           ['Error in parameter par2.',
                            'Expected dict in list but found str',
                            'bar']),
                          ('par3', [{'bar': 'b', 'foo': 2},
                                    {'bar': 'b', 'foo': 3}],
                           'foobar', False, str, 0,
                           ['Error in parameter par3.',
                            'Expected key foobar not in dict in list',
                            "{'bar': 'b', 'foo': 2}"]),
                          ('par4', [{'bar': 'b', 'foo': 2},
                                    {'bar': 'b', 'foo': 3}],
                           'bar', False, int, 0,
                           ['Error in parameter par4.',
                            'Value for key bar expected to be of type',
                            'of type int but is of type str',
                            '\nb\n']),
                          ('parr', [{'bar': 3, 'foo': 2},
                                    {'bar': 'b', 'foo': 3}],
                           'foo', False, int, 3,
                           ['Error in parameter parr.',
                            'Minimum 3 elements needed in list but ' +
                            'only 2 found'])])
def test_check_list_dict_nok(capsys,  # pylint: disable=too-many-arguments, too-many-positional-arguments # noqa: E501
                             par, inp, key, opt, vtype, mls, msgs):
    """Test not OK cases of Config.check_lst_dict."""
    with pytest.raises(SystemExit):
        Config.check_lst_dict(paramname=par, inp=inp, key=key,
                              key_optional=opt, valtype=vtype,
                              min_size_list=mls,
                              stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    for msg in msgs:
        assert msg in err


@pytest.mark.parametrize('par, inp, key, opt, vtype, mlso, mlsi, ',
                         [('parr', [{'bar': 3, 'foo': [2, 3]},
                                    {'bar': 'b', 'foo': [3, 5]}],
                           'foo', False, int, 1, 2),
                          ('par2', [{'bar': ['b', 'c'], 'foo': 2},
                                    {'bar': ['b', 'e'], 'foo': 3}],
                           'bar', False, str, 1, 2),
                          ('par3', [{'bar': 'b', 'foo': 2},
                                    {'bar': 'b', 'foo': 3}],
                           'foobar', True, str, 0, 0)])
def test_check_list_dict_lst_ok(capsys,  # pylint: disable=too-many-arguments, too-many-positional-arguments # noqa: E501
                                par, inp, key, opt, mlso, mlsi, vtype):
    """Test OK cases of Config.check_lst_dict_lst."""
    Config.check_lst_dict_lst(paramname=par, inp=inp, key=key,
                              key_optional=opt, valtype=vtype,
                              min_size_outer_list=mlso,
                              min_size_inner_list=mlsi,
                              stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('par, inp, key, opt, vtype, mlso, mlsi, msgs',
                         [('parr', [{'bar': 3, 'foo': [2, 'a']},
                                    {'bar': 'b', 'foo': [3, 5]}],
                           'foo', False, int, 0, 0,
                           ['Error in parameter parr.',
                            'Value for key foo expected to be list of int',
                            'But element in list is str', "\n[2, 'a']\n"]),
                          ('par2', [{'bar': ['a', 'c'], 'foo': 2},
                                    {'bar': [1, 'xx'], 'foo': 'c'}],
                           'bar', False, str, 0, 0,
                           ['Error in parameter par2.',
                            'Value for key bar expected to be list of str',
                            'But element in list is int', "\n[1, 'xx']\n"]),
                          ('par3', [{'bar': 'b', 'foo': 2},
                                    {'bar': 'b', 'foo': 3}],
                           'foobar', False, str, 0, 0,
                           ['Error in parameter par3.',
                            'Expected key foobar not in dict in list']),
                          ('par2', [{'bar': ['b', 'c'], 'foo': 2},
                                    {'bar': ['b', 'e'], 'foo': 3}],
                           'bar', False, str, 3, 1,
                           ['Error in parameter par2.',
                            'Minimum 3 elements needed in list but ' +
                            'only 2 found.']),
                          ('par2', [{'bar': ['b', 'c'], 'foo': 2},
                                    {'bar': ['b', 'e'], 'foo': 3}],
                           'bar', False, str, 1, 3,
                           ['Error in parameter par2.',
                            'List for key bar shall be minimum 3 elements.',
                            'But it is 2 elements only.'])])
def test_check_list_dict_lst_nok(capsys,  # pylint: disable=too-many-arguments, too-many-positional-arguments # noqa: E501
                                 par, inp, key, opt, vtype, mlso, mlsi, msgs):
    """Test not OK cases of Config.check_lst_dict_lst."""
    with pytest.raises(SystemExit):
        Config.check_lst_dict_lst(paramname=par, inp=inp, key=key,
                                  key_optional=opt, valtype=vtype,
                                  min_size_outer_list=mlso,
                                  min_size_inner_list=mlsi,
                                  stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    for msg in msgs:
        assert msg in err
