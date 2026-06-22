#! /usr/local/bin/python3
"""Test the file_must_exist function."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from pathlib import Path
from typing import Optional
from io import StringIO
import pytest
from config_as_json.file_must_exist import file_must_exist


@pytest.mark.parametrize('exi, exc',
                         [(True, SystemExit), (False, FileNotFoundError)])
@pytest.mark.parametrize('cre, rai', [(True, False), (False, True)])
@pytest.mark.parametrize('cont', [None, 'abxz', 'cdef'])
# pylint: disable-next=too-many-arguments, too-many-positional-arguments
def test_file_must_exist(tmp_path: Path, exi: bool, exc: type[Exception],
                         cre: bool, rai: bool, cont: Optional[str]) -> None:
    """Test combinations of file_must_exist."""
    filename = tmp_path / 'file.txt'
    err_file = StringIO()
    if cre:
        filename.write_text('file contents')
    if rai:
        with pytest.raises(exc) as exc_info:
            file_must_exist(filename=filename, with_content_txt=cont,
                            stderr_file=err_file, exit_if_missing=exi)
        assert exc_info.type is exc
        printed = err_file.getvalue()
        if cont is not None:
            assert cont in printed
        assert 'does not exist' in printed
    else:
        file_must_exist(filename=filename, with_content_txt=cont,
                        stderr_file=err_file, exit_if_missing=exi)
        assert err_file.getvalue() == ''
