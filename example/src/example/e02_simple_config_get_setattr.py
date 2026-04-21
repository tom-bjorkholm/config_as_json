#! /usr/local/bin/python3
"""Show a second example of a small configuration class backed by JSON.

This example is the same as the first example, but uses the
setattr function to set the configuration values, and the getattr
function to get the configuration values. This is to show that the
attributes can be accessed as normal Python attributes.

Some programmers prefer to use setattr and getattr to set and get
configuration values, rather than ordinary assignments to and from
instance attributes. Especially when looping over the configuration
variables, this approach can be more convenient.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional
import sys
from config_as_json.config import Config
from config_as_json.commontypes import PathOrStr
from .cmd_line_handling import SetValues, cmd_line_handling
from .e01_simple_config import SimpleConfig, INPUT_SPECS


# To simplify the error checking in the examples that use setattr and getattr,
# we define a helper function to get the list of the normal instance attribute
# names.

def get_normal_instance_attribute_names(config: Config) -> list[str]:
    """Get the list of the normal instance attribute names.

    Args:
        config: Configuration object.

    Returns:
        List of the normal instance attribute names.
    """
    return [i for i in vars(config).keys() if not
            callable(getattr(config, i)) and not i.startswith('_')]


# Here is a function that shows how to set the configuration
# values to something else than the defaults, and how to store
# the configuration in a JSON file.
# In this example, this function is called by the command line helper
# when the user wants to set the configuration values.

def e02_simple_config_set(set_values: SetValues,
                          config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    # Like in e01_simple_config.py,
    # when calling the constructor of the configuration object,
    # without any arguments, the configuration object is created with the
    # default values.
    config = SimpleConfig()
    for key, value in set_values.items():
        # In e01_simple_config.py, we used assignments to the instance
        # attributes. Here we use the setattr function to set the
        # configuration values. This is to show that the attributes can be
        # accessed both ways as normal Python attributes.
        if key not in get_normal_instance_attribute_names(config):
            raise ValueError(f'Invalid key: {key}')
        setattr(config, key, value)
    # As in e01_simple_config.py, we store the configuration in a JSON file,
    # by simply calling the write method of the configuration object.
    config.write(to_json_filename=config_file)
    print(f'Configuration written to {config_file}')


def e02_simple_config_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    # We read the configuration from a JSON file, by simply providing
    # the from_json_filename argument to the configuration constructor.
    config = SimpleConfig(from_json_filename=config_file)
    # In e01_simple_config.py, we printed the configuration values by
    # accessing the instance attributes directly. Here we use the getattr
    # function to get the configuration values. This is to show that the
    # attributes can be accessed both ways as normal Python attributes.
    for key in get_normal_instance_attribute_names(config):
        print(f'{key}: {getattr(config, key)}')
    print(f'Configuration read from {config_file}')


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

# pylint: disable=duplicate-code
def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e02_simple_config_get_setattr',
                      input_specs=INPUT_SPECS,
                      set_command=e02_simple_config_set,
                      print_command=e02_simple_config_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
