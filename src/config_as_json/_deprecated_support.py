#! /usr/local/bin/python3
"""Support compatibility shims for renamed internal hooks."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import warnings
from typing import NamedTuple


class DeprecatedHook(NamedTuple):
    """Describe a hook that was renamed during API migration."""

    owner_name: str
    old_name: str
    new_name: str


def method_is_overridden(instance: object, method_name: str,
                         base_class: type[object]) -> bool:
    """Return whether a method is overridden below a base class."""
    for cls in type(instance).__mro__:
        if method_name in cls.__dict__:
            return cls is not base_class
    raise AttributeError(method_name)


def warn_deprecated_hook(hook: DeprecatedHook, stacklevel: int) -> None:
    """Warn that a deprecated hook name was used."""
    msg = f'{hook.owner_name}.{hook.old_name}() is deprecated; '
    msg += f'use {hook.new_name}() instead.'
    warnings.warn(msg, DeprecationWarning, stacklevel=stacklevel)


def use_deprecated_hook(instance: object, base_class: type[object],
                        hook: DeprecatedHook, stacklevel: int) -> bool:
    """Return whether a deprecated hook override should be used."""
    old_overridden = method_is_overridden(instance, hook.old_name, base_class)
    new_overridden = method_is_overridden(instance, hook.new_name, base_class)
    if not old_overridden:
        return False
    if new_overridden:
        msg = f'{hook.owner_name} subclass overrides both '
        msg += f'{hook.old_name}() and {hook.new_name}(). '
        msg += f'Remove deprecated {hook.old_name}().'
        raise TypeError(msg)
    warn_deprecated_hook(hook, stacklevel=stacklevel)
    return True
