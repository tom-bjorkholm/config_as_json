#! /usr/local/bin/python3
"""Define declarative ROCF rules for value-producing migrations.

Application code can use these small rule objects when one old
configuration value needs to produce zero, one or several current JSON
values. The rules describe the public contract only in this first version.
The processing code is expected to live in this module when value migrations
are implemented.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Callable, NamedTuple
from config_as_json.commontypes import ConfigPath


def _identity_value(value: object) -> object:
    """Return ``value`` unchanged for default transform callbacks."""
    return value


def _always_true(value: object) -> bool:
    """Return ``True`` for default condition callbacks."""
    _ = value
    return True


class RocfValueWrite(NamedTuple):
    """Declare one possible current value written by a value migration.

    Application code uses this rule inside :class:`RocfValueMigration` when
    one old configuration value can create a value at one current JSON path.
    The containing migration decides when all writes are applied or skipped
    as one unit.

    ``new_path`` uses the same ROCF path syntax and validation rules as
    :class:`RocfKeyMove` target paths. The containing
    :class:`RocfValueMigration` validates how list wildcards in ``new_path``
    relate to the old path.

    ``condition`` is not a current-value conflict guard. Every declared
    ``new_path`` participates in current-value conflict detection before any
    callback is called, even when ``condition`` would return ``False``. If any
    declared current path already exists, current values win, no declared
    writes are applied, no ``condition`` or ``transform_value`` callbacks are
    called, and the old value is removed as handled old-schema data.

    When no current conflict skips the containing migration, the library calls
    ``condition`` with a deep copy of the old value. If it returns ``True``,
    the library calls ``transform_value`` with another deep copy of the old
    value and writes the returned value to ``new_path``. If ``condition``
    returns ``False``, this write does not produce a value for this
    ``new_path``. Application callbacks should not rely on mutating the
    received value because each callback receives its own copy.

    The value returned by ``transform_value`` is inserted into the parsed JSON
    data before normal current-schema validation. It should therefore be the
    Python representation expected by the current configuration at
    ``new_path``.

    Args:
        new_path: Absolute path where a produced value belongs in the current
            configuration data object.
        condition: Function deciding whether this write applies to the old
            value. Defaults to a function returning ``True``.
        transform_value: Function transforming the old value into the value to
            write at ``new_path``. Defaults to the identity function.
    """

    new_path: ConfigPath
    condition: Callable[[object], bool] = _always_true
    transform_value: Callable[[object], object] = _identity_value


class RocfValueMigration(NamedTuple):
    """Declare that one old value produces current configuration values.

    Application subclasses return these rules from a
    ``ReadOldConfiguration.get_value_migration()`` method when an old
    configuration parameter cannot be described as one fixed
    :class:`RocfKeyMove`. Typical cases are a value that routes to one of
    several current paths, or a value that is split into several derived
    current values.

    ``old_path`` and all write ``new_path`` values use the same ROCF path
    syntax, validation rules and list wildcard semantics as
    :class:`RocfKeyMove` paths. If ``old_path`` contains list wildcards, each
    actual old value reached by the expanded path is handled as a separate
    value migration.

    The allowed list wildcard shapes are intentionally the same as for
    :class:`RocfKeyMove`, and each write is checked against ``old_path``
    separately:

    - If old and new paths contain the same number of ``'['`` elements, list
      elements are paired by wildcard position and by actual list index.
    - If the new path contains one ``'['`` and the old path contains none,
      the old value is written as the first element of a new single-element
      current list when that current list is absent.
    - If the old path contains more ``'['`` elements than a write path, the
      migration is undefined in this declarative API.
    - Moving only one selected list element is not supported in this version.
    - All other unequal wildcard counts are rejected.

    Declared write paths for one actual old value must be distinct after
    wildcard expansion. If two writes could target the same actual current
    path, the application rule is ambiguous and should be rejected before the
    JSON data is changed.

    A value migration is transactional for each old value reached by
    ``old_path``. If the old path is absent, or if traversal of ``old_path``
    reaches a value with the wrong container type, the rule is a no-op. If
    any declared ``new_path`` already exists, current values win and none of
    the writes are applied. In that conflict case, no ``condition`` or
    ``transform_value`` callbacks are called and the old value is removed as
    handled old-schema data.

    Current-value conflict detection considers every declared write path, not
    only writes whose ``condition`` would return ``True``. This keeps
    application code reviews simple: the declared write set is the complete
    set of current paths that may be affected by the migration.

    Existing current values that overlap the actual old path being removed
    are handled the same way as overlapping :class:`RocfKeyMove` paths. The
    old value is read first, the old path is removed, and then current values
    are written.

    If the implementation needs to create an intermediate dictionary or list
    below a write path and an incompatible value already exists there,
    processing fails with :class:`RocfIncompatiblePathError`.

    If no current conflict exists, all writes whose condition returns
    ``True`` are applied. An empty ``writes`` list is valid. If ``writes`` is
    empty, or if no write condition returns ``True``, the migration is still
    considered handled and the old value is removed without writing any
    current values.

    The implementation evaluates callbacks and prepares all produced current
    values before mutating the JSON data for the actual old value. If a
    ``condition`` or ``transform_value`` callback raises, processing of that
    actual old value fails without deleting its old value or writing any
    values from this migration. Earlier ROCF rules, earlier actual values
    from the same wildcard migration, or earlier value migrations may already
    have changed the in-memory configuration data. Application code should
    therefore treat the original JSON file being read as the safe source to
    correct after such an error. Callback side effects outside the JSON data
    cannot be undone by the library, so callbacks should normally be pure.

    The old value passed to write callbacks has been processed by the normal
    ``parse_json`` method and registered ``parse_converters`` for the old
    path. The processing code deep-copies the old value before calling each
    write's ``condition`` and ``transform_value`` callbacks, so one callback
    cannot mutate the input seen by another callback.

    Automatic-change reporting keeps the existing
    ``ConfigAutoChangeHook.auto_changed()`` signature. When one old value
    produces one or more current values, the hook records one moved old-to-new
    path for each produced current value. When no write is produced, the hook
    records the actual old path as handled old-schema data. When current
    values win, the hook records the actual old path as handled and the
    diagnostic written to ``stderr_file`` lists the old path, the declared
    current paths considered, and the existing current paths that caused the
    conflict. Future implementations may add detailed hook attributes, but
    the summary passed to ``auto_changed()`` must remain backward-compatible.

    Args:
        old_path: Absolute path to the old value in the root configuration
            data object.
        writes: Current value writes to consider as one all-or-nothing
            migration.
    """

    old_path: ConfigPath
    writes: list[RocfValueWrite]
