#! /usr/local/bin/python3
"""Define callbacks for automatic configuration adjustments.

Hooks let an application learn that configuration input needed help while it
was parsed, for example because a missing optional key received a default
value or because an old key name was transparently mapped to a new one.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy
import sys
from typing import Optional, TextIO


class ConfigAutoChangeHook():
    """Collect and report automatic configuration changes during parsing.

    Applications that want to react when configuration data is normalized
    should derive from this class and pass an instance to ``Config``.
    """

    def __init__(self, stderr_file: Optional[TextIO] = None) -> None:
        """Initialize empty change tracking state.

        Args:
            stderr_file: Stream used by hooks that emit diagnostics.
                Defaults to ``sys.stderr``.
        """
        if stderr_file is None:
            stderr_file = sys.stderr
        self._stderr_file: TextIO = stderr_file
        self.old_keys: list[str] = []
        self.def_val_keys: list[str] = []

    def __deepcopy__(self, memo: dict[int, object]) -> 'ConfigAutoChangeHook':
        """Copy hook state while preserving the configured stream object.

        Args:
            memo: Standard ``copy.deepcopy`` memo dictionary.

        Returns:
            A deep-copied hook instance with the same diagnostic stream.
        """
        copied = type(self).__new__(type(self))
        memo[id(self)] = copied
        copied.__dict__ = {}
        for key, value in self.__dict__.items():
            if key == '_stderr_file':
                copied.__dict__[key] = value
            else:
                copied.__dict__[key] = deepcopy(value, memo)
        return copied

    def auto_changed(self, old_keys_handled: list[str],
                     def_vals_handled: list[str]) -> None:
        """React after parsing finished with one or more automatic changes.

        Derived classes override this method to log, warn, or otherwise react
        when configuration input was normalized.

        Args:
            old_keys_handled: Legacy key names that were accepted and mapped
                onto their current names.
            def_vals_handled: Keys that were filled with default values during
                parsing.
        """

    def old_key_handled(self, old_key: str) -> None:
        """Record that one legacy key name was accepted and remapped.

        Args:
            old_key: Legacy key name that was handled.
        """
        self.old_keys.append(old_key)

    def default_value_provided(self, def_val_key: str) -> None:
        """Record that parsing supplied a default value for one key.

        Args:
            def_val_key: Key that was absent from input and received a default
                value instead.
        """
        self.def_val_keys.append(def_val_key)

    def all_autochanges_done(self) -> None:
        """Notify the hook once all automatic changes have been collected.

        The default implementation calls :meth:`auto_changed` once if at
        least one automatic change was recorded.
        """
        if self.old_keys or self.def_val_keys:
            self.auto_changed(old_keys_handled=deepcopy(self.old_keys),
                              def_vals_handled=deepcopy(self.def_val_keys))
