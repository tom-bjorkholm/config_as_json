# config-as-json

`config-as-json` helps an application keep its configuration schema in a
Python class while storing actual configuration data in JSON files.

The intended usage model is:

- Derive an application-specific class from `config_as_json.config.Config`.
- Add one instance attribute per supported configuration parameter. An
  instance attribute can also be a dict or list, optionally with nested
  dicts and lists.
- Let the values assigned in the derived constructor act as the default
  configuration.
- Use the library to write those defaults as JSON and to read JSON back into
  the derived configuration object.

The library is designed to support evolving configuration formats by letting
applications define:

- custom parsers for values that should become richer Python types
- optional keys that receive default values when omitted
- backward-compatible key renames for older configuration files
- hooks that can warn or report when automatic compatibility changes were
  needed

## Installation

`config-as-json` requires Python 3.12 or newer.

```sh
pip install --upgrade config-as-json
```

## Main entry points

- `config_as_json.config.Config`
  Base class for JSON-backed configuration objects.
- `config_as_json.config_factory.config_factory_from_json`
  Select the correct configuration class by inspecting JSON input.
- `config_as_json.config_auto_change_hook.ConfigAutoChangeHook`
  Receive notifications about automatic changes during parsing.
- `config_as_json.migrate_cfg_warn_hook.MigrateCfgWarnHook`
  Warn when backward compatibility was used.
- `config_as_json.migrate_cfg.migrate_cfg`
  Read an older configuration file and write it back in the newest supported
  format.

## Documentation and examples

- Example directory: [example/src/example/README.md](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/README.md)
- Public API notes: [doc/api.md](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/doc/api.md)
- Protected/internal API notes: [doc/protected_api.md](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/doc/protected_api.md)
- Source repository: [config_as_json](https://bitbucket.org/tom-bjorkholm/config_as_json/)

The example directory is linked already because it is the planned place for
worked examples, even though its current content is still only a placeholder.

## Project status

This package is currently being extracted from a larger application into a
standalone reusable library. The package documentation describes the intended
contract of that library while the implementation and tests are being aligned
with it.

## License

MIT

## Test summary

- Test result: 3185 passed in 8s
- No flake8 warnings.
- No mypy errors found.
- Built version(s): 0.0.1
- Build and test using Python 3.14.3
