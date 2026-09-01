#! /usr/local/bin/python3
"""Choose a configuration class by inspecting JSON input.

Applications that support multiple configuration schemas can register matcher
functions together with the corresponding ``Config`` subclasses. This module
then reads JSON from text or file input, selects the first matching schema,
and creates the appropriate configuration object.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from typing import Optional, NamedTuple, Sequence, Callable, TextIO, NoReturn
from json import loads as json_loads
from json import JSONDecodeError
import sys
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.file_must_exist import file_must_exist
from config_as_json.commontypes import PathOrStr, JsonType


class MatchConfig(NamedTuple):
    """Pair one JSON matcher with the configuration class it selects."""

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
"""Ordered collection of matcher/class pairs used by the config factory."""


def _config_factory_get_text(from_json_text: Optional[str],
                             from_json_filename: Optional[PathOrStr],
                             stderr_file: TextIO) -> str:
    """Return configuration JSON from exactly one supported input source.

    Args:
        from_json_text: Optional JSON text supplied directly by the caller.
        from_json_filename: Optional path to a file containing JSON text.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        The JSON text that should be inspected by the factory.

    Raises:
        RuntimeError: Neither or both input sources were supplied.
        SystemExit: The requested file input does not exist.
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
                    with_content_txt='configuration JSON input',
                    stderr_file=stderr_file)
    with open(from_json_filename, mode='r', encoding='UTF-8') as file:
        text = file.read()
        return text


def _config_factory_exit(msg: str,
                         exc: Optional[JSONDecodeError] |
                         Optional[UnicodeDecodeError],
                         stderr_file: TextIO) -> NoReturn:
    """Print a fatal factory error message and terminate the process.

    Args:
        msg: Main user-facing error message.
        exc: Optional decoding exception whose text should be appended.
        stderr_file: Stream used for diagnostics.
    """
    msg2 = '\nDid you specify an incorrect configuration file?\n'
    totmsg = msg + msg2 + ('' if exc is None else str(exc)) + '\n'
    print(totmsg, file=stderr_file)
    sys.exit(1)


class JsonValueMatcher:
    """Match a configuration schema by checking one JSON key/value pair."""

    def __init__(self, key: str, value: JsonType) -> None:
        """Store the key and reference value used by the matcher.

        Args:
            key: JSON object key that identifies the schema.
            value: Expected value at ``key`` for this schema.
        """
        self._key: str = key
        self._value: JsonType = value

    def __call__(self, json_text: str, stderr_file: TextIO) -> bool:
        """Return whether one JSON document matches this key/value rule.

        Args:
            json_text: JSON text to inspect.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            ``True`` when the document is a JSON object containing ``self``
            key with a matching value, otherwise ``False``.
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
        """Compare an observed JSON value with the expected reference value.

        Derived classes may override this class method to implement other
        matching strategies. The default implementation compares strings
        case-insensitively and all other JSON values with ``==``.

        Args:
            value_at_key: Value read from the JSON document.
            expected_value: Reference value configured on the matcher.

        Returns:
            ``True`` when the values should be considered equivalent.
        """
        if isinstance(value_at_key, str) and isinstance(expected_value, str):
            return value_at_key.lower() == expected_value.lower()
        return value_at_key == expected_value


# pylint: disable-next=too-many-arguments
def config_factory_from_json(match_configs: MatchConfigSeq,
                             auto_ch_hook: ConfigAutoChangeHook,
                             from_json_filename: Optional[PathOrStr] = None,
                             from_json_data_text: Optional[str] = None,
                             stderr_file: TextIO = sys.stderr, *,
                             member_name: Optional[str]) -> Config:
    """Create the first configuration class whose matcher accepts the input.

    The function is intended for applications that support several related
    configuration schemas and want to decide which ``Config`` subclass to use
    by inspecting the input document itself.

    Args:
        match_configs: Ordered matcher/class pairs. The first matcher that
            returns ``True`` selects the configuration class to instantiate.
        auto_ch_hook: Hook that should receive automatic-change callbacks from
            the selected configuration object.
        from_json_filename: Optional file containing configuration JSON.
        from_json_data_text: Optional configuration JSON supplied directly.
        stderr_file: Stream used for user-facing diagnostics.
        member_name: Dotted and indexed path for reaching the created object
            by traversing nested attributes from the top level of the
            complete construction, such as ``outputs[1].section``. ``None``
            means that the created object is the top level and not a member
            of anything.

    Returns:
        An instance of the selected ``Config`` subclass populated from the
        supplied JSON.

    Raises:
        RuntimeError: Neither or both JSON input sources were supplied.
        SystemExit: The JSON could not be decoded, no matcher accepted it, or
            a referenced input file does not exist.
    """
    text: str = _config_factory_get_text(from_json_text=from_json_data_text,
                                         from_json_filename=from_json_filename,
                                         stderr_file=stderr_file)
    for match_config in match_configs:
        if match_config.match_func(text, stderr_file):
            return match_config.config_class(from_json_data_text=text,
                                             from_json_filename=None,
                                             auto_ch_hook=auto_ch_hook,
                                             stderr_file=stderr_file,
                                             member_name=member_name)
    msg = 'No matching config class found'
    if member_name is not None:
        msg += f' for {member_name}'
    _config_factory_exit(msg=msg, exc=None, stderr_file=stderr_file)
