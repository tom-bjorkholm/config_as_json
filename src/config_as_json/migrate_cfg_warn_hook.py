#! /usr/local/bin/python3
"""Class that warns user to migrate configuration file."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License

import sys
from copy import deepcopy
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook


class MigrateCfgWarnHook(ConfigAutoChangeHook):
    """Class that warns user to migrate configuration file."""

    @staticmethod
    def migrate_warn_msg() -> str:
        """Get message warning user suggesting migrating config."""
        txt = '\nBackward compatibility was used to read configuration file.'
        txt += '\nThis version of the program understood the configuration,\n'
        txt += 'but newer versions of the program may not understand it.\n\n'
        txt += 'Use "migrate-cfg" sub-command to migrate configuration '
        txt += 'to new format.\n\n'
        return deepcopy(txt)  # copy to make sure original is not manipulated.

    def auto_changed(self, old_keys_handled: list[str],
                     def_vals_handled: list[str]) -> None:
        """Warn user to migrate configuration.

        Override of base class method.
        Automatic changes have been made, this means configuration file is old.
        """
        print(self.migrate_warn_msg(), file=sys.stderr, end='')
