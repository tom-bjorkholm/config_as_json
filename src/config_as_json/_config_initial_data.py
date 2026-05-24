#! /usr/local/bin/python3
"""Copy neutral initial data into Config defaults and auto-wrap nesting.

This private module implements two related operations:

- ``copy_initial_data_impl`` copies public attribute values from a neutral
  data source (plain object, dataclass instance, or mapping) onto a Config
  target. It is the workhorse behind ``Config.copy_initial_data``.

- ``auto_wrap_nested_defaults_impl`` is called from ``Config.__init__``
  after the nested-config declarations have been validated. It walks the
  declared nested members and replaces any default value that is not yet
  an instance of its declared bridge ``config_type`` with a freshly
  constructed bridge-typed value whose public attributes were copied from
  the original neutral value.

Together these two operations let a derived Config inherit defaults from a
framework-neutral data class without copying every public attribute by
hand and without losing the bridge-typed schema for nested sections.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from collections.abc import Mapping
from typing import Iterator, TextIO, TYPE_CHECKING
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind


if TYPE_CHECKING:
    from config_as_json.config import Config


def _public_items_of(source: object) -> Iterator[tuple[str, object]]:
    """Yield ``(name, value)`` pairs for public attributes of ``source``.

    The source may be a :class:`collections.abc.Mapping` (typically a
    :class:`dict`), or any object with a ``__dict__`` (plain object or a
    dataclass instance). Names starting with ``_`` and callable values are
    skipped so that helper methods and private bookkeeping never leak into
    the copy.

    Args:
        source: Object or mapping to read public attributes from.

    Yields:
        Tuples of ``(attribute name, attribute value)`` in the source's
        own iteration order.

    Raises:
        TypeError: ``source`` exposes no readable public attributes, or a
            mapping key is not a string.
    """
    if isinstance(source, Mapping):
        yield from _public_items_of_mapping(source)
        return
    if hasattr(source, '__dict__'):
        yield from _public_items_of_object(source)
        return
    msg = (f'Initial data source of type {type(source).__name__} has no '
           'public attributes that can be copied.')
    raise TypeError(msg)


def _public_items_of_mapping(source: Mapping[object, object]) \
        -> Iterator[tuple[str, object]]:
    """Yield public ``(name, value)`` pairs for a Mapping source."""
    for key, value in source.items():
        if not isinstance(key, str):
            msg = f'Initial data mapping key {key!r} must be a string.'
            raise TypeError(msg)
        if key.startswith('_'):
            continue
        yield key, value


def _public_items_of_object(source: object) -> Iterator[tuple[str, object]]:
    """Yield public ``(name, value)`` pairs for an object source."""
    for name, value in vars(source).items():
        if name.startswith('_'):
            continue
        if callable(value):
            continue
        yield name, value


def copy_initial_data_impl(source: object, target: 'Config') -> None:
    """Copy public attributes from ``source`` onto a Config ``target``.

    The check for "extra" source attributes is enforced only when
    ``target`` already exposes at least one public attribute. That covers
    the common multiple-inheritance pattern where the neutral base class
    constructor has already created the schema on ``target``, and it also
    covers the internal wrap path where a freshly constructed bridge is
    being populated. When ``target`` has no public attributes yet (the
    pattern used when the neutral constructor takes required arguments
    that the bridge does not duplicate), the source's public attributes
    become the target's schema and no comparison can be made.

    Args:
        source: Plain object, mapping, or dataclass instance whose public
            attributes describe the desired default values.
        target: Config instance whose attributes should be assigned.

    Raises:
        TypeError: ``source`` cannot be read, or ``target`` has a known
            public schema and ``source`` exposes a public attribute that
            ``target`` does not declare.
    """
    target_keys = {name for name in vars(target).keys()
                   if not name.startswith('_')}
    enforce_known_schema = bool(target_keys)
    for name, value in _public_items_of(source):
        if enforce_known_schema and name not in target_keys:
            msg = (f'Initial data source has public attribute {name!r} '
                   f'that is not declared on '
                   f'{type(target).__name__}.')
            raise TypeError(msg)
        setattr(target, name, value)


def _wrap_one_value(source: object, config_type: 'type[Config]', name: str,
                    stderr_file: TextIO) -> 'Config':
    """Build a bridge Config instance whose values come from ``source``.

    Args:
        source: Neutral value (plain object, mapping, or dataclass).
        config_type: Bridge Config-derived class to construct.
        name: Diagnostic member name used in error messages.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A new bridge Config instance with attributes copied from
        ``source`` and any further nested neutrals wrapped recursively.

    Raises:
        TypeError: ``source`` cannot be read or describes attributes that
            ``config_type`` does not declare.
    """
    bridge = config_type(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)
    try:
        copy_initial_data_impl(source=source, target=bridge)
    except TypeError as exc:
        msg = f'Cannot wrap {name} as {config_type.__name__}: {exc}'
        print(msg, file=stderr_file)
        raise TypeError(msg) from exc
    # pylint: disable-next=protected-access
    bridge._auto_wrap_nested_defaults(stderr_file=stderr_file)
    return bridge


def _wrap_optional_or_member(current_value: object,
                             config_type: 'type[Config]', name: str,
                             allow_none: bool, stderr_file: TextIO) -> object:
    """Compute the auto-wrapped value for one direct nested member."""
    if current_value is None:
        return None if allow_none else current_value
    if isinstance(current_value, config_type):
        return current_value
    return _wrap_one_value(source=current_value, config_type=config_type,
                           name=name, stderr_file=stderr_file)


def _wrap_list_elements(current_value: object, config_type: 'type[Config]',
                        name: str, stderr_file: TextIO) -> object:
    """Compute the auto-wrapped list for a LIST_ELEMENT nested member."""
    if not isinstance(current_value, list):
        return current_value
    result: list[object] = []
    changed = False
    for index, element in enumerate(current_value):
        if isinstance(element, config_type):
            result.append(element)
            continue
        result.append(_wrap_one_value(source=element, config_type=config_type,
                                      name=f'{name}[{index}]',
                                      stderr_file=stderr_file))
        changed = True
    return result if changed else current_value


def _wrap_dict_values(current_value: object, config_type: 'type[Config]',
                      name: str, stderr_file: TextIO) -> object:
    """Compute the auto-wrapped dict for a DICT_VALUE nested member."""
    if not isinstance(current_value, dict):
        return current_value
    result: dict[str, object] = {}
    changed = False
    for key, value in current_value.items():
        if isinstance(value, config_type):
            result[key] = value
            continue
        result[key] = _wrap_one_value(source=value, config_type=config_type,
                                      name=f'{name}[{key}]',
                                      stderr_file=stderr_file)
        changed = True
    return result if changed else current_value


def _wrap_dict_value_by_key(current_value: object,
                            nestings: list[ConfigNesting], name: str,
                            stderr_file: TextIO) -> object:
    """Compute the auto-wrapped dict for DICT_VALUE_BY_KEY nestings."""
    if not isinstance(current_value, dict):
        return current_value
    nesting_by_key = _nesting_by_key(nestings)
    result: dict[str, object] = {}
    changed = False
    for key, value in current_value.items():
        nesting = nesting_by_key.get(key)
        if nesting is None:
            result[key] = value
            continue
        if isinstance(value, nesting.config_type):
            result[key] = value
            continue
        result[key] = _wrap_one_value(source=value,
                                      config_type=nesting.config_type,
                                      name=f'{name}[{key}]',
                                      stderr_file=stderr_file)
        changed = True
    return result if changed else current_value


def _nesting_by_key(nestings: list[ConfigNesting]) \
        -> dict[str, ConfigNesting]:
    """Return DICT_VALUE_BY_KEY declarations keyed by discriminator_key."""
    result: dict[str, ConfigNesting] = {}
    for nesting in nestings:
        assert nesting.discriminator_key is not None
        result[nesting.discriminator_key] = nesting
    return result


def _auto_wrap_one_member(member_name: str, current_value: object,
                          nestings: list[ConfigNesting],
                          stderr_file: TextIO) -> object:
    """Compute the auto-wrapped value for one declared nested member."""
    if nestings[0].kind == ConfigNestingKind.DICT_VALUE_BY_KEY:
        return _wrap_dict_value_by_key(current_value=current_value,
                                       nestings=nestings, name=member_name,
                                       stderr_file=stderr_file)
    nesting = nestings[0]
    if nesting.kind == ConfigNestingKind.LIST_ELEMENT:
        return _wrap_list_elements(current_value=current_value,
                                   config_type=nesting.config_type,
                                   name=member_name, stderr_file=stderr_file)
    if nesting.kind == ConfigNestingKind.DICT_VALUE:
        return _wrap_dict_values(current_value=current_value,
                                 config_type=nesting.config_type,
                                 name=member_name, stderr_file=stderr_file)
    allow_none = nesting.kind == ConfigNestingKind.OPTIONAL_MEMBER
    return _wrap_optional_or_member(current_value=current_value,
                                    config_type=nesting.config_type,
                                    name=member_name, allow_none=allow_none,
                                    stderr_file=stderr_file)


def auto_wrap_nested_defaults_impl(
        target: 'Config', nested_decls: dict[str, list[ConfigNesting]],
        stderr_file: TextIO) -> None:
    """Wrap any nested member defaults that are not yet bridge-typed.

    Args:
        target: Config instance whose declared nested members should be
            scanned and possibly replaced with bridge-typed wrappers.
        nested_decls: Validated nested-config declarations for ``target``.
        stderr_file: Stream used for user-facing diagnostics.
    """
    for member_name, nestings in nested_decls.items():
        current_value = getattr(target, member_name)
        new_value = _auto_wrap_one_member(member_name=member_name,
                                          current_value=current_value,
                                          nestings=nestings,
                                          stderr_file=stderr_file)
        if new_value is not current_value:
            setattr(target, member_name, new_value)
