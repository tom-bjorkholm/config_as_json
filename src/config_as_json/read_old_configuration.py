#! /usr/local/bin/python3
"""Describe contracts for normalizing old configuration data."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from typing import NamedTuple, TextIO
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.validator import InvalidConfiguration


type RocfPath = tuple[str, ...]
"""A path in the old or new configuration data object.

RocfPath values are absolute paths from the root configuration data object.
Path elements are dictionary keys unless they use reserved list syntax.

The path element ``'['`` means "each list element". Any path element that
starts with ``'['`` but is not exactly ``'['`` is reserved for future list
syntax and is illegal in this version. A dictionary key that starts with
``'['`` cannot be handled by declarative ROCF methods; use
:meth:`ReadOldConfiguration.pre_process_json` or
:meth:`ReadOldConfiguration.post_process_json` instead.

Declarative ROCF methods require non-empty paths.

The data addressed by a RocfPath has already been decoded from JSON.
Depending on the ``Config`` parse flow, scalar leaf values may also have
been converted by ``parse_converters()`` before ROCF processing sees them.
Migration rules should treat leaf values as opaque and reason only about
dictionary and list containers.
"""


class RocfKeyMove(NamedTuple):
    """Describe a key move from an old structure to a new structure.

    A key move copies a value from an old :class:`RocfPath` to a new
    :class:`RocfPath`.

    Empty paths are illegal. ``old_path`` and ``new_path`` must not be equal.

    An old path that is missing is a no-op, because the input may already use
    the current schema. If old-path traversal reaches a value with the wrong
    container type, that is also a no-op. Current-schema parsing later decides
    whether that data is valid.

    If new-path traversal needs an intermediate dictionary or list and an
    incompatible value already exists, processing should fail with
    :class:`RocfIncompatiblePathError`.

    If both the old value and the current-shape target value exist, the
    current-shape value wins. The old value should be discarded, a diagnostic
    should be written through the ``stderr_file`` supplied to
    :meth:`ReadOldConfiguration.process_json`, and the handled old path should
    be reported to the automatic-change hook.

    List handling is intentionally narrow:

    - A path without ``'['`` uses only dictionary traversal.
    - If old and new paths contain the same number of ``'['`` elements, list
      elements are paired by index. This covers renaming a key in every
      element of a list.
    - If the new path contains one ``'['`` and the old path contains none, the
      old value is wrapped into a single-element list when the current list is
      absent. If the current list already exists, it wins.
    - If the old path contains more ``'['`` elements than the new path, the
      move is undefined in this declarative API. Use pre-processing or
      post-processing for many-to-one migrations.
    - Moving only one selected list element is not supported in this version.

    Moving a whole object into a list element is preferred when changing an
    object-valued member into a list-valued member. For example,
    ``RocfKeyMove(old_path=('output',), new_path=('outputs', '['))`` turns the
    old ``output`` object into the first and only element of ``outputs``.

    Moves whose old and new paths overlap are legal. Implementations should
    read the old value first, remove the old path, and then write the new
    path. Overlapping moves are order-sensitive and should be avoided unless
    the migration really needs them.

    Attributes:
        old_path: Absolute path to the old value in the root configuration
            data object.
        new_path: Absolute path where the value belongs in the current
            configuration data object.
    """

    old_path: RocfPath
    new_path: RocfPath


RocfKeyRename = NamedTuple('RocfKeyRename', [('old', str), ('new', str)])
"""Describe a configuration key rename from an old name to a new name.

