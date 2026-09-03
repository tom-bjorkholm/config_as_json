# Example programs for config-as-json

This directory contains small example programs for programmers who are
new to the `config_as_json` API. The examples are arranged from the smallest
possible configuration example to more advanced topics.
A good way to learn the API is to read the examples in order and run
the ones that match the configuration case you are interested in.

Many of these examples use the predefined validators that come with
the package. For the complete catalogue of those validators, grouped
by the kind of problem they solve and with the combinations they are
built for, see the
[predefined validator guide](https://github.com/tom-bjorkholm/config_as_json/blob/master/doc/predefined_validators.md).

## Command lines and running examples

All examples use the shared command-line helper in
`cmd_line_handling.py`. That means they follow the same basic style:
you choose an output file to write configuration to with `-o` and
an input file to read configuration from with `-i`.
The command lines have two subcommands `set` and `print`.
The `set` subcommand optionally changes some configuration
values from their defaults based on command-line arguments, and writes
the configuration to a file.
The `print` subcommand reads the configuration from a file,
and prints the configuration to standard output.

To be able to run the example programs the `config_as_json` package
must be installed in your environment.

```sh
pip install --upgrade config-as-json
```

The example programs are *not* included in the package you install.

The example programs are intended to be read in a browser in the
GitHub repository, and you can download them from GitHub to run
them locally, or to run variations you want to test.
There is no package with the example programs.

With the `config_as_json` package installed in your environment,
you may also choose to clone the complete repository and run
some examples like this:

```sh
cd example/src
python3 -m example.e01_simple_config set -o /tmp/simple.cfg \
  --name Ada --confirmation yes
python3 -m example.e01_simple_config print -i /tmp/simple.cfg
```

## Simplest usage

The simplest way to use `config_as_json` is to derive from
`config_as_json.Config` and make each config parameter a normal instance
attribute. The values assigned in `__init__()` are the default
configuration.

The complete
[e01_simple_config.py example](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e01_simple_config.py)
explains this pattern more thoroughly.

````python
from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan


class MyConfig(Config):
    """Configuration for my application."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct configuration for my application."""
        self.report_name: str = 'My Report'
        self.story_points: int = 5
        self.participants: list[str] = ['Alice', 'Bob']
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

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

## e01_simple_config.py

[Source code for e01_simple_config.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e01_simple_config.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e01_simple_config.py)

This example keeps the configuration deliberately small so that the main
ideas are easy to see:

- defaults are ordinary instance attributes: int, str, float and an enum
- the configuration can be written to a JSON file
- the configuration can be read back later
- the application can then use the values as normal Python attributes

This shows the first example configuration class, that is a simple
configuration class that uses only scalar values. Our configuration class
is derived from the base class `Config` and may have any name and any number
of instance attributes. The instance attributes are the configuration values.
Later examples will teach more complex patterns, but what is shown here is
actually enough for many applications.

There is a function that changes configuration values, and writes the
configuration to a JSON file. There is another function that reads
in the configuration from a JSON file and prints the configuration values
to standard out.

In this example we use simple normal assignments to and from instance
attributes to keep the code as easy to understand as possible for the
beginner.

## e02_simple_config_get_setattr.py

[Source code for e02_simple_config_get_setattr.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e02_simple_config_get_setattr.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e02_simple_config_get_setattr.py)

This second example is very similar to the first example and it shares much
of the code by importing from the first example.

The difference here is that setattr and getattr are used to set and get
configuration variables. In some situations (like when looping over the
configuration variables) this approach needs less code.

## e03_scalar_validators.py

[Source code for e03_scalar_validators.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e03_scalar_validators.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e03_scalar_validators.py)

We introduce the concept of validators in the third example.
The application programmer can use the predefined validator classes to
validate that a configuration is consistent. By specifying arguments to the
validators we can define what values are allowed for which configuration
parameter.

In this example we still use only scalar configuration values, but we now
show four common validation patterns:

- `number_of_iterations` must stay within an integer range
- `estimate` must be one of a fixed set of allowed integer values
- `confidence` must stay within a floating-point range
- `issue_type` must be one of a fixed set of allowed strings

The `issue_type` validator also ignores case and normalizes the stored value
to the exact spelling from the allowed-values list. This shows that a
validator can both reject invalid input and normalize valid input.

The example introduces the validation-plan API used by `Config`.
`get_validation_plan()` returns an ordered `ValidationPlan`.
Each item in that plan is a step object. In this example all steps are
`MemberValidationStep` because each rule validates one named member.

The example also demonstrates that validation happens both when the
configuration is written and when it is read back. If an invalid value is
encountered, the `Config` base class prints a helpful error message and the
example stops instead of continuing with bad configuration data.

## Using a class from a third party

When another library already provides a configuration class, use multiple
inheritance to combine that class with `config_as_json.Config`. Initialize
the third-party class before `Config`, so its attributes are present when
`Config` reads or writes JSON.

The complete
[e04_third_party_class.py example](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e04_third_party_class.py)
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
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct configuration for my application."""
        # Initialize the third-party configuration before Config
        ThirdPartyConfig.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file, member_name=member_name)

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

## Adding validation to a third-party config class

A configuration class can also return a validation plan. This example uses
one predefined validator to restrict `story_points` to normal story-point
values. It also shows creating a config with defaults first, then calling
`read()` only when a file should be read.

The complete
[e03_scalar_validators.py example](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e03_scalar_validators.py)
explains predefined validators more thoroughly. The
[e04_third_party_class.py example](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e04_third_party_class.py)
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
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct configuration for my application."""
        # Initialize the third-party configuration before Config
        ThirdPartyConfig.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file, member_name=member_name)

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
        config.read(config_filename, stderr_file=sys.stderr, member_name=None)
    # A lot of application code not shown here
    print(f'Report name: {config.report_name}')
    # ...
    if update_config:
        config.write(config_filename)
````

## e04_third_party_class.py

[Source code for e04_third_party_class.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e04_third_party_class.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e04_third_party_class.py)

This example shows how to work with a third-party parameter class that
already defines the configuration members and their default values.

The example configuration class derives both from `Config` and from the
third-party parameter class. The third-party base class is initialized first
so that its public attributes already exist when `Config` inspects the
instance. That lets the application keep using the class shape expected by
the third-party library, while also getting JSON writing, JSON reading,
enum conversion, and validation from `config_as_json`.

The validators in this example are the same as in `e03_scalar_validators.py`.
The new thing to notice is that the validated members come from the
third-party base class instead of being created directly in the
`Config` subclass.

## e05_custom_validator.py

[Source code for e05_custom_validator.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e05_custom_validator.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e05_custom_validator.py)

This example shows how to derive your own validator class from
`WholeConfigValidator`, and when that is useful.

The configuration has 2 string values:

- `output_format`
- `output_subtype`

The important rule is that they depend on each other:

- for `CSV`, the subtype must be `excelDialect` or `unixDialect`
- for `Excel`, the subtype must be `PylightXL`, `OpenPyxl`, or
  `XlsxWriter`

The example first uses ordinary `StrValidator` objects to normalize the
spelling of both strings. After that it runs a custom validator on the
whole configuration object.

That lets the example teach both concrete step types in a `ValidationPlan`:

- `MemberValidationStep` for rules that validate one named member
- `WholeConfigValidationStep` for rules that need the whole configuration

This is often the cleanest design when one configuration value is only
valid in combination with another value. The example also includes a
small stub output library class, just to show how an application might
use the validated configuration after reading it.

In this example we also show that it is a good idea to have separate
exception types for mistakes by the end user, compared to programming
errors by the application programmer.

## e06_list_basic_validators.py

[Source code for e06_list_basic_validators.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e06_list_basic_validators.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e06_list_basic_validators.py)

