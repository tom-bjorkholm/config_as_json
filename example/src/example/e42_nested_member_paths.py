#! /usr/local/bin/python3
"""Teach the paths that diagnostics report for nested Config objects.

Every earlier nested example showed how to *build* nested configuration.
This example is about what the user of the configuration file is *told* when
a value inside a nested object is wrong.

A complete configuration usually has the same member name in more than one
place. This example has ``port`` twice: the port the service itself listens
on, and the port of each backend it forwards to. Telling the user only that
``port`` is invalid is useless, because the user has to guess which of the
three ports the message is about.

Therefore every diagnostic names the whole path from the top level
configuration down to the value it is about:

- the port of the service is reported as ``port``
- the port of the second backend is reported as ``backends[1].port``

The notation has two rules:

- going into an attribute of a nested Config object appends a dot and the
  attribute name, as in ``section.kind``
- indexing into a list or a dict appends the index or the key in square
  brackets, as in ``backends[1]`` or ``limits[cpu]``

The path is carried by the ``member_name`` argument. The library supplies it
whenever it constructs, parses, validates, or writes a nested object, and a
nested class only has to pass it on to ``super().__init__()``. ``None`` means
that the object is the top level configuration and not a member of anything,
and then its own members are reported by their plain names.

The path is text for a person to read, and not text for a program to parse
back into its parts. A dict key that itself holds a dot or a square bracket
therefore makes a path that cannot be taken apart again unambiguously.

Run the example to see a path in a real diagnostic:

```sh
python3 -m example.e42_nested_member_paths set -o /tmp/paths.cfg \
  --backends alpha=8080 beta=99999
```
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Mapping, Optional, TextIO, cast, override
from config_as_json import Config, ConfigNesting, ConfigNestingKind, \
    IntFloatValidator, InvalidConfiguration, InvalidConfigurationValue, \
    MemberValidationStep, NestedConfigs, PathOrStr, ValidationPlan
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling

LOWEST_PORT = 1
"""Lowest TCP port number that this example accepts."""

HIGHEST_PORT = 65535
"""Highest TCP port number that this example accepts."""


def port_validator() -> IntFloatValidator[int]:
    """Return the validator used for every port member in this example.

    Both configuration classes below validate their own ``port`` member with
    this one validator. The validator itself knows nothing about paths. It is
    handed the reported name of the member it validates, and that reported
    name is already the whole path. That is why one validator produces
    ``port`` for one member and ``backends[1].port`` for another.

    Returns:
        A validator that accepts the usable TCP port numbers.
    """
    return IntFloatValidator(min_value=LOWEST_PORT, max_value=HIGHEST_PORT,
                             allowed_values=None)


class BackendConfig(Config):
    """Configuration for one backend that the service forwards to."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Initialize one backend configuration.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Path for reaching this object from the top level
                configuration. ``None`` means that this object is the whole
                configuration and not a member of anything.
        """
        self.host: str = 'localhost'
        self.port: int = 8080
        # Passing ``member_name`` on is the whole obligation of a nested
        # class. The class does not build the path and does not need to know
        # where it is used. A class that leaves the argument out still works,
        # but then every diagnostic about its members loses the path and the
        # library warns that the class should accept it.
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for one backend."""
        _ = stderr_file
        # ``member_names`` are the local attribute names on this object. The
        # local name is what the library reads and writes the attribute by,
        # and the path is what it reports the attribute as.
        return [MemberValidationStep(member_names=['port'],
                                     validator=port_validator())]


class ExampleConfig42(Config):
    """Configuration for a service with a list of nested backends."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Initialize the service configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Path for reaching this object from the top level
                configuration. ``None`` means that this object is the whole
                configuration and not a member of anything.
        """
        self.service_name: str = 'reporting'
        self.port: int = 443
        # These two default objects are built by the application, so the
        # application is the one that could name them. They are the defaults
        # of a configuration that does not exist yet, so there is no path to
        # give them, and they keep the default ``member_name=None``. The
        # library supplies the real path when it builds a backend from JSON.
        self.backends: list[BackendConfig] = [
            BackendConfig(stderr_file=stderr_file),
            BackendConfig(stderr_file=stderr_file)]
        self.backends[1].host = 'backup'
        self.backends[1].port = 8081
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        return {
            'backends': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                      config_type=BackendConfig)
        }

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for the top level configuration."""
        _ = stderr_file
        # The very same validator as in BackendConfig, on a member with the
        # very same local name. This member is on the top level object, so it
        # is reported as the plain name ``port``.
        return [MemberValidationStep(member_names=['port'],
                                     validator=port_validator())]


def _backends_from_ports(host_ports: Mapping[str, int]) \
        -> list[BackendConfig]:
    """Build the nested backend list from ``host=port`` command line values.

    Args:
        host_ports: Port number for each backend host name, in the order the
            host names were given on the command line.

    Returns:
        One ``BackendConfig`` per host name.
    """
    backends: list[BackendConfig] = []
    for host, port in host_ports.items():
        backend = BackendConfig()
        backend.host = host
        backend.port = port
        backends.append(backend)
    return backends


# The set and print helpers below are the shared shape of every example in
# this directory. Keeping that shape is what lets a reader compare examples,
# so the accidental similarity is suppressed rather than factored out.
# pylint: disable=duplicate-code
def e42_member_paths_set(set_values: SetValues,
                         config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig42()
    for key, value in set_values.items():
        if key == 'backends':
            config.backends = _backends_from_ports(
                cast(Mapping[str, int], value))
        elif hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f'Invalid key: {key}')
    try:
        # Writing validates the whole configuration, nested objects
        # included. A refused value is named by its path here, in exactly
        # the same words as when a configuration file is read.
        config.write(to_json_filename=config_file)
        print(f'Configuration written to {config_file}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


def _print_backend(index: int, backend: BackendConfig) -> None:
    """Print one backend configuration.

    Args:
        index: Position of the backend in the configured list.
        backend: Nested backend configuration to print.
    """
    # The path that a diagnostic would use is built the same way as this
    # text: the member name of the list, the index in square brackets, a
    # dot, and the member name inside the nested object.
    print(f'backends[{index}].host: {backend.host}')
    print(f'backends[{index}].port: {backend.port}')


def e42_member_paths_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show the values and their paths.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        # Reading validates every nested object as it is built. A hand
        # edited port that is out of range is refused with a message that
        # names the path of that one backend port.
        config = ExampleConfig42(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'service_name: {config.service_name}')
        print(f'port: {config.port}')
        for index, backend in enumerate(config.backends):
            _print_backend(index, backend)
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# pylint: enable=duplicate-code

INPUT_SPECS = [
    InputSpec(name='service_name', single=True, value_type=str),
    InputSpec(name='port', single=True, value_type=int),
    # One ``host=port`` token per backend. The command line is deliberately
    # simple, because the interesting part of this example is the reported
    # path and not the command line.
    InputSpec(name='backends', single=False, value_type=int, dict_kv=True)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e42_nested_member_paths',
                      input_specs=INPUT_SPECS,
                      set_command=e42_member_paths_set,
                      print_command=e42_member_paths_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
