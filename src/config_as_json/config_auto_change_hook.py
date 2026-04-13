#! /usr/local/bin/python3
"""Base class for configuration auto change hooks."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy


class ConfigAutoChangeHook():
    """Hook to let application know if config was automatically changed.

    Application that wants this kind of information should derive from this
    class and register derived class as hook in Config.
    """

    def __init__(self) -> None:
        """Construct a ConfigAutoChangeHook object."""
        self.old_keys: list[str] = []
        self.def_val_keys: list[str] = []

    def auto_changed(self, old_keys_handled: list[str],
                     def_vals_handled: list[str]) -> None:
        """Let application know about changes.

        Called by parser at end of JSON parsing.
        Intended to be overriden in derived class interested in changes.
        @param old_keys_handled  The old key names read into configuration.
        @param def_vals_handled  The keys given default values.
        """

    def old_key_handled(self, old_key: str) -> None:
        """Record that an old keyword was handled.

        Called by parser whenever an old keyword is changed.
        Derived class may override this, but it is usually better
        to override auto_changed method.
        """
        self.old_keys.append(old_key)

    def default_value_provided(self, def_val_key: str) -> None:
        """Record that a default value was provided for keyword.

        Called by parser whenever a default value is provided to a key.
        Derived class may override this, but it is usually better
        to override auto_changed method.
        """
        self.def_val_keys.append(def_val_key)

    def all_autochanges_done(self) -> None:
        """Inform application if automatic changes were done.

        Called by parser when all automatic changes to JSON are done.
        Do NOT override this in derived class.
        Instead do override auto_changed.
        """
        if self.old_keys or self.def_val_keys:
            self.auto_changed(old_keys_handled=deepcopy(self.old_keys),
                              def_vals_handled=deepcopy(self.def_val_keys))