This is the first teaching example that uses list-valued configuration
members. It is meant for readers who already understand the basic
``Config`` pattern from the earlier examples and now want to validate
lists.

The example introduces 2 list validators that solve different problems:

- `ListValueValidator` checks each element in a list separately
- `ListSizeValidator` checks the size of the list as a whole

The example keeps the lists independent from each other so that the
reader can see the 2 ideas clearly:

- `retry_delays_seconds` shows per-element integer range validation
- `report_formats` shows per-element allowed-values validation where the
  allowed values come from a method
- `backup_servers` shows list-size validation

The important design lesson is that list validation can happen at
different levels. Sometimes the rule is about each element, and sometimes
the rule is about the list as a collection.

The `report_formats` validator receives `allowed_report_formats` instead of
a fixed list. `ListValueValidator` calls that method when validation runs,
so an application can calculate the allowed choices from runtime state.

## e07_list_order_vs_normalize.py

[Source code for e07_list_order_vs_normalize.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e07_list_order_vs_normalize.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e07_list_order_vs_normalize.py)

This example teaches 2 closely related validators that make different
design choices:

- `ListIsOrderedValidator` rejects a list if it is not already in the
  required order
- `ListOrderingValidator` reorders the list and stores the normalized
  result

The example uses:

- `alert_thresholds` to show the "reject invalid order" design
- `report_names` to show the "normalize the order for the user" design

It also shows a small custom less-than comparator for case-insensitive
string sorting. That keeps the example concrete and easy to understand,
while also showing how the ordering rules can be customized.

This is a useful example when you need to decide whether a list should be
treated as user-authored data that must already be correct, or as input
that your application should normalize automatically.

## e08_combined_list_validators.py

[Source code for e08_combined_list_validators.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e08_combined_list_validators.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e08_combined_list_validators.py)

This example is the first one where the order of the validation steps is
itself an important teaching point.

The configuration has one list member, `run_hours_utc`, and the example
applies 3 validators to that same member in sequence:

1. `ListValueValidator` checks that every hour is between 0 and 23
2. `ListOrderingValidator` sorts the list and removes duplicates
3. `ListSizeValidator` checks the size of the normalized list

This shows that each validation step receives the value returned by the
previous step. That is why the order in `ValidationPlan` is important.
If the steps were rearranged, the configuration would mean something
different.

This example is useful when one validator prepares data for the next
validator, or when a later rule should explicitly apply to the normalized
form rather than to the raw user input.

## e09_list_for_each.py

[Source code for e09_list_for_each.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e09_list_for_each.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e09_list_for_each.py)

This example introduces the general composition tool for per-element
validation, `ListForEachValidator`. It iterates the outer list and
applies a sequence of inner validators to every element, in order. It
does not try to implement any list-level rule on its own, so every
other list validator stays single-purpose.

`ListForEachValidator` is not restricted to a particular element shape.
Typical use cases include:

- **lists of lists**, where each inner list is checked with other list
  validators such as `ListSizeValidator` or `ListValueValidator`
- **lists of dicts**, where each element is checked with the built-in
  `DictKeysValidator` and `DictForEachValidator`, see `e13` below
- **lists of scalar values**, where each element is checked or
  normalized by a user-defined validator, for instance a custom
  `MemberValidator` that spell-checks each string or converts each
  string to upper case

Because `ListForEachValidator` is itself a `MemberValidator`, one
instance can be an element validator of another, so nesting is not
limited to a single inner layer.

The concrete example below demonstrates the list-of-lists case because
it is the one that cannot be expressed with the earlier list
validators alone. The configuration has one list-of-lists member,
`daily_hour_ranges`. Each inner list is a `[start_hour, end_hour]`
pair. The example uses 3 validators in sequence:

1. `ListSizeValidator` checks that the outer list has between 1 and 7
   entries.
2. `ListForEachValidator` applies the inner validators to every inner
   list:
   - `ListSizeValidator` rejects inner lists whose size is not exactly 2
   - `ListValueValidator` rejects hour values outside `0..23`
3. Because `ListForEachValidator` only delegates, the error messages
   come from the inner validators and include the outer member name
   with the element index appended in square brackets, for example
   `daily_hour_ranges[2]`.

The command line for this example accepts the matrix member via
`--daily-hour-ranges`, where each token is a comma-separated list of
ints describing one inner list. For instance
`--daily-hour-ranges 6,10 13,17 20,22` sets a three-day schedule. This
is enabled by the `nested=True` flag on the `InputSpec` and by the
nested-token parser inside the shared command line helper.

The important teaching point is that nested or per-element validation
is just composition. Each inner validator is either one of the
validators introduced by the earlier examples or a user-defined
`MemberValidator`, and `ListForEachValidator` is the small mechanism
that lets those validators reach inside one level of nesting.

## e10_dict_basic_validators.py

[Source code for e10_dict_basic_validators.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e10_dict_basic_validators.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e10_dict_basic_validators.py)

This is the first teaching example that uses dict-valued configuration
members. It introduces the smallest dict validator,
`DictKeysValidator`, and shows it in 2 modes side by side:

- `feature_flags` shows the *mandatory + optional* shape: some keys
  must be present and a few additional keys are accepted
- `port_assignments` shows the *exact-shape* form: only the listed
  keys are accepted, and they are all mandatory

Values are not validated in this example. The lesson is that the
*key set* is the schema and that `DictKeysValidator` never inspects
values.

For the common simple case where an open-ended dict should validate both
the key type and the value type, continue with `e22_dict_key_value_types.py`
after this example. It teaches the compact `DictKeyValueTypesValidator`
form for shapes such as `dict[str, int]`.

For dict-valued members, the `Config` base class already checks the
parsed JSON key set against the default (unknown keys are rejected). That
built-in check is enough for many fixed dict shapes and does not require
`DictKeysValidator`. This example opts out of that check with
`_unchecked_dicts` so `DictKeysValidator` can own the key policy, which is
required here for the optional `feature_flags` keys and is how e11 and e12
teach more flexible dict validation.

The command line for this example uses the `dict_kv=True` flag on
`InputSpec`. Each CLI token is parsed as `key=value`, e.g.
`--feature-flags logging=true metrics=false debug=true`.

## e11_dict_for_each.py

[Source code for e11_dict_for_each.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e11_dict_for_each.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e11_dict_for_each.py)

This example builds on `e10_dict_basic_validators.py` and adds
per-key value validation. It introduces `DictForEachValidator` and
the `DictRule` data shape that `DictForEachValidator` consumes.

The example uses one dict member `cache_settings` with mandatory
keys `ttl_seconds`, `refresh_seconds`, `max_entries`, and
`eviction_policy`. The validation plan has 2 steps on the same
member:

1. `DictKeysValidator` rejects unknown keys and missing keys
2. `DictForEachValidator` runs 3 `DictRule` entries that apply
   `IntFloatValidator` and `StrValidator` to the corresponding
   values

The first rule covers two keys at once (`ttl_seconds` and
`refresh_seconds`). That shows why `DictRule` exists: it groups keys
that share the same validator chain so the same chain is not
repeated.

The example also shows that `DictForEachValidator` silently skips a
rule key that is missing from the dict; enforcing key presence is
`DictKeysValidator`'s job.

The command line uses `json_value=True` because the dict has mixed
value types and `key=value` tokens cannot express that without
guessing per-key types. A full override looks like
`--cache-settings '{"ttl_seconds": 60, ...}'`.

## e12_dict_for_each_ordering.py

[Source code for e12_dict_for_each_ordering.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e12_dict_for_each_ordering.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e12_dict_for_each_ordering.py)

This example is the dict counterpart of `e08_combined_list_validators`.
The teaching point is that `DictForEachValidator` runs its rules in
order, and that each validator sees the value returned by the
previous validator.

