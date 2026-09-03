#! /usr/local/bin/python3
"""Test the kinds of callable that the ``member_name`` layer has to call.

The compatibility layer reads the signature of the application code the
library is about to call. It remembers the answer for a plain function, a
method, a class and a callable object, because each of those identifies its
own code by something that lives as long as the class it belongs to. A
``functools.partial`` identifies nothing that is safe to keep a reference
to, so it is asked again, and warned about again, every time. A callable
whose signature Python does not expose is called with the argument, which
is what the version before the argument existed did.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import inspect
import sys
from functools import partial
from typing import Callable, Optional, TextIO, override
import pytest
from config_as_json._deprecated_support import accepts_member_name, \
    use_member_name
from config_as_json.commontypes import PathOrStr
from config_as_json.config import Config
from config_as_json.config_nesting import ConfigFactory, ConfigNesting, \
    ConfigNestingKind, NestedConfigs
from config_as_json.validator import ValidationPlan
from .member_name_compat_tools import HOLDER_JSON, PlainLeaf, deprecations


class FactoryHolder(Config):
    """A configuration whose nested member is made by a supplied factory."""

    def __init__(self, factory: ConfigFactory,
                 from_json_data_text: Optional[str] = None,
                 member_name: Optional[str] = None) -> None:
        """Construct one holder using the supplied nested factory."""
        self._factory = factory
        self.part = PlainLeaf()
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the one nested Config declaration."""
        return {'part': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                      config_type=PlainLeaf,
                                      factory_function=self._factory)}

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation plan of its own."""
        _ = stderr_file
        return []


def _leaf_old(marker: str, *, from_json_data_text: Optional[str] = None,
              from_json_filename: Optional[PathOrStr] = None,
              stderr_file: TextIO = sys.stderr) -> Config:
    """Construct one nested leaf without accepting ``member_name``."""
    _ = marker
    return PlainLeaf(from_json_data_text=from_json_data_text,
                     from_json_filename=from_json_filename,
                     stderr_file=stderr_file)


def test_partial_warns_again() -> None:
    """A partial that leaves out ``member_name`` is warned about again.

    Nothing that lives as long as a class identifies the code of a
    ``functools.partial``, so the layer has nothing to remember it by and
    reads its signature for every construction.
    """
    factory = partial(_leaf_old, 'legacy')
    made: list[FactoryHolder] = []

    def action() -> None:
        """Construct one holder, which uses the partial factory."""
        made.append(FactoryHolder(factory, from_json_data_text=HOLDER_JSON))

    messages = deprecations(action)
    assert len(messages) == 1
    assert 'partial.__call__() does not accept the member_name' in messages[0]
    assert len(deprecations(action)) == 1
    assert isinstance(made[-1].part, PlainLeaf)
    assert made[-1].part.kind == 'parsed'


def test_partial_told_path() -> None:
    """A partial that accepts ``member_name`` is told the whole path."""
    told: list[Optional[str]] = []

    def make_leaf(marker: str, *, from_json_data_text: Optional[str] = None,
                  from_json_filename: Optional[PathOrStr] = None,
                  stderr_file: TextIO = sys.stderr,
                  member_name: Optional[str] = None) -> Config:
        """Construct one nested leaf, recording the path it was told."""
        _ = marker
        told.append(member_name)
        return PlainLeaf(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def action() -> Config:
        """Construct one holder below a named member."""
        return FactoryHolder(partial(make_leaf, 'modern'),
                             from_json_data_text=HOLDER_JSON,
                             member_name='outputs[1]')

    assert deprecations(action) == []
    assert told == ['outputs[1].part']


def test_object_warns_once() -> None:
    """A callable object that leaves out ``member_name`` warns once.

    The answer is remembered by the ``__call__`` of its class, so a second
    object of the same class is not asked, and is not warned about.
    """
    # pylint: disable-next=too-few-public-methods
    class LegacyFactory:
        """An application factory written before the argument existed."""

        def __call__(self, *, from_json_data_text: Optional[str] = None,
                     from_json_filename: Optional[PathOrStr] = None,
                     stderr_file: TextIO = sys.stderr) -> Config:
            """Construct one nested leaf the old way."""
            return PlainLeaf(from_json_data_text=from_json_data_text,
                             from_json_filename=from_json_filename,
                             stderr_file=stderr_file)

    def build(factory: LegacyFactory) -> Callable[[], Config]:
        """Return an action constructing one holder with the factory."""
        return lambda: FactoryHolder(factory,  # type: ignore[arg-type]
                                     from_json_data_text=HOLDER_JSON)

    messages = deprecations(build(LegacyFactory()))
    assert len(messages) == 1
    assert 'LegacyFactory.__call__() does not accept' in messages[0]
    assert deprecations(build(LegacyFactory())) == []


@pytest.mark.parametrize('func', [min, max, iter])
def test_unreadable_signature(func: Callable[..., object]) -> None:
    """A callable Python cannot describe is assumed to take the argument."""
    with pytest.raises(ValueError):
        _ = inspect.signature(func)
    assert accepts_member_name(func)
    assert deprecations(lambda: use_member_name(func, stacklevel=2)) == []


def test_hidden_signature() -> None:
    """A callable that hides its signature is assumed to take the argument.

    Which error Python fails with depends on the Python version, and the
    compatibility layer treats every one of them as an unreadable
    signature.
    """
    # pylint: disable-next=too-few-public-methods
    class HiddenFactory:
        """A callable whose ``__signature__`` cannot be interpreted."""

        __signature__ = 'hidden'

        def __call__(self, *, stderr_file: TextIO = sys.stderr) -> None:
            """Accept the one argument that the test hands it."""
            _ = stderr_file

    factory = HiddenFactory()
    with pytest.raises((TypeError, ValueError)):
        _ = inspect.signature(factory)
    assert accepts_member_name(factory)
    assert deprecations(lambda: use_member_name(factory, stacklevel=2)) == []
