#! /usr/local/bin/python3
"""Support compatibility shims for the API migrations of this package.

Two migrations are supported here. A renamed hook is supported by calling
the old name when a subclass overrides it. A method or a constructor of an
application that does not accept the ``member_name`` argument is supported
by calling it without that argument. Both warn that the old way is
deprecated.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import inspect
import warnings
from types import FunctionType
from typing import Callable, NamedTuple, Optional


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


def _signature_takes_member_name(func: Callable[..., object]) -> bool:
    """Return whether the signature of a callable takes ``member_name``.

    A callable whose signature cannot be read is assumed to take the
    argument, because that keeps the behaviour it had before the argument
    could be left out.

    Args:
        func: Callable that the library is about to call.

    Returns:
        Whether the callable has a ``member_name`` parameter, or a
        ``**kwargs`` parameter that any keyword argument reaches.
    """
    try:
        parameters = inspect.signature(func).parameters
    except (TypeError, ValueError):
        return True
    if 'member_name' in parameters:
        return True
    return any(param.kind == inspect.Parameter.VAR_KEYWORD
               for param in parameters.values())


def _remembered_for(func: Callable[..., object]) -> Optional[object]:
    """Return what identifies the code of a callable, or ``None``.

    A plain function, a method, a class, and an object whose class defines
    ``__call__`` in Python, each identify their own code by an object that
    lives as long as the class it belongs to, so what was found out about
    them is worth remembering. Another kind of callable object, such as a
    ``functools.partial``, identifies its own signature by nothing that is
    safe to keep a reference to, so it is asked again every time.

    Args:
        func: Callable that the library is about to call.

    Returns:
        The key to remember the callable by, or ``None`` for a callable that
        must not be remembered.
    """
    underlying = getattr(func, '__func__', func)
    if isinstance(underlying, (FunctionType, type)):
        return underlying
    call_method = getattr(type(underlying), '__call__', None)
    return call_method if isinstance(call_method, FunctionType) else None


_MEMBER_NAME_TAKERS: dict[object, bool] = {}
_MEMBER_NAME_WARNED: set[object] = set()


def accepts_member_name(func: Callable[..., object]) -> bool:
    """Return whether a callable accepts the ``member_name`` argument.

    The answer is remembered per function and per class, so that the
    signature of an application method is read once instead of once per
    validated configuration object.

    Args:
        func: Callable that the library is about to call.

    Returns:
        Whether ``member_name`` can be passed to the callable.
    """
    key = _remembered_for(func)
    if key is None:
        return _signature_takes_member_name(func)
    remembered = _MEMBER_NAME_TAKERS.get(key)
    if remembered is None:
        remembered = _signature_takes_member_name(func)
        _MEMBER_NAME_TAKERS[key] = remembered
    return remembered


def _callable_name(func: Callable[..., object]) -> str:
    """Return the name of a callable as a diagnostic should spell it."""
    if isinstance(func, type):
        return f'{func.__qualname__}.__init__'
    name = getattr(func, '__qualname__', None)
    if isinstance(name, str):
        return name
    return f'{type(func).__qualname__}.__call__'


def _no_member_name_message(func: Callable[..., object]) -> str:
    """Return the message about a callable that omits ``member_name``."""
    msg = f'{_callable_name(func)}() does not accept the member_name '
    msg += "keyword argument. Add 'member_name: Optional[str] = None' to it "
    msg += 'and pass the value on, so that a diagnostic can name the whole '
    msg += 'path for reaching a value in a nested configuration, such as '
    msg += 'outputs[1].kind. Until then a diagnostic about a nested '
    msg += 'configuration names a plain member name. Leaving out '
    msg += 'member_name will stop working in a future major release.'
    return msg


def use_member_name(func: Callable[..., object], stacklevel: int) -> bool:
    """Return whether ``member_name`` should be passed to a callable.

    Warn about a callable that does not accept the argument, once for each
    function and each class that has to be changed, so that an application
    overriding two methods learns about both of them.

    Args:
        func: Callable that the library is about to call.
        stacklevel: Stack level that the warning is attributed to, counted
            from the caller of this function.

    Returns:
        Whether ``member_name`` can be passed to the callable.
    """
    if accepts_member_name(func):
        return True
    key = _remembered_for(func)
    if key is not None:
        if key in _MEMBER_NAME_WARNED:
            return False
        _MEMBER_NAME_WARNED.add(key)
    warnings.warn(_no_member_name_message(func), DeprecationWarning,
                  stacklevel=stacklevel + 1)
    return False