The configuration has one dict member `team_tags` with three
mandatory keys (`region`, `environment`, `team`). Three `DictRule`
entries with deliberately overlapping `keys` lists make the
rule-major iteration shape visible:

1. Rule A on all three keys uses `StrValidator` with
   `ignore_case=True` and `normalize=True` to rewrite user input to
   the canonical spelling
2. Rule B on `region` and `environment` uses a stricter
   `StrValidator` with a smaller `allowed_values` list, applied to
   the value already normalized by Rule A
3. Rule C on `team` does the same with a different narrower list

If the rules were rearranged, the configuration would mean something
different. For example, running Rule B before Rule A would reject
the input `'eu'` because Rule B alone is case-sensitive.

The command line uses `dict_kv=True` because every value is a
string. A typical override is
`--team-tags region=eu environment=production team=engineering`,
and the canonical spelling (`Eu`, `Production`, `Engineering`) is
what ends up in the configuration file.

## e13_list_of_dicts.py

[Source code for e13_list_of_dicts.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e13_list_of_dicts.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e13_list_of_dicts.py)

This is one of the advanced examples in the validator series. It is for
readers who already understood the earlier list and dict examples
and now want to see how the building blocks compose when the
configuration shape mixes lists and dicts.

The configuration has one member `maintenance_windows` that is a
list of dicts. Each dict describes one maintenance window with
`name`, `hours_utc`, and an optional `priority`.

Two composition directions are visible in this single example:

- **dict in list** is taught by using `DictKeysValidator` and
  `DictForEachValidator` as `element_validators` of a
  `ListForEachValidator`. The earlier `e09_list_for_each` example
  used list validators in that role; this example uses the built-in
  dict validators in exactly the same slot.
- **list in dict** is taught by using `ListSizeValidator` and
  `ListValueValidator` inside a `DictRule`. The same dict rule
  could equally well include another `DictForEachValidator` for a
  nested dict shape; nesting is unbounded.

The lesson is that `MemberValidator` is the lingua franca of
composition. Any built-in or user-defined `MemberValidator` can be
plugged into any of the composition slots without special handling.

At this nesting depth (a list of mixed-type dicts that themselves
contain lists), reinventing more separators on the command line
stops teaching anything. The example therefore uses
`json_value=True`, and the command line accepts a single JSON
document for the whole `--maintenance-windows` value.

## e14_discriminated_dict_validator.py

[Source code for e14_discriminated_dict_validator.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e14_discriminated_dict_validator.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e14_discriminated_dict_validator.py)

This example teaches `DiscriminatedDictValidator`. It is useful when one
dict-valued configuration member has several allowed shapes, and one key in
the dict decides which shape applies.

The configuration has one member `export_target`. It is always a dict with
a `kind` key:

- if `kind` is `file`, the dict must contain `filename` and may contain
  `format`
- if `kind` is `queue`, the dict must contain `queue` and may contain
  `batch_size`

The example uses a normal `StrValidator` to validate and normalize `kind`.
Then `DiscriminatedDictValidator` uses that normalized value to select a
`DictVariant`. Each variant defines its own mandatory keys, optional keys,
and `DictRule` entries for validating only the values that belong to that
variant.

This is the same composition idea as e11 through e13, but packaged for the
common "one discriminator key chooses one dict shape" pattern. The command
line uses `json_value=True` because the value is a mixed-type dict.

## e15_projected_member_validator.py

[Source code for e15_projected_member_validator.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e15_projected_member_validator.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e15_projected_member_validator.py)

This example teaches `ProjectedMemberValidator`. It is useful when a
configuration member should be stored in one shape, but one validation rule
is easier to express against a projected view of that member.

The configuration has one member `release_steps`. It is a list of dicts, and
each dict contains a step `name`, an `order`, and `duration_minutes`.
Per-step validation is still done the same way as in `e13`: a
`ListForEachValidator` applies `DictKeysValidator` and `DictForEachValidator`
to every step dict.

The extra rule is about all steps together: the `order` values must be
unique and increasing. Instead of writing a custom validator class,
`ProjectedMemberValidator` first uses a `ListSizeValidator` as a
`source_validator` for the stored list. It then uses a small projector
function to compute this temporary list:

`[10, 20, 30]`

Then a normal `ListIsOrderedValidator` validates that projected list. The
stored configuration value remains the original list of dicts. A normalized
replacement returned from `source_validator` would only feed the projector,
and normalized values returned from validators on the projected list are
only passed to the next projected validator. They do not replace
`release_steps`.

This is the general escape hatch for "validate what can be calculated from
this member, but keep this member as it is". The command line uses
`json_value=True` because the value is a list of mixed-type dicts.

## e16_type_and_list_of_dicts_validators.py

[Source code for e16_type_and_list_of_dicts_validators.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e16_type_and_list_of_dicts_validators.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e16_type_and_list_of_dicts_validators.py)

This example teaches 3 small predefined validators that are about data
shape rather than values:

- `ValueTypeValidator` checks that one member value has a runtime type
- `ListValueTypeValidator` checks that a member is a list whose elements
  all have one runtime type
- `ListOfDictsKeysValidator` checks that every dict in a list has the
  required key set

The configuration has a scalar `worker_count`, a list of strings
`alert_recipients`, and a list of dicts `pipeline_steps`. The step dicts
must contain `name` and `enabled`, and may also contain `owner`.

The important teaching point is that these validators are deliberately
small. They are a good fit when the configuration shape is the rule. If the
member also needs ranges, allowed values, ordering, or per-key value checks,
use the more specific validators shown in the earlier examples.

The command line accepts `pipeline_steps` as JSON because it is a list of
dicts. A small override looks like:

`--pipeline-steps '[{"name":"extract","enabled":true}]'`

## e17_csv_dialect_and_encoding.py

[Source code for e17_csv_dialect_and_encoding.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e17_csv_dialect_and_encoding.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e17_csv_dialect_and_encoding.py)

This example teaches 2 validators for common file-format settings:

- `CharEncodingValidator` checks that an encoding string is recognized by
  Python
- `CsvDialectValidator` checks a JSON-friendly dictionary that describes a
  `csv.Dialect`

The configuration has `input_encoding`, `output_encoding`, and
`csv_dialect`. The dialect member is stored as a dict so it can be written
to JSON, but the example also has a `get_csv_dialect()` method that turns
that dict into a standard-library `csv.Dialect` object for application code.

`CsvDialectValidator` also normalizes missing optional dialect keys to
`None`. That lets a configuration file say only `{"name": "csv.excel_tab"}`
when the standard dialect defaults are good enough.

The command line accepts the dialect as one JSON value. For example:

`--csv-dialect '{"name":"csv.excel_tab","delimiter":";"}'`

## e18_replacing_config_check_helpers.py

[Source code for e18_replacing_config_check_helpers.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e18_replacing_config_check_helpers.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e18_replacing_config_check_helpers.py)

This example shows how to replace older direct `Config` check helper
patterns with validators.

The configuration has three list-of-dicts members:

- `column_mappings` shows the old "list of dicts with one typed key"
  pattern. `ListForEachValidator` applies `DictKeysValidator` and
  `DictForEachValidator` to every row.
- `merge_rules` shows the old "list of dicts where one key contains a list"
  pattern. The per-key rule validates that `columns` is a non-empty list of
  strings.
- `rewrite_rules` shows the old "list of dicts selected by kind" pattern.
  `ListForEachValidator` applies one `DiscriminatedDictValidator` to every
  row, and each `DictVariant` defines the keys and value validators for its
  selected shape.

