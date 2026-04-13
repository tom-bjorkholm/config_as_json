#! /usr/local/bin/python3
"""The test cases string_to_enum_best_match function."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code


from enum import Enum, auto
import pytest
from config_as_json.str_to_enum import string_to_enum_best_match


class YesNoAsk(Enum):
    """Enum for enum testing."""

    YES = auto()
    NO = auto()
    ASK = auto()


#  pylint: disable=invalid-name


class Tty(Enum):
    """Stupid enum just to test enum_prompt."""

    Teletype = auto()  # pylint: disable=invalid-name
    Telematic = auto()  # pylint: disable=invalid-name
    VT52 = auto()  # pylint: disable=invalid-name
    VT100 = auto()  # pylint: disable=invalid-name
    X = auto()  # pylint: disable=invalid-name


@pytest.mark.parametrize('x,y', [('telet', Tty.Teletype), ('VT52', Tty.VT52)])
def test_string_to_enum_best_match_match(x, y):
    """Test string to best match function."""
    z = string_to_enum_best_match(x, Tty)
    assert z == y


@pytest.mark.parametrize('x,y',
                         [('Teletype', Tty.Teletype),
                          ('teleType', Tty.Teletype),
                          ('telet', Tty.Teletype),
                          ('Telematic', Tty.Telematic),
                          ('teleMatic', Tty.Telematic),
                          ('telem', Tty.Telematic),
                          ('VT52', Tty.VT52),
                          ('VT5', Tty.VT52),
                          ('vt5', Tty.VT52),
                          ('VT100', Tty.VT100),
                          ('VT1', Tty.VT100),
                          ('vt1', Tty.VT100),
                          ('X', Tty.X),
                          ('x', Tty.X)])
def test_string_to_enum_best_match_match2(x, y):
    """Test string to best match function."""
    z = string_to_enum_best_match(x, Tty)
    assert z == y


@pytest.mark.parametrize('x', ['foobar', 'tele', 'vt', 'Tele', 'VT'])
def test_string_to_enum_best_match_bad(x):
    """Test string to best match function with bad input."""
    with pytest.raises(KeyError):
        z = string_to_enum_best_match(x, Tty)
        assert z == 'no match'  # never reached


def test_string_to_enum_bmatch_int():
    """Test string_to_enum_best_match with int not str input."""
    with pytest.raises(AssertionError) as exc:
        _ = string_to_enum_best_match(5, YesNoAsk)
    assert 'string_to_enum_best_match called with int not str' in str(exc)
