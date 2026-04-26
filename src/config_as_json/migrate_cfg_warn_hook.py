#! /usr/local/bin/python3
"""Warn users when backward compatibility was needed during parsing."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import TextIO
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook


class MigrateCfgWarnHook(ConfigAutoChangeHook):
    """Emit a migration warning when automatic compatibility changes occur."""

    @staticmethod
    def migrate_warn_msg() -> str:
        """Return the standard warning shown for old configuration files.

        Returns:
            Warning text encouraging the user to migrate the configuration to
            the newest supported format.
        """
        txt = '\nBackward compatibility was used to read a configuration '
        txt += 'file.'
        txt += '\nThe file was accepted, but a future version may remove '
        txt += 'this compatibility path.\n\n'
        txt += 'Use config_as_json.migrate_cfg, or the migration command '
        txt += 'provided by your application,\n'
        txt += 'to write the file in the current format.\n\n'
        return deepcopy(txt)  # copy to make sure original is not manipulated.

    def auto_changed(self, old_keys_handled: list[str],
                     def_vals_handled: list[str],
                     stderr_file: TextIO) -> None:
        """Print the standard migration warning.

        Args:
            old_keys_handled: Legacy key names accepted during parsing.
            def_vals_handled: Keys that were filled with default values during
                parsing.
            stderr_file: Stream used for user-facing diagnostics.
        """
        print(self.migrate_warn_msg(), file=stderr_file, end='')