The example deliberately uses `allow_extra_dict_keys=True` in the key-policy
validators. That models open row dictionaries: selected keys are required
and validated, while unrelated application-specific keys are passed through.
The command line accepts each member as a JSON value because all three
members are nested list-of-dicts structures.

## e19_config_method_validators.py

[Source code for e19_config_method_validators.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e19_config_method_validators.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e19_config_method_validators.py)

This example shows how to reuse validation and normalization methods that
already exist on the configuration object, often because they come from a
third-party base class.

The configuration derives from a pretend third-party class with methods that
normalize a region string, check a retry-count range, and check that an
endpoint belongs to the selected region. The validation plan uses:

- `CallingMemberValidator` to call a method for one member
- `CallingWholeConfigValidator` to call a method that checks the complete
  configuration
- `MemberValidatorSequence` to run several member validators immediately
  after each other for the same member

The important safety detail is that `CallingMemberValidator` is
validation-only by default. In that mode a called method returns `None` or
`True` to accept the value, and `False` to reject it. A method that should
replace or normalize the stored value must be used with `normalizing=True`.

The `region` member demonstrates this explicitly: first a method normalizes
friendly input such as `US_EAST` to `us-east`, then a normal `StrValidator`
checks the normalized value. The stored configuration keeps the normalized
spelling.

## e20_dynamic_dict_rules.py

[Source code for e20_dynamic_dict_rules.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e20_dynamic_dict_rules.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e20_dynamic_dict_rules.py)

This example returns to `DictForEachValidator` and teaches rules for open
dictionaries where the exact keys are not known in advance.

The configuration has 2 dict members:

- `cache_tunables` accepts arbitrary keys. Keys ending in `_seconds` are
  validated as integer seconds, and keys ending in `_slots` are validated
  against a numeric allowed-values function. Other keys are metadata and
  pass through unchanged.
- `pool_sizes` also accepts arbitrary keys, but every value in the dict must
  be one of the allowed pool sizes.

The example introduces the newer `DictRule.keys` forms:

- a key predicate function, called once for each present key, selects the
  keys that a rule applies to
- `accept_all_keys` is the convenience predicate for applying a rule to
  every present key

It also shows `IntFloatValidator` with a callable `allowed_values`
argument. The callable returns the allowed numeric values when validation
runs, so application code can calculate the choices from its own runtime
state instead of freezing them into the validator call site.

The command line accepts both dict members as JSON values. For example:

`--cache-tunables '{"frontend_seconds":30,"image_slots":8}' --pool-sizes '{"default":4}'`

## e21_as_dict_view_validator.py

[Source code for e21_as_dict_view_validator.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e21_as_dict_view_validator.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e21_as_dict_view_validator.py)

This example teaches `AsDictViewValidator`. It is useful when one
configuration member may be either a real `dict` or an application-defined
runtime object, but both forms should be validated with the same dictionary
rules.

This configuration shows one possible shape for configuration member
variables, and one of the possible shapes where `AsDictViewValidator` is
handy. It is not the one and only recommended shape for configuration
members.

The configuration has one member `retry_policy`. At runtime the default is a
`RetryPolicy` object with public attributes:

- `mode`
- `max_attempts`
- `backoff_seconds`

In JSON, the same member is stored as a dictionary. The example uses
`parse_converters()` to turn that JSON dictionary back into a `RetryPolicy`
object when reading a file. The validation plan uses
`AsDictViewValidator` with `public_attrs_to_dict`, so the object form and the
dict form are both checked with:

- a `DictKeysValidator` for the required key set
- `DictRule` entries for validating and normalizing the values

The important contract detail is that replacement values from dict
validation are stored back when the member is a dict. When the member is a
runtime object, the projected dict is only a validation view and the original
object remains the member value.

The command line accepts the retry policy as one JSON value. For example:

`--retry-policy '{"mode":"EXPONENTIAL","max_attempts":5,"backoff_seconds":60}'`

## e22_dict_key_value_types.py

[Source code for e22_dict_key_value_types.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e22_dict_key_value_types.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e22_dict_key_value_types.py)

This example teaches `DictKeyValueTypesValidator`, the compact validator for
uniform dictionaries. Use it when every key has one runtime type and every
value has one runtime type, such as `dict[str, int]` or
`dict[str, list[float]]`.

The configuration has 2 open dict members:

- `service_ports` is a `dict[str, int]`
- `sample_weights` is a `dict[str, list[float]]`

Both members are listed in `_unchecked_dicts` because their keys are
application data, not a closed schema from the defaults. The validators own
the whole policy instead:

- `DictKeyValueTypesValidator(str, int)` checks the flat `service_ports`
  dictionary
- `DictKeyValueTypesValidator(str, list, ListValueTypeValidator(float))`
  checks that `sample_weights` is a dictionary from strings to lists, and
  then checks the float items inside each list

The nested `value_validator` is deliberately used only to check inside each
list value. If different keys need different business rules, use
`DictForEachValidator` instead; that makes the per-key intent visible at the
call site.

The command line uses the simplest shape for each member:

`--service-ports http=8080 metrics=9090 --sample-weights '{"fast":[0.1,0.9]}'`

## e23_projected_whole_config_validator.py

[Source code for e23_projected_whole_config_validator.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e23_projected_whole_config_validator.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e23_projected_whole_config_validator.py)

This example teaches `ProjectedWholeConfigValidator`. Use it when a rule is
best expressed against a value calculated from the complete configuration
object, but that calculated value should not become a stored configuration
member.

The configuration has 2 members:

- `primary_region`
- `replica_regions`

Each member has its own ordinary validation. The primary region is validated
and normalized with `StrValidator`, and the replica list is checked with
`ListValueValidator`.

The cross-member rule is that the primary region and all replica regions must
be distinct. The validation plan projects the complete config to this
temporary list:

`[primary_region, *replica_regions]`

Then `ProjectedWholeConfigValidator` applies a normal
`ListIsOrderedValidator` to that projected list with `unique_values=True`.
The pseudo-member name `all_regions` exists only for diagnostics; it is not
written to JSON and it does not become an attribute on the configuration
object.

This is the whole-config counterpart to e15. Use
`ProjectedMemberValidator` when the calculated validation view comes from one
stored member. Use `ProjectedWholeConfigValidator` when the validation view
depends on several members or on the whole object.

## e24_list_relation_validator.py

[Source code for e24_list_relation_validator.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e24_list_relation_validator.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e24_list_relation_validator.py)

This example teaches `ListRelationValidator`. Use it when two list-like
values must have a declared relation, such as equal order, equal multisets,
equal distinct values, subset, or disjointness.

The configuration has 2 members:

- `declared_routes` is a list of routes the application should expose
- `route_handlers` is a dictionary from route name to handler name

The rule is that the distinct route names must match on both sides. Every
declared route needs one handler, and every handler key must correspond to a
declared route.

The first side of the relation is the stored `declared_routes` member. The
second side is projected from the keys of `route_handlers`:

`tuple(route_handlers.keys())`

The example uses `ListRelationKind.SET_EQUAL`, so order and duplicates are
ignored by the relation itself. Because duplicate route declarations should
still be rejected, the validation plan keeps that as a separate, explicit
`ListIsOrderedValidator(..., unique_values=True)` step before the relation
check.

This split is intentional. `ListRelationValidator` describes how two
sequences relate to each other. Other list validators should still own
single-list rules such as element type, allowed values, size, order, or
uniqueness.

## e25_value_as_type_validator.py

[Source code for e25_value_as_type_validator.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e25_value_as_type_validator.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e25_value_as_type_validator.py)

This example teaches `ValueAsTypeValidator`. Use it when configuration input
may arrive in a friendly or old representation, but application code should
see one normalized Python type after validation.

The configuration has 2 members:

- `retry_count` is used as an `int`
- `story_points` is also used as an `int`

