#! /usr/local/bin/python3
"""Support read old configuration file (ROCF) normalization rules.

Application code derives from :class:`ReadOldConfiguration` and returns small
rule objects from its methods. The config_as_json library applies those rules
while reading JSON, before validation and nested ``Config`` conversion.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import NamedTuple, Optional, Sequence, TextIO, cast
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.validator import InvalidConfiguration


type RocfPath = tuple[str, ...]
"""A path used by read old configuration file (ROCF) rules.

Application subclasses use ``RocfPath`` values when they return path-based
remove, move or missing-value rules. Each path is absolute from the root JSON
configuration object that is being read.

The library treats ordinary path elements as dictionary keys. The special path
element ``'['`` means "each list element". For example, the path
``('outputs', '[', 'encoding')`` addresses the ``encoding`` key in every item
of the ``outputs`` list.

Any path element that starts with ``'['`` but is not exactly ``'['`` is
reserved for future list syntax and is illegal in this version. If an old file
really contains a dictionary key that starts with ``'['``, handle that file in
:meth:`ReadOldConfiguration.pre_process_json` or
:meth:`ReadOldConfiguration.post_process_json` instead of a declarative rule.

Declarative ROCF paths must be non-empty and must start with a dictionary key.
The data has already been decoded from JSON before the library applies these
paths. Depending on the ``Config`` parse flow, scalar leaf values may also have
been converted by ``parse_converters()``. Application rules should therefore
reason about dictionary and list shape, and usually treat leaf values as
already parsed application values.
"""


class RocfKeyMove(NamedTuple):
    """Declare that an old value belongs at a current path.

    Application subclasses return ``RocfKeyMove`` objects from
    :meth:`ReadOldConfiguration.get_json_key_moves` when an old configuration
    file used a different JSON structure from the current configuration class.
    ``old_path`` says where old files may contain the value. ``new_path`` says
    where the same value belongs in the current JSON shape.

    The library validates both paths before applying a rule. Empty paths are
    illegal, and ``old_path`` and ``new_path`` must not be equal.

    If ``old_path`` is missing, the rule is a no-op because the input may
    already use the current schema. If traversal of ``old_path`` reaches a
    value with the wrong container type, the rule is also a no-op. Normal
    current-schema parsing later decides whether the remaining data is valid.

    If the library needs to create an intermediate dictionary or list below
    ``new_path`` and an incompatible value already exists there, processing
    fails with :class:`RocfIncompatiblePathError`.

    If both the old value and the current-shape target value exist in one
    input file, the current-shape value wins. The library deletes the old
    value, writes a diagnostic to the ``stderr_file`` supplied to
    :meth:`ReadOldConfiguration.process_json`, and reports the handled old path
    to the automatic-change hook.

    List handling is intentionally narrow so application rules stay
    predictable:

    - A path without ``'['`` uses only dictionary traversal.
    - If old and new paths contain the same number of ``'['`` elements, list
      elements are paired by index. For example,
      ``RocfKeyMove(old_path=('outputs', '[', 'encoding'),
      new_path=('outputs', '[', 'char_encoding'))`` renames a member in every
      existing list element.
    - If the new path contains one ``'['`` and the old path contains none, the
      old value is wrapped into a single-element list when the current list is
      absent. If the current list already exists, it wins.
    - If the old path contains more ``'['`` elements than the new path, the
      move is undefined in this declarative API. Use pre-processing or
      post-processing for many-to-one migrations.
    - Moving only one selected list element is not supported in this version.

    Moving a whole old object into a list element is preferred when changing an
    object-valued member into a list-valued current member. For example,
    ``RocfKeyMove(old_path=('output',), new_path=('outputs', '['))`` turns the
    old ``output`` object into the first and only element of ``outputs``.

    Moves whose old and new paths overlap are legal. The library reads the old
    value first, removes the old path, and then writes the new path.
    Overlapping moves are order-sensitive, so application code should avoid
    them unless the migration really needs them.

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

