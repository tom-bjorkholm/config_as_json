#! /usr/local/bin/python3
"""Define callbacks for automatic configuration adjustments.

Hooks let an application learn that configuration input needed help while it
was parsed, for example because a missing optional key received a default
value or because an old key name was transparently mapped to a new one.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import TextIO


class ConfigAutoChangeHook():
    """Collect and report automatic configuration changes during parsing.

    Applications that want to react when configuration data is normalized
    should derive from this class and pass an instance to ``Config``.
    """

    def __init__(self) -> None:
        """Initialize empty change tracking state."""
        self.old_keys: list[str] = []
        self.rocf_val_keys: list[str] = []

    def auto_changed(self, old_keys_handled: list[str],
                     rocf_vals_handled: list[str],
                     stderr_file: TextIO) -> None:
        """React after parsing finished with one or more automatic changes.

        Derived classes override this method to log, warn, or otherwise react
        when configuration input was normalized.

        Args:
            old_keys_handled: Old key names that were accepted during Reading
                an Old Configuration File (ROCF), for example by mapping them
                onto current names or by removing keys no longer used.
            rocf_vals_handled: Keys that were filled with default values during
                parsing during Reading an Old Configuration File (ROCF).
            stderr_file: Stream used for user-facing diagnostics.
        """

    def old_key_handled(self, old_key: str) -> None:
        """Record that one legacy key name was accepted and handled.

        Args:
            old_key: Legacy key name that was handled by renaming or removal.
        """
        self.old_keys.append(old_key)

    def rocf_missing_value_provided(self, rocf_val_key: str) -> None:
        """Record that parsing supplied a default value for one key.

        Args:
            rocf_val_key: Key that was absent from input and received a default
                value during Reading an Old Configuration File (ROCF).
        """
        self.rocf_val_keys.append(rocf_val_key)

    def all_autochanges_done(self, stderr_file: TextIO) -> None:
        """Notify the hook once all automatic changes have been collected.

        The default implementation calls :meth:`auto_changed` once if at
        least one automatic change was recorded.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        if self.old_keys or self.rocf_val_keys:
            self.auto_changed(old_keys_handled=deepcopy(self.old_keys),
                              rocf_vals_handled=deepcopy(self.rocf_val_keys),
                              stderr_file=stderr_file)
