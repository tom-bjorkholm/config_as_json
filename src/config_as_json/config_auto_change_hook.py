#! /usr/local/bin/python3
"""Define callbacks for automatic configuration adjustments.

Hooks let an application learn that configuration input needed help while it
was parsed, for example because old-file compatibility renamed a key, moved a
path, removed an obsolete key, or supplied a missing current value.
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
        self.old_paths_moved: list[tuple[str, str]] = []

    def auto_changed(self, old_keys_handled: list[str],
                     rocf_vals_handled: list[str],
                     stderr_file: TextIO) -> None:
        """React after parsing finished with one or more automatic changes.

        Derived classes override this method to log, warn, or otherwise react
        when configuration input was normalized.

        Args:
            old_keys_handled: Old keys or paths that were accepted during
                Reading an Old Configuration File (ROCF), for example by
                mapping them onto current names, moving them to current paths,
                or removing keys no longer used. Moved paths are reported here
                as ``old.path -> new.path`` strings.
            rocf_vals_handled: Current paths that received values during
                Reading an Old Configuration File (ROCF) because old input did
                not contain them.
            stderr_file: Stream used for user-facing diagnostics.
        """

    def old_key_handled(self, old_key: str) -> None:
        """Record that one legacy key name was accepted and handled.

        Args:
            old_key: Legacy key name that was handled by renaming or removal.
        """
        self.old_keys.append(old_key)

    def rocf_missing_value_provided(self, rocf_val_key: str) -> None:
        """Record that parsing supplied a compatibility value for one key.

        Args:
            rocf_val_key: Key that was absent from input and received a value
                during Reading an Old Configuration File (ROCF).
        """
        self.rocf_val_keys.append(rocf_val_key)

    def old_path_moved(self, old_path: str, new_path: str) -> None:
        """Record that one old path was moved to a current path.

        Args:
            old_path: Actual old path that was accepted and removed.
            new_path: Actual current path that received the old value, or
                already had a current value that won.
        """
        self.old_paths_moved.append((old_path, new_path))
        self.old_key_handled(f'{old_path} -> {new_path}')

    def all_autochanges_done(self, stderr_file: TextIO) -> None:
        """Notify the hook once all automatic changes have been collected.

        The default implementation calls :meth:`auto_changed` once if at
        least one automatic change was recorded.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        if self.old_keys or self.rocf_val_keys or self.old_paths_moved:
            self.auto_changed(old_keys_handled=deepcopy(self.old_keys),
                              rocf_vals_handled=deepcopy(self.rocf_val_keys),
                              stderr_file=stderr_file)
