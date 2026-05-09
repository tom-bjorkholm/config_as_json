#! /usr/local/bin/python3
"""Test CSV dialect helpers and validators."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import csv
import sys
from typing import Optional, cast
import pytest
from pytest import CaptureFixture
from config_as_json.config import Config
from config_as_json.csv_dialect import CsvDialectConfig, \
    CsvDialectValidator, get_csv_dialect
from config_as_json.validator import InvalidConfiguration


def _csv_config(**overrides: Optional[str]) -> CsvDialectConfig:
    """Return a complete CSV dialect configuration dictionary."""
    values: dict[str, Optional[str]] = {
        'name': 'csv.excel',
        'delimiter': ',',
        'quoting': None,
        'quotechar': '"',
        'lineterminator': None,
        'escapechar': None
    }
    values.update(overrides)
    name: str = values['name'] if values['name'] is not None else 'csv.excel'
    return {
        'name': name,
        'delimiter': values['delimiter'],
        'quoting': values['quoting'],
        'quotechar': values['quotechar'],
        'lineterminator': values['lineterminator'],
        'escapechar': values['escapechar']
    }


def _validate_csv_dialect(member_value: object) -> object:
    """Validate ``member_value`` with ``CsvDialectValidator``."""
    return CsvDialectValidator().validate_member(config=cast(Config, object()),
                                                 member_name='csv_settings',
                                                 member_value=member_value,
                                                 stderr_file=sys.stderr)


def test_csv_dialect_defaults(capsys: CaptureFixture[str]) -> None:
    """Test get_csv_dialect with default values."""
    dialect = get_csv_dialect(name='csv.excel', delimiter=None, quoting=None,
                              quotechar=None, lineterminator=None,
                              escapechar=None, stderr_file=sys.stderr)
    assert isinstance(dialect, csv.excel)
    assert dialect.delimiter == ','
    assert dialect.quoting == csv.QUOTE_MINIMAL
    assert dialect.quotechar == '"'
    assert dialect.lineterminator == '\r\n'
    assert dialect.escapechar == '\\'
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('name, expected_type, expected_lineterminator',
                         [('csv.excel', csv.excel, '\r\n'),
                          ('CSV.EXCEL_TAB', csv.excel_tab, '\r\n'),
                          ('csv.unix_dialect', csv.unix_dialect, '\n')])
def test_get_csv_dialect_standard(
        capsys: CaptureFixture[str], name: str, expected_type: type[object],
        expected_lineterminator: str) -> None:
    """Test all supported standard-library dialect names."""
    dialect = get_csv_dialect(name=name, delimiter=';', quoting=None,
                              quotechar='|', lineterminator=None,
                              escapechar='@', stderr_file=sys.stderr)
    assert isinstance(dialect, expected_type)
    assert dialect.delimiter == ';'
    assert dialect.quotechar == '|'
    assert dialect.lineterminator == expected_lineterminator
    assert dialect.escapechar == '@'
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('quoting, expected_quoting',
                         [('csv.quote_all', csv.QUOTE_ALL),
                          ('csv.quote_minimal', csv.QUOTE_MINIMAL),
                          ('csv.quote_none', csv.QUOTE_NONE),
                          ('csv.quote_nonnumeric', csv.QUOTE_NONNUMERIC)])
def test_csv_dialect_quoting(capsys: CaptureFixture[str], quoting: str,
                             expected_quoting: int) -> None:
    """Test all supported serialized quoting names."""
    dialect = get_csv_dialect(name='csv.excel', delimiter=None,
                              quoting=quoting, quotechar=None,
                              lineterminator='end', escapechar=None,
                              stderr_file=sys.stderr)
    assert dialect.quoting == expected_quoting
    assert dialect.lineterminator == 'end'
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('kwargs, error_text',
                         [({
                             'name': 'csv.missing',
                             'quoting': None
                         }, 'Unknown csv dialect: csv.missing'),
                          ({
                              'name': 'csv.excel',
                              'quoting': 'csv.quote_sometimes'
                          }, 'Unknown csv quoting: csv.quote_sometimes')])
def test_csv_dialect_bad_names(capsys: CaptureFixture[str],
                               kwargs: dict[str, Optional[str]],
                               error_text: str) -> None:
    """Test direct helper errors for unsupported serialized names."""
    with pytest.raises(KeyError) as exc_info:
        _ = get_csv_dialect(name=cast(str, kwargs['name']), delimiter=None,
                            quoting=kwargs['quoting'], quotechar=None,
                            lineterminator=None, escapechar=None,
                            stderr_file=sys.stderr)
    assert error_text in str(exc_info.value)
    out, err = capsys.readouterr()
    assert out == ''
    assert error_text in err


def test_csv_validator_full(capsys: CaptureFixture[str]) -> None:
    """Test CsvDialectValidator with all keys present."""
    ret = _validate_csv_dialect(_csv_config(quoting='csv.quote_all'))
    assert ret == _csv_config(quoting='csv.quote_all')
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


def test_csv_validator_missing_keys(capsys: CaptureFixture[str]) -> None:
    """Test CsvDialectValidator fills missing optional keys with None."""
    ret = _validate_csv_dialect({'name': 'csv.excel_tab'})
    assert ret == _csv_config(name='csv.excel_tab', delimiter=None,
                              quotechar=None)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


def test_csv_validator_none_name(capsys: CaptureFixture[str]) -> None:
    """Test CsvDialectValidator accepts None as the required name value."""
    with pytest.raises(InvalidConfiguration):
        _ = _validate_csv_dialect({'name': None})
    out, err = capsys.readouterr()
    assert out == ''
    assert "Value for key 'name' is None." in err
    assert "Invalid configuration: Value for csv_settings" in err


@pytest.mark.parametrize(
    'member_value, error_text',
    [([], 'Expected a dict.'),
     ({'delimiter': ','}, "Required key 'name' is missing."),
     ({'name': 'csv.excel', 'extra': None}, "Unknown key 'extra'."),
     ({1: None, 'name': 'csv.excel'}, 'Key 1 is not a string.'),
     ({'name': 'csv.excel', 'delimiter': 1},
      "Value for key 'delimiter' is not a string or None."),
     ({'name': 'csv.missing'}, 'Unknown csv dialect: csv.missing'),
     ({'name': 'csv.excel', 'quoting': 'csv.quote_sometimes'},
      'Unknown csv quoting: csv.quote_sometimes')])
def test_csv_validator_bad_config(capsys: CaptureFixture[str],
                                  member_value: object,
                                  error_text: str) -> None:
    """Test CsvDialectValidator reports invalid members clearly."""
    with pytest.raises(InvalidConfiguration) as exc_info:
        _ = _validate_csv_dialect(member_value)
    assert error_text in str(exc_info.value)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Invalid configuration: Value for csv_settings' in err
    assert error_text in err
