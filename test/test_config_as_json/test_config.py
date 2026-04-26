#! /usr/local/bin/python3
# mypy: disable-error-code="no-untyped-def,no-untyped-call"
"""Test the Config class."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code

from tempfile import NamedTemporaryFile as ntf
from os import remove as os_remove
from io import StringIO
from enum import Enum, auto
import csv
import sys
from typing import Any, cast, TextIO
import pytest
from config_as_json.config import _ConfigEncoder, \
    ConfigBadJson, _over_ride_needed, Config
from config_as_json.assert_dict_equal import assert_dict_equal
from config_as_json.validator import ValidationPlan


class EnumInTesting(Enum):
    """Enum to test enum in config."""

    FOOBAR = auto()
    BARFOO = auto()


@pytest.mark.parametrize('obj, res', [(EnumInTesting.FOOBAR, 'FOOBAR'),
                                      (EnumInTesting.BARFOO, 'BARFOO')])
def test_config_encode(capsys, obj, res):
    """Test ConfigEncoder."""
    enc = _ConfigEncoder()
    ret = enc.default(obj)
    out, err = capsys.readouterr()
    assert ret == res
    assert '' == err
    assert '' == out


@pytest.mark.parametrize('obj', [1, 'hello'])
def test_config_encode_bad(obj):
    """Test ConfigEncoder with bad arguments."""
    enc = _ConfigEncoder()
    with pytest.raises(TypeError):
        _ = enc.default(obj)


def test__over_ride_needed_1(capsys):
    """Test _over_ride_needed with None."""
    ret = _over_ride_needed(cast(Any, None))
    out, err = capsys.readouterr()
    assert 42 == ret
    assert '' == err
    assert '' == out


def test__over_ride_needed_2(capsys):
    """Test _over_ride_needed with non-None."""
    with pytest.raises(NotImplementedError) as exc:
        _ = _over_ride_needed('42')
    out, err = capsys.readouterr()
    assert 'Override' in str(exc)
    assert 'needed' in str(exc)
    assert '' == err
    assert '' == out


class ConfigSomething(Config):  # pylint: disable=too-many-instance-attributes
    """Class to test Config."""

    def __init__(self, from_json_text=None, from_json_filename=None,
                 stderr_file: TextIO = sys.stderr):
        """Construct configuration for test."""
        self.csv_dialect1 = {'name': 'csv.excel', 'delimiter': ',',
                             'quoting': None, 'quotechar': '"',
                             'lineterminator': None, 'escapechar': None}
        self.csv_dialect2 = {'name': 'csv.unix_dialect', 'delimiter': ',',
                             'quoting': None, 'quotechar': '"',
                             'lineterminator': None, 'escapechar': None}
        self.kind = EnumInTesting.FOOBAR
        self.aa1 = 'nice'
        self.abc = [{'def': 15, 'geh': ';', 'ijk': EnumInTesting.BARFOO},
                    {'def': 26, 'geh': 'x', 'ijk': EnumInTesting.FOOBAR}]
        self.mno = {'ab': 4, 'cd': 7}
        self.pqr = {'ef': [{'gh': EnumInTesting.FOOBAR, 'ij': 'kl', 'mn': 7},
                           {'gh': EnumInTesting.BARFOO, 'ij': 'op', 'mn': 9}],
                    'qr': [{'gh': EnumInTesting.BARFOO, 'ij': 'st', 'mn': 3},
                           {'gh': EnumInTesting.BARFOO, 'ij': 'uv', 'mn': 4}]}
        self._unchecked_dicts = ['mno', 'pqr']
        super().__init__(from_json_text, from_json_filename,
                         stderr_file=stderr_file)
        self.check_array_configs(stderr_file=stderr_file)

    def get_csv_dialect1(self, stderr_file: TextIO):
        """Get CSV dialect 1."""
        return self.get_csv_dialect(
            name=self.csv_dialect1['name'],
            delimiter=self.csv_dialect1['delimiter'],
            quoting=self.csv_dialect1['quoting'],
            quotechar=self.csv_dialect1['quotechar'],
            lineterminator=self.csv_dialect1['lineterminator'],
            escapechar=self.csv_dialect1['escapechar'],
            stderr_file=stderr_file)

    def get_csv_dialect2(self, stderr_file: TextIO):
        """Get CSV dialect 2."""
        return self.get_csv_dialect(
            name=self.csv_dialect2['name'],
            delimiter=self.csv_dialect2['delimiter'],
            quoting=self.csv_dialect2['quoting'],
            quotechar=self.csv_dialect2['quotechar'],
            lineterminator=self.csv_dialect2['lineterminator'],
            escapechar=self.csv_dialect2['escapechar'],
            stderr_file=stderr_file)

    def check_array_configs(self, stderr_file: TextIO):
        """Check that keywords in configuration arrays are OK."""
        abc_keys = ['def', 'geh', 'ijk']
        self.check_array_keys('abc', self.abc, abc_keys,
                              stderr_file=stderr_file)
        pqr_keys = ['gh', 'ij', 'mn']
        for _, val in self.pqr.items():
            self.check_array_keys('pqr', val, pqr_keys,
                                  stderr_file=stderr_file)

    def parse_converters(self):
        """Get converters for use when parsing JSON.

        Overriding in derived class.
        Return None if no conversions.
        Return dict of dict for use in json decoder hook.
        Structure of return value shall be:
        {key: {'result type': res_type, 'func': function,
        'args': {arg_name: arg_value}}}.
        """
        return {'kind': self.get_converter_dict(EnumInTesting),
                'ijk': self.get_converter_dict(EnumInTesting),
                'gh': self.get_converter_dict(EnumInTesting)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


def test_config_something_def(capsys):
    """Test default values of ConfigSomething."""
    xst = ConfigSomething()
    assert isinstance(xst.kind, EnumInTesting)
    assert isinstance(xst.aa1, str)
    assert isinstance(xst.abc, list)
    assert isinstance(xst.mno, dict)
    assert isinstance(xst.pqr, dict)
    assert len(xst.abc) > 0
    assert xst.aa1 == 'nice'
    assert len(xst.mno) == 2
    assert len(xst.pqr) == 2
    assert xst.abc[1]['def'] == 26
    assert xst.mno['cd'] == 7
    assert 'qr' in xst.pqr
    assert len(xst.pqr['qr']) == 2
    assert 'mn' in xst.pqr['qr'][0]
    assert xst.pqr['qr'][0]['mn'] == 3
    scfg = xst.as_json_string(stderr_file=sys.stderr)
    assert len(scfg) > 1
    assert 'pqr' in scfg
    assert 'FOOBAR' in scfg
    zst = ConfigSomething()
    assert_dict_equal(xst.__dict__, zst.__dict__, ['_hook_cfg_autochange'],
                      stderr_file=sys.stderr)
    yst = ConfigSomething(from_json_text=scfg)
    assert_dict_equal(yst.__dict__, xst.__dict__, ['_hook_cfg_autochange'],
                      stderr_file=sys.stderr)
    assert isinstance(yst.kind, EnumInTesting)
    assert isinstance(yst.aa1, str)
    assert isinstance(yst.abc, list)
    assert isinstance(yst.mno, dict)
    assert isinstance(yst.pqr, dict)
    assert len(yst.abc) > 0
    assert yst.aa1 == 'nice'
    assert len(yst.mno) == 2
    assert len(yst.pqr) == 2
    assert yst.abc[1]['def'] == 26
    assert yst.mno['cd'] == 7
    assert 'qr' in yst.pqr
    assert len(yst.pqr['qr']) == 2
    assert 'mn' in yst.pqr['qr'][0]
    assert yst.pqr['qr'][0]['mn'] == 3
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('indel, outdel',
                         [(';', ','), (':', ';')])
def test_config_something_changed(capsys, indel, outdel):
    """Test ConfigSomething with changed values."""
    xst = ConfigSomething()
    xst.csv_dialect1['delimiter'] = indel
    xst.csv_dialect2['delimiter'] = outdel
    scfg = xst.as_json_string(stderr_file=sys.stderr)
    yst = ConfigSomething(from_json_text=scfg)
    assert yst.csv_dialect1['delimiter'] == indel
    assert yst.csv_dialect2['delimiter'] == outdel
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('mno_not_pqr, value',
                         [(True, {'tgur': 2, 'c300': 5}),
                          (False,
                           {'reset': [{'gh': EnumInTesting.FOOBAR,
                                       'ij': 'aa', 'mn': 5},
                                      {'gh': EnumInTesting.BARFOO,
                                       'ij': 'xx', 'mn': 1}],
                            'start': [{'gh': EnumInTesting.BARFOO,
                                       'ij': 'bb', 'mn': 30},
                                      {'gh': EnumInTesting.BARFOO,
                                       'ij': 'yy', 'mn': 7}]})])
def test_config_something_changed2(capsys, mno_not_pqr, value):
    """Test ConfigSomething with other changed values."""
    xst = ConfigSomething()
    if mno_not_pqr:
        xst.mno = value
    else:
        xst.pqr = value
    scfg = xst.as_json_string(stderr_file=sys.stderr)
    yst = ConfigSomething(from_json_text=scfg)
    out, err = capsys.readouterr()
    assert_dict_equal(xst.__dict__, yst.__dict__, ['_hook_cfg_autochange'],
                      stderr_file=sys.stderr)
    if mno_not_pqr:
        assert yst.mno == value
    else:
        assert yst.pqr == value
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('abc_not_pqr, value, exm',
                         [(True, [{'def': 15, 'geh': ';', 'x': 2,
                                   'ijk': EnumInTesting.BARFOO},
                                  {'def': 26, 'geh': 'x',
                                   'ij': EnumInTesting.FOOBAR}],
                           'non-allowed key "x"'),
                          (True, [{'def': 15,
                                   'ijk': EnumInTesting.BARFOO},
                                  {'def': 26, 'geh': 'x',
                                   'ij': EnumInTesting.FOOBAR}],
                           'Missing key "geh"'),
                          (False,
                           {'reset': [{'gh': EnumInTesting.FOOBAR,
                                       'ij': 'aa', 'mn': 5},
                                      {'gh': EnumInTesting.BARFOO,
                                       'ij': 'xx', 'mn': 1}],
                            'start': [{'gh': EnumInTesting.BARFOO,
                                       'ij': 'bb', 'mn': 30, 'ext': 4},
                                      {'gh': EnumInTesting.BARFOO,
                                       'ij': 'yy', 'mn': 7}]},
                           'non-allowed key "ext"'),
                          (False,
                           {'reset': [{'gh': EnumInTesting.FOOBAR,
                                       'ij': 'aa', 'mn': 5},
                                      {'gh': EnumInTesting.BARFOO,
                                       'ij': 'xx', 'mn': 1}],
                            'start': [{'gh': EnumInTesting.BARFOO,
                                       'ij': 'bb'},
                                      {'gh': EnumInTesting.BARFOO,
                                       'ij': 'yy', 'mn': 7}]},
                           'Missing key "mn"')])
def test_config_something_cha_bad(capsys, abc_not_pqr, value, exm):
    """Test ConfigSomething with bad changed values."""
    xst = ConfigSomething(stderr_file=sys.stderr)
    if abc_not_pqr:
        xst.abc = value
    else:
        xst.pqr = value
    scfg = xst.as_json_string(stderr_file=sys.stderr)
    with pytest.raises(SystemExit):
        _ = ConfigSomething(from_json_text=scfg, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert exm in err


@pytest.mark.parametrize('indel, outdel',
                         [(';', ','), (':', ';')])
def test_config_something_writeread(capsys, indel, outdel):
    """Test ConfigSomething writing and reading."""
    xst = ConfigSomething()
    xst.csv_dialect1['delimiter'] = indel
    xst.csv_dialect2['delimiter'] = outdel
    fname = None
    with ntf(delete=False) as tfile:
        fname = tfile.name
        tfile.close()
        xst.write(fname)
        yst = ConfigSomething()
        yst.read(fname)
    os_remove(fname)
    assert yst.csv_dialect1['delimiter'] == indel
    assert yst.csv_dialect2['delimiter'] == outdel
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('indel, outdel',
                         [(';', ','), (':', ';')])
def test_config_something_writeinit(capsys, indel, outdel):
    """Test ConfigSomething writing and reading."""
    xst = ConfigSomething()
    xst.csv_dialect1['delimiter'] = indel
    xst.csv_dialect2['delimiter'] = outdel
    fname = None
    with ntf(delete=False) as tfile:
        fname = tfile.name
        tfile.close()
        xst.write(fname)
        yst = ConfigSomething(from_json_filename=fname)
    os_remove(fname)
    assert yst.csv_dialect1['delimiter'] == indel
    assert yst.csv_dialect2['delimiter'] == outdel
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('txt,indel',
                         [('{"csv_dialect1" : {"delimiter" : "B"}}', 'B'),
                          ('{"csv_dialect1" : {"delimiter" : ":"}}', ':')])
def test_config_smt_read_incompl1(capsys, txt, indel):
    """Test ConfigSomething read incomplete 1."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    outdelold = yst.csv_dialect2['delimiter']
    indelold = yst.csv_dialect1['delimiter']
    yst.parse_json(txt, ok_to_use_defaults=True, stderr_file=sys.stderr)
    assert yst.csv_dialect1['delimiter'] == indel
    assert yst.csv_dialect2['delimiter'] == outdelold
    assert yst.csv_dialect1['delimiter'] != indelold
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('txt',
                         ['{"csv_dialect1": {"delimiter" : "B"}}',
                          '{"csv_dialect1": {"delimiter" : ";"}}'])
