#! /usr/local/bin/python3
"""Describe detailed automatic changes recorded while reading old input.

Read Old Configuration File (ROCF) processing records one :class:`RocfChange`
for every actual change it applies. Applications that want structured details
about those changes read the records from
:class:`config_as_json.config_auto_change_hook.ConfigAutoChangeHook`.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from enum import Enum, auto
from typing import NamedTuple, Optional


class HookDataVersionError(RuntimeError):
    """Raised when a hook subclass expects another data structure version.

    A derived ``ConfigAutoChangeHook`` that reads the recorded data members
    declares the version it was written for. This exception reports that the
    installed config_as_json records another version, so the derived class
    needs to be reviewed before it can trust the recorded details.
    """


class RocfChangeKind(Enum):
    """Classify one automatic change applied while reading old input."""

    KEY_PRUNED = auto()
    """An old key name was removed recursively from the input data."""

    PATH_REMOVED = auto()
    """An old path was removed from the input data."""

    KEY_RENAMED = auto()
    """An old key name was replaced by the current key name."""

    PATH_MOVED = auto()
    """An old value was moved to the current path."""

    VALUE_MIGRATED = auto()
    """A value migration produced one current value from an old value."""

    OLD_VALUE_DISCARDED = auto()
    """An old value was accepted and removed without producing a value."""

    MISSING_VALUE_ADDED = auto()
    """A current path that was absent from the input received a value."""

    OLD_KEY_HANDLED = auto()
    """Application code reported old data that it handled itself."""


class RocfChange(NamedTuple):
    """Record one automatic change applied while reading old input.

    Paths are rendered in the same text style as the paths reported to
    ``ConfigAutoChangeHook.auto_changed``, for example
    ``outputs[2][csv_params][delimiter]``.

    Attributes:
        kind: What kind of automatic change this record describes.
        old_path: Actual old path that was accepted and handled, or ``None``
            when the change did not consume an old value.
        new_path: Actual current path that received a value, or ``None`` when
            the change did not produce a current value. For
            ``OLD_VALUE_DISCARDED`` it names the existing current path that
            won over the old value, when that path is known.
        value: Value inserted for ``MISSING_VALUE_ADDED`` records created by
            the library. It is ``None`` for every other kind, and also for
            records created through the legacy
            ``ConfigAutoChangeHook.rocf_missing_value_provided`` entry point,
            which does not receive the inserted value.
    """

    kind: RocfChangeKind
    old_path: Optional[str]
    new_path: Optional[str]
    value: object = None


_CHANGE_LABELS: dict[RocfChangeKind, str] = {
    RocfChangeKind.KEY_PRUNED: 'pruned old key  ',
    RocfChangeKind.PATH_REMOVED: 'removed old path',
    RocfChangeKind.KEY_RENAMED: 'renamed key     ',
    RocfChangeKind.PATH_MOVED: 'moved value     ',
    RocfChangeKind.VALUE_MIGRATED: 'migrated value  ',
    RocfChangeKind.OLD_VALUE_DISCARDED: 'discarded old   ',
    RocfChangeKind.MISSING_VALUE_ADDED: 'supplied value  ',
    RocfChangeKind.OLD_KEY_HANDLED: 'handled old key '}
"""Aligned report labels used by ``ConfigAutoChangeHook.print_changes``."""


def change_report_line(change: RocfChange) -> str:
    """Return one report line describing one automatic change.

    Args:
        change: Recorded automatic change to describe.

    Returns:
        One indented report line without a trailing newline.
    """
    label = _CHANGE_LABELS[change.kind]
    if change.kind is RocfChangeKind.MISSING_VALUE_ADDED:
        return f'  {label} {change.new_path} = {change.value!r}'
    if change.new_path is None:
        return f'  {label} {change.old_path}'
    if change.kind is RocfChangeKind.OLD_VALUE_DISCARDED:
        return f'  {label} {change.old_path} ' + \
            f'(current {change.new_path} wins)'
    return f'  {label} {change.old_path} -> {change.new_path}'


def nested_change(change: RocfChange, path_prefix: str) -> RocfChange:
    """Return one nested change record using parent-absolute paths.

    Args:
        change: Change recorded by a nested ``Config`` object about its own
            JSON data.
        path_prefix: Path text of the nested object inside the parent, for
            example ``outputs[0]``.

    Returns:
        The same change with both paths rewritten as paths in the parent.
    """
    return RocfChange(kind=change.kind,
                      old_path=_absolute_path(path_prefix, change.old_path),
                      new_path=_absolute_path(path_prefix, change.new_path),
                      value=change.value)


def _absolute_path(path_prefix: str, path: Optional[str]) -> Optional[str]:
    """Return one nested path text as a parent-absolute path text.

    The first step of a nested path is a plain dictionary key, and every
    later step is already bracketed. Prefixing therefore only has to bracket
    that first step, so ``csv_params[delimiter]`` below ``outputs[0]``
    becomes ``outputs[0][csv_params][delimiter]``.
    """
    if path is None:
        return None
    head, bracket, tail = path.partition('[')
    return f'{path_prefix}[{head}]{bracket}{tail}'
