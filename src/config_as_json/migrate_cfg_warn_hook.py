#! /usr/local/bin/python3
"""Warn users when backward compatibility was needed during parsing."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from copy import deepcopy
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
        txt = '\nBackward compatibility was used to read configuration file.'
        txt += '\nThis version of the program understood the configuration,\n'
        txt += 'but newer versions of the program may not understand it.\n\n'
        txt += 'Use "migrate-cfg" sub-command to migrate configuration '
        txt += 'to new format.\n\n'
        return deepcopy(txt)  # copy to make sure original is not manipulated.

    def auto_changed(self, old_keys_handled: list[str],
                     def_vals_handled: list[str]) -> None:
        """Print the standard migration warning.

        Args:
            old_keys_handled: Legacy key names accepted during parsing.
            def_vals_handled: Keys that were filled with default values during
                parsing.
        """
        print(self.migrate_warn_msg(), file=sys.stderr, end='')
