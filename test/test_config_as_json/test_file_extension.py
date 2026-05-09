#! /usr/local/bin/python3
"""Test the config_as_json file extension utility functionality."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code


from copy import deepcopy
import pytest
from pytest import CaptureFixture
from config_as_json.file_extension import fix_file_extension


@pytest.mark.parametrize('fil, add, rem, readp, res',
                         [('/bin/ls', '.bo', '.fo', True, '/bin/ls'),
                          ('/bin/ls', '.bo', '.fo', False, '/bin/ls.bo'),
                          ('/bin/ls.bo', '.bo', '.fo', True, '/bin/ls.bo'),
                          ('/bin/ls.bo', '.bo', '.fo', False, '/bin/ls.bo'),
                          ('/bin/ls.fo', '.bo', '.fo', True, '/bin/ls.bo'),
                          ('/bin/ls.fo', '.bo', '.fo', False, '/bin/ls.bo'),
                          ('/bin/ls/b', '.bo', '.fo', True, '/bin/ls/b.bo'),
                          ('/bin/ls/b', '.bo', '.fo', False, '/bin/ls/b.bo')])
# pylint: disable-next=R0913,R0917,C0301
def test_file_extension_1(capsys: CaptureFixture[str], fil: str, add: str,
                          rem: str, readp: bool, res: str) -> None:
    """Test fix_file_extension."""
    filn = deepcopy(fil)
    addn = deepcopy(add)
    remn = deepcopy(rem)
    readn = deepcopy(readp)
    ret = fix_file_extension(filename=filn, ext_to_add=addn,
                             ext_to_remove=remn, for_reading=readn)
    out, err = capsys.readouterr()
    assert filn == fil
    assert addn == add
    assert remn == rem
    assert readn == readp
    assert ret == res
    assert '' == out
    assert '' == err
