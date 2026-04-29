#! /usr/local/bin/python3
"""Choose a configuration class by looking at JSON before parsing it.

Some applications can run in more than one mode. A CAD program may for
example run in a 2D drawing mode or in a 3D modeling mode. The file that the
program starts with may also be the file that decides which mode to use.

This example teaches the small config factory pattern for that case:

- register one matcher for each supported file shape
- let each matcher inspect the raw JSON text
- construct the configuration class selected by the first matching rule
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO
from config_as_json import Config, ConfigAutoChangeHook, \
    config_factory_from_json, JsonValueMatcher, MatchConfig, MatchConfigSeq, \
    PathOrStr, ValidationPlan
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


MODE_2D = '2D'
"""Command-line mode used for 2D configuration files."""

MODE_3D = '3D'
"""Command-line mode used for 3D configuration files."""

DEFAULT_MODE = MODE_2D
"""Mode written by the ``set`` command when no mode is selected."""


class Cad2DConfig(Config):
    """Configuration for the 2D drawing mode of the example application."""

    def __init__(self,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the 2D configuration.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            auto_ch_hook: Hook notified if automatic changes are made.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.mode: str = MODE_2D
        self.project_name: str = 'demo-part'
        self.grid_size_mm: float = 1.0
        self.drawing_plane: str = 'XY'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        return []


class Cad3DConfig(Config):
    """Configuration for the 3D modeling mode of the example application."""

    def __init__(self,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the 3D configuration.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            auto_ch_hook: Hook notified if automatic changes are made.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.space: str = MODE_3D
        self.project_name: str = 'demo-part'
        self.grid_size_mm: float = 1.0
        self.default_view: str = 'isometric'
        self.show_shadows: bool = True
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        return []


# The selector key does not need to be modeled the same way in every class.
# Here the 2D config is selected by ``mode`` and the 3D config by ``space`` to
# make that visible. In a real application both classes could instead have
# one ``mode`` member with different values, or inherit a common selector
# member from a base class.
MATCH_CONFIGS: MatchConfigSeq = [
    MatchConfig(match_func=JsonValueMatcher('mode', MODE_2D),
                config_class=Cad2DConfig),
    MatchConfig(match_func=JsonValueMatcher('space', MODE_3D),
                config_class=Cad3DConfig)
]
"""Factory rules used to select the configuration class from JSON."""


def e32_config_factory_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show which class was selected.

    Read a CAD configuration file through the config factory.
    Args:
        config_file: Path to the configuration file to read.
    """
    config = config_factory_from_json(match_configs=MATCH_CONFIGS,
                                      auto_ch_hook=ConfigAutoChangeHook(),
                                      from_json_filename=config_file,
                                      stderr_file=sys.stderr)
    print(f'Configuration read from {config_file}')
    if isinstance(config, Cad2DConfig):
        print('Configuration class: Cad2DConfig')
        print(f'Selector mode: {config.mode}')
        print(f'Project name: {config.project_name}')
        print(f'Grid size: {config.grid_size_mm} mm')
        print(f'Drawing plane: {config.drawing_plane}')
        return
    assert isinstance(config, Cad3DConfig)
    print('Configuration class: Cad3DConfig')
    print(f'Selector space: {config.space}')
    print(f'Project name: {config.project_name}')
    print(f'Grid size: {config.grid_size_mm} mm')
    print(f'Default view: {config.default_view}')
    print(f'Show shadows: {config.show_shadows}')


# -----------------------------------------------------------------------------
# Only command line handling follows. The factory lesson is above.
# The functions below only let the example write small demo files from the
# command line, so they are not the point this example is trying to teach.
# -----------------------------------------------------------------------------


def _normalized_mode(mode: str) -> str:
    """Return a canonical command-line mode value.

    Args:
        mode: Mode text supplied by the user.

    Returns:
        The canonical mode value used by the writer helper.

    Raises:
        ValueError: The mode is not known by this example.
    """
    lowered = mode.lower()
    if lowered == MODE_2D.lower():
        return MODE_2D
    if lowered == MODE_3D.lower():
        return MODE_3D
    raise ValueError(f'Unknown CAD mode: {mode}')


def _mode_from_set_values(set_values: SetValues) -> str:
    """Return the selected mode from command line values.

    Args:
        set_values: Values that should differ from the defaults.

    Returns:
        The canonical mode value for the configuration to write.
    """
    mode_value = set_values.get('mode', DEFAULT_MODE)
    assert isinstance(mode_value, str)
    return _normalized_mode(mode_value)


def _default_config_for_mode(mode: str) -> Cad2DConfig | Cad3DConfig:
    """Create a default configuration object for one mode.

    Args:
        mode: Canonical mode value.

    Returns:
        A default configuration object for the requested mode.

    Raises:
        ValueError: The mode is not known by this example.
    """
    if mode == MODE_2D:
        return Cad2DConfig()
    if mode == MODE_3D:
        return Cad3DConfig()
    raise ValueError(f'Unknown CAD mode: {mode}')


def _apply_common_set_values(config: Cad2DConfig | Cad3DConfig,
                             set_values: SetValues) -> None:
    """Apply shared command-line values to one CAD configuration.

    Args:
        config: Configuration object that should receive the values.
        set_values: Values that should differ from the defaults.

    Raises:
        ValueError: The command line helper supplied an unknown key.
    """
    for key, value in set_values.items():
        if key == 'mode':
            continue
        if key == 'project_name':
            assert isinstance(value, str)
            config.project_name = value
        elif key == 'grid_size_mm':
            assert isinstance(value, float)
            config.grid_size_mm = value
        else:
            raise ValueError(f'Invalid key: {key}')


def e32_config_factory_set(set_values: SetValues,
                           config_file: PathOrStr) -> None:
    """Create the selected CAD configuration and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    mode = _mode_from_set_values(set_values)
    config = _default_config_for_mode(mode)
    _apply_common_set_values(config, set_values)
    config.write(to_json_filename=config_file)
    print(f'Configuration written to {config_file}')


INPUT_SPECS = [
    InputSpec(name='mode', single=True, value_type=str),
    InputSpec(name='project_name', single=True, value_type=str),
    InputSpec(name='grid_size_mm', single=True, value_type=float)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e32_config_factory',
                      input_specs=INPUT_SPECS,
                      set_command=e32_config_factory_set,
                      print_command=e32_config_factory_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
