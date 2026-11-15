#! /usr/local/bin/python3
"""Decode the JSON text of one configuration object.

Decoding tells three problems apart, and raises each as its own subclass of
:class:`ConfigBadJson`: text that is not JSON, a root that is not a JSON
object, and a parse converter that refuses a value. A converter failure is
carried out of ``json.loads`` by a private exception, because ``json.loads``
would otherwise let it through looking like any other exception.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from typing import Callable, Optional, TextIO
from config_as_json.config_errors import ConfigBadJson, \
    ConfigConversionFailed, ConfigMustBeJson, ConfigRootNotDict


class _ConversionFailure(Exception):
    """Carry a parse converter failure out of ``json.loads``."""

    def __init__(self, key: str, error: Exception) -> None:
        """Initialize the exception.

        Args:
            key: Key whose value the converter refused.
            error: Exception that the converter raised.
        """
        super().__init__(key)
        self.key: str = key
        self.error: Exception = error


def converted_value(key: str, value: object, func: Callable[..., object],
                    args: dict[str, object]) -> object:
    """Return ``value`` converted by one parse converter.

    Args:
        key: Key whose value is converted.
        value: Decoded JSON value to convert.
        func: Conversion function of the parse converter.
        args: Extra keyword arguments for ``func``.

    Returns:
        The converted value.

    Raises:
        NotImplementedError: A required custom converter was not supplied.
        _ConversionFailure: The converter raised any other exception.
    """
    try:
        return func(value, **args)
    except NotImplementedError:
        raise
    except Exception as exc:
        raise _ConversionFailure(key, exc) from exc


def _load_failed_message(where: str, error: Exception,
                         stderr_file: TextIO) -> str:
    """Return and print the message that the JSON text failed to load.

    Args:
        where: Text naming the configuration object, or ``''``.
        error: Exception that made the load fail.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        The message.
    """
    msg = f'Config.parse_json{where} failed to load JSON from '
    msg += 'string/file.\n'
    msg += 'Probably incorrectly edited configuration,\n'
    msg += 'or using wrong file (not config file) as configuration.\n'
    msg += str(error)
    print(msg, file=stderr_file)
    return msg


def decoded_json_object(from_json_text: str,
                        hook: Optional[Callable[[dict[str, object]],
                                                dict[str, object]]],
                        stderr_file: TextIO, *,
                        member_name: Optional[str]) -> dict[str, object]:
    """Decode the JSON text and return its root object.

    Args:
        from_json_text: JSON document describing configuration values.
        hook: Object hook applying the parse converters, or ``None``.
        stderr_file: Stream used for user-facing diagnostics.
        member_name: Reported path of the configuration object whose text it
            is, ``None`` for the top level.

    Returns:
        The decoded JSON object.

    Raises:
        ConfigMustBeJson: The text is not valid JSON.
        ConfigConversionFailed: A parse converter refused a value.
        ConfigRootNotDict: The root of the text is not a dict.
        ConfigBadJson: Decoding failed in any other way.
        NotImplementedError: A required custom converter was not supplied.
    """
    where = '' if member_name is None else f' for {member_name}'
    try:
        data = json.loads(from_json_text, object_hook=hook)
    except NotImplementedError:
        raise
    except _ConversionFailure as failure:
        msg = _load_failed_message(where, failure.error, stderr_file)
        raise ConfigConversionFailed(msg, '', 0, converted_key=failure.key,
                                     member_name=member_name) \
            from failure.error
    except json.JSONDecodeError as exc:
        msg = _load_failed_message(where, exc, stderr_file)
        raise ConfigMustBeJson(msg, exc.doc, exc.pos,
                               member_name=member_name) from exc
    except Exception as exc:
        msg = _load_failed_message(where, exc, stderr_file)
        raise ConfigBadJson(msg, '', 0, member_name=member_name) from exc
    if not isinstance(data, dict):
        msg = f'Configuration JSON root{where} must be a JSON object.'
        print(msg, file=stderr_file)
        raise ConfigRootNotDict(msg, from_json_text, 0,
                                member_name=member_name)
    return data
