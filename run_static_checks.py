#! /usr/bin/env python3
"""Thin wrapper calling static_checks in common_build_tools/src."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'common_build_tools' / 'src'))
from static_checks import static_checks_cmd    # noqa: E402


if __name__ == '__main__':
    static_checks_cmd()
