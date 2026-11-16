#! /usr/local/bin/python3
"""Teach an editor to start from defaults and to read an incomplete file.

An application that offers an editor for its configuration file has two
wishes that strict parsing does not fulfil:

- It wants to start editing from the values of a new configuration object,
  before any file has been opened.
- It wants to open a file that lacks some values, for example a file
  written by hand. The values that the file leaves out should not be
  errors, and the editor should be able to show the user which values
  those are.

Both are done with ``ok_to_use_defaults=True`` and
``Config.kept_value_paths()``:

- ``read(..., ok_to_use_defaults=True)`` accepts a file that lacks keys
  which strict parsing requires. A missing key keeps the value that it had
  when the read started. This holds at every nesting level.
- ``kept_value_paths()`` then returns the path of every value that was
  kept, so the editor can mark those values as not coming from the file.

Two kinds of values that do not come from the file are easily mixed up,
so this example uses two different words for them:

- The *starting values* are the values that a new ``ExampleConfig43()``
  holds. ``ExampleConfig43.__init__`` assigns them, also the values inside
  its nested objects. It sets ``logging.file`` to ``'reporting.log'``, and
  it gives its second backend the port 8081.
- The *class defaults* of a nested class are the values that the
  ``__init__`` of that nested class assigns. ``LoggingConfig`` assigns
  ``'service.log'`` to ``file``, and ``BackendConfig`` assigns 8080 to
  ``port``.

The file decides which nested objects exist, and that decides which of the
two a missing value gets:

- A member that the file lacks altogether keeps its starting value. That
  holds for a whole nested object too.
- A nested member that the file contains is read into the nested object
  that the configuration already holds. A value that the file lacks inside
  it keeps its starting value. A file that has ``"logging"`` without
  ``"file"`` gives ``logging.file`` the starting value ``'reporting.log'``.
- A list of nested objects that the file contains replaces the whole
  starting list. The list gets exactly the elements of the file, and every
  element is a new object, so a value that the file lacks inside an element
  gets the class default. A second backend without ``"port"`` gets the
  class default 8080, not the starting value 8081 of the second backend in
  the starting list.

Run the example to see it:

```sh
python3 -m example.e43_editor_defaults set -o /tmp/editor.cfg \
  --logging '{"level": "DEBUG"}' \
  --backends '[{"host": "alpha", "port": 9090}, {"host": "beta"}]'
python3 -m example.e43_editor_defaults print -i /tmp/editor.cfg
```
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from typing import Optional, TextIO, override
from config_as_json import Config, ConfigNesting, ConfigNestingKind, \
    ConfigParseError, InvalidConfiguration, InvalidConfigurationValue, \
    JsonPath, JsonType, member_path, NestedConfigs, PathOrStr, \
    ValidationPlan
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class LoggingConfig(Config):
    """Logging settings of the service."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None, *,
                 ok_to_use_defaults: bool = False) -> None:
        """Initialize the logging settings.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Path for reaching this object from the top level
                configuration. ``None`` means that this object is the whole
                configuration and not a member of anything.
            ok_to_use_defaults: Whether the JSON data may lack values, which
                then keep the class defaults assigned here.
        """
        self.level: str = 'INFO'
        self.file: str = 'service.log'
        # Accepting ok_to_use_defaults and passing it on is a good habit for
        # every Config class. It is only required for a nested class whose
        # class defaults are not valid on their own. A nested class that
        # does not accept it can still be read from JSON data that lacks
        # values: the library then constructs it with its class defaults
        # first, and reads the JSON data into it.
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name,
                         ok_to_use_defaults=ok_to_use_defaults)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan."""
        _ = stderr_file
        return []


# The backends below are the same as in example e42, so that this example
# can be read on its own. Keeping each example self-contained is what lets a
# reader learn from it, so the similarity is suppressed rather than factored
# out.
# pylint: disable=duplicate-code
class BackendConfig(Config):
    """Configuration for one backend that the service forwards to."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None, *,
                 ok_to_use_defaults: bool = False) -> None:
        """Initialize one backend configuration.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Path for reaching this object from the top level
                configuration. ``None`` means that this object is the whole
                configuration and not a member of anything.
            ok_to_use_defaults: Whether the JSON data may lack values, which
                then keep the class defaults assigned here.
        """
        # These are the class defaults of BackendConfig. Every backend that
        # the file contains is a new BackendConfig, so a value that the file
        # lacks for it gets its class default from here, see ExampleConfig43.
        self.host: str = 'localhost'
        self.port: int = 8080
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name,
                         ok_to_use_defaults=ok_to_use_defaults)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan."""
        _ = stderr_file
        return []


class ExampleConfig43(Config):
    """Configuration with a nested member and a list of nested backends."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None, *,
                 ok_to_use_defaults: bool = False) -> None:
        """Initialize the service configuration.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Path for reaching this object from the top level
                configuration. ``None`` means that this object is the whole
                configuration and not a member of anything.
            ok_to_use_defaults: Whether the JSON data may lack values, which
                then keep the starting values assigned here.
        """
        self.service_name: str = 'reporting'
        self.logging: LoggingConfig = LoggingConfig(stderr_file=stderr_file)
        # The values assigned in this __init__ are the starting values of the
        # configuration. Here the starting value of logging.file is set to
        # 'reporting.log', so it differs from the class default
        # 'service.log' of LoggingConfig.
        #
        # When a file contains "logging" but lacks "file", the file is read
        # into this very LoggingConfig object. So logging.file keeps its
        # starting value 'reporting.log'.
        self.logging.file = 'reporting.log'
        self.backends: list[BackendConfig] = [
            BackendConfig(stderr_file=stderr_file),
            BackendConfig(stderr_file=stderr_file)]
        # The starting list has two backends. The second one gets starting
        # values that differ from the class defaults of BackendConfig.
        #
        # These starting values are only used when the file lacks
        # "backends" altogether. A file that contains "backends" replaces
        # the whole starting list, and every backend in the file is a new
        # BackendConfig. So a second backend in the file that lacks "port"
        # gets the class default 8080, not the starting value 8081.
        self.backends[1].host = 'backup'
        self.backends[1].port = 8081
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name,
                         ok_to_use_defaults=ok_to_use_defaults)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        return {
            'logging': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                     config_type=LoggingConfig),
            'backends': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                      config_type=BackendConfig)
        }

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan."""
        _ = stderr_file
        return []


# pylint: enable=duplicate-code


def _path_text(path: JsonPath) -> str:
    """Return the path text that a diagnostic would use for a JsonPath.

    Args:
        path: Keys and list indexes from the root of the JSON data.

    Returns:
        Text such as ``backends[1].port``.
    """
    # A JsonPath is a tuple, such as ('backends', 1, 'port'). A str is a key
    # of a JSON object and an int is an index into a JSON list. This example
    # shows it in the same notation as the diagnostics, see example e42.
    # (A plain dict member would also give str keys, and they would then be
    # shown with a dot. This configuration has no plain dict member.)
    text: Optional[str] = None
    for step in path:
        if isinstance(step, int):
            text = f'{text}[{step}]'
        else:
            text = member_path(text, step)
    assert text is not None
    return text


def _json_leaves(value: JsonType,
                 path: JsonPath) -> list[tuple[JsonPath, JsonType]]:
    """Return every value in JSON data that is not a JSON object or list.

    Args:
        value: JSON data, or a part of it.
        path: Path of ``value`` from the root of the JSON data.

    Returns:
        The path and the value of each leaf, in the order of the data.
    """
    if isinstance(value, dict):
        return [leaf for key, item in value.items()
                for leaf in _json_leaves(item, path + (key,))]
    if isinstance(value, list):
        return [leaf for index, item in enumerate(value)
                for leaf in _json_leaves(item, path + (index,))]
    return [(path, value)]


def _not_from_file(path: JsonPath, kept_paths: list[JsonPath]) -> bool:
    """Return whether the value at ``path`` was not in the file.

    Args:
        path: Path of one leaf value from the root of the JSON data.
        kept_paths: The paths returned by ``kept_value_paths()``.

    Returns:
        True when the value did not come from the file.
    """
    # kept_value_paths() names only the outermost absent key. When the whole
    # "logging" member is absent from the file, it reports ('logging',) and
    # not the paths of "level" and "file" inside it. So a value did not come
    # from the file when its own path, or the path of anything holding it,
    # was kept. That is when a kept path is the beginning of its path.
    return any(path[:len(kept)] == kept for kept in kept_paths)


def _kept_text(kept_paths: list[JsonPath]) -> str:
    """Return the kept paths as text, or ``none``.

    Args:
        kept_paths: The paths returned by ``kept_value_paths()``.

    Returns:
        The path texts separated by commas.
    """
    # The order of kept_value_paths() is not guaranteed, so the texts are
    # sorted to give a stable printout.
    texts = sorted(_path_text(path) for path in kept_paths)
    return ', '.join(texts) if texts else 'none'


def _print_marked_values(config: ExampleConfig43,
                         kept_paths: list[JsonPath]) -> None:
    """Print every value, marking those that did not come from the file.

    Args:
        config: Configuration read with ``ok_to_use_defaults=True``.
        kept_paths: The paths returned by ``kept_value_paths()``.
    """
    # The paths of kept_value_paths() are paths in the JSON data, so the
    # simplest way to find every value and its path is to walk the JSON data
    # that the configuration writes.
    json_data = json.loads(config.as_json_string(stderr_file=sys.stderr,
                                                 member_name=None))
    # A value that did not come from the file is a starting value or a class
    # default. The marker does not say which, since the editor only needs to
    # show that the file did not contain the value.
    for path, value in _json_leaves(json_data, ()):
        marker = '  (not in file)' if _not_from_file(path, kept_paths) \
            else ''
        print(f'{_path_text(path)}: {value}{marker}')


def e43_editor_print(config_file: PathOrStr) -> None:
    """Read a possibly incomplete file the way an editor does.

    Args:
        config_file: Path to the configuration file to read.
    """
    # An editor starts with a new configuration object, which holds the
    # starting values. It can show and edit them before any file has been
    # opened.
    config = ExampleConfig43()
    try:
        # Then it opens a file. With ok_to_use_defaults=True a key that the
        # file lacks is not an error. The value gets its starting value, or
        # the class default inside a list element, as the module docstring
        # explains. A key that the file has but that the class does not
        # declare is still an error, and so is a value of a wrong shape.
        #
        # (Reading into a new object in one step also works:
        # ExampleConfig43(from_json_filename=..., ok_to_use_defaults=True))
        config.read(config_file, ok_to_use_defaults=True,
                    stderr_file=sys.stderr, member_name=None)
    except (ConfigParseError, InvalidConfiguration,
            InvalidConfigurationValue):
        return  # Error already printed by the Config object.
    print(f'Configuration read from {config_file}')
    # kept_value_paths() tells which values the file did not contain. It is
    # a new list of JsonPath tuples. After a read that found every value it
    # is empty, and so it is after a strict read.
    kept_paths = config.kept_value_paths()
    print(f'Not in the file: {_kept_text(kept_paths)}')
    _print_marked_values(config, kept_paths)


def e43_editor_set(set_values: SetValues, config_file: PathOrStr) -> None:
    """Write only the given values, which makes an incomplete file.

    Args:
        set_values: The values given on the command line.
        config_file: Path where to write the configuration file.
    """
    # Every other example writes with Config.write(), which writes every
    # value. This one deliberately writes only the values given on the
    # command line, as plain JSON, to make the kind of incomplete file that
    # the print command is about.
    with open(config_file, 'w', encoding='UTF-8') as file:
        json.dump(set_values, file, indent=4)
    print(f'Configuration written to {config_file}')


INPUT_SPECS = [
    InputSpec(name='service_name', single=True, value_type=str),
    # The nested values are given as JSON, so that a run can leave out keys
    # at any nesting level, such as --logging '{"level": "DEBUG"}'.
    InputSpec(name='logging', single=True, value_type=str, json_value=True),
    InputSpec(name='backends', single=True, value_type=str, json_value=True)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e43_editor_defaults',
                      input_specs=INPUT_SPECS, set_command=e43_editor_set,
                      print_command=e43_editor_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
