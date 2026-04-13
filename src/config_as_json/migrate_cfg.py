#! /usr/local/bin/python3
"""Migrate an older configuration file to the newest supported format."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License

from typing import TextIO
import sys
from os.path import exists
from config_as_json.config_factory import config_factory_from_json, \
    MatchConfigSeq
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.commontypes import PathOrStr


def migrate_cfg(infile: PathOrStr, outfile: PathOrStr,
                match_configs: MatchConfigSeq,
                stderr_file: TextIO = sys.stderr) -> int:
    """Read an old configuration file and write it back in current format.

    The input file is parsed through the normal backward-compatibility
    mechanisms of the registered configuration classes. The normalized
    in-memory configuration is then written to ``outfile`` using the current
    schema and key names.

    Args:
        infile: Existing configuration file to migrate.
        outfile: Destination path for the migrated configuration file.
        match_configs: Ordered matcher/class pairs used to choose the correct
            configuration class for ``infile``.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        ``0`` after a successful migration.

    Raises:
        SystemExit: ``infile`` does not exist or ``outfile`` already exists.
    """
    if not exists(infile):
        print(f'Cannot find input configuration file {infile}',
              file=stderr_file)
        sys.exit(1)
    if exists(outfile):
        print(f'Output configuration file {outfile} already exists.\n' +
              'Cowardly refusing to overwrite existing configuration file.',
              file=stderr_file)
        sys.exit(1)
    cfg = config_factory_from_json(match_configs=match_configs,
                                   from_json_filename=infile,
                                   from_json_data_text=None,
                                   auto_ch_hook=ConfigAutoChangeHook(),
                                   stderr_file=stderr_file)
    cfg.write(to_json_filename=outfile)
    return 0
