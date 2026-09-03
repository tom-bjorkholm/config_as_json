#! /usr/local/bin/python3
"""Test the config_as_json file extension utility functionality."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code


from copy import deepcopy
from pathlib import Path
from typing import Optional
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
                          ('/bin/ls/b', '.bo', '.fo', False, '/bin/ls/b.bo'),
                          ('/bin/ls', '.bo', None, True, '/bin/ls'),
                          ('/bin/ls', '.bo', None, False, '/bin/ls.bo'),
                          ('/bin/ls.bo', '.bo', None, True, '/bin/ls.bo'),
                          ('/bin/ls.BO', '.bo', None, False, '/bin/ls.BO'),
                          ('/bin/ls/b', '.bo', None, False, '/bin/ls/b.bo'),
                          ('rep.bo', '', None, False, 'rep.bo'),
                          ('rep.fo', '', '.fo', False, 'rep'),
                          ('a', '.bo', '.longer', False, 'a.bo'),
                          ('.bo', '.bo', '.fo', False, '.bo'),
                          ('.fo', '.bo', '.fo', False, '.bo')])
# pylint: disable-next=R0913,R0917,C0301
def test_file_extension_1(capsys: CaptureFixture[str], fil: str, add: str,
                          rem: Optional[str], readp: bool, res: str) -> None:
    """Test fix_file_extension.

    ``ext_to_remove`` is optional, and leaving it out only appends
    ``ext_to_add`` when the name does not already end with it.
    """
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


@pytest.mark.parametrize('fil, add, rem, res',
                         [('config.json.bak', '.json', '.bak', 'config.json'),
                          ('config.JSON.BAK', '.json', '.bak', 'config.JSON'),
                          ('a.bo.fo', '.bo', '.fo', 'a.bo'),
                          ('data.bo', '.bo', '.bo', 'data.bo'),
                          ('data.fo', '.bo', '.fo', 'data.bo')])
def test_add_after_remove(capsys: CaptureFixture[str], fil: str, add: str,
                          rem: str, res: str) -> None:
    """Test that the wanted extension is looked for after the removal.

    ``ext_to_remove`` is stripped before ``ext_to_add`` is applied, so a
    name that ends with ``ext_to_add`` once the removal has been made is
    already the wanted name and must not grow a second extension.
    """
    ret = fix_file_extension(filename=fil, ext_to_add=add, ext_to_remove=rem,
                             for_reading=False)
    out, err = capsys.readouterr()
    assert ret == res
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('name, rem', [('keep.fo', '.fo'),
                                       ('keep.bo', '.fo'),
                                       ('keep.bo', None)])
def test_for_reading_wins(tmp_path: Path, capsys: CaptureFixture[str],
                          name: str, rem: Optional[str]) -> None:
    """Test that an existing file is returned exactly as it was written.

    Reading asks for the file the user named. A name that exists is
    therefore used unchanged, even when the extension rules would have
    rewritten it.
    """
    existing = tmp_path / name
    existing.write_text('data', encoding='UTF-8')
    ret = fix_file_extension(filename=str(existing), ext_to_add='.bo',
                             ext_to_remove=rem, for_reading=True)
    out, err = capsys.readouterr()
    assert ret == str(existing)
    assert '' == out
    assert '' == err
