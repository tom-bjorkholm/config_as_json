#! /usr/local/bin/python3
"""Define declarative ROCF rules for value-producing migrations.

Application code can use these small rule objects when one old
configuration value needs to produce zero, one or several current JSON
values. The rules describe the public contract only.
"""

# Copyright (c) 2024-2026 Tom Björkholm
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

    The library calls ``condition`` with the old value. If it returns
    ``True``, the library calls ``transform_value`` with a deep copy of the old
    value and writes the returned value to ``new_path``. If ``condition``
    returns ``False``, this write does not produce a value for this old input.

    Every declared ``new_path`` participates in current-value conflict
    detection, even when ``condition`` returns ``False``. If any declared
    current path already exists, current values win, no declared writes are
    applied, and the old value is removed as handled old-schema data.

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
    """Declare that one old value produces current JSON values.

    Application subclasses return these rules from a
    ``ReadOldConfiguration`` method when an old configuration parameter cannot
    be described as one fixed :class:`RocfKeyMove`. Typical cases are a value
    that routes to one of several current paths, or a value that is split into
    several derived current values.

    A value migration is transactional for each old value reached by
    ``old_path``. If the old path is absent, the rule is a no-op. If any
    declared ``new_path`` already exists, current values win and none of the
    writes are applied. If no current conflict exists, all writes whose
    condition returns ``True`` are applied. If no write condition returns
    ``True``, the migration is still considered handled and the old value is
    removed without writing any current values.

    The old value passed to write callbacks has been processed by the normal
    ``parse_json`` method and registered ``parse_converters`` for the old
    path. The processing code deep-copies the old value before calling each
    write's ``transform_value`` callback, so one write callback cannot mutate
    the input seen by another write.

    Args:
        old_path: Absolute path to the old value in the root configuration
            data object.
        writes: Current value writes to consider as one all-or-nothing
            migration.
    """

    old_path: ConfigPath
    writes: list[RocfValueWrite]