def test_config_smt_read_incompl2(capsys, txt):
    """Test ConfigSomething read incomplete 2."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    with pytest.raises(KeyError) as exc_info:
        yst.parse_json(txt, ok_to_use_defaults=False, stderr_file=sys.stderr)
    assert exc_info.type is KeyError
    out, err = capsys.readouterr()
    assert out == ''
    assert 'No value for' in err


def test_config_smt_read_nonexist(capsys):
    """Test ConfigSomething read non-existing."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    with pytest.raises(SystemExit) as exc_info:
        yst.read(from_json_filename='file-that-does-not-exist',
                 ok_to_use_defaults=True, stderr_file=sys.stderr)
    assert exc_info.type is SystemExit
    out, err = capsys.readouterr()
    assert out == ''
    assert 'File file-that-does-not-exist' in err
    assert 'with configuration JSON input does not exist' in err


def test_config_smt_read_uses_supplied_stderr_file(capsys):
    """Test that read() forwards a custom stderr stream to parse_json()."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    stderr_file = StringIO()
    filename = None
    with ntf(mode='w', delete=False, encoding='UTF-8') as tfile:
        filename = tfile.name
        tfile.write('not valid json')
    try:
        with pytest.raises(ConfigBadJson):
            yst.read(from_json_filename=filename, stderr_file=stderr_file)
    finally:
        assert filename is not None
        os_remove(filename)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert 'Config.parse_json failed to load JSON from string/file.' in \
        stderr_file.getvalue()


@pytest.mark.parametrize('txt',
                         ['{"csv_dialect1": {"delimiter" : "B"}}',
                          '{"csv_dialect1": {"delimiter" : ";"}}'])
def test_config_smt_init_incompl(capsys, txt):
    """Test ConfigSomething init incomplete."""
    with pytest.raises(KeyError) as exc_info:
        yst = ConfigSomething(from_json_text=txt, stderr_file=sys.stderr)
        assert yst.csv_dialect1['delimiter'] == ''
    assert exc_info.type is KeyError
    out, err = capsys.readouterr()
    assert out == ''
    assert 'No value for' in err


@pytest.mark.parametrize('txt',
                         ['{"csv_dialect1": {"delimiter2" : "B"}}',
                          '{"csv_dialec": {"delimiter" : ";"}}'])
def test_config_something_read_bad(capsys, txt):
    """Test ConfigSomething read bad."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    with pytest.raises(KeyError) as exc_info:
        yst.parse_json(txt, ok_to_use_defaults=True, stderr_file=sys.stderr)
    assert exc_info.type is KeyError
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Unexpected parameter' in err