`retry_count` demonstrates direct conversion. The validation plan accepts
strings and normalizes them with the target constructor:

`int("5")`

That means command line text or JSON text can become the integer `5` before
the application uses the value. The example then applies
`ValueTypeValidator(int, not_allowed_type=bool)` as a second step. This is
intentional because Python treats `bool` as a subclass of `int`; the
normalizing validator keeps an existing boolean unchanged, and the explicit
type validator documents that booleans are not valid retry counts.

`story_points` demonstrates callable conversion. Current configuration files
store story points as integers, but older files may still contain T-shirt
sizes. The validator receives a conversion function, so `"XS"`, `"S"`, `"M"`,
`"L"`, and `"XL"` can become `1`, `2`, `3`, `5`, and `8`.

This is intentionally not an enum example. Normal `Enum` and `IntEnum`
reading has better built-in support through `Config` parse converters; see
`e38_write_side_hook.py` for that pattern.

The command line accepts both values as text:

`--retry-count 5 --story-points XL`

The file written by the example contains the normalized forms: an integer
retry count and integer story points.

## e26_key_ordering_validator.py

[Source code for e26_key_ordering_validator.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e26_key_ordering_validator.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e26_key_ordering_validator.py)

This example teaches `ListKeyOrderingValidator`. Use it when a configuration
member stores a list of complex elements, such as dictionaries, but the list
should be normalized by one scalar key from each element.

The configuration member is `release_steps`. Each list element is a dict with
these keys:

- `step` is the integer ordering key
- `name` is the release step name
- `owner` is optional

The application programmer provides the key function. The key function must
either handle the element shape itself or be used after earlier validators
have checked that shape. This example uses the usually clearer pattern: first
validate the list and dict contents, then keep the key function small and
focused on extracting the ordering value. After that,
`ListKeyOrderingValidator` calls the key function for each dict, sorts the
original dicts by the returned integer key, and removes duplicate `step`
entries because `keep_only_unique=True`.

The file written by the example contains the normalized list of dicts. The
dicts themselves are kept; only their list order and duplicate-key entries
are changed.

The command line accepts the list of dicts as JSON:

`--release-steps '[{"step":20,"name":"test"},{"step":10,"name":"build"}]'`

## e30_optional_user_preference.py

[Source code for e30_optional_user_preference.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e30_optional_user_preference.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e30_optional_user_preference.py)

This example is for configuration values where most users have no opinion,
but expert users may want to pin a choice. When the value is not configured,
the application keeps using its current runtime default. When the value is
configured, the user's explicit preference is stored in JSON and used later.

Most configuration members have a concrete default value and are always
written to the configuration file. That is the right design when the file
should fully describe the value the application will use. Sometimes a missing
configuration value has a better meaning: "the user has no opinion; the
application should choose".

This is useful when your application calls another library that already has a
good default, or when the best choice may change between releases. In that
case, a migration step should not write today's default into every user's
configuration file, because doing so would turn "no opinion" into "always use
this old choice".

The example uses a small report-export configuration. Two members are always
written:

- `report_name`
- `delivery_format`

Two members are intentionally optional:

- `author_note` is an optional string
- `palette` is an optional enum

The configuration class lists those two optional members in
`_omit_none_from_json()`. When a JSON file omits them, the Python object keeps
the constructor value `None`. If the JSON file explicitly contains `null`,
that is also read as `None`. When the configuration is written again, those
members are left out while they are still `None`.

The example also shows the usual application-side pattern: keep the raw
configuration member as `None`, and use a small method such as
`selected_palette()` when the application needs the effective value.

## e31_read_old_configuration_file.py

[Source code for e31_read_old_configuration_file.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e31_read_old_configuration_file.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e31_read_old_configuration_file.py)

This example is for applications that need to keep reading configuration
files written by older releases. It teaches the "Read Old Configuration File"
compatibility hooks, usually shortened to ROCF in the API names.

The example uses a small report configuration. The old file format has these
keys:

- `title`
- `output_format`
- `refresh_interval`
- `debug_trace`

The current file format has these keys:

- `format_version`
- `report_name`
- `output_format`
- `refresh_seconds`
- `max_items`

The example demonstrates three kinds of compatibility:

- `title` is an old name for `report_name`
- `refresh_interval` is an old name for `refresh_seconds`
- old files do not contain `format_version`
- old files do not contain `max_items`
- `debug_trace` only existed in the old format and is removed

The current configuration class handles this by overriding
`_get_read_old_config()` and returning a small
`ReadOldConfiguration` subclass. That subclass describes the compatibility
rules:

- `get_json_key_renames()` maps old key names to current key names
- `get_missing_path_values()` supplies values for mandatory current keys that
  old files did not have
- `get_keys_to_prune()` accepts and drops keys that only existed in the old
  format

The standard application pattern is important: application code constructs
the current configuration class even when the file on disk was written by an
old application version. The old configuration class in this example only
exists so the example can write an old file for demonstration. Normal
application code should not read through the old class.

The example also derives an application-specific class from
`MigrateCfgWarnHook`. The custom `migrate_instructions()` method tells users
the exact command for migrating this example's configuration file. Reading an
old file with the `print` command succeeds, but also prints that warning.

That hook class also overrides `auto_changed()` and calls `print_changes()`
after the standard warning. The two list arguments that `auto_changed()`
receives are the older summary form. They are kept unchanged forever so that
old hook classes keep working, but they are only a summary: they cannot say
whether an `old_name -> new_name` entry was a real move or an old value that
was thrown away because a current value won.

`print_changes()` writes one line per automatic change that really happened,
including that distinction:

```text
Automatic configuration changes were applied:
  pruned old key   debug_trace
  renamed key      title -> report_name
  renamed key      refresh_interval -> refresh_seconds
  supplied value   format_version = 2
  supplied value   max_items = 25
```

It prints nothing at all when no automatic change was applied, so it is safe
to call unconditionally. It needs no knowledge of how the hook stores its
records, so a hook that only calls `print_changes()` keeps working unchanged
when a future config_as_json version records more detail than it does today.

An application that wants those details as data instead of as text reads the
records in `ConfigAutoChangeHook.changes`. That is shown in
`e37_read_old_nested_configuration_file.py`.

The command line is deliberately different from the earlier examples because
migration needs a few distinct workflows:

- `write-old` writes an old-format file for demonstration
- `write-new` writes a current-format file
- `print` reads either old or current files and prints current member names
- `migrate` reads either old or current files and writes current-format JSON

The `migrate` command follows the same standard pattern as the `print`
command: construct the current configuration class from the input file, then
write it back to a new output file. It refuses to overwrite an existing output
file, which is usually the right behavior for a migration command.

## e32_config_factory.py

[Source code for e32_config_factory.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e32_config_factory.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e32_config_factory.py)

This example is for applications that can run in more than one mode, where
each mode has its own configuration class. A CAD program is used as the
teaching story: one mode edits 2D drawings and another mode edits 3D models.

The important code is the small `MATCH_CONFIGS` list. Each `MatchConfig`
pairs a `JsonValueMatcher` with the configuration class to construct when
that matcher accepts the JSON file:

- `mode` equal to `2D` selects `Cad2DConfig`
- `space` equal to `3D` selects `Cad3DConfig`

The two selector keys are intentionally different. The selector value only
needs to be something the matcher can find in the raw JSON text before the
full configuration object is built. In a real application the selector could
just as well be the same member in both classes, or it could be supplied by a
common base class.

The `print` command passes `MATCH_CONFIGS` to `config_factory_from_json()`.
The user does not need to tell the command which mode the file contains; the
file content selects the class.

