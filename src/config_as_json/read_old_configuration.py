#! /usr/local/bin/python3
"""Describe how old configuration JSON data is normalized."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from typing import NamedTuple, TextIO
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.commontypes import JsonType


class RocfKeyMove(NamedTuple):
    """Describe a key move from an old structure to a new structure.

    A key move copies one value from an old absolute path in the root JSON
    object to a new absolute path in the current JSON structure. The path
    elements are JSON object keys. List indexes are intentionally not part of
    this first contract.

    During processing, an implementation should create missing intermediate
    dictionaries in the new path. If an intermediate value already exists and
    is not a JSON object, processing should fail with a clear error.

    If both old and new values exist, the current-shape value should win. The
    old value should be discarded and a diagnostic should be written through
    the ``stderr_file`` supplied to :meth:`ReadOldConfiguration.process_json`.

    Attributes:
        old_path: Absolute path to the old value in the root JSON object.
        new_path: Absolute path where the value belongs in the current JSON
            object.
    """

    old_path: tuple[str, ...]
    new_path: tuple[str, ...]


RocfKeyRename = NamedTuple('RocfKeyRename', [('old', str), ('new', str)])
"""Describe a configuration key rename from an old name to a new name.

Renaming rule for Reading Old Configuration File (ROCF). Used by derived
classes to describe key names in old configuration files that should be
mapped onto their current names during parsing.
"""


class ReadOldConfiguration:
    """Normalize possibly old configuration JSON data.

    ``Config.parse_json()`` should decode JSON text first. It should then use
    a ``ReadOldConfiguration`` object to turn the parsed root JSON object into
    current-schema JSON data. The rest of ``Config`` should only need to check
    and apply the current schema.

    Application-specific subclasses should normally override only the
    declarative methods:

    - :meth:`get_keys_to_remove`
    - :meth:`get_json_key_renames`
    - :meth:`get_json_key_moves`
    - :meth:`get_values_for_missing_json_keys`

    Unusual migrations can override :meth:`pre_process_json` or
    :meth:`post_process_json`.
    """

    def process_json(self, json_data: dict[str, JsonType],
                     auto_ch_hook: ConfigAutoChangeHook,
                     stderr_file: TextIO) -> dict[str, JsonType]:
        """Return current-schema JSON data from possibly old JSON data.

        Args:
            json_data: Parsed root JSON object to normalize.
            auto_ch_hook: Hook that records automatic compatibility changes.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            JSON data matching the current configuration schema.

        The intended default processing order is:

        1. :meth:`pre_process_json`
        2. remove keys from :meth:`get_keys_to_remove`
        3. rename keys from :meth:`get_json_key_renames`
        4. move paths from :meth:`get_json_key_moves`
        5. add values from :meth:`get_values_for_missing_json_keys`
        6. :meth:`post_process_json`

        Missing values are intentionally applied after renames and moves so
        old values get a chance to populate the current shape before defaults
        are supplied.
        """
        _ = json_data, auto_ch_hook, stderr_file
        raise NotImplementedError

    def get_json_key_moves(self) -> list[RocfKeyMove]:
        """Return key moves from old paths to current paths.

        Derived classes override this method when an old configuration value
        must move into a different JSON object structure in the current
        schema.

        Returns:
            Key moves to apply while reading old configuration files.
        """
        return []

    def get_keys_to_remove(self) -> list[str]:
        """Return old JSON keys to remove while reading old files.

        When Reading an Old Configuration File (ROCF), the old configuration
        version in the file might have keys that no longer exist in the
        current configuration. This method returns those old key names.
        Derived classes should override this method as needed.

        Returns:
            A list of old keys that should be removed from the JSON input.
        """
        return []

    def get_values_for_missing_json_keys(self) -> dict[str, JsonType]:
        """Return values for missing JSON keys.

        When Reading an Old Configuration File (ROCF), some now existing
        and mandatory keys may be missing in the JSON input from the
        old configuration file. This method returns the values that should
        be supplied for these missing keys.
        Derived classes should override this method as needed.

        Returns:
            A mapping from missing key name to the value that should
            be supplied when the key is absent from JSON input.
        """
        return {}

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return configuration key renames for Reading Old Configuration File.

        Derived classes override this method to describe key names
        in old configuration files that should be mapped onto their current
        names during parsing of an old configuration file.

        Returns:
            A list of ``RocfKeyRename`` entries describing accepted key
            renames.
        """
        return []

    def pre_process_json(self, json_data: dict[str, JsonType],
                         auto_ch_hook: ConfigAutoChangeHook,
                         stderr_file: TextIO) -> dict[str, JsonType]:
        """Pre-process JSON data before declarative old-file handling.

        Derived classes override this method only for migrations that cannot
        be expressed with removals, renames, moves or missing values.

        Args:
            json_data: Parsed root JSON object to normalize.
            auto_ch_hook: Hook that records automatic compatibility changes.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            JSON data to pass to the declarative old-file processing steps.
        """
        _ = auto_ch_hook, stderr_file
        return json_data

    def post_process_json(self, json_data: dict[str, JsonType],
                          auto_ch_hook: ConfigAutoChangeHook,
                          stderr_file: TextIO) -> dict[str, JsonType]:
        """Post-process JSON data after declarative old-file handling.

        Derived classes override this method only for migrations that need to
        inspect or adjust the result of the declarative old-file processing.

        Args:
            json_data: Current-shape JSON data after declarative processing.
            auto_ch_hook: Hook that records automatic compatibility changes.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            JSON data matching the current configuration schema.
        """
        _ = auto_ch_hook, stderr_file
        return json_data
