#! /usr/local/bin/python3
"""Build CSV dialects from JSON-friendly configuration values."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import csv
from io import StringIO
import sys
from typing import Literal, NoReturn, Optional, TextIO, \
    TYPE_CHECKING, TypedDict
from config_as_json.validator import InvalidConfiguration, MemberValidator
if TYPE_CHECKING:
    from config_as_json.config import Config


class CsvDialectConfig(TypedDict, total=False):
    """Describe serialized ``csv.Dialect`` configuration values.

    The ``name`` key is required, and its value may not be ``None``.
    The remaining keys are optional when validated through
    :class:`CsvDialectValidator`; missing optional keys are
    treated as if they were present with value ``None``.

    Keys:
        name: Dialect template name, such as ``'csv.excel'``.
        delimiter: Optional field delimiter override.
        quoting: Optional quoting constant name, such as
            ``'csv.quote_minimal'``.
        quotechar: Optional quoting character override.
        lineterminator: Optional line terminator override.
        escapechar: Optional escape character override.
    """

    name: str
    delimiter: Optional[str]
    quoting: Optional[str]
    quotechar: Optional[str]
    lineterminator: Optional[str]
    escapechar: Optional[str]


_CSV_DIALECT_KEYS = ('name', 'delimiter', 'quoting', 'quotechar',
                     'lineterminator', 'escapechar')


def _csv_dialect_from_name(name: str, stderr_file: TextIO) -> csv.Dialect:
    """Return the CSV dialect template selected by ``name``."""
    if name.lower() == 'csv.excel':
        dialect: csv.Dialect = csv.excel()
        dialect.lineterminator = '\r\n'
        return dialect
    if name.lower() == 'csv.excel_tab':
        dialect = csv.excel_tab()
        dialect.lineterminator = '\r\n'
        return dialect
    if name.lower() == 'csv.unix_dialect':
        dialect = csv.unix_dialect()
        dialect.lineterminator = '\n'
        return dialect
    errmsg = f'Unknown csv dialect: {name}'
    print(errmsg, file=stderr_file)
    raise KeyError(errmsg)


def _csv_quoting_from_name(quoting: Optional[str],
                           stderr_file: TextIO) -> Literal[0, 1, 2, 3, 4, 5]:
    """Return the CSV quoting constant selected by ``quoting``."""
    if quoting is None:
        return csv.QUOTE_MINIMAL
    quoting_values: dict[str, Literal[0, 1, 2, 3, 4, 5]] = {
        'csv.quote_all': csv.QUOTE_ALL,
        'csv.quote_minimal': csv.QUOTE_MINIMAL,
        'csv.quote_none': csv.QUOTE_NONE,
        'csv.quote_nonnumeric': csv.QUOTE_NONNUMERIC}
    try:
        return quoting_values[quoting.lower()]
    except KeyError as exc:
        errmsg = f'Unknown csv quoting: {quoting}'
        print(errmsg, file=stderr_file)
        raise KeyError(errmsg) from exc


# pylint: disable=too-many-arguments
def get_csv_dialect(*, name: str, delimiter: Optional[str],
                    quoting: Optional[str], quotechar: Optional[str],
                    lineterminator: Optional[str], escapechar: Optional[str],
                    stderr_file: TextIO = sys.stderr) -> csv.Dialect:
    """Build a ``csv.Dialect`` from serialized configuration fields.

    Args:
        name: Name of a standard-library dialect template to start from.
        delimiter: Optional field delimiter override.
        quoting: Optional quoting constant name such as ``'csv.quote_all'``.
        quotechar: Optional quoting character override.
        lineterminator: Optional line terminator override.
        escapechar: Optional escape character override.
        stderr_file: Stream used for user-facing diagnostics. Defaults to
            ``sys.stderr``.

    Returns:
        A configured ``csv.Dialect`` instance.

    Raises:
        KeyError: ``name`` or ``quoting`` is not one of the supported
            serialized values.
    """
    dialect = _csv_dialect_from_name(name=name, stderr_file=stderr_file)
    if delimiter is not None:
        dialect.delimiter = delimiter
    dialect.quoting = _csv_quoting_from_name(quoting=quoting,
                                             stderr_file=stderr_file)
    if quotechar is None:
        dialect.quotechar = '"'
    else:
        dialect.quotechar = quotechar
    if lineterminator is not None:
        dialect.lineterminator = lineterminator
    if escapechar is None:
        dialect.escapechar = '\\'
    else:
        dialect.escapechar = escapechar
    return dialect


def _invalid_csv_dialect(member_name: str, message: str,
                         stderr_file: TextIO) -> NoReturn:
    """Raise ``InvalidConfiguration`` for one CSV dialect problem."""
    error_message = 'Invalid configuration: '
    error_message += f'Value for {member_name} is not a valid CSV dialect. '
    error_message += message
    print(error_message, file=stderr_file)
    raise InvalidConfiguration(error_message)


def _validate_csv_dialect_key(member_name: str, key: object,
                              stderr_file: TextIO) -> str:
    """Validate and return one key in a CSV dialect member."""
    if not isinstance(key, str):
        _invalid_csv_dialect(member_name=member_name,
                             message=f'Key {key!r} is not a string.',
                             stderr_file=stderr_file)
    if key not in _CSV_DIALECT_KEYS:
        _invalid_csv_dialect(member_name=member_name,
                             message=f'Unknown key {key!r}.',
                             stderr_file=stderr_file)
    return key


def _validate_csv_dialect_value(member_name: str, key: str, value: object,
                                stderr_file: TextIO) -> Optional[str]:
    """Validate and return one value in a CSV dialect member."""
    if value is None or isinstance(value, str):
        return value
    errmsg = f'Value for key {key!r} is not a string or None.'
    _invalid_csv_dialect(member_name=member_name, message=errmsg,
                         stderr_file=stderr_file)


def _normalized_csv_dialect_config(member_name: str, member_value: object,
                                   stderr_file: TextIO) -> CsvDialectConfig:
    """Validate and normalize one CSV dialect member."""
    if not isinstance(member_value, dict):
        _invalid_csv_dialect(member_name=member_name,
                             message='Expected a dict.',
                             stderr_file=stderr_file)
    normalized: dict[str, Optional[str]] = {'name': None}
    for key, value in member_value.items():
        checked_key = _validate_csv_dialect_key(member_name=member_name,
                                                key=key,
                                                stderr_file=stderr_file)
        normalized[checked_key] = _validate_csv_dialect_value(
            member_name=member_name, key=checked_key, value=value,
            stderr_file=stderr_file)
    if 'name' not in member_value:
        namemiss = "Required key 'name' is missing."
        _invalid_csv_dialect(member_name=member_name, message=namemiss,
                             stderr_file=stderr_file)
    assert 'name' in member_value
    if member_value['name'] is None:
        nameisnone = "Value for key 'name' is None."
        _invalid_csv_dialect(member_name=member_name, message=nameisnone,
                             stderr_file=stderr_file)
    assert member_value['name'] is not None
    name: str = member_value['name']
    return {'name': name,
            'delimiter': normalized.get('delimiter'),
            'quoting': normalized.get('quoting'),
            'quotechar': normalized.get('quotechar'),
            'lineterminator': normalized.get('lineterminator'),
            'escapechar': normalized.get('escapechar')}


# pylint: disable-next=too-few-public-methods
class CsvDialectValidator(MemberValidator):
    """Validate one CSV dialect configuration dictionary.

    The member value must be a ``dict[str, Optional[str]]``. No keys other
    than ``name``, ``delimiter``, ``quoting``, ``quotechar``,
    ``lineterminator``, and ``escapechar`` are allowed. The ``name`` key is
    mandatory. Missing optional keys are normalized to ``None`` in the value
    returned by ``validate_member``.

    After the dictionary shape has been checked, the validator calls
    :func:`get_csv_dialect` to verify that the values can actually create a
    ``csv.Dialect``. Any failure from that construction is reported as
    :class:`InvalidConfiguration`.
    """

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one CSV dialect member and return a normalized dict.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the member to validate.
            member_value: The member value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            A normalized ``CsvDialectConfig`` with all supported keys present.

        Raises:
            InvalidConfiguration: If the member is not a valid CSV dialect
                configuration dictionary.
        """
        _ = config
        normd = _normalized_csv_dialect_config(member_name=member_name,
                                               member_value=member_value,
                                               stderr_file=stderr_file)
        try:
            _ = get_csv_dialect(name=normd['name'],
                                delimiter=normd.get('delimiter'),
                                quoting=normd.get('quoting'),
                                quotechar=normd.get('quotechar'),
                                lineterminator=normd.get('lineterminator'),
                                escapechar=normd.get('escapechar'),
                                stderr_file=StringIO())
        except (KeyError, TypeError, ValueError, csv.Error) as exc:
            errmsg = f'Could not create csv.Dialect: {exc}'
            _invalid_csv_dialect(member_name=member_name, message=errmsg,
                                 stderr_file=stderr_file)
        return normd
