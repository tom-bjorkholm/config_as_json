#! /usr/local/bin/python3
"""Define callbacks for automatic configuration adjustments.

Hooks let an application learn that configuration input needed help while it
was parsed, for example because old-file compatibility renamed a key, moved a
path, removed an obsolete key, or supplied a missing current value.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import ClassVar, Optional, TextIO
from config_as_json.rocf_change import HookDataVersionError, RocfChange, \
    RocfChangeKind, change_report_line, nested_change


_MERGED_AS_MOVED = frozenset({RocfChangeKind.PATH_MOVED,
                              RocfChangeKind.VALUE_MIGRATED})
"""Nested change kinds recorded as moves in the backward-compatible members."""


class ConfigAutoChangeHook():
    """Collect and report automatic configuration changes during parsing.

    Applications that want to react when configuration data is normalized
    should derive from this class and pass an instance to ``Config``.

    ``Config`` keeps a reference to the instance it is given, so the
    application can read the recorded changes from its own object after
    parsing. ``Config.parse_json`` calls :meth:`clear` before each parse, so
    one instance can be reused for several parses and each :meth:`auto_changed`
    call then reports only the changes of the current parse. One instance
    shared by several ``Config`` objects therefore holds the changes of the
    most recent parse only, and one instance must not be used for parsing in
    several threads at the same time.
    """

    DATA_STRUCTURE_VERSION: ClassVar[int] = 1
    """Version of the recorded data structure read by derived classes.

    The version is stepped whenever the recorded data members change,
    including purely additive changes, so that a derived class reading the
    data members is forced to review the new structure. Derived classes that
    read the data members should call :meth:`check_data_version`.
    """

    def __init__(self) -> None:
        """Initialize empty change tracking state."""
        self.old_keys: list[str] = []
        self.rocf_val_keys: list[str] = []
        self.old_paths_moved: list[tuple[str, str]] = []
        self.changes: list[RocfChange] = []

    @classmethod
    def check_data_version(cls, written_for: int) -> None:
        """Check that the recorded data structure has the expected version.

        Derived classes that read the recorded data members directly should
        call this with the version they were written for. An incompatible
        library version then fails with a clear message instead of silently
        reporting details that no longer mean what the derived class expects.

        Args:
            written_for: Value of :attr:`DATA_STRUCTURE_VERSION` that the
                derived class was written for.

        Raises:
            HookDataVersionError: The library records another version.
        """
        if written_for != cls.DATA_STRUCTURE_VERSION:
            msg = f'{cls.__name__} was written for hook data structure '
            msg += f'version {written_for}, but this config_as_json records '
            msg += f'version {cls.DATA_STRUCTURE_VERSION}.'
            raise HookDataVersionError(msg)

    def auto_changed(self, old_keys_handled: list[str],
                     rocf_vals_handled: list[str],
                     stderr_file: TextIO) -> None:
        """React after parsing finished with one or more automatic changes.

        Derived classes override this method to log, warn, or otherwise react
        when configuration input was normalized.

        The arguments are fixed because of unknown old derived classes that
        we have no control over. If only a printout or logging is needed, and
        you want it to be detailed and version independent, call
        :meth:`print_changes`.

        Derived classes that want more specific structured information should
        read it from the object members, primarily ``self.changes``. The
        members ``self.old_keys``, ``self.rocf_val_keys`` and
        ``self.old_paths_moved`` are kept for backward compatibility and hold
        the same summary as the arguments of this method. A derived class that
        reads the object members directly should call
        :meth:`check_data_version` to ensure that the derived class is
        up-to-date for the currently recorded data structure.

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

    def _add(self, kind: RocfChangeKind, old_path: Optional[str] = None,
             new_path: Optional[str] = None, value: object = None) -> None:
        """Append one detailed record describing one automatic change."""
        self.changes.append(RocfChange(kind=kind, old_path=old_path,
                                       new_path=new_path, value=value))

    def _legacy_moved(self, old_path: str, new_path: str) -> None:
        """Record one moved path in the backward-compatible members."""
        self.old_paths_moved.append((old_path, new_path))
        self.old_keys.append(f'{old_path} -> {new_path}')

    def old_key_handled(self, old_key: str) -> None:
        """Record that one legacy key name was accepted and handled.

        Application code in ``ReadOldConfiguration.pre_process_json`` and
        ``post_process_json`` calls this for old data it handles itself. The
        library uses the more specific recording methods instead.

        Args:
            old_key: Legacy key name or path that was handled by renaming or
                removal.
        """
        self.old_keys.append(old_key)
        self._add(RocfChangeKind.OLD_KEY_HANDLED, old_path=old_key)

    def rocf_missing_value_provided(self, rocf_val_key: str) -> None:
        """Record that parsing supplied a compatibility value for one key.

        Application code that supplies missing current values itself calls
        this. The library calls :meth:`missing_value_added` instead, because
        the library also knows the inserted value.

        Args:
            rocf_val_key: Key that was absent from input and received a value
                during Reading an Old Configuration File (ROCF).
        """
        self.rocf_val_keys.append(rocf_val_key)
        self._add(RocfChangeKind.MISSING_VALUE_ADDED, new_path=rocf_val_key)

    def old_path_moved(self, old_path: str, new_path: str) -> None:
        """Record that one old path was moved to a current path.

        Args:
            old_path: Actual old path that was accepted and removed.
            new_path: Actual current path that received the old value.
        """
        self._legacy_moved(old_path, new_path)
        self._add(RocfChangeKind.PATH_MOVED, old_path=old_path,
                  new_path=new_path)

    def key_pruned(self, key: str, at_paths: list[str]) -> None:
        """Record where one old key name was pruned recursively.

        Args:
            key: Old key name from the prune rule.
            at_paths: Actual paths where the old key name was removed. An
                empty list records nothing, because the rule then did not
                change the input data.
        """
        if not at_paths:
            return
        self.old_keys.append(key)
        for path in at_paths:
            self._add(RocfChangeKind.KEY_PRUNED, old_path=path)

    def path_removed(self, path: str) -> None:
        """Record that one old path was accepted and removed.

        Args:
            path: Actual old path that was removed from the input data.
        """
        self.old_keys.append(path)
        self._add(RocfChangeKind.PATH_REMOVED, old_path=path)

    def key_renamed(self, old_key: str,
                    at_paths: list[tuple[str, Optional[str]]]) -> None:
        """Record where one old key name was replaced by the current name.

        Args:
            old_key: Old key name from the rename rule.
            at_paths: One ``(old actual path, new actual path)`` pair for every
                place where the old key name was found. The new path is
                ``None`` when the current key name already existed there, so
                the current value won and the old value was discarded. An
                empty list records nothing.
        """
        if not at_paths:
            return
        self.old_keys.append(old_key)
        for old_path, new_path in at_paths:
            kind = RocfChangeKind.KEY_RENAMED if new_path is not None \
                else RocfChangeKind.OLD_VALUE_DISCARDED
            self._add(kind, old_path=old_path, new_path=new_path)

    def move_discarded(self, old_path: str, new_path: str) -> None:
        """Record that a current value won over an old value that could move.

        Args:
            old_path: Actual old path that was accepted and removed.
            new_path: Actual current path whose existing value won.
        """
        self._legacy_moved(old_path, new_path)
        self._add(RocfChangeKind.OLD_VALUE_DISCARDED, old_path=old_path,
                  new_path=new_path)

    def value_migrated(self, old_path: str, new_path: str) -> None:
        """Record that a value migration produced one current value.

        Args:
            old_path: Actual old path that was accepted and removed.
            new_path: Actual current path that received a produced value.
        """
        self._legacy_moved(old_path, new_path)
        self._add(RocfChangeKind.VALUE_MIGRATED, old_path=old_path,
                  new_path=new_path)

    def migration_discarded(self, old_path: str, new_paths: list[str]) -> None:
        """Record that a value migration produced no current value.

        Args:
            old_path: Actual old path that was accepted and removed.
            new_paths: Existing current paths that won over the old value. An
                empty list means that the migration itself produced no value.
        """
        self.old_keys.append(old_path)
        if not new_paths:
            self._add(RocfChangeKind.OLD_VALUE_DISCARDED, old_path=old_path)
            return
        for new_path in new_paths:
            self._add(RocfChangeKind.OLD_VALUE_DISCARDED, old_path=old_path,
                      new_path=new_path)

    def missing_value_added(self, path: str, value: object) -> None:
        """Record that one absent current path received a value.

        Args:
            path: Actual current path that received the value.
            value: Value that was inserted at ``path``. It is copied so later
                changes to the configuration data do not change the record.
        """
        self.rocf_val_keys.append(path)
        self._add(RocfChangeKind.MISSING_VALUE_ADDED, new_path=path,
                  value=deepcopy(value))

    def merge_nested(self, nested: 'ConfigAutoChangeHook',
                     path_prefix: str) -> None:
        """Merge changes recorded by a nested Config object into this hook.

        ``Config`` calls this after a nested ``Config`` object has parsed its
        own JSON data, so that automatic changes inside nested objects reach
        the hook the application passed to the top-level ``Config``. The
        nested paths are rewritten as paths in the parent configuration data.

        In the backward-compatible members, merged moved and migrated values
        are recorded as ``old -> new`` entries and every other merged change
        is recorded with its absolute old path.

        Args:
            nested: Hook that recorded the nested object's changes. Merging a
                hook into itself is a no-op, which keeps an application
                factory function that reuses the parent hook harmless.
            path_prefix: Path text of the nested object inside the parent, for
                example ``outputs[0]``.
        """
        if nested is self:
            return
        for change in list(nested.changes):
            self._merge_one(nested_change(change, path_prefix))

    def _merge_one(self, change: RocfChange) -> None:
        """Record one already rewritten change from a nested Config object."""
        if change.kind is RocfChangeKind.MISSING_VALUE_ADDED:
            assert change.new_path is not None
            self.rocf_val_keys.append(change.new_path)
        elif change.kind in _MERGED_AS_MOVED:
            assert change.old_path is not None
            assert change.new_path is not None
            self._legacy_moved(change.old_path, change.new_path)
        else:
            assert change.old_path is not None
            self.old_keys.append(change.old_path)
        self.changes.append(change)

    def has_changes(self) -> bool:
        """Return whether at least one automatic change has been recorded."""
        return any([self.changes, self.old_keys, self.rocf_val_keys,
                    self.old_paths_moved])

    def all_autochanges_done(self, stderr_file: TextIO) -> None:
        """Notify the hook once all automatic changes have been collected.

        The default implementation calls :meth:`auto_changed` once if at
        least one automatic change was recorded.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        if self.has_changes():
            self.auto_changed(old_keys_handled=list(self.old_keys),
                              rocf_vals_handled=list(self.rocf_val_keys),
                              stderr_file=stderr_file)

    def print_changes(self, stderr_file: TextIO) -> None:
        """Print a detailed report of all automatic changes to the stream.

        This is the version-independent way to report automatic changes, and
        is safe to call from derived classes that override :meth:`auto_changed`
        and do not want to be affected by future changes in the data structure
        of the object members. Nothing at all is printed when no automatic
        change was recorded, so the method can be called unconditionally.
        Derived classes may override this method to change the report format.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        if not self.changes:
            return
        print('Automatic configuration changes were applied:',
              file=stderr_file)
        for change in self.changes:
            print(change_report_line(change), file=stderr_file)

    def clear(self) -> None:
        """Clear all recorded automatic changes.

        This is called when a new parsing session starts, so that the hook
        can be reused for multiple parsing sessions, and still in each
        call to :meth:`auto_changed` only report the changes that happened
        during the current parsing session.

        A derived class that adds data members of its own should override this
        method, clear its own members, and call ``super().clear()``.
        """
        self.old_keys.clear()
        self.rocf_val_keys.clear()
        self.old_paths_moved.clear()
        self.changes.clear()
