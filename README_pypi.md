# config-as-json

`config-as-json` helps an application keep its configuration schema in a
Python class while storing actual configuration data in JSON files.

The intended usage model is:

- Derive an application-specific class from `config_as_json.Config` (or use
  multiple inheritance to derive from both a class with your paramaters and
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
- backward-compatible key renames for older configuration files
- hooks that can warn or report when automatic compatibility changes were
  needed

## Nested config sections

For a repeated group of related settings, an application can put that group
in its own class derived from `config_as_json.Config`, and then declare a
member of the main configuration as a nested config section with
`ConfigNesting`.

The supported nested shapes are:

- `ConfigNestingKind.MEMBER`
  The member is a mandatory nested `Config` object.
- `ConfigNestingKind.OPTIONAL_MEMBER`
  The member is either `None` or a nested `Config` object. To make omission
  from JSON behave like other optional members, also list that member in
  `_omit_none_from_json()`.
- `ConfigNestingKind.LIST_ELEMENT`
  The member is a list, and every list element is a nested `Config` object.

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
the factory is then called once for every JSON object in the list.

`ConfigNestingKind.DICT_VALUE` and
`ConfigNestingKind.DICT_VALUE_BY_KEY` are reserved for future nested-shape
support and currently raise `NotImplementedError`.

## Installation

`config-as-json` requires Python 3.12 or newer.

```sh
pip install --upgrade config-as-json
```

## Main entry points

- `config_as_json.Config`
  Base class for JSON-backed configuration objects.
- `config_as_json.ConfigFactory`
  Protocol for optional nested-config factory functions.
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

- Test result: 3905 passed in 12s
- No flake8 warnings.
- No mypy errors found.
- No python layout warnings.
- Built version(s): 0.5.1
- Build and test using Python 3.14.4