The `set` command is only there to write small files for the example. It uses
the same command-line helper as most earlier examples and accepts `--mode`,
`--project-name`, and `--grid-size-mm`. The mode argument is optional and
defaults to `2D`.

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
             stderr_file: TextIO = sys.stderr,
             member_name: Optional[str] = None) -> None:
```

They may have additional optional arguments, but the base class constructs
nested objects from JSON using the four keyword names shown above.

`member_name` is the path for reaching the constructed object from the top
level configuration, such as `outputs[1].section`. The base class supplies
it when it constructs a nested object, and a nested class should pass it on
to `super().__init__()` so that diagnostics about the nested object name the
whole path. `None` means that the object is the top level configuration and
not a member of anything. The example `e42_nested_member_paths` shows what
those paths look like in a real diagnostic.

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

## e33_nested_configs.py

[Source code for e33_nested_configs.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e33_nested_configs.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e33_nested_configs.py)

This example shows how to put a repeated group of related settings in its
own `Config` class and then use that class as a nested Config object inside
a larger configuration.

The teaching story is a course registration export. The main configuration
has:

- `course_name`
- `participant_output`, a mandatory nested `TableOutputConfig`
- `audit_output`, an optional nested `TableOutputConfig`

`TableOutputConfig` is an ordinary `Config` class with its own defaults and
validators. It contains:

- `file_name`
- `output_format`
- `encoding`

The main configuration declares the nested members by overriding
`nested_configs()`. The examples use `@override` on this method so a type
checker can catch a misspelled method name:

- `participant_output` uses `ConfigNestingKind.MEMBER`
- `audit_output` uses `ConfigNestingKind.OPTIONAL_MEMBER`

The method should just return stable declaration metadata. It should not
parse data, validate data, mutate the object, or have other side effects.

The optional member also appears in `_omit_none_from_json()`. That makes
`audit_output` behave like other optional members: it may be absent from JSON,
explicit JSON `null` is read as `None`, and it is omitted again while its
value remains `None`.

Nested config classes must derive from `Config` and must be constructible
with the standard keyword arguments `from_json_data_text`,
`from_json_filename`, and `stderr_file`. This is the constructor shape the
base class uses when it parses a nested JSON object.

## e34_list_nested_configs.py

[Source code for e34_list_nested_configs.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e34_list_nested_configs.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e34_list_nested_configs.py)

This example shows how to use a list where every element is a nested
`Config` object.

The teaching story is again a course export tool, but now the course can
produce any number of report outputs. Each report output has the same
settings:

- `name`
- `file_name`
- `output_format`
- `encoding`

Those repeated settings live in `ReportOutputConfig`. The top-level
configuration stores:

- `course_name`
- `reports`, a `list[ReportOutputConfig]`

The important declaration is:

- `reports` uses `ConfigNestingKind.LIST_ELEMENT`

The key returned by `nested_configs()` is the top-level list member. The
`config_type` is the type of each list element. When JSON is read, the base
class expects `reports` to be a JSON list, and each element in that list must
be a JSON object. Each object is parsed by constructing one
`ReportOutputConfig`, so the normal defaults, converters, and validators for
that nested class are applied to every element.

When JSON is written, each `ReportOutputConfig` element is serialized back to
a JSON object. Empty lists are valid, and default lists may also contain one
or more nested config objects.

The command-line helper accepts the whole `reports` value as JSON. That keeps
the example focused on the library feature instead of inventing a separate
command-line syntax for objects inside lists.

## e35_dict_nested_configs.py

[Source code for e35_dict_nested_configs.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e35_dict_nested_configs.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e35_dict_nested_configs.py)

This example shows how to use a dictionary where every value is a nested
`Config` object.

The teaching story is still a course export tool. In example 34 the report
outputs were stored in a list. Here every report has a stable report id, so
a dictionary is a better model:

- `participants` identifies the participant report
- `audit` identifies the audit report
- each dictionary value is a `ReportOutputConfig`

The top-level configuration stores:

- `course_name`
- `reports_by_id`, a `dict[str, ReportOutputConfig]`

The important declaration is:

- `reports_by_id` uses `ConfigNestingKind.DICT_VALUE`

The key returned by `nested_configs()` is the top-level dictionary member.
The `config_type` is the type of each dictionary value. When JSON is read,
the base class expects `reports_by_id` to be a JSON object. Each value in
that object must also be a JSON object, and each value is parsed by
constructing one `ReportOutputConfig`.

When JSON is written, every `ReportOutputConfig` value is serialized back to
a JSON object under its dictionary key. Empty dictionaries are valid, and
default dictionaries may also contain one or more nested config objects.

The command-line helper accepts the whole `reports_by_id` value as JSON. That
keeps the example focused on `ConfigNestingKind.DICT_VALUE` instead of
inventing a separate command-line syntax for fields inside named objects.

## e36_dict_by_key_nested_configs.py

[Source code for e36_dict_by_key_nested_configs.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e36_dict_by_key_nested_configs.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e36_dict_by_key_nested_configs.py)

This example shows how to use one dictionary where selected keys are nested
`Config` objects and the remaining keys are plain JSON values.

The teaching story is still a course export tool. The dictionary
`reports_by_key` contains:

- `participants`, a nested `ReportOutputConfig`
- `audit`, a nested `WebhookOutputConfig`
- `owner`, a plain string
- `max_attempts`, a plain integer

The important declaration is:

- `reports_by_key` uses a list of `ConfigNesting` entries
- every entry in that list uses `ConfigNestingKind.DICT_VALUE_BY_KEY`
- `discriminator_key` names the dictionary key handled by that entry

The list form is needed because two keys inside the same dictionary are
nested Config values. The outer `nested_configs()` key is still only
`reports_by_key`, because that is the public member on the top-level
configuration object. The example uses `@override` on `nested_configs()` so a
type checker can catch a misspelled method name.

When JSON is read, the base class looks inside the `reports_by_key`
dictionary. The value at `participants` is constructed as
`ReportOutputConfig`, and the value at `audit` is constructed as
`WebhookOutputConfig`. The `audit` declaration also has a `factory_function`,
so the base class calls the factory instead of calling the class constructor
directly. The factory has the same keyword arguments as a nested Config
constructor and must return the declared config type or a subclass.

Keys that are not listed by `discriminator_key`, such as `owner` and
`max_attempts`, are written to JSON and read from JSON as ordinary JSON
values. They must not contain `Config` objects in the Python configuration
object, because the base class has no nested Config declaration for those
keys.

The command-line helper accepts the whole `reports_by_key` value as JSON.
That keeps the example focused on `ConfigNestingKind.DICT_VALUE_BY_KEY`
instead of inventing a separate command-line syntax for a mixed dictionary.

## e37_read_old_nested_configuration_file.py

[Source code for e37_read_old_nested_configuration_file.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e37_read_old_nested_configuration_file.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e37_read_old_nested_configuration_file.py)

This example extends e31 to a structural migration with nested Config
objects. The old file format has one optional direct `output` object. The
current file format has `outputs`, a list where each element is a nested
`ReportOutputConfig`.

The example also demonstrates value transformation during ROCF migration. Old
files use `OldOutputFormat` with values such as `COMMA_SEPARATED_VALUES` and
`PLAIN_TEXT`. Current files use the shorter `OutputFormat` values `CSV` and
`TXT`. The meaning is the same, but the enum type and symbolic names changed.
The helper `output_format_from_old()` translates one old enum member to the
matching current enum member.

The `Example37ReadOldConfig` class shows several `ReadOldConfiguration`
features together:

- `course_title` is renamed to `course_name`
- `default_format` is moved to `default_output_format` and transformed from
  `OldOutputFormat` to `OutputFormat`
- `output.format` is moved to `output.output_format` and transformed from
  `OldOutputFormat` to `OutputFormat`
- the whole old `output` object is moved into `outputs[0]`
- if the old optional `output` object is absent, `('outputs',): []` supplies
  the current empty list
- `debug_trace` is removed recursively

The example also highlights one parse-order detail. `parse_converters()` run
before `ReadOldConfiguration`, so enum-valued settings need converters for
both old and current key names when values are moved or renamed. In this
example the current keys use the current enum converter, while the old keys
use the old enum converter. The move rules then pass
`transform_value=output_format_from_old`, so the value arriving at the current
path already has the current enum type before nested Config conversion and
validation.

The function `report_change_records()` shows the other way to report
automatic changes. Instead of printing the ready-made report that
`e31_read_old_configuration_file.py` uses, it reads the structured records in
`ConfigAutoChangeHook.changes`. Each record is a `RocfChange` with:

- `kind`, a `RocfChangeKind` saying what kind of change happened
- `old_path` and `new_path`, the actual paths that were involved
- `value`, the inserted value for `MISSING_VALUE_ADDED` records

Reading the records makes two things possible that a printout cannot do. The
example counts how many changes of each kind happened, and it reports the
values this application version supplied for settings that the old file did
not contain. That value is only available from the records:

```text
Old-file compatibility changed this configuration:
  1 x KEY_PRUNED
  1 x KEY_RENAMED
  1 x MISSING_VALUE_ADDED
  3 x PATH_MOVED