Renaming rule for Reading Old Configuration File (ROCF). Used by derived
classes to describe key names in old configuration files that should be
mapped onto their current names during parsing.
"""


class RocfConflictError(InvalidConfiguration):
    """Raised when old-file migration rules produce conflicting writes.

    Several :class:`RocfKeyMove` rules may declare the same ``new_path``. This
    is useful when a current configuration version can read files from more
    than one older version. It is a conflict only if more than one rule
    actually writes a value to the same current target while processing one
    input file.
    """


class RocfIncompatiblePathError(InvalidConfiguration):
    """Raised when a current-schema path cannot be created.

    Declarative ROCF processing raises this when a target path needs an
    intermediate dictionary or list and an incompatible value already exists
    in the input data.
    """


class ReadOldConfiguration:
    """Normalize possibly old configuration data.

    ``Config.parse_json()`` should decode JSON text first. It should then use
    a ``ReadOldConfiguration`` object to turn the parsed root object into
    current-schema configuration data. The rest of ``Config`` should only need
    to check and apply the current schema.

    This class runs on every read. Therefore, current-format input must pass
    through as a no-op when no old-format data is present.

    The input data has already been decoded from JSON. Depending on the
    ``Config`` parse flow, scalar leaf values may already have been converted
    by ``parse_converters()`` before this object sees the data. The data has
    not yet been validated, and dictionaries have not yet been converted into
    nested ``Config`` objects.

    Application-specific subclasses should normally override only the
    declarative methods:

    - :meth:`get_keys_to_remove_recursively`
    - :meth:`get_keys_to_remove`
    - :meth:`get_json_key_renames`
    - :meth:`get_json_key_moves`
    - :meth:`get_values_for_missing_json_keys`

    Unusual migrations can override :meth:`pre_process_json` or
    :meth:`post_process_json`.
    """

    def process_json(self, json_data: dict[str, object],
                     auto_ch_hook: ConfigAutoChangeHook,
                     stderr_file: TextIO) -> dict[str, object]:
        """Return current-schema data from possibly old configuration data.

        The intended default processing order is:

        1. :meth:`pre_process_json`
        2. remove keys from :meth:`get_keys_to_remove_recursively`
        3. remove keys from :meth:`get_keys_to_remove`
        4. rename keys from :meth:`get_json_key_renames`
        5. move paths from :meth:`get_json_key_moves`
        6. add values from :meth:`get_values_for_missing_json_keys`
        7. :meth:`post_process_json`

        Missing values are intentionally applied after renames and moves so
        old values get a chance to populate the current shape before defaults
        are supplied.

        This method may mutate ``json_data`` in place. Callers must use the
        returned object.

        Implementations should report actual performed moves, not move rules.
        A wildcard move over three list elements should therefore report three
        individual moves. Moved paths should use the same text style as member
        names used by member validators, for example
        ``outputs[2].csv_params[delimiter]``.

        Move reporting should use ``ConfigAutoChangeHook.old_path_moved`` with
        the signature ``old_path_moved(old_path: str, new_path: str)``. Adding
        that method to ``ConfigAutoChangeHook`` is backward compatible with
        existing application hook subclasses because their ``auto_changed()``
        signature does not need to change.

        Args:
            json_data: Parsed root object to normalize. Depending on the
                ``Config`` parse flow, ``parse_converters()`` may already have
                converted scalar values, for example strings to enum members.
                The data is not yet validated, and dictionaries have not yet
                been converted to nested ``Config`` objects.
            auto_ch_hook: Hook that records automatic compatibility changes.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            Configuration data matching the current schema.

        """
        _ = json_data, auto_ch_hook, stderr_file
        raise NotImplementedError

    def get_json_key_moves(self) -> list[RocfKeyMove]:
        """Return key moves from old paths to current paths.

        Derived classes override this method when an old configuration value
        must move into a different JSON object structure in the current
        schema.

        Several rules may declare the same target path, but only one rule may
        actually write that target while processing one input file. Rules that
        overlap by ancestor or descendant paths are legal but order-sensitive.

        Returns:
            Key moves to apply in list order while reading old configuration
            files.
        """
        return []

    def get_keys_to_remove_recursively(self) -> list[str]:
        """Return old key names to remove recursively.

        When Reading an Old Configuration File (ROCF), the old configuration
        version in the file might have keys that no longer exist in the
        current configuration. This method returns old key names to remove
        anywhere in the configuration data.

        Key removal is name-based and recursive through dictionaries and
        lists. New code should prefer :meth:`get_keys_to_remove` for precise
        path-based removal unless recursive name-based behavior is really
        intended.

        Returns:
            Old key names that should be removed from the input data.
        """
        return []

    def get_keys_to_remove(self) -> list[RocfPath]:
        """Return old paths to remove while reading old files.

        When Reading an Old Configuration File (ROCF), the old configuration
        version in the file might have keys that no longer exist in the
        current configuration. This method returns precise old paths to remove
        from the configuration data.

        Missing paths are ignored. If traversal reaches a value with the wrong
        container type, the path is ignored because the input may already use
        the current schema.

        Returns:
            Old paths that should be removed from the input data.
        """
        return []

    def get_values_for_missing_json_keys(self) -> dict[RocfPath, object]:
        """Return values for missing current-schema paths.

        When Reading an Old Configuration File (ROCF), some now existing
        and mandatory keys may be missing in the JSON input from the
        old configuration file. This method returns the values that should
        be supplied for these missing keys.

        Values are supplied after removals, renames and moves. Intermediate
        dictionaries and lists may be created as needed. If an incompatible
        value already exists while creating the path, processing should raise
        :class:`RocfIncompatiblePathError`.

        Returns:
            A mapping from missing key path to the value that should be
            supplied when the path is absent from the input data.
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

        Key renaming is name-based and recursive through dictionaries and
        lists. For precise structural migration, use
        :meth:`get_json_key_moves`.
        """
        return []

    def pre_process_json(self, json_data: dict[str, object],
                         auto_ch_hook: ConfigAutoChangeHook,
                         stderr_file: TextIO) -> dict[str, object]:
        """Pre-process data before declarative old-file handling.

        Derived classes override this method only for migrations that cannot
        be expressed with removals, renames, moves or missing values.

        This method may mutate ``json_data`` in place. Its caller must use the
        returned object.

        Args:
            json_data: Parsed root object to normalize. Depending on the
                ``Config`` parse flow, ``parse_converters()`` may already have
                converted scalar values, for example strings to enum members.
                The data is not yet validated, and dictionaries have not yet
                been converted to nested ``Config`` objects.
            auto_ch_hook: Hook that records automatic compatibility changes.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            Data to pass to the declarative old-file processing steps.

        """
        _ = auto_ch_hook, stderr_file
        return json_data

    def post_process_json(self, json_data: dict[str, object],
                          auto_ch_hook: ConfigAutoChangeHook,
                          stderr_file: TextIO) -> dict[str, object]:
        """Post-process data after declarative old-file handling.

        Derived classes override this method only for migrations that need to
        inspect or adjust the result of the declarative old-file processing.

        This method may mutate ``json_data`` in place. Its caller must use the
        returned object.

        Args:
            json_data: Current-shape data after declarative processing steps
                in ReadOldConfiguration. The data is not yet validated, and
                dictionaries have not yet been converted to nested ``Config``
                objects.
            auto_ch_hook: Hook that records automatic compatibility changes.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            Data matching the current configuration schema. This data is now
            ready to be validated and converted to nested Config objects.
        """
        _ = auto_ch_hook, stderr_file
        return json_data
