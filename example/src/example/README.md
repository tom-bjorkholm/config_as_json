# Example programs for config-as-json

This directory contains small example programs for programmers who are
new to the `config_as_json` API. The examples are arranged from the smallest
possible configuration example to more advanced topics.
A good way to learn the API is to read the examples in order and run
the ones that match the configuration case you are interested in.

## Command lines and running examples

All examples use the shared command-line helper in
`cmd_line_handling.py`. That means they follow the same basic style:
you choose an output file to write configuration to with `-o` and
input file to read configuration from with `-i`.
The command lines have two sub-commands `set` and `print`.
The sub-command `set` is optionally changes some configuration
values (to something else than the default) based on command line
arguments, and writes the configuration to a file.
The sub-command `print` reads the configuration from a file,
and prints the configuration to standard output.

To be able to run the example programs the `config_as_json` package
must be installed in your environment.

```sh
pip install --upgrade config-as-json
```

The example programs are *not* included in the package you install.

The example programs are intended to be read in a browser towards to
Bitbucket repository, and you can download them from Bitbucket to run
them locally (or to run variations you want to test).
There is no package with the example programs.

With the `config_as_json` package installed in your environment,
you may also choose to close the complete repository and run
some examples like this:

```sh
cd example/src
python3 -m example.e01_simple_config set -o /tmp/simple.cfg \
  --name Ada --confirmation yes
python3 -m example.e01_simple_config print -i /tmp/simple.cfg
```

## e01_simple_config.py

[Source code for e01_simple_config.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e01_simple_config.py)

This example keeps the configuration deliberately small so that the main
ideas are easy to see:

- defaults are ordinary instance attributes: int, str, float and an enum
- the configuration can be written to a JSON file
- the configuration can be read back later
- the application can then use the values as normal Python attributes

This shows the first example configuration class, that is a simple
configuration class that uses only scalar values. Our configuration class
is derived from the base class Config and may have any name and any number
of instance attributes. The instance attributes are the configuration values.
Later examples will teach more complex patterns, but what is shown here is
actually enough for many applications.

There is a function that changes configuration values, and writes the
configuration to a JSON file. There is another function that reads
in the configuration from a JSON file and prints the configuration values
to standard out.