Application subclasses return these from
:meth:`ReadOldConfiguration.get_json_key_renames` when reading old
configuration files (ROCF). The library recursively changes dictionary members
named ``old`` to ``new`` in dictionaries and lists. If both names exist in the
same dictionary, the current name wins and the old value is discarded.
"""


class RocfConflictError(InvalidConfiguration):
    """Raised when several old-file move rules write one current path.

    Application code may declare several :class:`RocfKeyMove` rules with the
    same ``new_path`` when one current configuration version can read files
    from more than one older version. The library raises this exception only
    if more than one rule actually writes to the same current target while
    processing one input file.
    """


class RocfIncompatiblePathError(InvalidConfiguration):
    """Raised when the library cannot create a declared current path.

    Declarative read old configuration file (ROCF) processing raises this when
    a move or missing-value rule needs an intermediate dictionary or list, but
    the input data already has an incompatible value at that location.
    """


class _MovedValue(NamedTuple):
    """One existing old value found by expanding a move rule."""

    actual_path: list[str | int]
    indexes: list[int]
    value: object


class _MoveContext(NamedTuple):
    """Library state shared while applying one batch of move rules."""

    json_data: dict[str, object]
    written_paths: set[str]
    auto_ch_hook: ConfigAutoChangeHook
    stderr_file: TextIO


def _as_dict(value: object) -> Optional[dict[str, object]]:
    """Return ``value`` as a JSON-object dictionary if possible."""
    if isinstance(value, dict):
        return cast(dict[str, object], value)
    return None


def _as_list(value: object) -> Optional[list[object]]:
    """Return ``value`` as a JSON-array list if possible."""
    if isinstance(value, list):
        return cast(list[object], value)
    return None


def _path_text(path: Sequence[str | int]) -> str:
    """Return the path text used in diagnostics and hook callbacks."""
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
    """Validate a path returned by an application ROCF method."""
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
    """Return the number of each-list wildcards in ``path``."""
    return sum(1 for part in path if part == '[')


def _validate_move(move: RocfKeyMove) -> None:
    """Validate one application-supplied move rule before applying it."""
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
    """Write the user-facing diagnostic for a current value winning."""
    print('Inconsistent configuration:', file=stderr_file)
    print(f'Both new config parameter {new_path} and old {old_path} '
          'present.', file=stderr_file)
    print(f'Ignoring old parameter {old_path}', file=stderr_file)


def _remove_key_recursive(data: object, key: str) -> bool:
    """Remove an old key name from every dictionary below ``data``."""
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
    """Apply one recursive old-name to current-name rename rule."""
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
    """Collect old values reached by expanding one move-rule path."""
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
    """Return the current target path for one collected old value."""
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
    """Delete an old actual path after it has been handled."""
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
    """Return whether a current actual path already exists."""
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
    """Return whether ``first`` is an ancestor path of ``second``."""
    if len(first) > len(second):
        return False
    return list(first) == list(second[:len(first)])


def _paths_overlap(first: Sequence[str | int],
                   second: Sequence[str | int]) -> bool:
    """Return whether either actual path is an ancestor of the other."""
    return _path_is_prefix(first, second) or _path_is_prefix(
        first=second, second=first)


def _wrap_prefix(move: RocfKeyMove,
                 target: list[str | int]) -> Optional[list[str | int]]:
    """Return the current-list path for an object-to-list move."""
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
    """Return whether an actual path exists and its current value."""
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
    """Return the empty container needed before ``next_part``."""
    if isinstance(next_part, int):
        return []
    return {}


def _require_dict(value: object, path: Sequence[str | int]) \
        -> dict[str, object]:
    """Return a dict or raise when a rule needs a dict path."""
    dict_data = _as_dict(value)
    if dict_data is None:
        msg = f'Path {_path_text(path)} must be a dictionary'
        raise RocfIncompatiblePathError(msg)
    return dict_data


def _require_list(value: object, path: Sequence[str | int]) -> list[object]:
    """Return a list or raise when a rule needs a list path."""
    list_data = _as_list(value)
    if list_data is None:
        msg = f'Path {_path_text(path)} must be a list'
        raise RocfIncompatiblePathError(msg)
    return list_data


def _write_path(data: object, path: Sequence[str | int],
                value: object) -> None:
    """Write a moved or missing value, creating current containers."""
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
    """Apply one old-path remove rule and return removed path texts."""
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
    """Apply one current missing-value rule and return changed paths."""
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
    """Base class for application-specific old-file compatibility.

    Applications derive from this class when the current ``Config`` subclass
    should accept configuration files written by older application versions.
    The current ``Config`` subclass normally returns that derived object from
    ``_get_read_old_configuration()``.

    The config_as_json library calls this object while reading every
    configuration file. It has already decoded JSON text and may already have
    applied ``parse_converters()`` to scalar leaf values. It has not yet
    validated the data or converted dictionaries into nested ``Config``
    objects.

    A subclass should describe only the differences between old files and the
    current JSON shape. Current-format input should therefore pass through
    unchanged when no old names, old paths or missing current values are
    present.

    Application-specific subclasses should normally override only declarative
    methods:

    - :meth:`get_keys_to_remove_recursively`
    - :meth:`get_keys_to_remove`
    - :meth:`get_json_key_renames`
    - :meth:`get_json_key_moves`
    - :meth:`get_values_for_missing_json_keys`

    Unusual migrations can override :meth:`pre_process_json` or
    :meth:`post_process_json`. See ``example/src`` for complete examples.
    """

    def process_json(self, json_data: dict[str, object],
                     auto_ch_hook: ConfigAutoChangeHook,
                     stderr_file: TextIO) -> dict[str, object]:
        """Let the library normalize parsed data to the current shape.

        Application code normally does not call this method directly.
        ``Config.parse_json()`` calls it after JSON decoding and before normal
        validation. Subclasses customize the result by overriding the rule
        methods called below.

        The library applies rules in this order:

        1. :meth:`pre_process_json`
        2. remove keys from :meth:`get_keys_to_remove_recursively`
        3. remove keys from :meth:`get_keys_to_remove`
        4. rename keys from :meth:`get_json_key_renames`
        5. move paths from :meth:`get_json_key_moves`
        6. add values from :meth:`get_values_for_missing_json_keys`
        7. :meth:`post_process_json`

        Missing values are applied after renames and moves so old values get a
        chance to populate the current shape before fallback values are
        supplied.

        This method may mutate ``json_data`` in place. The caller must use the
        returned object because overrides may return another dictionary.

        The library reports actual performed compatibility changes to
        ``auto_ch_hook``. A wildcard move over three list elements is therefore
        reported as three individual moved paths. Moved paths use the same text
        style as member names used by member validators, for example
        ``outputs[2].csv_params[delimiter]``.

        Current-shape values win over old-shape values if both are present.
        In that case the library removes the old value, writes a diagnostic to
        ``stderr_file``, and reports that the old value was handled.

        Args:
            json_data: Parsed root object to normalize. The object has not yet
                been validated or converted to nested ``Config`` objects.
            auto_ch_hook: Hook that records automatic compatibility changes.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            Parsed configuration data matching the current JSON schema.

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
        """Apply application-declared recursive key removals."""
        for key in self.get_keys_to_remove_recursively():
            if not isinstance(key, str):
                raise TypeError('recursive remove keys must be strings')
            if _remove_key_recursive(json_data, key):
                auto_ch_hook.old_key_handled(old_key=key)

    def _remove_keys_by_path(self, json_data: dict[str, object],
                             auto_ch_hook: ConfigAutoChangeHook) -> None:
        """Apply application-declared path-based key removals."""
        for path in self.get_keys_to_remove():
            _validate_path(path, 'remove path')
            for old_path in _remove_path(json_data, path, []):
                auto_ch_hook.old_key_handled(old_key=old_path)

    def _rename_json_keys(self, json_data: dict[str, object],
                          auto_ch_hook: ConfigAutoChangeHook,
                          stderr_file: TextIO) -> None:
        """Apply application-declared recursive key renames."""
        for rename in self.get_json_key_renames():
            if _rename_key_recursive(rename, json_data, stderr_file):
                auto_ch_hook.old_key_handled(old_key=rename.old)

    def _move_json_keys(self, json_data: dict[str, object],
                        auto_ch_hook: ConfigAutoChangeHook,
                        stderr_file: TextIO) -> None:
        """Apply application-declared path moves in declaration order."""
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
        """Move one collected old value or discard it if current wins."""
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
        """Return whether the current-shape value exists and wins."""
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
        """Apply application-declared current missing-value rules."""
        for path, value in self.get_values_for_missing_json_keys().items():
            _validate_path(path, 'missing-value path')
            for applied_path in _apply_missing(json_data, path, value, []):
                auto_ch_hook.rocf_missing_value_provided(applied_path)

    def get_json_key_moves(self) -> list[RocfKeyMove]:
        """Return old paths whose values should move to current paths.

        Application subclasses override this when an old file stores a value
        in one JSON structure and the current configuration expects the same
        value in another structure. Return ``RocfKeyMove`` entries in the order
        they should be applied.

        The library ignores a rule when the old path is absent. If the old
        value exists and the current target does not, the library moves the
        value and removes the old path. If both old and current values exist,
        the current value wins, the old path is removed, and a diagnostic is
        written.

        Several rules may declare the same target path so one current version
        can read several older file shapes. During one file read, only one
        rule may actually write a given current target. Rules that overlap by
        ancestor or descendant paths are legal but order-sensitive.

        Example:
            ``RocfKeyMove(old_path=('output',), new_path=('outputs', '['))``
            moves an old direct ``output`` object into the first element of the
            current ``outputs`` list.

        Returns:
            Move rules to apply in list order while reading old files.
        """
        return []

    def get_keys_to_remove_recursively(self) -> list[str]:
        """Return old key names to remove recursively.

        Application subclasses override this when old configuration files may
        contain a member name that no longer exists anywhere in the current
        configuration.

        The library removes each returned name from every dictionary it finds
        below the root object, including dictionaries inside lists. New code
        should usually prefer :meth:`get_keys_to_remove` for precise
        path-based removal unless this recursive name-based behavior is really
        intended.

        Example:
            Returning ``['debug_trace']`` removes ``debug_trace`` wherever an
            old file contains it.

        Returns:
            Old dictionary member names that should be accepted and removed.
        """
        return []

    def get_keys_to_remove(self) -> list[RocfPath]:
        """Return old paths to remove while reading old files.

        Application subclasses override this when old configuration files may
        contain a value at a known path that no longer exists in the current
        configuration.

        The library removes each returned path when it exists. Missing paths
        are ignored. If traversal reaches a value with the wrong container
        type, that path is ignored because the input may already use the
        current schema.

        Example:
            Returning ``[('sections', '[', 'stale')]`` removes the old
            ``stale`` key from every object in the ``sections`` list.

        Returns:
            Old paths that should be accepted and removed from the input data.
        """
        return []

    def get_values_for_missing_json_keys(self) -> dict[RocfPath, object]:
        """Return values for missing current-schema paths.

        Application subclasses override this when old configuration files lack
        a value that is mandatory in the current configuration. Return current
        paths and the values that should be inserted when those paths are
        absent.

        The library applies these values after removals, renames and moves.
        This gives old values a chance to populate the current shape before
        fallback values are supplied. The value is deep-copied before it is
        inserted so later changes to one inserted container do not affect
        another.

        Intermediate dictionaries may be created as needed. If the path
        contains the list wildcard ``'['``, the value is supplied inside
        existing list elements only. To supply an empty list that is itself
        missing, use the path to the list member, for example
        ``{('outputs',): []}``.

        If an incompatible value already exists while creating the path,
        the library raises :class:`RocfIncompatiblePathError`.

        Example:
            Returning ``{('format_version',): 2}`` inserts
            ``format_version`` only when the input file does not contain it.

        Returns:
            A mapping from current paths to values supplied when absent.
        """
        return {}

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return old dictionary member names mapped to current names.

        Application subclasses override this when old files used different key
        names for values that still live in the same relative JSON structure.

        The library applies these renames recursively through dictionaries and
        lists. If both the old and current names exist in the same dictionary,
        the current value wins, the old value is removed, and a diagnostic is
        written.

        Use :meth:`get_json_key_moves` instead when the migration depends on a
        precise path or changes the JSON structure.

        Example:
            Returning ``[RocfKeyRename(old='title', new='report_name')]``
            accepts old files that used ``title`` and converts them to the
            current ``report_name`` key before validation.

        Returns:
            Accepted old-name to current-name rename rules.
        """
        return []

    def pre_process_json(self, json_data: dict[str, object],
                         auto_ch_hook: ConfigAutoChangeHook,
                         stderr_file: TextIO) -> dict[str, object]:
        """Pre-process data before declarative old-file handling.

        Application subclasses override this only for old-file migrations that
        cannot be expressed with removals, renames, moves or missing values.
        Prefer the declarative methods when they are enough, because the
        library can then handle reporting, current-value conflicts and path
        validation consistently.

        The library calls this before any declarative rules. The override may
        mutate ``json_data`` in place or return a replacement dictionary. It
        should report any compatibility changes it performs through
        ``auto_ch_hook`` and write user-facing diagnostics to ``stderr_file``
        when needed.

        Args:
            json_data: Parsed root object to normalize. The data is not yet
                validated, and dictionaries have not yet been converted to
                nested ``Config`` objects.
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

        Application subclasses override this only for old-file migrations that
        need to inspect or adjust the result of the declarative processing.
        Prefer declarative rules when possible.

        The library calls this after removals, renames, moves and missing
        values. The override may mutate ``json_data`` in place or return a
        replacement dictionary. It should report any compatibility changes it
        performs through ``auto_ch_hook`` and write user-facing diagnostics to
        ``stderr_file`` when needed.

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