@pytest.mark.parametrize('txt',
                         ['{"csv_dialect1": {"delimiter2" : "B"}}',
                          '{"csv_dialect2t": {"delimiter" : ";"}}'])
def test_config_something_read_bad2(capsys, txt):
    """Test ConfigSomething read bad 2."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    with pytest.raises(KeyError) as exc_info:
        yst.parse_json(txt, ok_to_use_defaults=True, stderr_file=sys.stderr)
    assert exc_info.type is KeyError
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Unexpected parameter' in err


@pytest.mark.parametrize('txt',
                         ['{"csv_dialect1"... {"delimiter2" : "B"}}',
                          'do you beleave in music'])
def test_config_something_read_bad3(capsys, txt):
    """Test ConfigSomething read bad 3."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    with pytest.raises(ConfigBadJson) as exc_info:
        yst.parse_json(txt, ok_to_use_defaults=True, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert exc_info.type is ConfigBadJson
    assert 'failed to load JSON' in str(exc_info)
    assert out == ''
    assert 'failed to load JSON' in err


@pytest.mark.parametrize('txt',
                         [b'\xff\xf8\x00\x00\x00\x00\x00\xff',
                          b'\xff'])
def test_config_something_read_bad4(capsys, txt):
    """Test ConfigSomething read bad 4."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    with pytest.raises(ConfigBadJson) as exc_info:
        yst.parse_json(txt, ok_to_use_defaults=True,
                       stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert exc_info.type is ConfigBadJson
    assert 'decode byte 0xff in position 0' in str(exc_info)
    assert out == ''
    assert 'decode byte 0xff in position 0' in err


@pytest.mark.parametrize('txt, errtxt',
                         [('{"csv_dialect1": "B"}', 'Not dictionary for'),
                          ('{"abc": {"delimiter" : ";"}}',
                           'Unexpected dictionary for')])
def test_config_smt_read_dict_mism(capsys, txt, errtxt):
    """Test ConfigSomething read dict mismatch."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    with pytest.raises(KeyError) as exc_info:
        yst.parse_json(txt, ok_to_use_defaults=True,
                       stderr_file=sys.stderr)
    assert exc_info.type is KeyError
    out, err = capsys.readouterr()
    assert out == ''
    assert errtxt in err


def test_config_something_csv_ok_1(capsys):
    """Test ConfigSomething csv OK 1."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    txt = """{"csv_dialect2": {"name": "csv.excel", "delimiter": "+",
    "quoting": null, "quotechar": "'",
    "lineterminator": null, "escapechar": null}}"""
    yst.parse_json(txt, ok_to_use_defaults=True, stderr_file=sys.stderr)
    dial = yst.get_csv_dialect2(stderr_file=sys.stderr)
    assert dial.delimiter == '+'
    assert dial.__module__ == 'csv'
    assert isinstance(dial, csv.excel)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


def test_config_something_csv_bad_1(capsys):
    """Test ConfigSomething csv bad 1."""
    yst = ConfigSomething(stderr_file=sys.stderr)
    txt = """{"csv_dialect2": {"name": "csv.excelent", "delimiter": "+",
    "quoting": null, "quotechar": "'",
    "lineterminator": null, "escapechar": null}}"""
    with pytest.raises(KeyError) as exc_info:
        yst.parse_json(txt, ok_to_use_defaults=True)
        dial = yst.get_csv_dialect2(stderr_file=sys.stderr)
        assert dial.delimiter == '+'
    assert exc_info.type is KeyError
    out, err = capsys.readouterr()
    assert out == ''
    assert "csv.excelent" in err
    assert "Unknown csv dialect" in err


def test_config_smt_csv_def(capsys):
    """Test ConfigSomething csv default."""
    yst = ConfigSomething()
    out = yst.get_csv_dialect2(stderr_file=sys.stderr)
    assert out.delimiter == ','
    inp = yst.get_csv_dialect1(stderr_file=sys.stderr)
    assert inp.delimiter == ','
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


def par_json_quote(var):
    """Quote parameter for JSON string."""
    if var is None:
        return 'null'
    return '"' + var + '"'


def csv_combinations_chcker(nam,   # pylint: disable=too-many-arguments, too-many-positional-arguments, line-too-long, too-many-branches, too-many-locals # noqa: E501
                            dlm, esc, quot, qchar, lterm, err):
    """Check test combinations of CSV configurations."""
    scfg = '{"csv_dialect2": {"name": ' + par_json_quote(nam)\
        + ', "delimiter": '\
        + par_json_quote(dlm) + ', "quoting": ' + par_json_quote(quot)\
        + ', "quotechar": ' + par_json_quote(qchar) + ', "lineterminator": '\
        + par_json_quote(lterm) + ', "escapechar": '\
        + par_json_quote(esc) + '}}'
    yst = ConfigSomething()
    if err:
        with pytest.raises(KeyError) as exc_info:
            yst.parse_json(scfg, ok_to_use_defaults=True)
            dial = yst.get_csv_dialect2(stderr_file=sys.stderr)
            assert dial.delimiter == dlm
        assert exc_info.type is KeyError
    else:
        yst.parse_json(scfg, ok_to_use_defaults=True)
        dial = yst.get_csv_dialect2(stderr_file=sys.stderr)
        if dlm is not None:
            assert dial.delimiter == dlm
        if esc is not None:
            assert dial.escapechar == esc
        if qchar is not None:
            assert dial.quotechar == qchar
        if lterm is not None:
            assert dial.lineterminator == lterm
        if lterm is None:
            assert dial.lineterminator in ('\n', '\r\n')
        if quot is not None:
            if quot == 'csv.quote_all':
                assert dial.quoting == csv.QUOTE_ALL
            if quot == 'csv.quote_minimal':
                assert dial.quoting == csv.QUOTE_MINIMAL
            if quot == 'csv.quote_none':
                assert dial.quoting == csv.QUOTE_NONE
            if quot == 'csv.quote_nonnumeric':
                assert dial.quoting == csv.QUOTE_NONNUMERIC
        if nam is not None:
            if nam == 'csv.excel':
                assert isinstance(dial, csv.excel)
            if nam == 'csv.excel_tab':
                assert isinstance(dial, csv.excel_tab)
            if nam == 'csv.unix_dialect':
                assert isinstance(dial, csv.unix_dialect)


@pytest.mark.parametrize('nam,er1', [('csv.excel', False),
                                     ('csv.excel_tab', False),
                                     ('csv.unix_dialect', False),
                                     ('csv.my_dialect', True)])
@pytest.mark.parametrize('dmt,er2', [(';', False), ('-', False),
                                     (None, False)])
@pytest.mark.parametrize('esc,er3', [('%', False), ('@', False),
                                     (None, False)])
@pytest.mark.parametrize('quo,er4', [(None, False),
                                     ('csv.quote_all', False),
                                     ('csv.quote_minimal', False),
                                     ('csv.quote_none', False),
                                     ('csv.quote_nonnumeric', False),
                                     ('csv.quote_some', True)])
@pytest.mark.parametrize('qch,er5', [(None, False), ('\'', False),
                                     ('|', False)])
@pytest.mark.parametrize('ltr,er6', [(None, False), ('end', False),
                                     ('>', False), (None, False)])
def test_config_smt_csv_comb_s(capsys,  # pylint: disable=too-many-arguments, too-many-positional-arguments, line-too-long, too-many-locals # noqa: E501
                               nam, dmt, esc, quo, qch,
                               ltr, er1, er2, er3, er4, er5,
                               er6):
    """Test combinations of CSV configurations thorough."""
    err = er1 or er2 or er3 or er4 or er5 or er6
    csv_combinations_chcker(nam, dmt, esc, quo, qch, ltr, err)
    out, err = capsys.readouterr()
    assert out == ''
    if err:
        assert err != ''
    else:
        assert err == ''


@pytest.mark.parametrize('nam,er1', [('csv.excel', False),
                                     ('csv.excel_tab', False),
                                     ('csv.unix_dialect', False),
                                     ('csv.my_dialect', True)])
@pytest.mark.parametrize('dmt,er2', [(';', False)])
@pytest.mark.parametrize('esc,er3', [('%', False)])
@pytest.mark.parametrize('quo,er4', [(None, False),
                                     ('csv.quote_all', False)])
@pytest.mark.parametrize('qch,er5', [(None, False)])
@pytest.mark.parametrize('ltr,er6', [('>', False), (None, False)])
def test_config_smt_csv_comb_f1(capsys,  # pylint: disable=too-many-arguments, too-many-positional-arguments, line-too-long, too-many-locals # noqa: E501
                                nam, dmt, esc, quo, qch,
                                ltr, er1, er2, er3, er4, er5,
                                er6):
    """Test combinations of CSV configurations f1."""
    err = er1 or er2 or er3 or er4 or er5 or er6
    csv_combinations_chcker(nam, dmt, esc, quo, qch, ltr, err)
    out, err = capsys.readouterr()
    assert out == ''
    if err:
        assert err != ''
    else:
        assert err == ''


@pytest.mark.parametrize('nam,er1', [('csv.excel', False)])
@pytest.mark.parametrize('dmt,er2', [(';', False)])
@pytest.mark.parametrize('esc,er3', [('%', False)])
@pytest.mark.parametrize('quo,er4', [(None, False)])
@pytest.mark.parametrize('qch,er5', [(None, False)])
@pytest.mark.parametrize('ltr,er6', [(None, False), ('end', False),
                                     ('>', False)])
def test_config_smt_csv_comb_f6(capsys,  # pylint: disable=too-many-arguments, too-many-positional-arguments, line-too-long, too-many-locals # noqa: E501
                                nam, dmt, esc, quo,
                                qch, ltr, er1, er2, er3,
                                er4, er5, er6):
    """Test combinations of CSV configurations f6."""
    err = er1 or er2 or er3 or er4 or er5 or er6
    csv_combinations_chcker(nam, dmt, esc, quo, qch, ltr, err)
    out, err = capsys.readouterr()
    assert out == ''
    if err:
        assert err != ''
    else:
        assert err == ''


class ConfigSomething2(Config):
    """Class to test Config."""

    def __init__(self, from_json_text=None, from_json_filename=None,
                 stderr_file: TextIO = sys.stderr):
        """Construct configuration for test."""
        self.in_type = EnumInTesting.FOOBAR
        super().__init__(from_json_text, from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


def test_config_something2_bad(capsys):
    """Test error handling no parsse_converters."""
    xst = ConfigSomething2()
    scfg = xst.as_json_string(stderr_file=sys.stderr)
    with pytest.raises(NotImplementedError) as exc:
        _ = ConfigSomething2(from_json_text=scfg, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Override of Config.parse_converters needed.' in str(exc)
    assert out == ''
    assert err == ''


class ConfigSomething3(Config):
    """Class to test Config."""

    def __init__(self, from_json_text=None, from_json_filename=None,
                 stderr_file: TextIO = sys.stderr):
        """Construct configuration for test."""
        self.in_type = EnumInTesting.FOOBAR
        super().__init__(from_json_text, from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self):
        """Use no parse converters."""
        return None

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


def test_config_something3_bad(capsys):
    """Test error handling no parsse_converters."""
    xst = ConfigSomething3(stderr_file=sys.stderr)
    scfg = xst.as_json_string(stderr_file=sys.stderr)
    yst = ConfigSomething3(from_json_text=scfg, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert xst.in_type != yst.in_type
    assert xst.in_type.name == cast(str, yst.in_type)
    assert out == ''
    assert err == ''


class ConfigSomething4(Config):
    """Class to test Config."""

    def __init__(self, from_json_text=None, from_json_filename=None,
                 stderr_file: TextIO = sys.stderr):
        """Construct configuration for test."""
        self.in_type = EnumInTesting.FOOBAR
        super().__init__(from_json_text, from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self):
        """Use no parse converters."""
        return {'in_type': self.get_converter_dict(EnumInTesting)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


def test_config_something4_ok(capsys):
    """Test error handling no parsse_converters."""
    xst = ConfigSomething4(stderr_file=sys.stderr)
    scfg = xst.as_json_string(stderr_file=sys.stderr)
    yst = ConfigSomething4(from_json_text=scfg, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert isinstance(xst.in_type, type(yst.in_type))
    assert xst.in_type == yst.in_type
    assert out == ''
    assert err == ''


class ConfigSomething5(Config):
    """Class to test Config."""

    def __init__(self, from_json_text=None, from_json_filename=None,
                 stderr_file: TextIO = sys.stderr):
        """Construct configuration for test."""
        self.in_type = EnumInTesting.FOOBAR
        self._unchecked_dicts = cast(Any, 'in_type')
        super().__init__(from_json_text, from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self):
        """Use no parse converters."""
        return {'in_type': self.get_converter_dict(EnumInTesting)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


def test_config_something5_bad(capsys):
    """Test error handling no parsse_converters."""
    with pytest.raises(TypeError) as exc:
        _ = ConfigSomething5(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '_unchecked_dicts must be a list' in str(exc)
    assert out == ''
    assert err == ''


class ConfigEmpty(Config):
    """Class to test Config."""

    def __init__(self, from_json_text=None, from_json_filename=None,
                 stderr_file: TextIO = sys.stderr):
        """Construct configuration for test."""
        self._unchecked_dictscfg = ['in_type']
        super().__init__(from_json_text, from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self):
        """Use no parse converters."""
        return None

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


def test_config_empty_bad(capsys):
    """Test error handling no parsse_converters."""
    with pytest.raises(AttributeError) as exc:
        _ = ConfigEmpty()
    out, err = capsys.readouterr()
    assert 'No object variables in object' in str(exc)
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('inp, totype, res',
                         [('aha', str, 'aha'),
                          (1, int, 1),
                          ('1', int, 1),
                          (1, str, '1')])
def test_value_of_type(capsys, inp, totype, res):
    """Test method value_of_type."""
    ret = Config.value_of_type(input_value=inp, to_type=totype)
    out, err = capsys.readouterr()
    assert isinstance(ret, totype)
    assert ret == res
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('arr, mand, allow',
                         [([], ['foo', 'bar'], ['baz']),
                          ([], ['foo', 'bar'], None),
                          ([{'foo': 1, 'bar': 2},
                            {'foo': 3, 'bar': 4, 'baz': 5}],
                           ['foo', 'bar'], ['baz']),
                          ([{'foo': 1, 'bar': 2},
                            {'foo': 3, 'bar': 4, 'baz': 5}],
                           [], ['foo', 'bar', 'baz']),
                          ([{'foo': 1, 'bar': 2},
                            {'foo': 3, 'bar': 4}],
                           ['foo', 'bar'], []),
                          ([{'foo': 1, 'bar': 2},
                            {'foo': 3, 'bar': 4}],
                           ['foo', 'bar'], None),
                          ([{'foo': 1, 'bar': 2},
                            {'foo': 3, 'bar': 4, 'baz': 5}],
                           ['foo', 'bar'], ['baz', 'xyz'])])
def test_check_array_keys_ok(capsys, arr, mand, allow):
    """Test ok cases for check_array_keys."""
    Config.check_array_keys(name_of_cfg='test_py', array=arr,
                            mandatory_keys=mand, allowed_keys=allow,
                            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('arr, mand, allow, msg',
                         [([{'foo': 1, 'bar': 2},
                            {'foo': 3, 'baz': 5}],
                           ['foo'], ['baz'],
                           'non-allowed key "bar"'),
                          ([{'foo': 1, 'bar': 2},
                            {'foo': 3, 'bar': 4, 'baz': 5}],
                           [], ['bar', 'baz'],
                           'non-allowed key "foo"'),
                          ([{'foo': 1, 'bar': 2, 'baz': 7},
                            {'bar': 4}],
                           ['foo', 'bar'], ['baz'],
                           'Missing key "foo"')])
def test_check_array_keys_nok(capsys, arr, mand, allow, msg):
    """Test not ok cases for check_array_keys."""
    with pytest.raises(SystemExit):
        Config.check_array_keys(name_of_cfg='test_py', array=arr,
                                mandatory_keys=mand, allowed_keys=allow,
                                stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert msg in err


@pytest.mark.parametrize('arr, kkey, ktype, tmplts',
                         [([], 'foo', EnumInTesting,
                           {EnumInTesting.FOOBAR: {'foo': EnumInTesting,
                                                   'a': str, 'b': int}}),
                          ([{'foo': EnumInTesting.BARFOO, 'c': 2, 'd': 4},
                            {'foo': EnumInTesting.FOOBAR, 'a': 'hej',
                             'b': 7}],
                           'foo', EnumInTesting,
                           {EnumInTesting.FOOBAR: {'foo': EnumInTesting,
                                                   'a': str, 'b': int},
                            EnumInTesting.BARFOO: {'foo': EnumInTesting,
                                                   'c': int, 'd': int}})
                          ])
def test_check_array_dicts_ok(capsys, arr, kkey, ktype, tmplts):
    """Test ok cases for check_array_dicts."""
    Config.check_array_dicts(name_of_cfg='test_py', array=arr, kind_key=kkey,
                             kind_type=ktype, dict_of_templates=tmplts,
                             stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('arr, kkey, ktype, tmplts, msg',
                         [([], 'foo', EnumInTesting,
                           {EnumInTesting.FOOBAR:  ['a', 'b']},
                           'template not dict of dicts'),
                          ([], 'foo', EnumInTesting,
                           [EnumInTesting.FOOBAR,  {'a': str, 'b': int}],
                           'template not dict of dicts'),
                          ([], 'foo', EnumInTesting,
                           {EnumInTesting.FOOBAR:  ['a', 'b']},
                           'in template for FOOBAR')])
def test_check_array_dicts_nok1(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments,line-too-long  # noqa: E501
                                arr, kkey, ktype, tmplts, msg):
    """Test not ok cases for check_array_dicts."""
    with pytest.raises(KeyError) as exc:
        Config.check_array_dicts(name_of_cfg='test_py', array=arr,
                                 kind_key=kkey, kind_type=ktype,
                                 dict_of_templates=tmplts,
                                 stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert msg in str(exc)
    assert out == ''
    assert msg in err


@pytest.mark.parametrize('arr, kkey, ktype, tmplts, msg',
                         [('arr', 'foo', EnumInTesting,
                           {EnumInTesting.FOOBAR:  {'a': str, 'b': int}},
                           'argument not list of dicts'),
                          ([{'foo': EnumInTesting.BARFOO, 'c': 2, 'd': 4},
                            ['foo', EnumInTesting.FOOBAR, 'a', 'hej',
                             'b', 7]],
                           'foo', EnumInTesting,
                           {EnumInTesting.FOOBAR: {'foo': EnumInTesting,
                                                   'a': str, 'b': int},
                            EnumInTesting.BARFOO: {'foo': EnumInTesting,
                                                   'c': int, 'd': int}},
                           'argument not list of dicts'),
                          ([{'foo': EnumInTesting.BARFOO, 'c': 2, 'd': 4},
                            {'a': 'hej', 'b': 7}],
                           'foo', EnumInTesting,
                           {EnumInTesting.FOOBAR: {'foo': EnumInTesting,
                                                   'a': str, 'b': int},
                            EnumInTesting.BARFOO: {'foo': EnumInTesting,
                                                   'c': int, 'd': int}},
                           'Key foo not in dict'),
                          ([{'foo': EnumInTesting.BARFOO, 'd': 4},
                            {'foo': EnumInTesting.FOOBAR, 'a': 'hej',
                             'b': 7}],
                           'foo', EnumInTesting,
                           {EnumInTesting.FOOBAR: {'foo': EnumInTesting,
                                                   'a': str, 'b': int},
                            EnumInTesting.BARFOO: {'foo': EnumInTesting,
                                                   'c': int, 'd': int}},
                           'Key c not in dict'),
                          ([{'foo': EnumInTesting.BARFOO, 'c': 2, 'd': 4},
                            {'foo': EnumInTesting.FOOBAR, 'a': 3,
                             'b': 7}],
                           'foo', EnumInTesting,
                           {EnumInTesting.FOOBAR: {'foo': EnumInTesting,
                                                   'a': str, 'b': int},
                            EnumInTesting.BARFOO: {'foo': EnumInTesting,
                                                   'c': int, 'd': int}},
                           'Value for key a = 3 is not str')
                          ])
def test_check_array_dicts_nok2(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments,line-too-long  # noqa: E501
                                arr, kkey, ktype, tmplts, msg):
    """Test not ok cases for check_array_dicts."""
    with pytest.raises(SystemExit):
        Config.check_array_dicts(name_of_cfg='test_py', array=arr,
                                 kind_key=kkey, kind_type=ktype,
                                 dict_of_templates=tmplts,
                                 stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert msg in err


@pytest.mark.parametrize('data,par',
                         [([1, 2, 3], 'test'),
                          ([1, 4, 3, 2], 'test')])
def test_check_no_dupl_ok(capsys, data, par):
    """Test check_no_duplicates for OK cases."""
    Config.check_no_duplicates(data, par, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('data,par',
                         [([1, 2, 3, 2], 'test'),
                          ([1, 2, 3, 1], 'test')])
def test_check_no_dupl_nok(capsys, data, par):
    """Test check:_no_cuplicates for OK cases."""
    with pytest.raises(SystemExit):
        Config.check_no_duplicates(data, par, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Duplicates not allowed in' in err