Value supplied by this application version: format_version = 2
```

Paths inside nested `Config` objects are rewritten as paths in the top-level
configuration, for example `outputs[0][encoding]`, so one hook on the
top-level `Config` reports the whole configuration.

Code that reads the records depends on how those records are built.
`ConfigAutoChangeHook.DATA_STRUCTURE_VERSION` is stepped whenever the
recorded members change, including purely additive changes. Such code
therefore declares the version it was written for and checks it:

```python
HOOK_DATA_VERSION = 1
"""Recorded hook data structure version this example was written for."""


def report_change_records(hook: ConfigAutoChangeHook,
                          stderr_file: TextIO) -> None:
    """Report old-file compatibility from the structured change records."""
    hook.check_data_version(written_for=HOOK_DATA_VERSION)
    if not hook.has_changes():
        return
    ...
```

`check_data_version()` raises `HookDataVersionError` when the installed
config_as_json records another version. An incompatible upgrade then fails
with one clear message instead of producing a report that silently says the
wrong thing. Code that only calls `print_changes()` does not need this check.
`has_changes()` is false when the file already used the current shape, so
nothing at all is reported for a current file.

Note where the records are read: not inside the hook class, but in the
application code that constructed the configuration. `Config` keeps the hook
object that the application passed to it, so the records of the parse are
still there afterwards. An application that does not want a hook class of its
own can read the very same records from `config.auto_change_hook().changes`.

The command line mirrors e31:

```sh
python3 -m example.e37_read_old_nested_configuration_file write-old --output old.cfg
python3 -m example.e37_read_old_nested_configuration_file write-old --output old-txt.cfg --default-format plain --output-format plain
python3 -m example.e37_read_old_nested_configuration_file write-new --output new.cfg
python3 -m example.e37_read_old_nested_configuration_file print --input old.cfg
python3 -m example.e37_read_old_nested_configuration_file migrate --input old.cfg --output migrated.cfg
```

## e38_write_side_hook.py

[Source code for e38_write_side_hook.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e38_write_side_hook.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e38_write_side_hook.py)

This example teaches the write-side JSON conversion hook
(`serialize_converters`). The hook runs before `json.dumps` and replaces
rich Python values with JSON-compatible ones, so the file on disk stays
plain JSON while the Python code keeps working with the original types.

The motivating case is `enum.IntEnum`. Because `IntEnum` is a subclass of
`int`, `json.dumps` treats it as an integer and never offers it to a
custom encoder. A pre-serialization hook is the clean way around the
problem. Plain `enum.Enum` members do not have this problem; the library
already has a built-in fallback that converts every `Enum` and `IntEnum`
member to its symbolic `.name`. An explicit converter is only needed
when the value needs a different shape (for example, the numeric value
instead of the name) or when the matched type is not an enum at all.

The `TaskConfig` class in this example stores:

- `project`, a plain string.
- `output_file`, a `pathlib.Path`. `Path` is not a JSON-native type, so
  an explicit converter writes the portable POSIX form. The matching
  `parse_converters` rule reads it back as a `Path`.
- `review_state`, a plain `Enum`. No explicit converter is needed; the
  built-in fallback writes the `.name`.
- `priority`, an `IntEnum`. The explicit converter writes the `.name`,
  which makes the file human-readable and stable across renumbering.

The example demonstrates two selector kinds:

- A *recursive key selector* (a plain string such as `'priority'`)
  matches every dictionary member with that name in data owned by this
  Config object.
- An *absolute path selector* (a `ConfigPath` tuple such as
  `('output_file',)`) targets one specific location in the tree.

Path selectors also support a literal `'['` step to mean "every list
element" or "every dictionary value" at that point. This example does
not use that form because Python lists of plain `Enum` values do not
round-trip through `parse_converters` (which expects scalar JSON values
per top-level key). The typical way to model a list of rich Python
objects is a nested `Config` per element (see `e34_list_nested_configs`),
where each child object declares its own `serialize_converters` and
`parse_converters`.

The command line mirrors e30 and e34:

```sh
python3 -m example.e38_write_side_hook set --output config.cfg
python3 -m example.e38_write_side_hook print --input config.cfg
```

## e39_neutral_base_class.py

[Source code for e39_neutral_base_class.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e39_neutral_base_class.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e39_neutral_base_class.py)

This example is for applications that already have a framework-neutral
data class describing the configuration shape. The neutral class is not
tied to ``config_as_json``; it could equally well be consumed by another
serialization library or by application code that has no serialization
at all. The example shows how to add a thin bridge subclass that
combines the neutral class with ``Config`` so the same data also reads
and writes JSON, validates, and supports nested-config plumbing.

The teaching story uses three neutral classes:

- ``NSubA`` is a leaf section with no constructor arguments
- ``NSubB`` is a leaf section with optional argument-driven defaults
- ``NConfigEager`` is the top-level neutral class with required
  constructor arguments and non-``None`` nested defaults

For each one the example defines a 1:1 bridge subclass (``MySubA``,
``MySubB``, ``MyConfigEager``) that also derives from ``Config``. The
leaf bridges use the familiar ``e04`` multiple-inheritance pattern. The
top-level bridge demonstrates the case where the neutral constructor
requires arguments that the bridge does not want to duplicate.

Two library mechanisms drive the bridge:

- ``Config.copy_initial_data(source, target)`` copies public attributes
  from a neutral source (plain object, dataclass, or mapping) onto a
  ``Config`` target. The bridge calls this in its ``__init__`` to seed
  the bridge's schema from a supplied neutral instance, without having
  to enumerate every member by hand.
- ``Config.__init__`` automatically auto-wraps nested member defaults.
  When the default value of a nested member is a neutral instance
  (rather than the declared bridge type), the library constructs a
  fresh bridge object and copies the neutral's public attributes onto
  it. The auto-wrap pass is recursive and leaves already-wrapped
  values, ``None`` for ``OPTIONAL_MEMBER``, and unrelated scalar
  members unchanged.

The application owns the construction of the neutral instance and the
bridge stays small:

```python
neutral = NConfigEager(c1='hello', b1p=True, b3p=4)
config = MyConfigEager(neutral=neutral)
config.write('example.cfg')
```

The command line mirrors the earlier examples:

```sh
python3 -m example.e39_neutral_base_class set --output config.cfg \
  --c1 hello --b1p true --b3p 4
