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
an input file to read configuration from with `-i`.
The command lines have two sub-commands `set` and `print`.
The sub-command `set` optionally changes some configuration
values from their defaults based on command-line arguments, and writes
the configuration to a file.
The sub-command `print` reads the configuration from a file,
and prints the configuration to standard output.

To be able to run the example programs the `config_as_json` package
must be installed in your environment.

```sh
pip install --upgrade config-as-json
```

The example programs are *not* included in the package you install.

The example programs are intended to be read in a browser in the
Bitbucket repository, and you can download them from Bitbucket to run
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

## e01_simple_config.py

[Source code for e01_simple_config.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e01_simple_config.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e01_simple_config.py)

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

[Source code for e02_simple_config_get_setattr.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e02_simple_config_get_setattr.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e02_simple_config_get_setattr.py)

This second example is very similar to the first example and it shares much
of the code by importing from the first example.

The difference here is that setattr and getattr are used to set and get
configuration variables. In some situations (like when looping over the
configuration variables) this approach needs less code.

## e03_scalar_validators.py

[Source code for e03_scalar_validators.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e03_scalar_validators.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e03_scalar_validators.py)

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

## e04_third_party_class.py

[Source code for e04_third_party_class.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e04_third_party_class.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e04_third_party_class.py)

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

[Source code for e05_custom_validator.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e05_custom_validator.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e05_custom_validator.py)

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

[Source code for e06_list_basic_validators.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e06_list_basic_validators.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e06_list_basic_validators.py)

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
- `report_formats` shows per-element allowed-values validation
- `backup_servers` shows list-size validation

The important design lesson is that list validation can happen at
different levels. Sometimes the rule is about each element, and sometimes
the rule is about the list as a collection.

## e07_list_order_vs_normalize.py

[Source code for e07_list_order_vs_normalize.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e07_list_order_vs_normalize.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e07_list_order_vs_normalize.py)

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

[Source code for e08_combined_list_validators.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e08_combined_list_validators.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e08_combined_list_validators.py)

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

[Source code for e09_list_for_each.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e09_list_for_each.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e09_list_for_each.py)

This example introduces the general composition tool for per-element
validation, `ListForEachValidator`. It iterates the outer list and
applies a sequence of inner validators to every element, in order. It
does not try to implement any list-level rule on its own, so every
other list validator stays single-purpose.

`ListForEachValidator` is not restricted to a particular element shape.
Typical use cases include:

- **lists of lists**, where each inner list is checked with other list
  validators such as `ListSizeValidator` or `ListValueValidator`
- **lists of dicts**, where each element is checked with a user-defined
  validator that looks at the dict keys
- **lists of scalar values**, where each element is checked or
  normalised by a user-defined validator, for instance a custom
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
