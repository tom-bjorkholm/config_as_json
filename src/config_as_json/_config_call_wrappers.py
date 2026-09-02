#! /usr/local/bin/python3
"""Call the overridable methods of a configuration on behalf of the library.

Every call the library itself makes to ``parse_json``, ``validate``,
``read`` or ``as_json_string`` on a :class:`Config` object, and every call it
makes to ``apply`` on a :class:`ValidationStep`, goes through this module. An
application calls those methods directly instead.

The reason for the detour is that ``member_name`` was added to all of them
after applications had already been written against the versions without it.
An override that does not accept ``member_name`` is called without it, and
warns that it should be changed. See
:func:`config_as_json._deprecated_support.use_member_name`.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO, TYPE_CHECKING
from config_as_json.commontypes import PathOrStr
from config_as_json._deprecated_support import use_member_name
from config_as_json.validator import ValidationStep


if TYPE_CHECKING:
    from config_as_json.config import Config


def wrap_parse_json(config: 'Config', from_json_text: str,
                    ok_to_use_defaults: bool = False,
                    stderr_file: TextIO = sys.stderr, *,
                    member_name: Optional[str] = None) -> None:
    """Call ``parse_json`` on one Config object.

    Args:
        config: Configuration object to parse the JSON text into.
        from_json_text: JSON document describing configuration values.
        ok_to_use_defaults: Whether missing declared keys may remain at their
            already assigned default values.
        stderr_file: Stream used for user-facing diagnostics. Defaults to
            ``sys.stderr``.
        member_name: Dotted and indexed path for reaching ``config`` by
            traversing nested attributes from the top level of the complete
            ``parse_json()`` operation, such as ``outputs[1].section``.
            ``None`` means that ``config`` is the top level and not a member
            of anything.
    """
    if use_member_name(config.parse_json, stacklevel=2):
        config.parse_json(from_json_text, ok_to_use_defaults,
                          stderr_file=stderr_file, member_name=member_name)
        return
    config.parse_json(from_json_text, ok_to_use_defaults,
                      stderr_file=stderr_file)


def wrap_validate(config: 'Config', stderr_file: TextIO, *,
                  member_name: Optional[str] = None) -> None:
    """Call ``validate`` on one Config object.

    Args:
        config: Configuration object to validate.
        stderr_file: Stream used for user-facing diagnostics.
        member_name: Dotted and indexed path for reaching ``config`` by
            traversing nested attributes from the top level of the complete
            ``validate()`` operation, such as ``outputs[1].section``.
            ``None`` means that ``config`` is the top level and not a member
            of anything.
    """
    if use_member_name(config.validate, stacklevel=2):
        config.validate(stderr_file=stderr_file, member_name=member_name)
        return
    config.validate(stderr_file=stderr_file)


def wrap_read(config: 'Config', from_json_filename: PathOrStr,
              ok_to_use_defaults: bool = False,
              stderr_file: TextIO = sys.stderr, *,
              member_name: Optional[str] = None) -> None:
    """Call ``read`` on one Config object.

    Args:
        config: Configuration object to read the JSON file into.
        from_json_filename: File containing configuration JSON.
        ok_to_use_defaults: Whether missing declared keys may remain at their
            already assigned default values.
        stderr_file: Stream used for user-facing diagnostics. Defaults to
            ``sys.stderr``.
        member_name: Dotted and indexed path for reaching ``config`` by
            traversing nested attributes from the top level of the complete
            ``read()`` operation, such as ``outputs[1].section``. ``None``
            means that ``config`` is the top level and not a member of
            anything.
    """
    if use_member_name(config.read, stacklevel=2):
        config.read(from_json_filename, ok_to_use_defaults,
                    stderr_file=stderr_file, member_name=member_name)
        return
    config.read(from_json_filename, ok_to_use_defaults,
                stderr_file=stderr_file)


def wrap_as_json_string(config: 'Config', stderr_file: TextIO, *,
                        member_name: Optional[str] = None) -> str:
    """Call ``as_json_string`` on one Config object.

    Args:
        config: Configuration object to serialize.
        stderr_file: Stream used for user-facing diagnostics during
            validation.
        member_name: Dotted and indexed path for reaching ``config`` by
            traversing nested attributes from the top level of the complete
            ``as_json_string()`` operation, such as ``outputs[1].section``.
            ``None`` means that ``config`` is the top level and not a member
            of anything.

    Returns:
        A JSON document containing every public, non-callable instance
        attribute on the configuration object.
    """
    if use_member_name(config.as_json_string, stacklevel=2):
        return config.as_json_string(stderr_file=stderr_file,
                                     member_name=member_name)
    return config.as_json_string(stderr_file=stderr_file)


def wrap_apply(validation_step: ValidationStep, config: 'Config',
               stderr_file: TextIO, *,
               member_name: Optional[str] = None) -> None:
    """Call ``apply`` on one validation step.

    Args:
        validation_step: Validation step to apply to ``config``.
        config: Configuration object to validate.
        stderr_file: Stream used for user-facing diagnostics.
        member_name: Dotted and indexed path for reaching ``config`` by
            traversing nested attributes from the top level of the complete
            ``validate()`` operation, such as ``outputs[1].section``.
            ``None`` means that ``config`` is the top level and not a member
            of anything.
    """
    if use_member_name(validation_step.apply, stacklevel=2):
        validation_step.apply(config, stderr_file, member_name=member_name)
        return
    validation_step.apply(config, stderr_file)