python3 -m example.e39_neutral_base_class print --input config.cfg
```

## e40_value_migration.py

[Source code for e40_value_migration.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e40_value_migration.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e40_value_migration.py)

This example teaches `RocfValueMigration`, which is the declarative
read-old-configuration rule for cases where one old value produces zero,
one, or several current values. Use it when `RocfKeyMove` is too simple
because the target path depends on the old value, or because one old value
must be split into several current values.

The teaching story uses this old file shape:

- `report_kind`, one string that is either `summary` or `detail`
- `retention_days`, one integer retention setting

The current file shape uses nested dictionaries instead:

- `reports.summary.enabled`
- `reports.detail.enabled`
- `retention.min_days`
- `retention.max_days`

`Example40ReadOldConfig.get_value_migrations()` declares two migrations:

- `report_kind` has two possible writes. The `condition` callback on each
  write decides whether that current path should be produced. A `summary`
  old value writes `reports.summary.enabled`; a `detail` old value writes
  `reports.detail.enabled`.
- `retention_days` has two unconditional writes. One callback derives
  `retention.min_days`, and the other derives `retention.max_days`.

The example also shows how value migrations interact with missing current
values. Missing values are applied after value migrations, so the selected
report kind writes `True` first and the unselected report kind receives the
fallback value `False`.

The command line mirrors the earlier read-old-configuration examples:

```sh
python3 -m example.e40_value_migration write-old --output old.cfg \
  --report-kind detail --retention-days 40
python3 -m example.e40_value_migration write-new --output new.cfg
python3 -m example.e40_value_migration print --input old.cfg
python3 -m example.e40_value_migration migrate --input old.cfg --output migrated.cfg
```

## e41_hex_and_octal.py

[Source code for e41_hex_and_octal.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e41_hex_and_octal.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e41_hex_and_octal.py)

This example teaches `OctalNumber` and `HexadecimalNumber`. They are for
configuration values that are integers to the application, but that the
user of the configuration file reads and writes in another notation:

- a file mode is `0644`, and not the integer 420
- a umask is `0o022`, and not the integer 18
- a Tk colour is `#204060`, and not the integer 2113632
- a bit mask is `0x0000000f`, and not the integer 15

Each such value is a small nested `Config` object with one single public
member holding the written text: `oct_str` for an octal value and `hex_str`
for a hexadecimal one. The configuration file of the example therefore looks
like this:

```json
{
    "feature_bits": {"hex_str": "0x0000000f"},
    "file_mode": {"oct_str": "0644"},
    "report_name": "monthly-report",
    "umask": {"oct_str": "0o022"},
    "window_colour": {"hex_str": "#204060"}
}
```

Storing the written text, and not the integer, is what keeps the notation
through a write, a read, and every parse that an editor makes. An editor
such as `edit-cfg-json-tk` shows the member `oct_str` or `hex_str`, so the
user edits `0644` and never sees the integer 420.

The application asks for the integer with `get()`, and gives a new value
with `set()`. The integer is cached, so asking for it often is cheap.
`set()` accepts any of the notations of its class, so `0o644`, `0644`, and
`644` all set the same file mode, and all three are stored as `0644`. A
hand-edited file is normalized in the same way when it is read, and a value
that is not written in the notation of its class is refused with a message
telling what is wrong with it.

The prefix and the smallest number of digits are a decision of the
application, so they are not stored in the file. The example shows the two
ways of saying them:

- `FileMode` and `TkColour` are subclasses whose `__init__` supplies the
  format. The nested declaration then needs nothing but the class.
- `umask` and `feature_bits` use `OctalNumber.factory()` and
  `HexadecimalNumber.factory()`. The nested declaration gives the factory as
  `ConfigNesting(factory_function=...)`, so the library builds every parsed
  value with that same format.

Both ways matter, because the base class constructs a fresh nested object
every time JSON is parsed. A declaration that says nothing about the format
would be rebuilt with the default format, which is no prefix and as few
digits as the value needs.

The octal prefixes are `Prefix.NONE`, `Prefix.ZERO_O` for the `0o755` of
Python, and `Prefix.ZERO` for the `0755` of the chmod documentation. The
leading zero of `Prefix.ZERO` is kept when a value is read, because it
cannot be told from the padding zeros of a written value, and the value
reads as the same number either way. Declare at least three digits with
that prefix, because the prefix is always written, and the value zero would
otherwise be written as the odd looking `00`. The hexadecimal prefixes are
`Prefix.NONE`, `Prefix.ZERO_X` for `0xff`, and `Prefix.HASH` for the
`#204060` that Tk expects.

Two more things are worth knowing, although the example does not need them:

- `OctalStringValidator` and `HexadecimalStringValidator` validate and
  normalize any plain string member of any `Config` class, for an
  application that wants the written text and not the integer.
- `RadixNumber`, `RadixValidator`, and `RadixSpec` are the shared base of
  the two notations. An application that needs another notation, such as
  binary, declares one `RadixSpec` and derives its own pair of classes.

The command line takes every written number as text, in any accepted
notation:

```sh
python3 -m example.e41_hex_and_octal set --output config.cfg \
  --file-mode 600 --umask 0o077 --window-colour ffffff --feature-bits 0x10
python3 -m example.e41_hex_and_octal print --input config.cfg
```

## e42_nested_member_paths.py

[Source code for e42_nested_member_paths.py: https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e42_nested_member_paths.py](https://github.com/tom-bjorkholm/config_as_json/blob/master/example/src/example/e42_nested_member_paths.py)

Every earlier nested example taught how to *build* nested configuration.
This one is about what the user of the configuration file is *told* when a
value inside a nested object is wrong.

A real configuration has the same member name in more than one place. This
example has `port` twice: the port the service itself listens on, and the
port of each backend it forwards to. Telling the user only that `port` is
invalid is useless, because the user then has to guess which of the three
ports the message is about.

Every diagnostic therefore names the whole path from the top level
configuration down to the value it is about. The notation has two rules:

- Going into an attribute of a nested `Config` object appends a dot and the
  attribute name, as in `section.kind`.
- Indexing into a list or a dict appends the index or the key in square
  brackets, as in `backends[1]` or `limits[cpu]`.

The example uses one single validator, `port_validator()`, for both `port`
members. The validator knows nothing about paths. It is handed the reported
name of the member it validates, and that reported name is already the whole
path. So the same validator produces two different messages:

```sh
python3 -m example.e42_nested_member_paths set -o config.cfg --port 99999
```

```text
Invalid configuration: Value 99999 for port is greater than maximum 65535.
```

```sh
python3 -m example.e42_nested_member_paths set -o config.cfg \
  --backends alpha=8080 beta=99999
```

```text
Invalid configuration: Value 99999 for backends[1].port is greater than maximum 65535.
```

That is the whole point of the paths. The two messages are about two members
that are both called `port`, and the message says which one it is.

The path is carried by the `member_name` argument. The library supplies it
whenever it constructs, parses, validates, or writes a nested object, so a
nested class such as `BackendConfig` only has to pass it on to
`super().__init__()`. `None` means that the object is the top level
configuration and not a member of anything, and then its own members are
reported by their plain names.

Two more things are worth knowing:

- The path is text for a person to read, and not text for a program to parse
  back into its parts. A dict key that itself holds a dot or a square
  bracket therefore makes a path that cannot be taken apart again
  unambiguously.
- The same message appears whether the value came from a configuration file
  or from the application. The example refuses `--backends beta=99999` when
  it writes the file, and refuses the same value with the same words when it
  reads a hand-edited file.

The `print` subcommand labels every value with the path that a diagnostic
would use for it:

```sh
python3 -m example.e42_nested_member_paths set -o config.cfg \
  --service-name audit --backends alpha=8080 beta=9090
python3 -m example.e42_nested_member_paths print -i config.cfg
```
