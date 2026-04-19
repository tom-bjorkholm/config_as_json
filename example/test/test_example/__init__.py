#! /usr/local/bin/python3
"""Test example programs for config-as-json."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from pathlib import Path
import sys


EXAMPLE_SRC = Path(__file__).resolve().parents[2] / 'src'
"""Source folder that contains the example package."""

if str(EXAMPLE_SRC) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_SRC))
