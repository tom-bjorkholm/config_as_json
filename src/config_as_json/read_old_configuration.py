#! /usr/local/bin/python3
"""Describe contracts for normalizing old configuration data."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import NamedTuple, Optional, Sequence, TextIO, cast
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


class _MovedValue(NamedTuple):
    """One actual value found by a move rule."""

    actual_path: list[str | int]
    indexes: list[int]
    value: object


class _MoveContext(NamedTuple):
    """State shared while applying move rules."""

    json_data: dict[str, object]
    written_paths: set[str]
    auto_ch_hook: ConfigAutoChangeHook
    stderr_file: TextIO


def _as_dict(value: object) -> Optional[dict[str, object]]:
    """Return ``value`` as a string-key dictionary if possible."""
    if isinstance(value, dict):
        return cast(dict[str, object], value)
    return None


def _as_list(value: object) -> Optional[list[object]]:
    """Return ``value`` as a list if possible."""
    if isinstance(value, list):
        return cast(list[object], value)
    return None


def _path_text(path: Sequence[str | int]) -> str:
    """Return a member-validator style text form of one actual path."""
    result = ''
    previous_was_index = False
    for part in path:
        if isinstance(part, int):
            result += f'[{part}]'
            previous_was_index = True
        elif not result:
            result = part
            previous_was_index = False
        elif previous_was_index:
            result += f'.{part}'
            previous_was_index = False
        else:
            result += f'[{part}]'
            previous_was_index = False
    return result


def _validate_path(path: RocfPath, name: str) -> None:
    """Validate path syntax shared by declarative ROCF methods."""
    if not path:
        raise ValueError(f'{name} must not be empty')
    if path[0] == '[':
        raise ValueError(f'{name} must start with a dictionary key')
    for part in path:
        if not isinstance(part, str):
            raise TypeError(f'{name} elements must be strings')
        if part.startswith('[') and part != '[':
            raise ValueError(f'{name} element {part} is reserved')


def _list_marker_count(path: RocfPath) -> int:
    """Return the number of list wildcards in ``path``."""
    return sum(1 for part in path if part == '[')


def _validate_move(move: RocfKeyMove) -> None:
    """Validate one move rule before applying it."""
    _validate_path(move.old_path, 'old_path')
    _validate_path(move.new_path, 'new_path')
    if move.old_path == move.new_path:
        raise ValueError('old_path and new_path must not be equal')
    old_lists = _list_marker_count(move.old_path)
    new_lists = _list_marker_count(move.new_path)
    if old_lists == new_lists:
        return
    if old_lists == 0 and new_lists == 1:
        return
    msg = 'ROCF moves support equal list wildcard counts, or wrapping one '
    msg += 'non-list old value into one new list'
    raise ValueError(msg)


def _conflict_diag(old_path: str, new_path: str, stderr_file: TextIO) -> None:
    """Write the standard diagnostic for a current value winning."""
    print('Inconsistent configuration:', file=stderr_file)
    print(f'Both new config parameter {new_path} and old {old_path} '
          'present.', file=stderr_file)
    print(f'Ignoring old parameter {old_path}', file=stderr_file)


def _remove_key_recursive(data: object, key: str) -> bool:
    """Remove a dictionary key from all dictionaries below ``data``."""
    dict_data = _as_dict(data)
    if dict_data is not None:
        found = key in dict_data
        if found:
            del dict_data[key]
        for value in list(dict_data.values()):
            found = _remove_key_recursive(value, key) or found
        return found
    list_data = _as_list(data)
    if list_data is not None:
        found = False
        for value in list_data:
            found = _remove_key_recursive(value, key) or found
        return found
    return False


def _rename_key_recursive(rename: RocfKeyRename, data: object,
                          stderr_file: TextIO) -> bool:
    """Rename a dictionary key in all dictionaries below ``data``."""
    assert rename.old is not None
    assert rename.new is not None
    assert rename.old != rename.new
    dict_data = _as_dict(data)
    if dict_data is not None:
        found = False
        if rename.old in dict_data:
            found = True
            if rename.new in dict_data:
                _conflict_diag(rename.old, rename.new, stderr_file)
            else:
                dict_data[rename.new] = dict_data[rename.old]
            del dict_data[rename.old]
        for value in list(dict_data.values()):
            found = _rename_key_recursive(rename, value, stderr_file) or found
        return found
    list_data = _as_list(data)
    if list_data is not None:
        found = False
        for value in list_data:
            found = _rename_key_recursive(rename, value, stderr_file) or found
        return found
    return False


def _collect_path_values(data: object, path: RocfPath, actual: list[str | int],
                         indexes: list[int]) -> list[_MovedValue]:
    """Collect existing values reached by one declarative path."""
    part = path[0]
    rest = path[1:]
    if part == '[':
        list_data = _as_list(data)
        if list_data is None:
            return []
        values = []
        for index, value in enumerate(list_data):
            actual_path = actual + [index]
            list_indexes = indexes + [index]
            if not rest:
                values.append(_MovedValue(actual_path, list_indexes, value))
                continue
            values.extend(_collect_path_values(
                value, rest, actual_path, list_indexes))
        return values
    dict_data = _as_dict(data)
    if dict_data is None or part not in dict_data:
        return []
    new_actual = actual + [part]
    if not rest:
        return [_MovedValue(new_actual, indexes, dict_data[part])]
    return _collect_path_values(dict_data[part], rest, new_actual, indexes)


def _target_path(new_path: RocfPath, indexes: list[int]) -> list[str | int]:
    """Return the actual target path for one collected old value."""
    target: list[str | int] = []
    next_index = 0
    for part in new_path:
        if part == '[':
            if indexes:
                target.append(indexes[next_index])
                next_index += 1
            else:
                target.append(0)
        else:
            target.append(part)
    return target


def _delete_path(data: object, path: Sequence[str | int]) -> None:
    """Delete an existing actual path if it can still be reached."""
    if not path:
        return
    part = path[0]
    rest = path[1:]
    if isinstance(part, int):
        list_data = _as_list(data)
        if list_data is None or part >= len(list_data):
            return
        if rest:
            _delete_path(list_data[part], rest)
        else:
            del list_data[part]
        return
    dict_data = _as_dict(data)
    if dict_data is None or part not in dict_data:
        return
    if rest:
        _delete_path(dict_data[part], rest)
    else:
        del dict_data[part]


def _path_exists(data: object, path: Sequence[str | int]) -> bool:
    """Return whether an actual path exists in ``data``."""
    current = data
    for part in path:
        if isinstance(part, int):
            list_data = _as_list(current)
            if list_data is None or part >= len(list_data):
                return False
            current = list_data[part]
        else:
            dict_data = _as_dict(current)
            if dict_data is None or part not in dict_data:
                return False
            current = dict_data[part]
    return True


def _path_is_prefix(first: Sequence[str | int],
                    second: Sequence[str | int]) -> bool:
    """Return whether ``first`` is a path prefix of ``second``."""
    if len(first) > len(second):
        return False
    return list(first) == list(second[:len(first)])


def _paths_overlap(first: Sequence[str | int],
                   second: Sequence[str | int]) -> bool:
    """Return whether either path is an ancestor of the other."""
    return _path_is_prefix(first, second) or _path_is_prefix(
        first=second, second=first)


def _wrap_prefix(move: RocfKeyMove,
                 target: list[str | int]) -> Optional[list[str | int]]:
    """Return the current-list path for a wrap move, if any."""
    if _list_marker_count(move.old_path) != 0:
        return None
    if _list_marker_count(move.new_path) != 1:
        return None
    for index, part in enumerate(target):
        if isinstance(part, int):
            return target[:index]
    return None


def _get_existing_value(data: object,
                        path: Sequence[str | int]) -> tuple[bool, object]:
    """Return whether an actual path exists and its value when present."""
    current = data
    for part in path:
        if isinstance(part, int):
            list_data = _as_list(current)
            if list_data is None or part >= len(list_data):
                return False, None
            current = list_data[part]
        else:
            dict_data = _as_dict(current)
            if dict_data is None or part not in dict_data:
                return False, None
            current = dict_data[part]
    return True, current


def _container_for(next_part: str | int) -> object:
    """Return an empty container suitable before ``next_part``."""
    if isinstance(next_part, int):
        return []
    return {}


def _require_dict(value: object, path: Sequence[str | int]) \
        -> dict[str, object]:
    """Return ``value`` as dict or raise an incompatible-path error."""
    dict_data = _as_dict(value)
    if dict_data is None:
        msg = f'Path {_path_text(path)} must be a dictionary'
        raise RocfIncompatiblePathError(msg)
    return dict_data


def _require_list(value: object, path: Sequence[str | int]) -> list[object]:
    """Return ``value`` as list or raise an incompatible-path error."""
    list_data = _as_list(value)
    if list_data is None:
        msg = f'Path {_path_text(path)} must be a list'
        raise RocfIncompatiblePathError(msg)
    return list_data


def _write_path(data: object, path: Sequence[str | int],
                value: object) -> None:
    """Write ``value`` to an actual path, creating containers as needed."""
    current = data
    for index, part in enumerate(path[:-1]):
        next_part = path[index + 1]
        if isinstance(part, int):
            list_data = _require_list(current, path[:index])
            while len(list_data) <= part:
                list_data.append(_container_for(next_part))
            current = list_data[part]
        else:
            dict_data = _require_dict(current, path[:index])
            if part not in dict_data:
                dict_data[part] = _container_for(next_part)
            current = dict_data[part]
    last = path[-1]
    if isinstance(last, int):
        list_data = _require_list(current, path[:-1])
        while len(list_data) <= last:
            list_data.append(None)
        list_data[last] = value
    else:
        dict_data = _require_dict(current, path[:-1])
        dict_data[last] = value


def _remove_path(data: object, path: RocfPath,
                 actual: list[str | int]) -> list[str]:
    """Remove one path rule and return actual removed path texts."""
    part = path[0]
    rest = path[1:]
    if part == '[':
        list_data = _as_list(data)
        if list_data is None:
            return []
        if not rest:
            removed = [_path_text(actual + [index])
                       for index in range(len(list_data))]
            list_data.clear()
            return removed
        removed = []
        for index, value in enumerate(list_data):
            removed.extend(_remove_path(value, rest, actual + [index]))
        return removed
    dict_data = _as_dict(data)
    if dict_data is None or part not in dict_data:
        return []
    new_actual = actual + [part]
    if rest:
        return _remove_path(dict_data[part], rest, new_actual)
    del dict_data[part]
    return [_path_text(new_actual)]


def _apply_missing(data: object, path: RocfPath, value: object,
                   actual: list[str | int]) -> list[str]:
    """Apply one missing-value rule and return actual path texts."""
    part = path[0]
    rest = path[1:]
    if part == '[':
        list_data = _require_list(data, actual)
        if not rest:
            return []
        applied = []
        for index, item in enumerate(list_data):
            applied.extend(_apply_missing(item, rest, value, actual + [index]))
        return applied
    dict_data = _require_dict(data, actual)
    new_actual = actual + [part]
    if not rest:
        if part in dict_data:
            return []
        dict_data[part] = deepcopy(value)
        return [_path_text(new_actual)]
    if part not in dict_data:
        if rest[0] == '[':
            return []
        dict_data[part] = {}
    return _apply_missing(dict_data[part], rest, value, new_actual)


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
        json_data = self.pre_process_json(
            json_data=json_data, auto_ch_hook=auto_ch_hook,
            stderr_file=stderr_file)
        self._remove_keys_recursively(json_data, auto_ch_hook)
        self._remove_keys_by_path(json_data, auto_ch_hook)
        self._rename_json_keys(json_data, auto_ch_hook, stderr_file)
        self._move_json_keys(json_data, auto_ch_hook, stderr_file)
        self._apply_missing_values(json_data, auto_ch_hook)
        return self.post_process_json(
            json_data=json_data, auto_ch_hook=auto_ch_hook,
            stderr_file=stderr_file)

    def _remove_keys_recursively(self, json_data: dict[str, object],
                                 auto_ch_hook: ConfigAutoChangeHook) -> None:
        """Apply recursive key removals to ``json_data``."""
        for key in self.get_keys_to_remove_recursively():
            if not isinstance(key, str):
                raise TypeError('recursive remove keys must be strings')
            if _remove_key_recursive(json_data, key):
                auto_ch_hook.old_key_handled(old_key=key)

    def _remove_keys_by_path(self, json_data: dict[str, object],
                             auto_ch_hook: ConfigAutoChangeHook) -> None:
        """Apply path-based key removals to ``json_data``."""
        for path in self.get_keys_to_remove():
            _validate_path(path, 'remove path')
            for old_path in _remove_path(json_data, path, []):
                auto_ch_hook.old_key_handled(old_key=old_path)

    def _rename_json_keys(self, json_data: dict[str, object],
                          auto_ch_hook: ConfigAutoChangeHook,
                          stderr_file: TextIO) -> None:
        """Apply recursive key renames to ``json_data``."""
        for rename in self.get_json_key_renames():
            if _rename_key_recursive(rename, json_data, stderr_file):
                auto_ch_hook.old_key_handled(old_key=rename.old)

    def _move_json_keys(self, json_data: dict[str, object],
                        auto_ch_hook: ConfigAutoChangeHook,
                        stderr_file: TextIO) -> None:
        """Apply path moves to ``json_data`` in declaration order."""
        context = _MoveContext(json_data=json_data, written_paths=set(),
                               auto_ch_hook=auto_ch_hook,
                               stderr_file=stderr_file)
        for move in self.get_json_key_moves():
            _validate_move(move)
            moved = _collect_path_values(json_data, move.old_path, [], [])
            for moved_value in moved:
                self._move_one_path(context, move, moved_value)

    def _move_one_path(self, context: _MoveContext, move: RocfKeyMove,
                       moved_value: _MovedValue) -> None:
        """Apply one actual move produced by a move rule."""
        target = _target_path(move.new_path, moved_value.indexes)
        old_text = _path_text(moved_value.actual_path)
        new_text = _path_text(target)
        if new_text in context.written_paths:
            msg = f'More than one ROCF move wrote {new_text}'
            raise RocfConflictError(msg)
        wrap_prefix = _wrap_prefix(move, target)
        if self._target_is_current(context, moved_value, wrap_prefix, target):
            _delete_path(context.json_data, moved_value.actual_path)
            context.auto_ch_hook.old_path_moved(old_path=old_text,
                                                new_path=new_text)
            return
        _delete_path(context.json_data, moved_value.actual_path)
        _write_path(context.json_data, target, deepcopy(moved_value.value))
        context.written_paths.add(new_text)
        context.auto_ch_hook.old_path_moved(old_path=old_text,
                                            new_path=new_text)

    def _target_is_current(self, context: _MoveContext,
                           moved_value: _MovedValue,
                           wrap_prefix: Optional[list[str | int]],
                           target: list[str | int]) -> bool:
        """Return whether a current target exists and should win."""
        old_actual = moved_value.actual_path
        old_text = _path_text(old_actual)
        new_text = _path_text(target)
        if wrap_prefix is not None:
            exists, value = _get_existing_value(context.json_data, wrap_prefix)
            if exists and not _paths_overlap(old_actual, wrap_prefix):
                _ = _require_list(value, wrap_prefix)
                _conflict_diag(old_text, new_text, context.stderr_file)
                return True
        if _path_exists(context.json_data, target) and not _paths_overlap(
                old_actual, target):
            _conflict_diag(old_text, new_text, context.stderr_file)
            return True
        return False

    def _apply_missing_values(self, json_data: dict[str, object],
                              auto_ch_hook: ConfigAutoChangeHook) -> None:
        """Apply missing-value rules to ``json_data``."""
        for path, value in self.get_values_for_missing_json_keys().items():
            _validate_path(path, 'missing-value path')
            for applied_path in _apply_missing(json_data, path, value, []):
                auto_ch_hook.rocf_missing_value_provided(applied_path)

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
        dictionaries may be created as needed. If the path contains the list
        wildcard ``'['``, the value is supplied inside existing list elements
        only. To supply an empty list that is itself missing, use the path to
        the list member, for example ``{('outputs',): []}``.

        If an incompatible value already exists while creating the path,
        processing should raise
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
