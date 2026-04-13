#! /usr/local/bin/python3
"""Factory for creating config objects."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from typing import Optional, NamedTuple, Sequence, Callable, TextIO, NoReturn
from pathlib import Path
from json import loads as json_loads
from json import JSONDecodeError
import sys
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.file_must_exist import file_must_exist
from config_as_json.commontypes import PathOrStr, JsonType


class MatchConfig(NamedTuple):
    """Matching check of JSON text tied to a config class."""

    match_func: Callable[[str, TextIO], bool]
    """Function to check if JSON text matches the config class.

    Args:
        json_text: The JSON text to check.
        stderr_file: File to write error messages to.
    Returns:
        True if JSON text matches the config class, False otherwise.
    """

    config_class: type[Config]
    """Config class for the case that JSON text matches."""


type MatchConfigSeq = Sequence[MatchConfig]
"""Sequence of matching checks foe config class."""


def _config_factory_get_text(from_json_text: Optional[str],
                             from_json_filename: Optional[PathOrStr],
                             stderr_file: TextIO) -> str:
    """Get JSON text to use from file or string.

    Args:
        from_json_text: Optional string to read JSON from.
                        Either this or from_json_filename must be provided.
        from_json_filename: Optional file name to read JSON from.
                            Either this or from_json_text must be provided.
    Returns:
        The JSON text to use.
    """
    if from_json_filename is None and from_json_text is None:
        msg = 'Either JSON text or JSON file needed. Both cannot be None.'
        print(msg, file=stderr_file)
        raise RuntimeError(msg)
    if from_json_filename is not None and from_json_text is not None:
        msg = 'Either JSON text or JSON file needed. Both cannot be given.'
        print(msg, file=stderr_file)
        raise RuntimeError(msg)
    if from_json_text is not None:
        return from_json_text
    assert from_json_filename is not None
    file_must_exist(filename=from_json_filename,
                    with_content_txt='configuration JSON input')
    with open(from_json_filename, mode='r', encoding='UTF-8') as file:
        text = file.read()
        return text


def _config_factory_exit(msg: str,
                         exc: Optional[JSONDecodeError] |
                         Optional[UnicodeDecodeError],
                         stderr_file: TextIO) -> NoReturn:
    """Report config factory error and exit."""
    msg2 = '\nDid you specify an incorrect configuration file?\n'
    totmsg = msg + msg2 + ('' if exc is None else str(exc)) + '\n'
    print(totmsg, file=sys.stderr)
    sys.exit(1)


class JsonValueMatcher:
    """Matcher comparing JSON value for key."""

    def __init__(self, key: str, value: JsonType) -> None:
        """Initialize matcher.

        Args:
            key: The key to check.
            value: The value to check for in JSON data for key.
        """
        self._key: str = key
        self._value: JsonType = value

    def __call__(self, json_text: str, stderr_file: TextIO) -> bool:
        """Check if JSON text matches the matcher.

        Args:
            json_text: The JSON text to check.
            stderr_file: File to write error messages to.
        Returns:
            True if JSON text matches the matcher, False otherwise.
        """
        data: JsonType = None
        try:
            data = json_loads(json_text)
        except JSONDecodeError as exc:
            msg = 'Configuration JSON cannot be decoded.'
            _config_factory_exit(msg, exc, stderr_file)
        except UnicodeDecodeError as exc:
            msg = 'Invalid UTF-8 in configuration data.\n'
            _config_factory_exit(msg, exc, stderr_file)
        if data is None or not isinstance(data, dict):
            msg = 'JSON data is not valid configuration. Top level not dict'
            _config_factory_exit(msg, None, stderr_file)
        assert data is not None
        assert isinstance(data, dict)
        if self._key not in data:
            return False
        return self.compare_value(data[self._key], self._value)

    @classmethod
    def compare_value(cls, value_at_key: JsonType,
                      expected_value: JsonType) -> bool:
        """Compare value at key to expected value.

        Derived class may override this method to compare values in
        a different way. Default is to check strings case insensitively,
        and other types as using == operator."""
        if isinstance(value_at_key, str) and isinstance(expected_value, str):
            return value_at_key.lower() == expected_value.lower()
        return value_at_key == expected_value


def config_factory_from_json(match_configs: MatchConfigSeq,
                             auto_ch_hook: ConfigAutoChangeHook,
                             from_json_filename: Optional[PathOrStr] = None,
                             from_json_data_text: Optional[str] = None,
                             stderr_file: TextIO = sys.stderr) -> Config:
    """Create a config object from a JSON file or string.

    Reads JSON text from file or string and checks if it matches
    one of the match configurations. If it does, creates an instance
    of the corresponding config class.
    Args:
        match_configs: Sequence of matching checks for config classes.
                       The in the sequence where the match_func returns True
                       is the config class to use.
        auto_ch_hook: Hook to let application know about automatic changes
                      applied when reading the configuration.
        from_json_filename: Optional file name to read JSON from.
                            Either this or from_json_data_text must be provided.
        from_json_data_text: Optional string to read JSON from.
                            Either this or from_json_filename must be provided.
        stderr_file: File to write error messages to.
    Raises:
        RuntimeError: If the JSON text cannot be read or parsed.
    Returns:
        An object of the config class that matches the JSON text, initialized
        from the JSON text. The returned object is of a derived class of
        Config.
    """
    text: str = _config_factory_get_text(from_json_text=from_json_data_text,
                                        from_json_filename=from_json_filename,
                                        stderr_file=stderr_file)
    for match_config in match_configs:
        if match_config.match_func(text, stderr_file):
            return match_config.config_class(from_json_data_text=text,
                                             from_json_filename=None,
                                             auto_ch_hook=auto_ch_hook,
                                             stderr_file=stderr_file)
    _config_factory_exit(msg='No matching config class found',
                         exc=None,
                         stderr_file=stderr_file)
  