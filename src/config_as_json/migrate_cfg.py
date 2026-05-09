#! /usr/local/bin/python3
"""Migrate an older configuration file to the newest supported format."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from collections.abc import Sequence
from os.path import exists
from typing import TextIO, cast
import sys
from config_as_json.config import Config
from config_as_json.config_factory import config_factory_from_json, \
    MatchConfig, MatchConfigSeq
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.commontypes import PathOrStr


def _match_config_seq(config_class: object) -> MatchConfigSeq:
    """Validate and return matcher/class pairs for configuration selection.

    Args:
        config_class: Object supplied as the ``config_class`` argument to
            ``migrate_cfg``.

    Returns:
        The validated matcher/class pair sequence.

    Raises:
        TypeError: ``config_class`` is not a valid selector.
    """
    msg = 'config_class must be a Config subclass or a MatchConfig sequence'
    if isinstance(config_class, (str, bytes, bytearray)):
        raise TypeError(msg)
    if not isinstance(config_class, Sequence):
        raise TypeError(msg)
    if not config_class:
        raise TypeError('config_class must not be an empty MatchConfig '
                        'sequence')
    if not all(isinstance(item, MatchConfig) for item in config_class):
        raise TypeError('config_class MatchConfig sequence contains '
                        'non-MatchConfig items')
    return cast(MatchConfigSeq, config_class)


def migrate_cfg(infile: PathOrStr, outfile: PathOrStr,
                config_class: type[Config] | MatchConfigSeq,
                stderr_file: TextIO = sys.stderr) -> int:
    """Read an old configuration file and write it back in current format.

    The input file is parsed through the normal read old configuration file
    (ROCF) mechanisms of the registered configuration classes. The normalized
    in-memory configuration is then written to ``outfile`` using the current
    schema and key names.

    The ``config_class`` argument can be either:
    - The configuration class to use (when reading ``infile`` and
      writing ``outfile``).
    - An ordered matcher/class pairs used to choose the correct configuration
      class to use (when reading ``infile`` and writing ``outfile``).

    The normal case is to use a single configuration class.

    When the application supports multiple configuration variants, the
    ``config_class`` argument can be an ordered sequence of matcher/class
    pairs used to choose the correct configuration class for ``infile``.
    Multiple variants are for different configuration classes like for
    instance Config2D and Config3D for a CAD application.

    Multiple variants shall not be confused with multiple versions of the
    same variant. A migration is always done between two versions of the
    same variant.

    Args:
        infile: Existing configuration file to migrate.
        outfile: Destination path for the migrated configuration file.
        config_class: Either the configuration class to use,
                      or an ordered sequence of matcher/class pairs used to
                      choose the correct configuration class (for applications
                      with multiple configuration variants) to use.
        stderr_file: Stream used for user-facing diagnostics. Defaults to
                     ``sys.stderr``.

    Returns:
        ``0`` after a successful migration.

    Raises:
        SystemExit: ``infile`` does not exist or ``outfile`` already exists,
                    or no matcher accepts ``infile``.
        TypeError: ``config_class`` is neither a ``Config`` subclass nor a
                   non-empty sequence of ``MatchConfig`` items.
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
    if isinstance(config_class, type) and issubclass(config_class, Config):
        cfg = config_class(from_json_data_text=None, from_json_filename=infile,
                           auto_ch_hook=ConfigAutoChangeHook(),
                           stderr_file=stderr_file)
        cfg.write(to_json_filename=outfile)
        return 0
    match_configs = _match_config_seq(config_class)
    cfg = config_factory_from_json(match_configs=match_configs,
                                   from_json_filename=infile,
                                   from_json_data_text=None,
                                   auto_ch_hook=ConfigAutoChangeHook(),
                                   stderr_file=stderr_file)
    cfg.write(to_json_filename=outfile)
    return 0
