# config-as-json

`config-as-json` helps an application keep its configuration schema in a
Python class while storing actual configuration data in JSON files.

The intended usage model is:

- Derive an application-specific class from `config_as_json.Config` (or use
  multiple inheritance to derive from both a class with your parameters and
  from `config_as_json.Config`).
- Add one instance attribute per supported configuration parameter. An
  instance attribute can also be a dict or list, optionally with nested
  dicts and lists.
- Let the values assigned in the derived constructor act as the default
  configuration.
- Use the library to write those defaults as JSON and to read JSON back into
  the derived configuration object.
- Use the included validators to validate the configuration.

The library is designed to support evolving configuration formats by letting
applications define:

- custom parsers for values that should become richer Python types
- optional keys that receive default values when omitted
- backward-compatible key renames, path moves, removals, and missing-value
  rules for older configuration files
- hooks that can warn or report when automatic compatibility changes were
  needed

## Simplest usage

The simplest way to use `config_as_json` is to derive from
`config_as_json.Config` and make each config parameter a normal instance
attribute. The values assigned in `__init__()` are the default
configuration.

The fuller
[e01_simple_config.py example](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e01_simple_config.py)
explains this pattern more thoroughly.

````python
from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan


class MyConfig(Config):
    """Configuration for my application."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for my application."""
        self.report_name: str = 'My Report'
        self.story_points: int = 5
        self.participants: list[str] = ['Alice', 'Bob']
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan."""
        return []


def application(config_filename: PathOrStr, update_config: bool) -> None:
    """Simulate a simple application that uses MyConfig."""
    # Read configuration from file that already exists
    config = MyConfig(from_json_filename=config_filename,
                      stderr_file=sys.stderr)
    # A lot of application code not shown here
    print(f'Report name: {config.report_name}')
    # ...
    if update_config:
        config.write(config_filename)
````

## Using a class from a third party

When another library already provides a configuration class, use multiple
inheritance to combine that class with `config_as_json.Config`. Initialize
the third-party class before `Config`, so its attributes are present when
`Config` reads or writes JSON.

The fuller
[e04_third_party_class.py example](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e04_third_party_class.py)
explains this pattern more thoroughly.

````python
from typing import Optional, TextIO
from dataclasses import dataclass
import sys
from config_as_json import Config, PathOrStr, ValidationPlan


@dataclass
class ThirdPartyConfig:
    """Configuration for my application."""

    report_name: str = 'My Report'
    story_points: int = 5
    is_done: bool = False


class MyConfig(ThirdPartyConfig, Config):
    """Configuration for my application."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for my application."""
        # Initialize the third-party configuration before Config
        ThirdPartyConfig.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan."""
        return []


def application(config_filename: PathOrStr, update_config: bool) -> None:
    """Simulate a simple application that uses MyConfig."""
    # Read configuration from file that already exists
    config = MyConfig(from_json_filename=config_filename,
                      stderr_file=sys.stderr)
    # A lot of application code not shown here
    print(f'Report name: {config.report_name}')
    # ...
    if update_config:
        config.write(config_filename)
````

## Adding simple validation

A configuration class can also return a validation plan. This example uses
one predefined validator to restrict `story_points` to normal story-point
values. It also shows creating a config with defaults first, then calling
`read()` only when a file should be read.

The fuller
[e03_scalar_validators.py example](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e03_scalar_validators.py)
explains predefined validators more thoroughly. The
[e04_third_party_class.py example](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e04_third_party_class.py)
shows the same idea with a third-party class.

````python
from typing import Optional, TextIO
from dataclasses import dataclass
import sys
from config_as_json import Config, IntFloatValidator, \
    MemberValidationStep, PathOrStr, ValidationPlan


@dataclass
class ThirdPartyConfig:
    """Configuration for my application."""

    report_name: str = 'My Report'
    story_points: int = 5
    is_done: bool = False


class MyConfig(ThirdPartyConfig, Config):
    """Configuration for my application."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for my application."""
        # Initialize the third-party configuration before Config
        ThirdPartyConfig.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the validation plan for my application."""
        _ = stderr_file
        story_point_validator = IntFloatValidator(
            min_value=None, max_value=None,
            allowed_values=[0, 1, 2, 3, 5, 8, 13, 20, 40, 100])
        return [MemberValidationStep(member_names=['story_points'],
                                     validator=story_point_validator)]


def application(config_filename: PathOrStr, update_config: bool,
                read_file: bool) -> None:
    """Simulate a simple application that uses MyConfig."""
    config = MyConfig(stderr_file=sys.stderr)
    if read_file:
        config.read(config_filename, stderr_file=sys.stderr)
    # A lot of application code not shown here
    print(f'Report name: {config.report_name}')
    # ...
    if update_config:
        config.write(config_filename)
````

## Nested configurations

For a repeated group of related settings, an application can put that group
in its own class derived from `config_as_json.Config`, and then override
`nested_configs()` in the main configuration to declare nested config
sections with `ConfigNesting`.

Annotate the override as returning `NestedConfigs`, and use `@override` so
type checkers can catch a misspelled method name:

```python
from typing import override
from config_as_json import ConfigNesting, ConfigNestingKind, NestedConfigs
```

The method should just return declarative metadata. It should be constant, or
at least constant from the time the derived constructor calls
`super().__init__()`, and it should have no side effects.

The supported nested shapes are:

- `ConfigNestingKind.MEMBER`
  The member is a mandatory nested `Config` object.
- `ConfigNestingKind.OPTIONAL_MEMBER`
  The member is either `None` or a nested `Config` object. To make omission
  from JSON behave like other optional members, also list that member in
  `_omit_none_from_json()`.
- `ConfigNestingKind.LIST_ELEMENT`
  The member is a list, and every list element is a nested `Config` object.
- `ConfigNestingKind.DICT_VALUE`
  The member is a dict with string keys, and every dict value is a nested
  `Config` object.
- `ConfigNestingKind.DICT_VALUE_BY_KEY`
  The member is a dict with string keys, and selected dict keys have nested
  `Config` values. Other keys in the same dict remain ordinary JSON values.

Nested config classes must derive from `Config` and must be constructible
with these keyword arguments:

```python
def __init__(self, from_json_data_text: Optional[str] = None,
             from_json_filename: Optional[PathOrStr] = None,
             stderr_file: TextIO = sys.stderr) -> None:
```

They may have additional optional arguments, but the base class constructs
nested objects from JSON using the three keyword names shown above.

If construction needs application-specific logic, keep `config_type` as the
expected runtime type and add `factory_function` to the `ConfigNesting`
declaration. The factory must accept the same keyword arguments and must
return an instance of `config_type` or a subclass:

```python
ConfigNesting(kind=ConfigNestingKind.MEMBER,
              config_type=OutputConfig,
              factory_function=create_output_config)
```

The same factory form can be used with `ConfigNestingKind.LIST_ELEMENT`;
the factory is then called once for every JSON object in the list. It can
also be used with `ConfigNestingKind.DICT_VALUE`; the factory is then called
once for every JSON object stored as a dict value.

For `ConfigNestingKind.DICT_VALUE_BY_KEY`, use a list of `ConfigNesting`
entries when several keys inside the same dict should be nested configs:

```python
@override
def nested_configs(self) -> NestedConfigs:
    """Return nested Config declarations."""
    return {
        'reports_by_key': [
            ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                          config_type=ReportOutputConfig,
                          discriminator_key='participants'),
            ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                          config_type=WebhookOutputConfig,
                          discriminator_key='audit',
                          factory_function=create_webhook_output)
        ]
    }
```

Here `discriminator_key` is the key inside `reports_by_key`. When JSON is
read, the value at `participants` becomes a `ReportOutputConfig`, the value
at `audit` becomes a `WebhookOutputConfig`, and any other keys in
`reports_by_key` stay plain JSON values. A declaration list with more than
one entry may only contain `DICT_VALUE_BY_KEY` entries. The list form itself
is reserved for `DICT_VALUE_BY_KEY`; use a direct `ConfigNesting` value for
`MEMBER`, `OPTIONAL_MEMBER`, `LIST_ELEMENT`, and `DICT_VALUE`.

## Installation

`config-as-json` requires Python 3.12 or newer.

```sh
pip install --upgrade config-as-json
```

## Main entry points

- `config_as_json.Config`
  Base class for JSON-backed configuration objects.
- `config_as_json.ConfigNesting` and `config_as_json.ConfigNestingKind`
  Declarative metadata for nested configuration objects.
- `config_as_json.NestedConfigs`
  Return type for `Config.nested_configs()` declarations.
- `config_as_json.ConfigFactory`
  Protocol for optional nested-config factory functions.
- `config_as_json.ReadOldConfiguration`
  Base class for backward-compatible old-file normalization rules.
- `config_as_json.RocfKeyRename`, `config_as_json.RocfKeyMove`, and
  `config_as_json.ConfigPath`
  Rule helpers for old-file key renames, path moves, removals, and missing
  current values.
- `config_as_json.config_factory_from_json`
  Select the correct configuration class by inspecting JSON input.
- `config_as_json.ConfigAutoChangeHook`
  Receive notifications about automatic changes during parsing.
- `config_as_json.MigrateCfgWarnHook`
  Warn when backward compatibility was used.
- `config_as_json.migrate_cfg`
  Read an older configuration file and write it back in the newest supported
  format.

The generated API reference also shows the implementation modules where these
public objects are defined.

## Documentation and examples

- Example directory: [example/src/example/README.md](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/README.md)
- Public API notes: [doc/api.md](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/doc/api.md)
- Protected/internal API notes: [doc/protected_api.md](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/doc/protected_api.md)
- Source repository: [config_as_json](https://bitbucket.org/tom-bjorkholm/config_as_json/)

The example directory contains worked examples for new users. It is not
included in the package installed from PyPI.

## License

MIT

## Test summary

- Test result: 4316 passed in 14s
- No flake8 warnings.
- No mypy errors found.
- No python layout warnings.
- Built version(s): 0.7.1
- Build and test using Python 3.14.4
