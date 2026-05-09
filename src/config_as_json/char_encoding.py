#! /usr/local/bin/python3
"""Validate text encoding names used by configuration values."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from tempfile import TemporaryFile
from typing import Optional, TextIO, TYPE_CHECKING
from config_as_json.validator import InvalidConfiguration, MemberValidator
if TYPE_CHECKING:
    from config_as_json.config import Config


def valid_char_encoding(enc: str) -> bool:
    """Return whether ``enc`` names a valid text encoding.

    Args:
        enc: Encoding name to test.

    Returns:
        ``True`` when Python recognizes ``enc`` as a text encoding, otherwise
        ``False``.
    """
    try:
        with TemporaryFile(mode='w', encoding=enc) as _:
            pass
    except LookupError as exc:
        if 'unknown encoding' in str(exc):
            return False
        raise exc  # pragma: no cover
    return True


def check_char_encoding(enc: str, stderr_file: TextIO = sys.stderr) -> None:
    """Fail fast when a named character encoding is not recognized.

    Args:
        enc: Encoding name to validate.
        stderr_file: Stream used for user-facing diagnostics. Defaults to
            ``sys.stderr``.

    Raises:
        SystemExit: ``enc`` is not a recognized text encoding.
    """
    if not valid_char_encoding(enc=enc):
        print(f'{enc} is not a recognized encoding', file=stderr_file)
        sys.exit(1)


# pylint: disable-next=too-few-public-methods
class CharEncodingValidator(MemberValidator):
    """Validate that one string member names a recognized text encoding."""

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one character encoding member.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the member to validate.
            member_value: The member value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            The original encoding string.

        Raises:
            InvalidConfiguration: If the member value is not a string or does
                not name a recognized text encoding.
        """
        _ = config
        if not isinstance(member_value, str):
            msg = 'Invalid configuration: '
            msg += f'Value for {member_name} is not a string.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        if valid_char_encoding(member_value):
            return member_value
        msg = 'Invalid configuration: '
        msg += f'{member_value} is not a recognized character encoding for '
        msg += f'{member_name}.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)
