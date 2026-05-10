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

[Source code for e10_dict_basic_validators.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e10_dict_basic_validators.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e10_dict_basic_validators.py)

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

[Source code for e11_dict_for_each.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e11_dict_for_each.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e11_dict_for_each.py)

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

[Source code for e12_dict_for_each_ordering.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e12_dict_for_each_ordering.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e12_dict_for_each_ordering.py)

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

[Source code for e13_list_of_dicts.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e13_list_of_dicts.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e13_list_of_dicts.py)

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

[Source code for e14_discriminated_dict_validator.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e14_discriminated_dict_validator.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e14_discriminated_dict_validator.py)

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

[Source code for e15_projected_member_validator.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e15_projected_member_validator.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e15_projected_member_validator.py)

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

[Source code for e16_type_and_list_of_dicts_validators.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e16_type_and_list_of_dicts_validators.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e16_type_and_list_of_dicts_validators.py)

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

[Source code for e17_csv_dialect_and_encoding.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e17_csv_dialect_and_encoding.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e17_csv_dialect_and_encoding.py)

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

[Source code for e18_replacing_config_check_helpers.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e18_replacing_config_check_helpers.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e18_replacing_config_check_helpers.py)

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

[Source code for e19_config_method_validators.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e19_config_method_validators.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e19_config_method_validators.py)

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

[Source code for e20_dynamic_dict_rules.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e20_dynamic_dict_rules.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e20_dynamic_dict_rules.py)

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

[Source code for e21_as_dict_view_validator.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e21_as_dict_view_validator.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e21_as_dict_view_validator.py)

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

[Source code for e22_dict_key_value_types.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e22_dict_key_value_types.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e22_dict_key_value_types.py)

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

[Source code for e23_projected_whole_config_validator.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e23_projected_whole_config_validator.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e23_projected_whole_config_validator.py)

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

[Source code for e24_list_relation_validator.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e24_list_relation_validator.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e24_list_relation_validator.py)

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

## e30_optional_user_preference.py

[Source code for e30_optional_user_preference.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e30_optional_user_preference.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e30_optional_user_preference.py)

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

[Source code for e31_read_old_configuration_file.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e31_read_old_configuration_file.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e31_read_old_configuration_file.py)

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

Three kinds of compatibility are shown:

- `title` is an old name for `report_name`
- `refresh_interval` is an old name for `refresh_seconds`
- old files do not contain `format_version`
- old files do not contain `max_items`
- `debug_trace` only existed in the old format and is removed

The current configuration class handles this by overriding three methods.
`_rocf_get_json_key_renames()` describes old key names that should be mapped
to current key names. `_rocf_values_for_missing_json_keys()` supplies values
for mandatory current keys that old files did not have.
`_rocf_get_keys_to_remove()` lists old key names that should be accepted and
dropped because the current configuration no longer has those settings.

The standard application pattern is important: application code constructs
the current configuration class even when the file on disk was written by an
old application version. The old configuration class in this example only
exists so the example can write an old file for demonstration. Normal
application code should not read through the old class.

The example also derives an application-specific class from
`MigrateCfgWarnHook`. The custom `migrate_instructions()` method tells users
the exact command for migrating this example's configuration file. Reading an
old file with the `print` command succeeds, but also prints that warning.

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

[Source code for e32_config_factory.py: https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e32_config_factory.py](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/e32_config_factory.py)

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
