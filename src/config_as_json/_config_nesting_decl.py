#! /usr/local/bin/python3
"""Check the nested Config declarations returned by ``nested_configs()``.

``Config.__init__`` runs these checks on whatever ``nested_configs()``
returned, before any nested Config object is parsed, written, or validated.
The checks cover the runtime types inside one ``ConfigNesting``, the
combinations of nesting kinds that are allowed for one public member, and
that every default value visibly holding a nested Config object was in fact
declared.

The ``Config`` base class is received as the ``config_base`` argument rather
than imported, because ``config.py`` imports this module.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import TYPE_CHECKING
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind


if TYPE_CHECKING:
    from config_as_json.config import Config


def _check_config_nesting(key: str, nesting: ConfigNesting,
                          config_base: 'type[Config]') -> None:
    """Validate one nested Config declaration.

    Args:
        key: Public member name described by ``nesting``.
        nesting: Nested configuration declaration to validate.
        config_base: Base class that ``config_type`` must derive from.

    Raises:
        TypeError: The declaration has the wrong runtime type.
        ValueError: ``discriminator_key`` is used with the wrong kind.
    """
    if not isinstance(nesting.kind, ConfigNestingKind):
        msg = f'nested_configs()[{key}].kind must be ConfigNestingKind'
        raise TypeError(msg)
    if not isinstance(nesting.config_type, type):
        msg = f'nested_configs()[{key}].config_type must be a type'
        raise TypeError(msg)
    if not issubclass(nesting.config_type, config_base):
        msg = 'nested_configs()'
        msg += f'[{key}].config_type must derive from Config'
        raise TypeError(msg)
    if nesting.factory_function is not None and \
            not callable(nesting.factory_function):
        msg = f'nested_configs()[{key}].factory_function must be callable'
        raise TypeError(msg)
    discriminator = nesting.discriminator_key
    if discriminator is not None and not isinstance(discriminator, str):
        msg = 'nested_configs()'
        msg += f'[{key}].discriminator_key must be a string'
        raise TypeError(msg)
    if discriminator is not None and \
            nesting.kind != ConfigNestingKind.DICT_VALUE_BY_KEY:
        msg = 'nested_configs() discriminator_key is reserved for '
        msg += 'DICT_VALUE_BY_KEY'
        raise ValueError(msg)


def _check_config_nesting_kinds(key: str, nestings: list[ConfigNesting],
                                list_form: bool) -> None:
    """Validate combinations of nested Config declaration kinds.

    Args:
        key: Public member name described by the declarations.
        nestings: Checked declarations for one public member.
        list_form: Whether the declarations used list syntax.

    Raises:
        ValueError: The declarations combine incompatible nesting kinds.
    """
    by_key_kind = ConfigNestingKind.DICT_VALUE_BY_KEY
    by_key_nestings = [
        nesting for nesting in nestings if nesting.kind == by_key_kind]
    if list_form and len(by_key_nestings) != len(nestings):
        msg = f'nested_configs()[{key}] list '
        msg += 'may only contain DICT_VALUE_BY_KEY declarations'
        raise ValueError(msg)
    if not by_key_nestings:
        return
    used_keys: set[str] = set()
    for nesting in by_key_nestings:
        discriminator = nesting.discriminator_key
        if discriminator is None:
            msg = f'nested_configs()[{key}] DICT_VALUE_BY_KEY '
            msg += 'requires discriminator_key'
            raise ValueError(msg)
        if discriminator in used_keys:
            msg = f'nested_configs()[{key}] duplicate '
            msg += f'discriminator_key {discriminator}'
            raise ValueError(msg)
        used_keys.add(discriminator)


def _checked_config_nesting_list(key: str, nesting_raw: object,
                                 config_base: 'type[Config]') \
        -> list[ConfigNesting]:
    """Return the checked declaration list for one nested member.

    Args:
        key: Public member name described by the declarations.
        nesting_raw: Raw value from ``nested_configs()``.
        config_base: Base class that ``config_type`` must derive from.

    Returns:
        One or more checked ``ConfigNesting`` declarations.

    Raises:
        TypeError: The raw value or a list entry has the wrong type.
        ValueError: The list shape is not valid for the declared kinds.
    """
    if isinstance(nesting_raw, ConfigNesting):
        nestings = [nesting_raw]
    elif isinstance(nesting_raw, list):
        if not nesting_raw:
            msg = f'nested_configs()[{key}] list must not be empty'
            raise ValueError(msg)
        nestings = []
        for nesting in nesting_raw:
            if not isinstance(nesting, ConfigNesting):
                msg = f'nested_configs()[{key}] list entries must be '
                msg += 'ConfigNesting'
                raise TypeError(msg)
            nestings.append(nesting)
    else:
        msg = f'nested_configs()[{key}] must be ConfigNesting or list'
        raise TypeError(msg)
    for nesting in nestings:
        _check_config_nesting(key=key, nesting=nesting,
                              config_base=config_base)
    list_form = isinstance(nesting_raw, list)
    _check_config_nesting_kinds(key=key, nestings=nestings,
                                list_form=list_form)
    return nestings


def _checked_nested_configs(nested_raw: object, self_keys: list[str],
                            config_base: 'type[Config]') \
        -> dict[str, list[ConfigNesting]]:
    """Return validated and normalized nested Config declarations.

    Args:
        nested_raw: Raw value returned by ``nested_configs()``.
        self_keys: Public member names of the configuration object.
        config_base: Base class that every ``config_type`` must derive from.

    Returns:
        One checked declaration list per declared public member name.

    Raises:
        TypeError: The returned value, one of its keys, or a declaration has
            the wrong type.
        KeyError: A declared key is not a public member name.
        ValueError: The declarations combine incompatible nesting kinds.
    """
    if not isinstance(nested_raw, dict):
        msg = 'nested_configs() must return a dict'
        raise TypeError(msg)
    nested_configs: dict[str, list[ConfigNesting]] = {}
    for key, nesting_raw in nested_raw.items():
        if not isinstance(key, str):
            msg = 'nested_configs() keys must be strings'
            raise TypeError(msg)
        if key not in self_keys:
            msg = f'nested_configs() returned unknown key {key}'
            raise KeyError(msg)
        nested_configs[key] = _checked_config_nesting_list(
            key=key, nesting_raw=nesting_raw, config_base=config_base)
    return nested_configs


def _value_has_config(value: object, config_base: 'type[Config]') -> bool:
    """Return whether a default value visibly contains a Config object.

    Args:
        value: Default value of one public configuration member.
        config_base: Base class that a nested Config object derives from.

    Returns:
        ``True`` when the value is, or directly contains, a Config object.
    """
    if isinstance(value, config_base):
        return True
    if isinstance(value, list):
        return any(isinstance(item, config_base) for item in value)
    if isinstance(value, dict):
        return any(isinstance(item, config_base) for item in value.values())
    return False


def _check_nested_config_members(
        config: 'Config', self_keys: list[str],
        nested_configs: dict[str, list[ConfigNesting]],
        config_base: 'type[Config]') -> None:
    """Validate that visible nested Config defaults are declared.

    Args:
        config: Configuration object holding the default values.
        self_keys: Public member names of the configuration object.
        nested_configs: Checked declarations per public member name.
        config_base: Base class that a nested Config object derives from.

    Raises:
        TypeError: A default value contains a Config object for a member that
            ``nested_configs()`` does not declare.
    """
    for key in self_keys:
        if key in nested_configs:
            continue
        if _value_has_config(getattr(config, key), config_base):
            msg = f'Nested Config member {key} is not returned from '
            msg += 'nested_configs()'
            raise TypeError(msg)
