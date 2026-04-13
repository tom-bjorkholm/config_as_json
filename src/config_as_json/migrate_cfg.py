#! /usr/local/bin/python3
"""Check and assert that dicts are equal ignoring some keys."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License

import sys
from os.path import exists
from config_as_json.config_factory import config_factory_from_json
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook


def migrate_cfg(infile: str, outfile: str) -> int:
    """Migrate configuration to newest format.

    Read in input configuration file using backward compatibility.
    Write out configuration using newest format.
    @param infile  Name of input configuation file.
    @param outfile Name of output configuration file.
    """
    if not exists(infile):
        print(f'Cannot find input configuration file {infile}',
              file=sys.stderr)
        sys.exit(1)
    if exists(outfile):
        print(f'Output configuration file {outfile} already exists.\n' +
              'Cowardly refusing to overwrite existing configuration file.',
              file=sys.stderr)
        sys.exit(1)
    cfg = config_factory_from_json(from_json_filename=infile,
                                   auto_ch_hook=ConfigAutoChangeHook())
    cfg.write(to_json_filename=outfile)
    return 0
