# Predefined validators in config-as-json

`config-as-json` ships with a large collection of ready-made validators.
Most of the validation an application needs is already written, tested and
documented here. The validators are also designed to be combined, so
problems that no single validator covers are usually solved by putting two
or three of them together.

The purpose of this document is to help you *find* the validator, or the
combination of validators, that already solves your problem, before you
write one yourself.

**How to use this document**

- In a hurry? Start at
  [Which validator do I need?](#which-validator-do-i-need) and look up your
  problem in plain words.
- Browsing a problem area? Use
  [Validators by problem area](#validators-by-problem-area).
- Know the name already? Use the
  [Alphabetical index](#alphabetical-index).
- Facing something that needs more than one validator? See
  [Combination recipes](#combination-recipes).

Every validator below has its own section with a description, its
configuration options, the validators it combines well with, a short code
snippet, a link to a worked example program where one exists, and a link
to its full API description in [api.md](api.md).

## Contents

- [How validators are plugged in](#how-validators-are-plugged-in)
- [Which validator do I need?](#which-validator-do-i-need)
- [Validators by problem area](#validators-by-problem-area)
- [Alphabetical index](#alphabetical-index)
- [Scalar value validators](#scalar-value-validators)
- [String validators](#string-validators)
- [List validators](#list-validators)
- [Dictionary validators](#dictionary-validators)
- [Composition and adapter validators](#composition-and-adapter-validators)
- [Whole-configuration validators](#whole-configuration-validators)
- [Domain-specific validators](#domain-specific-validators)
- [Supporting types](#supporting-types)
- [Validation helper functions](#validation-helper-functions)
- [Combination recipes](#combination-recipes)

## How validators are plugged in

Your configuration class overrides `get_validation_plan()` and returns an
ordered list of validation steps. A `MemberValidationStep` applies one
`MemberValidator` to one or more named members. A
`WholeConfigValidationStep` applies one `WholeConfigValidator` to the whole
configuration object.

````python
from typing import Optional, TextIO
import sys
from config_as_json import Config, IntFloatValidator, \
    MemberValidationStep, PathOrStr, ValidationPlan


class MyConfig(Config):
    """Configuration for my application."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for my application."""
        self.story_points: int = 5
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this configuration."""
        _ = stderr_file
        points = IntFloatValidator(min_value=1, max_value=13,
                                   allowed_values=None)
        return [MemberValidationStep(member_names=['story_points'],
                                     validator=points)]
````

Three properties of the plan are worth knowing before you pick validators,
because they are what makes combining validators work:

1. **The order of the steps is part of your design.** Steps run in list
   order, and later steps see whatever earlier steps left behind.
2. **A validator may normalize.** The value returned from
   `validate_member()` is stored back into the configuration member. That
   is how `ListOrderingValidator` can sort a list and how
   `ValueAsTypeValidator` can convert a value. Validators that only check
   return the value unchanged.
3. **Errors name the member.** Failures raise `InvalidConfiguration` or
   `InvalidConfigurationValue` after writing a message naming the member.
   When a validator descends into a list or dict, the reported name carries
   the index or key, for example `run_hours_utc[3]` or `columns[width]`.

## Which validator do I need?

| I need to ... | Reach for |
| --- | --- |
| Keep a number inside a range, or restrict it to a set of numbers | [IntFloatValidator](#intfloatvalidator) |
| Reject `True`/`False` where an integer is expected | [ValueTypeValidator](#valuetypevalidator) with `not_allowed_type=bool`; see [recipe](#an-integer-between-0-and-15-that-is-not-a-bool) |
| Restrict a string to a set of allowed words | [StrValidator](#strvalidator) |
| Accept an abbreviation such as `war` for `warning` | [StrValidator](#strvalidator) with `best_match=True` |
| Limit how long a string may be | [StrLenValidator](#strlenvalidator) |
| Require or enforce capitalization | [StrCaseValidator](#strcasevalidator), [StrCaseChangeValidator](#strcasechangevalidator) |
| Check that a value has a given Python type | [ValueTypeValidator](#valuetypevalidator) |
| Accept several input types and convert to one | [ValueAsTypeValidator](#valueastypevalidator) |
| Allow a member to be `None` but validate it otherwise | [OptionalMemberValidator](#optionalmembervalidator) |
| Apply several validators to the same member | [MemberValidatorSequence](#membervalidatorsequence) |
| Limit how many entries a list may have | [ListSizeValidator](#listsizevalidator) |
| Require every list element to have one type | [ListValueTypeValidator](#listvaluetypevalidator) |
| Range-check every element of a list of numbers | [ListValueValidator](#listvaluevalidator) |
| Require a list to be sorted, or free of duplicates | [ListIsOrderedValidator](#listisorderedvalidator) |
| Sort a list, or remove duplicates from it, for the user | [ListOrderingValidator](#listorderingvalidator) |
| Sort a list of dicts by one field, or drop duplicate ids | [ListKeyOrderingValidator](#listkeyorderingvalidator) |
| Validate every element of a list with other validators | [ListForEachValidator](#listforeachvalidator) |
| Check the keys of every dict in a list of dicts | [ListOfDictsKeysValidator](#listofdictskeysvalidator) |
| Require certain dict keys and reject unknown ones | [DictKeysValidator](#dictkeysvalidator) |
| Validate the value stored at specific dict keys | [DictForEachValidator](#dictforeachvalidator) with [DictRule](#dictrule) |
| Validate a uniform `dict[str, int]`-shaped member | [DictKeyValueTypesValidator](#dictkeyvaluetypesvalidator) |
| Let a `kind` field decide which keys a dict must have | [DiscriminatedDictValidator](#discriminateddictvalidator) |
| Accept either a dict or an application object for one member | [AsDictViewValidator](#asdictviewvalidator) |
| Validate something computed from a member rather than the member | [ProjectedMemberValidator](#projectedmembervalidator) |
| Validate something computed from several members | [ProjectedWholeConfigValidator](#projectedwholeconfigvalidator) |
| Require two lists to be equal, disjoint, or a subset | [ListRelationValidator](#listrelationvalidator) |
| Reuse validation code that already lives in a base class | [CallingMemberValidator](#callingmembervalidator), [CallingWholeConfigValidator](#callingwholeconfigvalidator) |
| Check that a string names a real character encoding | [CharEncodingValidator](#charencodingvalidator) |
| Validate CSV dialect settings from the configuration file | [CsvDialectValidator](#csvdialectvalidator) |
| Keep a number written as hexadecimal text such as `#204060` | [HexadecimalStringValidator](#hexadecimalstringvalidator) |
| Keep a file mode written as octal text such as `0644` | [OctalStringValidator](#octalstringvalidator) |
| Write a number in some other base | [RadixValidator](#radixvalidator) |

## Validators by problem area

### Numbers and value ranges

- [IntFloatValidator](#intfloatvalidator) — bounds and allowed values for
  one `int` or `float` member.
- [ListValueValidator](#listvaluevalidator) — the same bounds applied to
  every element of a list.
- [ValueTypeValidator](#valuetypevalidator) — the runtime type check that
  separates `int` from `bool`.

### Text

- [StrValidator](#strvalidator) — allowed words, case-insensitive
  matching, abbreviation matching, normalization.
- [StrLenValidator](#strlenvalidator) — minimum and maximum length.
- [StrCaseValidator](#strcasevalidator) — require a capitalization style.
- [StrCaseChangeValidator](#strcasechangevalidator) — apply a
  capitalization style.
- [CharEncodingValidator](#charencodingvalidator) — the string must name a
  text encoding Python knows.

### Runtime types and conversion

- [ValueTypeValidator](#valuetypevalidator) — require a type, forbid a
  type, or require an exact type.
- [ValueAsTypeValidator](#valueastypevalidator) — accept several input
  types and normalize to one.
- [ListValueTypeValidator](#listvaluetypevalidator) — one type for every
  list element.
- [DictKeyValueTypesValidator](#dictkeyvaluetypesvalidator) — one key type
  and one value type for a whole dict.

### Lists seen as a whole

- [ListSizeValidator](#listsizevalidator) — length bounds.
- [ListIsOrderedValidator](#listisorderedvalidator) — reject a list that is
  unsorted or has duplicates.
- [ListOrderingValidator](#listorderingvalidator) — sort, reverse, and
  deduplicate a list of scalars.
- [ListKeyOrderingValidator](#listkeyorderingvalidator) — the same, for
  complex elements ordered by a projected key.
- [ListRelationValidator](#listrelationvalidator) — require a relation
  between two lists.

### Lists seen element by element

- [ListForEachValidator](#listforeachvalidator) — apply any validators to
  every element; the general composition mechanism for lists.
- [ListOfDictsKeysValidator](#listofdictskeysvalidator) — the key policy of
  every dict in a list of dicts.
- [ListValueValidator](#listvaluevalidator) — bounds and allowed values for
  scalar elements.

### Dictionary key sets

- [DictKeysValidator](#dictkeysvalidator) — mandatory keys, optional keys,
  and whether unknown keys are accepted.
- [ListOfDictsKeysValidator](#listofdictskeysvalidator) — the same policy
  applied to every dict in a list.
- [DiscriminatedDictValidator](#discriminateddictvalidator) — a different
  key policy per variant, chosen by one field.

### Dictionary values

- [DictForEachValidator](#dictforeachvalidator) — per-key validators driven
  by [DictRule](#dictrule) entries.
- [DictKeyValueTypesValidator](#dictkeyvaluetypesvalidator) — uniform key
  and value types.
- [AsDictViewValidator](#asdictviewvalidator) — one dictionary policy for a
  member that may be a dict or an application object.

### Optional values and composition

- [OptionalMemberValidator](#optionalmembervalidator) — skip validation
  while the value is `None`.
- [MemberValidatorSequence](#membervalidatorsequence) — several validators
  on one member, in order.
- [ListForEachValidator](#listforeachvalidator) — descend into a list.
- [DictForEachValidator](#dictforeachvalidator) — descend into a dict.
- [ProjectedMemberValidator](#projectedmembervalidator) — validate a
  computed view of a member.

### Rules that span several members

- [ListRelationValidator](#listrelationvalidator) — two list-like values
  must be equal, a subset, disjoint, and so on.
- [ProjectedWholeConfigValidator](#projectedwholeconfigvalidator) —
  validate a value computed from the whole configuration.
- [CallingWholeConfigValidator](#callingwholeconfigvalidator) — call a
  method on the configuration object.

### Reusing validation logic you already have

- [CallingMemberValidator](#callingmembervalidator) — call a method of the
  configuration object to validate one member. Useful when your
  configuration class also derives from a third-party class that already
  validates.
- [CallingWholeConfigValidator](#callingwholeconfigvalidator) — the same
  for the whole configuration.
- [AsDictViewValidator](#asdictviewvalidator) — reuse dictionary rules for
  an application object.
- [ProjectedMemberValidator](#projectedmembervalidator) — reuse existing
  validators on a computed view.

### Validators that normalize the stored value

These validators may return a value different from the one they received,
and that returned value replaces the configuration member. Use them when
you want to accept forgiving input and store a canonical value.

- [StrValidator](#strvalidator) — with `normalize=True` or
  `best_match=True`.
- [StrCaseChangeValidator](#strcasechangevalidator) — always rewrites the
  string.
- [ValueAsTypeValidator](#valueastypevalidator) — converts to the target
  type.
- [ListOrderingValidator](#listorderingvalidator) and
  [ListKeyOrderingValidator](#listkeyorderingvalidator) — return a
  reordered or deduplicated list.
- [CsvDialectValidator](#csvdialectvalidator) — fills missing optional keys
  with `None`.
- [RadixValidator](#radixvalidator),
  [HexadecimalStringValidator](#hexadecimalstringvalidator) and
  [OctalStringValidator](#octalstringvalidator) — rewrite the value with
  the declared prefix and digit count.
- [CallingMemberValidator](#callingmembervalidator) — when
  `normalizing=True`.
- Container validators such as
  [ListForEachValidator](#listforeachvalidator),
  [DictForEachValidator](#dictforeachvalidator) and
  [MemberValidatorSequence](#membervalidatorsequence) pass normalized
  values through from the validators they wrap.

### File formats and notations

- [CsvDialectValidator](#csvdialectvalidator) — CSV dialect settings.
- [CharEncodingValidator](#charencodingvalidator) — text encoding names.
- [HexadecimalStringValidator](#hexadecimalstringvalidator) — hexadecimal
  text such as `#204060`.
- [OctalStringValidator](#octalstringvalidator) — octal text such as
  `0644`.
- [RadixValidator](#radixvalidator) — the base class for other notations.

## Alphabetical index

Every predefined validator, supporting type, and validation helper in
`config_as_json`, in alphabetical order.

| Name | Purpose |
| --- | --- |
| [accept_all_keys](#accept_all_keys) | Key predicate that selects every key of a dict |
| [AsDictViewValidator](#asdictviewvalidator) | One dictionary policy for a member that is a dict or an application object |
| [CallingMemberValidator](#callingmembervalidator) | Validate a member by calling a method of the configuration object |
| [CallingWholeConfigValidator](#callingwholeconfigvalidator) | Validate the configuration by calling a method of the configuration object |
| [CharEncodingValidator](#charencodingvalidator) | The string must name a text encoding Python recognizes |
| [check_char_encoding](#check_char_encoding) | Exit with a helpful message when an encoding name is unknown |
| [CsvDialectConfig](#csvdialectconfig) | The `TypedDict` shape of a CSV dialect configuration member |
| [CsvDialectValidator](#csvdialectvalidator) | Validate and normalize CSV dialect settings |
| [DictForEachValidator](#dictforeachvalidator) | Apply per-key validators to selected dict keys |
| [DictKeysValidator](#dictkeysvalidator) | Mandatory, optional, and unknown key policy for a dict |
| [DictKeyValueTypesValidator](#dictkeyvaluetypesvalidator) | One key type and one value type for a uniform dict |
| [DictRule](#dictrule) | Bind a sequence of validators to a set of dict keys |
| [DictVariant](#dictvariant) | Describe one allowed shape of a discriminated dict |
| [DiscriminatedDictValidator](#discriminateddictvalidator) | Pick the dict shape from the value of one discriminator key |
| [file_must_exist](#file_must_exist) | Stop early with a clear message when a required file is missing |
| [fix_file_extension](#fix_file_extension) | Normalize a filename to the extension the application expects |
| [get_csv_dialect](#get_csv_dialect) | Build a `csv.Dialect` from validated configuration fields |
| [HexadecimalStringValidator](#hexadecimalstringvalidator) | Validate and normalize hexadecimal text such as `#204060` |
| [IntFloatValidator](#intfloatvalidator) | Bounds and allowed values for one `int` or `float` member |
| [ListForEachValidator](#listforeachvalidator) | Apply a sequence of validators to every list element |
| [ListIsOrderedValidator](#listisorderedvalidator) | Reject a list that is unsorted or contains duplicates |
| [ListKeyOrderingValidator](#listkeyorderingvalidator) | Sort or deduplicate complex list elements through a scalar key |
| [ListOfDictsKeysValidator](#listofdictskeysvalidator) | The key policy of every dict in a list of dicts |
| [ListOrderingValidator](#listorderingvalidator) | Sort, reverse, and deduplicate a list of scalars |
| [ListRelationKind](#listrelationkind) | The relation required between two list-like values |
| [ListRelationValidator](#listrelationvalidator) | Require a relation between two list-like values |
| [ListSizeValidator](#listsizevalidator) | Minimum and maximum length of a list |
| [ListValueTypeValidator](#listvaluetypevalidator) | One runtime type for every element of a list |
| [ListValueValidator](#listvaluevalidator) | Bounds and allowed values for every scalar element of a list |
| [MemberProjector](#memberprojector) | Callable that computes the validation view of one member |
| [MemberValidatorSequence](#membervalidatorsequence) | Apply several validators to one member, in order |
| [OctalStringValidator](#octalstringvalidator) | Validate and normalize octal text such as `0644` |
| [OptionalMemberValidator](#optionalmembervalidator) | Skip validation while the member value is `None` |
| [ProjectedMemberValidator](#projectedmembervalidator) | Validate a computed view of one member |
| [ProjectedWholeConfigValidator](#projectedwholeconfigvalidator) | Validate a value computed from the whole configuration |
| [public_attrs_to_dict](#public_attrs_to_dict) | Project the public attributes of an object to a dict |
| [RadixSpec](#radixspec) | Describe one number notation for `RadixValidator` |
| [RadixValidator](#radixvalidator) | Validate and normalize a number written in a chosen base |
| [StrCaseChangeValidator](#strcasechangevalidator) | Rewrite a string to a capitalization style |
| [StrCaseSpec](#strcasespec) | The case required or applied at a position |
| [StrCaseValidator](#strcasevalidator) | Require a capitalization style |
| [StrLenValidator](#strlenvalidator) | Minimum and maximum length of a string |
| [StrPositionSpec](#strpositionspec) | The positions a case rule applies to |
| [string_best_match](#string_best_match) | Match a string to allowed values, accepting a unique prefix |
| [string_to_enum_best_match](#string_to_enum_best_match) | Match a string to an enum member, accepting a unique prefix |
| [StrValidator](#strvalidator) | Restrict a string to allowed values, with optional normalization |
| [valid_char_encoding](#valid_char_encoding) | Report whether a string names a text encoding Python recognizes |
| [ValueAsTypeValidator](#valueastypevalidator) | Accept several input types and normalize to one |
| [ValueTypeValidator](#valuetypevalidator) | Require a runtime type, and optionally forbid one |
| [WholeConfigProjector](#wholeconfigprojector) | Callable that computes a validation view from the whole configuration |

## Scalar value validators

### IntFloatValidator

`IntFloatValidator` is the validator for a single numeric configuration
member. It checks that the value is exactly an `int` or exactly a `float`
(whichever the constraints imply), and then that the value satisfies every
constraint you supplied: a lower bound, an upper bound, and membership in a
set of allowed values. This is the validator for "story points must be
between 1 and 13", "the timeout must not be negative", and "the sample rate
must be one of 8000, 16000, or 44100".

The numeric type is inferred from the constraints, so
`IntFloatValidator(min_value=0, max_value=10, allowed_values=None)` requires
an `int` member and `IntFloatValidator(min_value=0.0, max_value=1.0,
allowed_values=None)` requires a `float` member. At least one of the three
constraints must be supplied; a validator with no constraint at all would
have nothing to check and is rejected in the constructor. `allowed_values`
may be a callable that is invoked at validation time, which is how you
express a set of allowed values that depends on another part of the
configuration.

One thing to watch: the type check uses `isinstance`, and in Python `bool`
is a subclass of `int`. A member holding `True` therefore passes an
`int`-typed `IntFloatValidator`. When a JSON `true` must not be silently
accepted as the number 1, put a
[ValueTypeValidator](#valuetypevalidator) with `not_allowed_type=bool`
before it; see
[the recipe below](#an-integer-between-0-and-15-that-is-not-a-bool).

**Combines well with:** [ValueTypeValidator](#valuetypevalidator) to reject
`bool`, [OptionalMemberValidator](#optionalmembervalidator) when the member
may be `None`, [MemberValidatorSequence](#membervalidatorsequence) to chain
the two, [DictRule](#dictrule) inside
[DictForEachValidator](#dictforeachvalidator) to bound one dict value, and
[ListForEachValidator](#listforeachvalidator) to bound each element of a
list of dicts.

````python
from config_as_json import IntFloatValidator

points = IntFloatValidator(min_value=1, max_value=13, allowed_values=None)
rate = IntFloatValidator(min_value=None, max_value=None,
                         allowed_values=[8000, 16000, 44100])
````

Worked example:
[e03_scalar_validators.py](../example/src/example/e03_scalar_validators.py)

Full API:
[`IntFloatValidator`](api.md#config_as_json.validator.IntFloatValidator)

### ValueTypeValidator

`ValueTypeValidator` checks the runtime type of one member value and
nothing else. It solves the problem of a configuration file that parses as
valid JSON but puts the wrong kind of value in a member: a string where a
number belongs, `true` where an integer belongs, or a list where a dict
belongs. Because it only checks the type, it is the natural first validator
in a chain, running before validators that assume the value already has the
right shape.

There are three configuration options. `value_type` is the required type,
or a list of types when several are acceptable. `not_allowed_type` names
types that are rejected even though they would otherwise pass, and the
motivating case is `not_allowed_type=bool` with `value_type=int`, which
turns Python's "`bool` is an `int`" rule off for that member. `strict`
switches from `isinstance` semantics to exact `type(value)` matching, which
also excludes `bool` from `int` and additionally excludes every other
subclass. The constructor rejects contradictory arguments, so a validator
that could never accept anything fails at construction rather than at
runtime.

**Combines well with:** [IntFloatValidator](#intfloatvalidator) and
[StrValidator](#strvalidator) as the type gate in front of a value check,
[MemberValidatorSequence](#membervalidatorsequence) to chain them,
[ListForEachValidator](#listforeachvalidator) to type-check each element,
and [DictRule](#dictrule) to type-check one dict key.

````python
from config_as_json import ValueTypeValidator

# An int, and not a bool.
count = ValueTypeValidator(value_type=int, not_allowed_type=bool)
# Either an int or a float.
measure = ValueTypeValidator(value_type=[int, float],
                             not_allowed_type=bool)
# Exactly an int, no subclasses at all.
exact = ValueTypeValidator(value_type=int, strict=True)
````

Worked example:
[e16_type_and_list_of_dicts_validators.py](../example/src/example/e16_type_and_list_of_dicts_validators.py)

Full API:
[`ValueTypeValidator`](api.md#config_as_json.type_validators.ValueTypeValidator)

### ValueAsTypeValidator

`ValueAsTypeValidator` accepts a member value written in any of several
forms and normalizes it to one target type. It solves the "be liberal in
what you accept" problem for configuration files edited by hand: the user
may write `8080` or `"8080"`, `1` or `1.0`, and the application still gets
one predictable type. A value that already has the target type is returned
unchanged.

Two mechanisms produce the conversion. `direct_types` lists input types
converted by calling the target type's own constructor, as in `int("8080")`.
`convertable_types` maps an input type to a callable you supply, for cases
where the constructor is not the right conversion. If a value matches both
a direct type and a convertable type, the type closest to the value's own
type in the method resolution order decides. A value matching neither is
rejected, as is a conversion that raises or that returns the wrong type,
and all three produce an `InvalidConfigurationType` naming the member.
Because this validator derives from
[ValueTypeValidator](#valuetypevalidator), it also carries the plain type
check for the target type.

**Combines well with:** [IntFloatValidator](#intfloatvalidator) placed
after it, so the range check runs on the converted value;
[MemberValidatorSequence](#membervalidatorsequence) to express that order;
and [ListForEachValidator](#listforeachvalidator) or
[DictForEachValidator](#dictforeachvalidator) to normalize elements of a
container.

````python
from config_as_json import ValueAsTypeValidator

# Accept 8080, '8080' and 8080.0; always store an int.
port = ValueAsTypeValidator(value_type=int, direct_types=[str, float])
# Accept a str through a custom conversion.
minutes = ValueAsTypeValidator(
    value_type=int,
    convertable_types={str: lambda v: int(str(v).removesuffix('min'))})
````

Worked example:
[e25_value_as_type_validator.py](../example/src/example/e25_value_as_type_validator.py)

Full API:
[`ValueAsTypeValidator`](api.md#config_as_json.type_validators.ValueAsTypeValidator)

## String validators

### StrValidator

`StrValidator` restricts a string member to a set of allowed values. It is
the validator for configuration members that are really a choice: a log
level, a colour name, an output format, a mode. It first checks that the
value is a string at all, then compares it against the allowed values, and
raises `InvalidConfigurationValue` listing the allowed values when nothing
matches. That error message, which names the member and shows what would
have been acceptable, is a large part of what makes this validator worth
using instead of a hand-written membership test.

Four options change how forgiving and how normalizing it is.
`ignore_case=True` makes the comparison case-insensitive, so `Warning`
matches `warning`. `normalize=True` returns the entry from `allowed_values`
rather than what the user wrote, so the stored value is the canonical
spelling. `best_match=True` additionally accepts a unique prefix ignoring
case, so `war` matches `warning` as long as no other allowed value starts
with those letters; note that a best match always returns the matched
allowed value, so this option normalizes even when `normalize` is `False`.
`allowed_values` may be a callable evaluated at validation time when the
allowed set depends on other configuration.

Enum members do not need this validator. The `Config` base class already
validates a member whose default is an enum member, so a `Severity` member
is checked without any validation step of your own.

**Combines well with:** [StrLenValidator](#strlenvalidator) and
[StrCaseValidator](#strcasevalidator) for free-form strings that are not a
fixed choice, [OptionalMemberValidator](#optionalmembervalidator) for a
member that may be `None`,
[MemberValidatorSequence](#membervalidatorsequence) to chain several string
rules, and [DictRule](#dictrule) or
[DictVariant](#dictvariant) to apply it to one key of a dict. It is also
the natural `discriminator_validator` for
[DiscriminatedDictValidator](#discriminateddictvalidator).

````python
from config_as_json import StrValidator

# Strict membership.
fmt = StrValidator(allowed_values=['csv', 'json', 'xml'], ignore_case=False)
# Forgiving: accepts 'WARN', 'warn' and 'w' for 'warning'.
level = StrValidator(allowed_values=['debug', 'info', 'warning', 'error'],
                     ignore_case=True, best_match=True, normalize=True)
````

Worked example:
[e03_scalar_validators.py](../example/src/example/e03_scalar_validators.py)

Full API:
[`StrValidator`](api.md#config_as_json.str_validators.StrValidator)

### StrLenValidator

`StrLenValidator` checks that a string member's length is within bounds. It
covers the cases where a string is free-form but not unlimited: a report
title that must fit a column, a prefix that must be non-empty, an
identifier that a downstream system truncates. Passing `min_length=1`
is the compact way to say "this string may not be empty".

Either bound may be `None` to leave that side unconstrained, but not both,
since a validator with no bound would check nothing. Either bound may also
be a callable evaluated at validation time, which lets one member's
allowed length depend on another member's value. Negative bounds and a
minimum greater than the maximum are rejected in the constructor.

**Combines well with:** [StrValidator](#strvalidator) when the string is
both a choice and length-limited, [StrCaseValidator](#strcasevalidator) or
[StrCaseChangeValidator](#strcasechangevalidator) for capitalization,
[MemberValidatorSequence](#membervalidatorsequence) to chain them,
[ListForEachValidator](#listforeachvalidator) to bound the length of every
string in a list, and [OptionalMemberValidator](#optionalmembervalidator)
for a member that may be `None`.

````python
from config_as_json import StrLenValidator

title = StrLenValidator(min_length=1, max_length=60)
not_empty = StrLenValidator(min_length=1, max_length=None)
````

Full API:
[`StrLenValidator`](api.md#config_as_json.str_validators.StrLenValidator)

### StrCaseValidator

`StrCaseValidator` checks the capitalization of a string member without
changing it. It expresses rules such as "the report title must be in title
case", "the environment variable name must be upper case", and "the tag
must be lower case". A character that violates the rule produces an error
naming the member, the character, and the position, so the user can see
exactly what to change.

The rule is described by three arguments. `special_position` is a
[StrPositionSpec](#strpositionspec) that says which characters are special:
the first character of the string, the first character of each word, the
first character of each sentence, or every character.
`special_position_case` is the [StrCaseSpec](#strcasespec) required at
those positions, and `other_position_case` is the one required everywhere
else. `StrCaseSpec.ORIGINAL` means "no requirement here", which is how you
constrain only the special positions.

Use this validator when a violation should be reported to the user. Use
[StrCaseChangeValidator](#strcasechangevalidator) instead when the
application should silently fix the capitalization.

**Combines well with:** [StrValidator](#strvalidator) and
[StrLenValidator](#strlenvalidator) chained through
[MemberValidatorSequence](#membervalidatorsequence), and
[ListForEachValidator](#listforeachvalidator) for a list of strings.

````python
from config_as_json import StrCaseSpec, StrCaseValidator, StrPositionSpec

# Every character must be upper case.
env_name = StrCaseValidator(
    special_position=StrPositionSpec.EVERY_CHARACTER,
    special_position_case=StrCaseSpec.UPPER,
    other_position_case=StrCaseSpec.UPPER)
# Title case: each word starts upper, the rest is lower.
title = StrCaseValidator(special_position=StrPositionSpec.FIRST_IN_WORD,
                         special_position_case=StrCaseSpec.UPPER,
                         other_position_case=StrCaseSpec.LOWER)
````

Full API:
[`StrCaseValidator`](api.md#config_as_json.str_validators.StrCaseValidator)

### StrCaseChangeValidator

`StrCaseChangeValidator` takes the same three arguments as
[StrCaseValidator](#strcasevalidator) but rewrites the string instead of
rejecting it. It is the choice when the capitalization is a presentation
detail your application owns rather than something the user should be
nagged about: normalizing a tag to lower case before it is used as a
lookup key, or capitalizing a report heading regardless of how it was
typed. The rewritten string is what gets stored in the configuration
member, and therefore what is written back to the JSON file.

Because the value is always rewritten, this validator never fails on
capitalization. It still rejects a member value that is not a string.

**Combines well with:** [StrValidator](#strvalidator) placed *after* it, so
membership is tested against the normalized spelling;
[MemberValidatorSequence](#membervalidatorsequence) to express that order;
and [ListForEachValidator](#listforeachvalidator) or
[DictForEachValidator](#dictforeachvalidator) to normalize strings inside a
container.

````python
from config_as_json import StrCaseChangeValidator, StrCaseSpec, \
    StrPositionSpec

to_lower = StrCaseChangeValidator(
    special_position=StrPositionSpec.EVERY_CHARACTER,
    special_position_case=StrCaseSpec.LOWER,
    other_position_case=StrCaseSpec.LOWER)
sentence = StrCaseChangeValidator(
    special_position=StrPositionSpec.FIRST_IN_SENTENCE,
    special_position_case=StrCaseSpec.UPPER,
    other_position_case=StrCaseSpec.ORIGINAL)
````

Full API:
[`StrCaseChangeValidator`](api.md#config_as_json.str_validators.StrCaseChangeValidator)

## List validators

### ListSizeValidator

`ListSizeValidator` checks that a list member holds between `min_size` and
`max_size` elements, inclusive. It answers "at least one output column must
be configured", "no more than eight worker names", and "exactly three
coordinates" (which is `min_size=3, max_size=3`). Both bounds are
mandatory, which keeps the intent explicit; use a large `max_size` when
there is genuinely no upper limit worth enforcing.

The validator accepts only an actual `list`. Both bounds must be exactly
`int`, must not be negative, and `min_size` may not exceed `max_size`;
these are checked in the constructor.

Where you place this step matters. Put it *before* a normalizing validator
to check what the user actually wrote, or *after* one to check what the
application will actually use. A list `[12, 12]` passes a
`min_size=2` check placed first, but fails it when placed after a
[ListOrderingValidator](#listorderingvalidator) with
`keep_only_unique=True` has collapsed the list to `[12]`.

**Combines well with:** [ListValueValidator](#listvaluevalidator) and
[ListValueTypeValidator](#listvaluetypevalidator) for element checks,
[ListOrderingValidator](#listorderingvalidator) for normalization, and
[ListForEachValidator](#listforeachvalidator) when the elements are
themselves containers. It is also useful as an inner validator of
`ListForEachValidator` to bound the length of each row of a matrix.

````python
from config_as_json import ListSizeValidator

at_least_one = ListSizeValidator(min_size=1, max_size=32)
exactly_three = ListSizeValidator(min_size=3, max_size=3)
````

Worked example:
[e06_list_basic_validators.py](../example/src/example/e06_list_basic_validators.py)

Full API:
[`ListSizeValidator`](api.md#config_as_json.list_value_validators.ListSizeValidator)

### ListValueTypeValidator

`ListValueTypeValidator` checks that a member is a list and that every
element is an instance of one runtime type. It is the compact answer to
"this must be a list of strings" or "this must be a list of dicts", and it
is worth reaching for before any validator that assumes the elements
already have a known shape.

The single `element_type` argument is checked with `isinstance`, so
subclasses are accepted. As with any `isinstance` check on `int`, a `bool`
element passes an `int` list; use
[ListForEachValidator](#listforeachvalidator) with an inner
[ValueTypeValidator](#valuetypevalidator) when that matters.

**Combines well with:** [ListSizeValidator](#listsizevalidator) for length,
[ListValueValidator](#listvaluevalidator) for element ranges,
[ListOfDictsKeysValidator](#listofdictskeysvalidator) when the type is
`dict`, and [DictKeyValueTypesValidator](#dictkeyvaluetypesvalidator) as
the `value_validator` for a `dict[str, list[float]]`-shaped member.

````python
from config_as_json import ListValueTypeValidator

names = ListValueTypeValidator(element_type=str)
rows = ListValueTypeValidator(element_type=dict)
````

Worked example:
[e16_type_and_list_of_dicts_validators.py](../example/src/example/e16_type_and_list_of_dicts_validators.py)

Full API:
[`ListValueTypeValidator`](api.md#config_as_json.list_value_validators.ListValueTypeValidator)

### ListValueValidator

`ListValueValidator` applies the same value constraints to every element of
a list of scalars: a lower bound, an upper bound, and membership in a set
of allowed values. It is the list counterpart of
[IntFloatValidator](#intfloatvalidator), and it covers "every run hour must
be between 0 and 23", "every weight must be between 0.0 and 1.0", and
"every column name must be one of the known columns". When one element
fails, the error message names the member and the index of the offending
element.

The element type is inferred from the constraints and may be `int`,
`float`, `str`, or `bool`. At least one constraint must be supplied.
`allowed_values` may be a callable evaluated at validation time. A
`lt_comparator` argument lets you supply an ordering other than `<`, which
matters for strings that should be compared case-insensitively or by a
locale-aware rule.

**Combines well with:** [ListSizeValidator](#listsizevalidator) for length,
[ListOrderingValidator](#listorderingvalidator) to normalize after the
values are known to be sound, and
[ListIsOrderedValidator](#listisorderedvalidator) to require sortedness.
For lists whose elements are not scalars, use
[ListForEachValidator](#listforeachvalidator) instead.

````python
from config_as_json import ListValueValidator

hours = ListValueValidator(min_value=0, max_value=23, allowed_values=None)
weights = ListValueValidator(min_value=0.0, max_value=1.0,
                             allowed_values=None)
````

Worked example:
[e06_list_basic_validators.py](../example/src/example/e06_list_basic_validators.py)

Full API:
[`ListValueValidator`](api.md#config_as_json.list_value_validators.ListValueValidator)

### ListIsOrderedValidator

`ListIsOrderedValidator` checks that a list of scalars is sorted, and
optionally that it contains no duplicates, without changing it. Use it when
the order in the configuration file is meaningful to the person editing the
file and a wrong order should be reported rather than silently fixed, or
when duplicates indicate a genuine mistake the user should see.

Every element must be an instance of `element_type`, one of `int`, `float`,
`str`, or `bool`, checked with `isinstance`. `is_ordered` (true by default)
requires non-strict ascending order, and `is_reversed` switches that to
descending. Equal neighbours are therefore allowed unless `unique_values`
is also set. Duplicate detection uses ordinary Python equality even when a
custom `lt_comparator` supplies the ordering, so a comparator that treats
two values as equivalent for sorting does not make them duplicates.

The counterpart that fixes the order for the user is
[ListOrderingValidator](#listorderingvalidator). Both exist because the
right choice is an application decision, not a technical one.

**Combines well with:** [ListValueValidator](#listvaluevalidator) to check
the values before the order, [ListSizeValidator](#listsizevalidator), and
[ProjectedMemberValidator](#projectedmembervalidator) when the thing that
must be ordered is computed from the member rather than stored.

````python
from config_as_json import ListIsOrderedValidator

sorted_unique = ListIsOrderedValidator(element_type=int, is_ordered=True,
                                       unique_values=True)
descending = ListIsOrderedValidator(element_type=float, is_ordered=True,
                                    is_reversed=True)
````

Worked example:
[e07_list_order_vs_normalize.py](../example/src/example/e07_list_order_vs_normalize.py)

Full API:
[`ListIsOrderedValidator`](api.md#config_as_json.list_ordering_validators.ListIsOrderedValidator)

### ListOrderingValidator

`ListOrderingValidator` normalizes a list of scalars by sorting it,
reversing it, removing duplicates, or a combination of those, and returns
the normalized list to be stored in the configuration member. It is the
choice when the order in the file is a convenience for the user rather than
information: the user may list run hours in any order and the application
wants them sorted and deduplicated.

`order` (true by default) sorts with `lt_comparator`, and adding `reverse`
makes the sorted result descending. With `order=False` and `reverse=True`
the original order is simply reversed. `keep_only_unique` removes
duplicates *after* any ordering or reversing, keeping the first occurrence
in the resulting order. As with
[ListIsOrderedValidator](#listisorderedvalidator), duplicate detection uses
ordinary equality even when `lt_comparator` is custom.

Remember that later steps see the normalized list. That is usually what you
want, and it is also why a [ListSizeValidator](#listsizevalidator) placed
after this one measures the deduplicated length.

**Combines well with:** [ListValueValidator](#listvaluevalidator) placed
before it, so bad values are reported against what the user wrote;
[ListSizeValidator](#listsizevalidator) placed after it, to measure what
the application will use; and
[ListKeyOrderingValidator](#listkeyorderingvalidator) when the elements are
not scalars.

````python
from config_as_json import ListOrderingValidator

sort_unique = ListOrderingValidator(element_type=int, order=True,
                                    keep_only_unique=True)
newest_first = ListOrderingValidator(element_type=str, order=True,
                                     reverse=True)
````

Worked example:
[e08_combined_list_validators.py](../example/src/example/e08_combined_list_validators.py)

Full API:
[`ListOrderingValidator`](api.md#config_as_json.list_ordering_validators.ListOrderingValidator)

### ListKeyOrderingValidator

`ListKeyOrderingValidator` does for complex elements what
[ListOrderingValidator](#listorderingvalidator) does for scalars: it sorts
a list, or removes duplicates from it, but through a scalar key projected
from each element. This is the validator for a list of dictionaries that
should come out sorted by `name`, or for a list of records where two
entries with the same `id` are a duplicate the application should collapse.
The returned list holds the original elements, reordered; only the ordering
decision goes through the key.

The arguments are keyword-only. `element_type` is the required runtime type
of each element, typically `dict`. `key` is your callable that maps one
element to its scalar key, and `key_type` is the required type of that key,
one of `int`, `float`, `str`, or `bool`. `order`, `reverse`,
`keep_only_unique`, and `lt_comparator` behave exactly as in
`ListOrderingValidator`, with duplicate detection comparing the projected
keys. A key of the wrong type raises
[`InvalidListKeyType`](api.md#config_as_json.list_ordering_validators.InvalidListKeyType).

Your `key` callable owns the projection, and exceptions it raises are not
caught or wrapped. Validate the element shape in an earlier step, with
[ListOfDictsKeysValidator](#listofdictskeysvalidator) or
[ListForEachValidator](#listforeachvalidator), so the callable can assume
the key is there.

**Combines well with:** [ListOfDictsKeysValidator](#listofdictskeysvalidator)
or [ListForEachValidator](#listforeachvalidator) run first to guarantee the
key exists and has the right type, and
[ListSizeValidator](#listsizevalidator) run after to measure the
deduplicated list.

````python
from config_as_json import ListKeyOrderingValidator

by_name = ListKeyOrderingValidator(
    element_type=dict, key=lambda e: str(e['name']), key_type=str,
    order=True, keep_only_unique=True)
````

Worked example:
[e26_key_ordering_validator.py](../example/src/example/e26_key_ordering_validator.py)

Full API:
[`ListKeyOrderingValidator`](api.md#config_as_json.list_ordering_validators.ListKeyOrderingValidator)

### ListForEachValidator

`ListForEachValidator` is the general composition mechanism for list
members. It iterates the list and applies a sequence of inner validators to
each element in turn, threading the value each validator returns into the
next one. It has no opinion about what an element is, so the elements may
be scalars, lists, dicts, or application objects, and the inner validators
may be any `MemberValidator` including another `ListForEachValidator`.
That is what makes lists of lists, lists of dicts, and deeper nestings
reachable with predefined validators alone.

The optional `element_type` argument adds a type check on each element
before the inner validators run. When it is `None`, the inner validators
are solely responsible for type checking. `element_validators` must be
non-empty. When an inner validator reports an error, the member name it
receives is the outer name with the index appended, for example
`matrix[3]`, so the message points at the element that failed.

List-level checks are deliberately not part of this validator. Put a
[ListSizeValidator](#listsizevalidator) or
[ListIsOrderedValidator](#listisorderedvalidator) in a separate step
before or after it.

**Combines well with:** essentially everything. Common inner validators are
[DictKeysValidator](#dictkeysvalidator) and
[DictForEachValidator](#dictforeachvalidator) for lists of dicts,
[ListSizeValidator](#listsizevalidator) and
[ListValueValidator](#listvaluevalidator) for lists of lists, and
[ValueTypeValidator](#valuetypevalidator),
[StrValidator](#strvalidator) or [StrLenValidator](#strlenvalidator) for
lists of scalars. For the specific case of a list of dicts with a fixed key
policy, [ListOfDictsKeysValidator](#listofdictskeysvalidator) says the same
thing more briefly.

````python
from config_as_json import ListForEachValidator, ListSizeValidator, \
    ListValueValidator

# A matrix: every row is a list of three values between 0.0 and 1.0.
row_size = ListSizeValidator(min_size=3, max_size=3)
row_values = ListValueValidator(min_value=0.0, max_value=1.0,
                                allowed_values=None)
matrix = ListForEachValidator(element_validators=[row_size, row_values],
                              element_type=list)
````

Worked example:
[e09_list_for_each.py](../example/src/example/e09_list_for_each.py)

Full API:
[`ListForEachValidator`](api.md#config_as_json.list_element_validators.ListForEachValidator)

### ListOfDictsKeysValidator

`ListOfDictsKeysValidator` validates the key set of every dictionary in a
list of dictionaries. It is the dedicated shorthand for a very common
configuration shape: a list of records where each record must carry the
same mandatory fields. Using it is equivalent to a
[ListForEachValidator](#listforeachvalidator) with `element_type=dict` and
one inner [DictKeysValidator](#dictkeysvalidator), but it says the intent
in one line.

The three arguments match `DictKeysValidator`. `mandatory_keys` must be
present in every element. `allowed_keys` are permitted but not required.
`allow_extra_dict_keys=True` opens the shape, so each element must carry
the mandatory keys but may also carry application-specific extras. The
validator checks keys only; it never looks at the values.

**Combines well with:** [ListSizeValidator](#listsizevalidator) for the
number of records, [ListKeyOrderingValidator](#listkeyorderingvalidator) to
sort or deduplicate the records afterwards, and
[ListForEachValidator](#listforeachvalidator) with an inner
[DictForEachValidator](#dictforeachvalidator) to validate the values behind
those keys.

````python
from config_as_json import ListOfDictsKeysValidator

columns = ListOfDictsKeysValidator(mandatory_keys=['name', 'width'],
                                   allowed_keys=['align'])
````

Worked example:
[e16_type_and_list_of_dicts_validators.py](../example/src/example/e16_type_and_list_of_dicts_validators.py)

Full API:
[`ListOfDictsKeysValidator`](api.md#config_as_json.list_element_validators.ListOfDictsKeysValidator)

## Dictionary validators

### DictKeysValidator

`DictKeysValidator` enforces a key policy on a dict member: which keys must
be present, which are optional, and whether unknown keys are tolerated. It
never inspects the values and never modifies the dict, which makes it the
natural first step of a dictionary validation plan, with value checks
following in later steps.

`mandatory_keys` lists keys that must be present; a missing one is an
error. `allowed_keys` lists further keys that are permitted. The permitted
set is the union of the two, and listing a key in both is harmless.
`allow_extra_dict_keys=True` accepts unknown keys once the mandatory ones
have been found, which is how you validate a selected subset of an open
dictionary and pass the rest through.

There is an important interaction with the `Config` base class. `Config`
already enforces a key policy for every dict member by matching the parsed
JSON against the member's default value, so for a dict with a fixed closed
key set you often need no validator at all. Reach for `DictKeysValidator`
when you need optional keys, a different policy, or when a
[DictForEachValidator](#dictforeachvalidator) will validate the values and
the base class must not reject a valid key set first. In those cases list
the member name in `_unchecked_dicts` on your configuration class so the
base-class check steps aside.

**Combines well with:** [DictForEachValidator](#dictforeachvalidator) as
the very next step, [DictRule](#dictrule) entries inside it,
[ListForEachValidator](#listforeachvalidator) when the dicts live in a
list, and [AsDictViewValidator](#asdictviewvalidator) as one of its
whole-dict `validators`. When the required keys depend on a `kind` field,
use [DiscriminatedDictValidator](#discriminateddictvalidator) instead.

````python
from config_as_json import DictKeysValidator

strict = DictKeysValidator(mandatory_keys=['host', 'port'],
                           allowed_keys=['timeout'])
open_shape = DictKeysValidator(mandatory_keys=['host'],
                               allow_extra_dict_keys=True)
````

Worked example:
[e10_dict_basic_validators.py](../example/src/example/e10_dict_basic_validators.py)

Full API:
[`DictKeysValidator`](api.md#config_as_json.dict_validators.DictKeysValidator)

### DictForEachValidator

`DictForEachValidator` applies validators to the values stored at selected
keys of a dict. It is how you say "the value at `port` must be an integer
between 1 and 65535, and the value at `host` must be a non-empty string"
with predefined validators. Each rule is a [DictRule](#dictrule) that binds
a set of keys to a sequence of validators, and the validator returns a new
dict carrying any normalized values; the original dict is never modified in
place.

Rules are applied in declaration order, and within a rule the keys are
visited in order and then the validators in order. When two rules cover the
same key, the second rule sees the value the first one left, so
normalization composes. A key named by a rule but absent from the dict is
silently skipped, which keeps this validator strictly orthogonal to
[DictKeysValidator](#dictkeysvalidator): presence is that validator's job.
Keys covered by no rule are copied through unchanged. Inner validators
receive the member name with the key appended, for example
`server[port]`.

A rule's `keys` may also be a callable predicate rather than a fixed
sequence. The predicate is offered each key present in the dict and selects
the ones it returns truthy for, which is how you validate a dict whose keys
are not known when the code is written. [accept_all_keys](#accept_all_keys)
is the ready-made predicate that selects every key.

**Combines well with:** [DictKeysValidator](#dictkeysvalidator) run first to
establish which keys exist, every scalar validator as the contents of a
`DictRule`, [ListForEachValidator](#listforeachvalidator) to reach dicts
inside a list, and [AsDictViewValidator](#asdictviewvalidator) which builds
one of these internally from its `rules`.

````python
from config_as_json import DictForEachValidator, DictRule, \
    IntFloatValidator, StrLenValidator

port_rule = DictRule(keys=['port'],
                     validators=[IntFloatValidator(min_value=1,
                                                   max_value=65535,
                                                   allowed_values=None)])
host_rule = DictRule(keys=['host'],
                     validators=[StrLenValidator(min_length=1,
                                                 max_length=253)])
server = DictForEachValidator(rules=[port_rule, host_rule])
````

Worked examples:
[e11_dict_for_each.py](../example/src/example/e11_dict_for_each.py),
[e20_dynamic_dict_rules.py](../example/src/example/e20_dynamic_dict_rules.py)

Full API:
[`DictForEachValidator`](api.md#config_as_json.dict_validators.DictForEachValidator)

### DictKeyValueTypesValidator

`DictKeyValueTypesValidator` is the compact validator for a dict whose keys
all have one type and whose values all have one type: a `dict[str, int]` of
thresholds, a `dict[str, list[float]]` of measurement series, a
`dict[str, str]` of labels. Every key is checked with
`isinstance(key, key_type)` and every value with
`isinstance(value, value_type)`. An empty dict is valid.

The optional `value_validator` is applied to each value after the type
check, through an internal
[DictForEachValidator](#dictforeachvalidator). It exists for composite
values that need to be traversed, such as validating the `list[float]`
inside a `dict[str, list[float]]`. Simple scalar values need no such hook.

This validator cannot describe a non-uniform dict where different keys have
different value policies. For that shape use
[DictKeysValidator](#dictkeysvalidator) together with
[DictForEachValidator](#dictforeachvalidator) and one or more
[DictRule](#dictrule) entries, or
[DiscriminatedDictValidator](#discriminateddictvalidator) when a field
selects the shape.

**Combines well with:** [ListValueTypeValidator](#listvaluetypevalidator)
or [ListValueValidator](#listvaluevalidator) as the `value_validator` for
list-valued dicts, and
[ListRelationValidator](#listrelationvalidator) when the dict's keys must
agree with another member.

````python
from config_as_json import DictKeyValueTypesValidator, ListValueValidator

thresholds = DictKeyValueTypesValidator(key_type=str, value_type=int)
series = DictKeyValueTypesValidator(
    key_type=str, value_type=list,
    value_validator=ListValueValidator(min_value=0.0, max_value=1.0,
                                       allowed_values=None))
````

Worked example:
[e22_dict_key_value_types.py](../example/src/example/e22_dict_key_value_types.py)

Full API:
[`DictKeyValueTypesValidator`](api.md#config_as_json.dict_validators.DictKeyValueTypesValidator)

### DiscriminatedDictValidator

`DiscriminatedDictValidator` validates a dict whose required keys depend on
the value of one field. This is the "tagged union" shape that shows up
whenever a configuration describes one of several kinds of thing: an output
that is a `file` and needs a `path`, or a `database` and needs a `dsn` and
a `table`. Writing that with a single key list means either accepting keys
that make no sense for the chosen kind or rejecting valid configurations.

`discriminator_key` names the field that chooses the shape, such as
`'kind'`. It is always mandatory and always allowed, independently of the
variant. `variants` maps each discriminator value to a
[DictVariant](#dictvariant) that carries that shape's mandatory keys,
optional keys, per-key [DictRule](#dictrule) entries, and its own
`allow_extra_dict_keys` setting. The optional `discriminator_validator`
runs on the discriminator value *before* the variant is looked up, which
lets a [StrValidator](#strvalidator) normalize `FILE` or `fil` to `file`
so the variant lookup sees a canonical value.

Validation never mutates the input dict; a new dict is returned carrying
the normalized discriminator and any per-key normalization from the
selected variant's rules.

**Combines well with:** [StrValidator](#strvalidator) as the
`discriminator_validator`, [DictRule](#dictrule) inside each
[DictVariant](#dictvariant), and
[ListForEachValidator](#listforeachvalidator) when the configuration holds
a list of such tagged dicts.

````python
from config_as_json import DictRule, DictVariant, \
    DiscriminatedDictValidator, StrLenValidator, StrValidator

path_rule = DictRule(keys=['path'],
                     validators=[StrLenValidator(min_length=1,
                                                 max_length=None)])
variants = {
    'file': DictVariant(mandatory_keys=['path'], rules=[path_rule]),
    'database': DictVariant(mandatory_keys=['dsn', 'table'])}
output = DiscriminatedDictValidator(
    discriminator_key='kind', variants=variants,
    discriminator_validator=StrValidator(allowed_values=['file', 'database'],
                                         ignore_case=True, normalize=True))
````

Worked example:
[e14_discriminated_dict_validator.py](../example/src/example/e14_discriminated_dict_validator.py)

Full API:
[`DiscriminatedDictValidator`](api.md#config_as_json.discriminated_dict_validators.DiscriminatedDictValidator)

### AsDictViewValidator

`AsDictViewValidator` lets one member hold either a real `dict` or an
instance of one application-defined class, and validates both through the
same dictionary rules. It solves the problem that appears when a
configuration value is parsed into an application object: you still want a
single, readable statement of the validation policy, and you do not want to
write it twice.

`non_dict_type` is the accepted application class, which may not be `dict`
or a subclass of it. `to_dict` is the callable that produces the dictionary
view of such an object;
[public_attrs_to_dict](#public_attrs_to_dict) is the ready-made choice when
the view should be the object's public instance attributes. `validators`
is an optional sequence applied to the whole dictionary view first, and
`rules` are [DictRule](#dictrule) entries applied afterwards through an
internal [DictForEachValidator](#dictforeachvalidator).

The two representations differ in one important way. When the member is a
`dict`, normalized values are returned and therefore stored back into the
configuration. When the member is an instance of `non_dict_type`, the
projected view is used only inside the validation chain and the original
object is what stays in the configuration. Only `dict` and the one named
class are accepted; other mapping types are deliberately not, which keeps
the storing rule unambiguous.

**Combines well with:** [DictKeysValidator](#dictkeysvalidator) as one of
its whole-dict `validators`, [DictRule](#dictrule) for the per-key work,
and [public_attrs_to_dict](#public_attrs_to_dict) as `to_dict`.

````python
from config_as_json import AsDictViewValidator, DictKeysValidator, \
    DictRule, IntFloatValidator, public_attrs_to_dict

# Endpoint is the application class this member may also hold.
port_rule = DictRule(keys=['port'],
                     validators=[IntFloatValidator(min_value=1,
                                                   max_value=65535,
                                                   allowed_values=None)])
endpoint = AsDictViewValidator(
    non_dict_type=Endpoint, rules=[port_rule],
    to_dict=public_attrs_to_dict,
    validators=[DictKeysValidator(mandatory_keys=['host', 'port'])])
````

Worked example:
[e21_as_dict_view_validator.py](../example/src/example/e21_as_dict_view_validator.py)

Full API:
[`AsDictViewValidator`](api.md#config_as_json.as_dict_view_validator.AsDictViewValidator)

## Composition and adapter validators

### OptionalMemberValidator

`OptionalMemberValidator` wraps another validator, or a list of validators,
and applies it only while the member value is not `None`. It is the answer
to "this setting is optional, but when the user does set it, these rules
apply". Without it, every optional member would need a validator that knows
about `None`, and most predefined validators deliberately do not.

A `None` value is returned unchanged and no inner validator runs. Any other
value is passed to the wrapped validator, and whatever that validator
returns, including a normalized value, is returned. Passing a list of
validators is a convenience: the list is wrapped in a
[MemberValidatorSequence](#membervalidatorsequence) for you.

This is about *validating* an optional value. Whether an unset member is
written to the JSON file at all is a separate concern, handled by the
`_omit_none_from_json()` hook on your configuration class.

**Combines well with:** any member validator, most usefully
[StrValidator](#strvalidator),
[IntFloatValidator](#intfloatvalidator),
[StrLenValidator](#strlenvalidator), and
[MemberValidatorSequence](#membervalidatorsequence) for several rules on
one optional member.

````python
from config_as_json import IntFloatValidator, OptionalMemberValidator, \
    ValueTypeValidator

# An optional retry count: None, or an int between 0 and 10.
retries = OptionalMemberValidator(
    validator=[ValueTypeValidator(value_type=int, not_allowed_type=bool),
               IntFloatValidator(min_value=0, max_value=10,
                                 allowed_values=None)])
````

Full API:
[`OptionalMemberValidator`](api.md#config_as_json.optional_validator.OptionalMemberValidator)

### MemberValidatorSequence

`MemberValidatorSequence` applies several validators to one member value,
in order, passing each validator's returned value to the next. It exists
because a `ValidationPlan` naturally reads the other way round: one step
applies one validator to several members. When you want the opposite
grouping, several validators finished on one member before moving on, this
is the validator that expresses it.

There are two reasons to prefer it over several separate plan steps. The
first is that some validators only accept one validator as an argument, and
a sequence is how you give them several. The second is readability: a
member with three rules reads better as one named sequence than as three
steps scattered through the plan.

`validators` must be a non-empty sequence of `MemberValidator` objects,
checked in the constructor. There is nothing else to configure.

**Combines well with:** everything, but especially
[ValueTypeValidator](#valuetypevalidator) followed by a value check,
[StrCaseChangeValidator](#strcasechangevalidator) followed by
[StrValidator](#strvalidator), and
[ValueAsTypeValidator](#valueastypevalidator) followed by
[IntFloatValidator](#intfloatvalidator). It is also what you pass as the
single inner validator of
[OptionalMemberValidator](#optionalmembervalidator) or
[DictKeyValueTypesValidator](#dictkeyvaluetypesvalidator).

````python
from config_as_json import IntFloatValidator, MemberValidatorSequence, \
    ValueAsTypeValidator

# Accept '8080' or 8080.0, store an int, then check the range.
port = MemberValidatorSequence(
    validators=[ValueAsTypeValidator(value_type=int,
                                     direct_types=[str, float]),
                IntFloatValidator(min_value=1, max_value=65535,
                                  allowed_values=None)])
````

Worked example:
[e25_value_as_type_validator.py](../example/src/example/e25_value_as_type_validator.py)

Full API:
[`MemberValidatorSequence`](api.md#config_as_json.validator.MemberValidatorSequence)

### ProjectedMemberValidator

`ProjectedMemberValidator` validates something *computed from* a member
rather than the member itself, while leaving the stored value alone. The
motivating cases are members whose natural validation view is not what is
stored: a list of dicts whose `name` fields must be unique, a dict whose
keys must form a sorted set, an application object whose derived total must
stay within a budget. You compute the view, and then reuse ordinary
predefined validators on it.

`projector` is a callable receiving the config object, the member name, the
member value, and the diagnostic stream, and returning the value to
validate. `validators` are applied to that projected value in order, each
seeing what the previous one returned. The optional `source_validator` runs
on the original member value *before* projection, which is how you make
sure the projector can rely on the shape it is given.

Nothing the chain returns is stored. The projected value is discarded on
success and the original member value is returned. Note that no copying is
done, so a projector or validator that mutates a shared mutable object can
still affect the stored member; return detached values when that matters.

**Combines well with:**
[ListIsOrderedValidator](#listisorderedvalidator) with
`unique_values=True` applied to a projected list of keys,
[ListSizeValidator](#listsizevalidator),
[DictKeysValidator](#dictkeysvalidator), and any other member validator
that fits the projected shape. Its whole-configuration counterpart is
[ProjectedWholeConfigValidator](#projectedwholeconfigvalidator).

````python
from typing import TextIO
from config_as_json import Config, ListIsOrderedValidator, \
    ProjectedMemberValidator


def _names(config: Config, member_name: str, member_value: object,
           stderr_file: TextIO) -> object:
    """Project the name field of every element to a list of names."""
    _ = config, member_name, stderr_file
    assert isinstance(member_value, list)
    return [element['name'] for element in member_value]


unique_names = ProjectedMemberValidator(
    projector=_names,
    validators=[ListIsOrderedValidator(element_type=str, is_ordered=False,
                                       unique_values=True)])
````

Worked example:
[e15_projected_member_validator.py](../example/src/example/e15_projected_member_validator.py)

Full API:
[`ProjectedMemberValidator`](api.md#config_as_json.projected_validators.ProjectedMemberValidator)

### CallingMemberValidator

`CallingMemberValidator` validates one member by calling a named method of
the configuration object. It exists for the case where the validation logic
already exists and should not be duplicated: your configuration class
derives both from `Config` and from a third-party class that brings its own
checking, or your own class has a method that knows the rule. The validator
turns that method into an ordinary plan step.

`method_name` is the method to call, and it must accept all its arguments
as keyword arguments. `arg_name_value` is the parameter name that receives
the member value; `arg_name_member_name` optionally names a parameter that
receives the member's name, which lets a shared method produce precise
messages. `other_args` supplies any further fixed keyword arguments. The
constructor rejects an `other_args` key that would collide with a generated
one.

`normalizing` decides how the return value is read. With `normalizing`
false, the method is a predicate: returning `None` or `True` means valid,
returning `False` means invalid, and the original member value is kept.
With `normalizing` true, whatever the method returns becomes the new member
value. In either mode the method may also raise, and the exception
propagates.

**Combines well with:**
[MemberValidatorSequence](#membervalidatorsequence) to run predefined
checks around the borrowed one, and
[CallingWholeConfigValidator](#callingwholeconfigvalidator) for rules that
span members. Where the reused logic is a *conversion* rather than a
method, [ValueAsTypeValidator](#valueastypevalidator) is usually simpler.

````python
from config_as_json import CallingMemberValidator

# Calls config.check_column(value=..., name=...) for each named member.
column = CallingMemberValidator(method_name='check_column',
                                arg_name_value='value',
                                arg_name_member_name='name')
````

Worked example:
[e19_config_method_validators.py](../example/src/example/e19_config_method_validators.py)

Full API:
[`CallingMemberValidator`](api.md#config_as_json.validator.CallingMemberValidator)

## Whole-configuration validators

### ListRelationValidator

`ListRelationValidator` requires a relation to hold between two list-like
values in the configuration. This is the validator for consistency rules
that no single member can express: the columns selected for output must all
exist among the columns defined, the input and output field names must not
overlap, the enabled features and the licensed features must match exactly.

`kind` is a [ListRelationKind](#listrelationkind) and selects the relation:
`EQUAL` for same elements in same order, `MULTISET_EQUAL` for same elements
with same counts in any order, `SET_EQUAL` ignoring order and duplicates,
`SUBSET` for A contained in B, and `DISJOINT` for no shared element.

Each side is either a named `Config` member or a projected value. Without a
projector, `member_a_name` names a member holding a finite sequence, which
may not be a `str`, `bytes`, or `bytearray`. With `a_projector` supplied,
the name becomes a pseudo-member name used only in error messages, and the
projector computes the sequence, which is how you compare the *keys* of a
dict against a list. `eq_comparator` and `lt_comparator` let you supply
comparison and ordering other than `==` and `<`, for example to compare
strings case-insensitively.

This is a `WholeConfigValidator`, so it goes into the plan as a
`WholeConfigValidationStep`.

**Combines well with:**
[DictKeyValueTypesValidator](#dictkeyvaluetypesvalidator) and
[ListValueTypeValidator](#listvaluetypevalidator) run earlier so the two
sides are known to have the right shape, and
[ProjectedWholeConfigValidator](#projectedwholeconfigvalidator) for
cross-member rules that are not a list relation.

````python
from typing import TextIO
from config_as_json import Config, ListRelationKind, ListRelationValidator


def _defined_keys(config: Config, stderr_file: TextIO) -> object:
    """Project the keys of the defined-columns dict to a list."""
    _ = stderr_file
    return list(config.defined_columns.keys())


selected_exist = ListRelationValidator(
    kind=ListRelationKind.SUBSET, member_a_name='selected_columns',
    member_b_name='defined_columns_keys', b_projector=_defined_keys)
````

Worked example:
[e24_list_relation_validator.py](../example/src/example/e24_list_relation_validator.py)

Full API:
[`ListRelationValidator`](api.md#config_as_json.list_relation_validator.ListRelationValidator)

### ProjectedWholeConfigValidator

`ProjectedWholeConfigValidator` computes one value from the whole
configuration and validates it with ordinary member validators. It is the
general mechanism for rules that involve several members at once and are
not a list relation: a set of weights across members that must sum to 1.0,
a derived list that must be sorted, a computed capacity that must stay
within a bound.

`projector` receives the config object and the diagnostic stream and
returns the value to validate. `pseudo_member_name` is the name that value
is reported under, so choose something the user of the configuration file
will understand, such as `'total weight'`. `validators` are applied to the
projected value in order, each seeing what the previous returned.

As with [ProjectedMemberValidator](#projectedmembervalidator), nothing is
stored: the projected value is discarded on success and the configuration
is unchanged. No copying is done, so avoid in-place mutation of shared
objects inside the projector or the inner validators.

This is a `WholeConfigValidator`, so it goes into the plan as a
`WholeConfigValidationStep`.

**Combines well with:** [IntFloatValidator](#intfloatvalidator) for a
computed total, [ListIsOrderedValidator](#listisorderedvalidator) for a
computed sequence, [ListValueValidator](#listvaluevalidator), and
[ListRelationValidator](#listrelationvalidator) when the rule really is a
relation between two lists.

````python
from typing import TextIO
from config_as_json import Config, IntFloatValidator, \
    ProjectedWholeConfigValidator


def _total_weight(config: Config, stderr_file: TextIO) -> object:
    """Project the sum of all configured weights."""
    _ = stderr_file
    return sum(config.weights.values())


total_ok = ProjectedWholeConfigValidator(
    projector=_total_weight, pseudo_member_name='total weight',
    validators=[IntFloatValidator(min_value=0.0, max_value=1.0,
                                  allowed_values=None)])
````

Worked example:
[e23_projected_whole_config_validator.py](../example/src/example/e23_projected_whole_config_validator.py)

Full API:
[`ProjectedWholeConfigValidator`](api.md#config_as_json.projected_validators.ProjectedWholeConfigValidator)

### CallingWholeConfigValidator

`CallingWholeConfigValidator` validates the whole configuration by calling
a named method of the configuration object. Like
[CallingMemberValidator](#callingmembervalidator), it exists to reuse
validation logic that already lives somewhere else, most usefully when the
configuration class also derives from a third-party class that validates
itself.

`method_name` names the method, which must accept all its arguments as
keyword arguments, and `other_args` supplies any fixed keyword arguments.
The method reports failure by raising, or by returning `False`. Returning
`None` or `True` means the configuration is valid. There is no normalizing
mode: a whole-configuration method that needs to change values should
mutate the configuration object directly.

This is a `WholeConfigValidator`, so it goes into the plan as a
`WholeConfigValidationStep`.

**Combines well with:**
[CallingMemberValidator](#callingmembervalidator) for the per-member half
of a borrowed validation policy, and
[ProjectedWholeConfigValidator](#projectedwholeconfigvalidator) when the
rule is better expressed as a computed value than as a method.

````python
from config_as_json import CallingWholeConfigValidator

# Calls config.check_consistency(strict=True).
consistent = CallingWholeConfigValidator(method_name='check_consistency',
                                         other_args={'strict': True})
````

Worked example:
[e19_config_method_validators.py](../example/src/example/e19_config_method_validators.py)

Full API:
[`CallingWholeConfigValidator`](api.md#config_as_json.validator.CallingWholeConfigValidator)

## Domain-specific validators

### CharEncodingValidator

`CharEncodingValidator` checks that a string member names a text encoding
that Python actually recognizes. Applications that let the user choose the
encoding of an input or output file need this, because a typo such as
`utf8-` or `latin` produces a `LookupError` deep inside the file handling
otherwise, long after the configuration was read. This validator turns that
into a clear message naming the member and the bad encoding name at
configuration time.

There is nothing to configure; construct it and put it in a plan step. The
member value is returned unchanged, so the encoding name the user wrote is
what gets stored. A value that is not a string is rejected with the same
kind of message.

The same check is available outside a validation plan as
[valid_char_encoding](#valid_char_encoding), which returns a bool, and
[check_char_encoding](#check_char_encoding), which exits with a message.

**Combines well with:** [CsvDialectValidator](#csvdialectvalidator), since
a CSV file usually needs both an encoding and a dialect, and
[OptionalMemberValidator](#optionalmembervalidator) when the encoding may
be left unset for the application default.

````python
from config_as_json import CharEncodingValidator

encoding = CharEncodingValidator()
````

Worked example:
[e17_csv_dialect_and_encoding.py](../example/src/example/e17_csv_dialect_and_encoding.py)

Full API:
[`CharEncodingValidator`](api.md#config_as_json.char_encoding.CharEncodingValidator)

### CsvDialectValidator

`CsvDialectValidator` validates a dict member that describes a CSV dialect
and checks that the described dialect can actually be built. Letting users
configure the delimiter, the quoting rule, and the line terminator of a CSV
file is common, and the failure mode without this validator is an obscure
error from the `csv` module when the first row is written. This validator
reports the problem while the configuration is being read.

The member must be a `dict[str, Optional[str]]` whose keys are drawn from
`name`, `delimiter`, `quoting`, `quotechar`, `lineterminator`, and
`escapechar`. `name` is mandatory and names a standard-library dialect
template such as `'csv.excel'`. The others are optional overrides; missing
ones are normalized to `None` in the returned value, so the application
always sees a complete dict. That shape is described by the
[CsvDialectConfig](#csvdialectconfig) `TypedDict`. After the shape is
checked, the validator calls
[get_csv_dialect](#get_csv_dialect) and reports any failure as
`InvalidConfiguration`.

Use [get_csv_dialect](#get_csv_dialect) in your application code to turn
the validated dict into the actual `csv.Dialect`.

**Combines well with:** [CharEncodingValidator](#charencodingvalidator) on
the companion encoding member, and
[OptionalMemberValidator](#optionalmembervalidator) when CSV output is
itself optional.

````python
from config_as_json import CsvDialectValidator, get_csv_dialect

dialect_validator = CsvDialectValidator()
# Later, in application code, on a validated csv_dialect member:
dialect = get_csv_dialect(name=config.csv_dialect['name'],
                          delimiter=config.csv_dialect['delimiter'],
                          quoting=config.csv_dialect['quoting'],
                          quotechar=config.csv_dialect['quotechar'],
                          lineterminator=config.csv_dialect['lineterminator'],
                          escapechar=config.csv_dialect['escapechar'])
````

Worked example:
[e17_csv_dialect_and_encoding.py](../example/src/example/e17_csv_dialect_and_encoding.py)

Full API:
[`CsvDialectValidator`](api.md#config_as_json.csv_dialect.CsvDialectValidator)

### RadixValidator

`RadixValidator` validates a string member holding a number written in a
chosen base, and normalizes it to the notation the application declared. It
is the base class behind
[HexadecimalStringValidator](#hexadecimalstringvalidator) and
[OctalStringValidator](#octalstringvalidator), and you derive from it when
you need a notation this package does not predefine.

The member value must be a string of digits for the notation, optionally
preceded by any of the prefixes the notation recognizes and optionally
surrounded by whitespace. A non-negative integer is also accepted, which is
what a configuration file written before the value became text contains.
The returned value is rewritten with the configured `prefix` and padded
with leading zeros to `digits`, so a hand-edited file is normalized rather
than rejected. `digits=0`, the default, writes as few digits as the value
needs.

A derived class declares its notation by setting the class member `_SPEC`
to a [RadixSpec](#radixspec) and taking that notation's prefix enum as its
type argument. Note that this validator works on any plain string member of
any configuration class; you do not need to use it together with
`RadixNumber`.

**Combines well with:** [StrLenValidator](#strlenvalidator) when the number
of digits must be exact and the validator's own padding is not enough, and
[OptionalMemberValidator](#optionalmembervalidator) for a member that may
be unset.

Full API:
[`RadixValidator`](api.md#config_as_json.radix_number.RadixValidator)

### HexadecimalStringValidator

`HexadecimalStringValidator` validates and normalizes a member holding a
number written as hexadecimal text. This is the validator for values that
users think of in hexadecimal and want to see that way in the configuration
file: a Tk colour such as `#204060`, a feature bit mask such as
`0x0000001f`, a device address. Storing them as decimal integers would make
the file harder to read and edit.

The value may be written with any of the prefixes in
`HexadecimalNumber.Prefix` — `NONE` for bare digits, `ZERO_X` for `0x`, and
`HASH` for `#` — in either letter case and with surrounding whitespace, and
a non-negative integer is accepted as well. The `prefix` and `digits`
constructor arguments say how the value is written back, so a user who
types `#2a` into a member declared with `Prefix.HASH` and six digits gets
`#00002a` stored and written to the file.

Where the value should behave as an integer in application code rather than
as a string, the companion `HexadecimalNumber` nested configuration class
keeps the integer and the written form together. This validator is the
right choice when the member is and should stay a plain string.

**Combines well with:**
[OptionalMemberValidator](#optionalmembervalidator) for an unset colour,
and [DictRule](#dictrule) inside
[DictForEachValidator](#dictforeachvalidator) for a dict of colours.

````python
from config_as_json import HexadecimalNumber, HexadecimalStringValidator

colour = HexadecimalStringValidator(prefix=HexadecimalNumber.Prefix.HASH,
                                    digits=6)
mask = HexadecimalStringValidator(prefix=HexadecimalNumber.Prefix.ZERO_X,
                                  digits=8)
````

Worked example:
[e41_hex_and_octal.py](../example/src/example/e41_hex_and_octal.py)

Full API:
[`HexadecimalStringValidator`](api.md#config_as_json.hexadecimal_number.HexadecimalStringValidator)

### OctalStringValidator

`OctalStringValidator` validates and normalizes a member holding a number
written as octal text. The motivating case is a POSIX file mode: users
expect to see and type `0644`, not `420`, and a configuration file that
shows the decimal value is a configuration file people get wrong.

The value may be written with any of the prefixes in `OctalNumber.Prefix` —
`NONE` for bare digits, `ZERO_O` for Python's `0o`, and `ZERO` for the
traditional single leading zero — and with surrounding whitespace, and a
non-negative integer is accepted as well. `prefix` and `digits` say how the
value is written back. Note that with `Prefix.ZERO` the leading zero is
kept when a value is read, because it cannot be told apart from padding
zeros, and the value reads as the same number either way.

Where the value should behave as an integer in application code, the
companion `OctalNumber` nested configuration class keeps the integer and
the written form together. This validator is the right choice when the
member is and should stay a plain string.

**Combines well with:**
[OptionalMemberValidator](#optionalmembervalidator), and
[ListForEachValidator](#listforeachvalidator) for a list of file modes.

````python
from config_as_json import OctalNumber, OctalStringValidator

file_mode = OctalStringValidator(prefix=OctalNumber.Prefix.ZERO, digits=3)
umask = OctalStringValidator(prefix=OctalNumber.Prefix.ZERO_O, digits=3)
````

Worked example:
[e41_hex_and_octal.py](../example/src/example/e41_hex_and_octal.py)

Full API:
[`OctalStringValidator`](api.md#config_as_json.octal_number.OctalStringValidator)

## Supporting types

These types are not validators themselves. They are the arguments and
enums that the validators above take, and they are listed here so that a
name you meet in a signature can be looked up.

### StrCaseSpec

The case required at a position by
[StrCaseValidator](#strcasevalidator), or applied at a position by
[StrCaseChangeValidator](#strcasechangevalidator). The members are `LOWER`,
`UPPER`, and `ORIGINAL`. Use `ORIGINAL` for the positions that should be
left alone, which is how you constrain only the special positions.

Full API:
[`StrCaseSpec`](api.md#config_as_json.str_validators.StrCaseSpec)

### StrPositionSpec

The positions that a case rule treats as special. The members are
`FIRST_IN_STRING`, `FIRST_IN_WORD`, `FIRST_IN_SENTENCE`, and
`EVERY_CHARACTER`. Every position that does not match is governed by the
`other_position_case` argument instead.

Full API:
[`StrPositionSpec`](api.md#config_as_json.str_validators.StrPositionSpec)

### DictRule

`DictRule` binds a sequence of validators to a set of dict keys. It is the
unit of work for [DictForEachValidator](#dictforeachvalidator), for the
`rules` of a [DictVariant](#dictvariant), and for the `rules` of
[AsDictViewValidator](#asdictviewvalidator).

`keys` is either a sequence of hashable key values or a callable predicate
that receives one key and returns a truthy value when the rule applies. The
predicate form is what makes dicts with keys unknown at coding time
validatable; [accept_all_keys](#accept_all_keys) is the predicate that
selects every key. `validators` are applied in order to the value at each
selected key, threading normalized values forward.

Full API:
[`DictRule`](api.md#config_as_json.dict_validators.DictRule)

### DictVariant

`DictVariant` describes one allowed shape of a dictionary validated by
[DiscriminatedDictValidator](#discriminateddictvalidator). It carries
`mandatory_keys` and `allowed_keys` for that variant, the per-key
[DictRule](#dictrule) entries to apply once the key set is accepted, and
its own `allow_extra_dict_keys` setting. The discriminator key itself is
always mandatory and always allowed, so it need not be listed.

Full API:
[`DictVariant`](api.md#config_as_json.discriminated_dict_validators.DictVariant)

### ListRelationKind

The relation required by [ListRelationValidator](#listrelationvalidator).
`EQUAL` requires the same elements in the same order. `MULTISET_EQUAL`
requires the same elements with the same counts, in any order.
`SET_EQUAL` ignores both order and duplicates. `SUBSET` requires every
element of A to appear in B. `DISJOINT` requires no shared element.

Full API:
[`ListRelationKind`](api.md#config_as_json.list_relation_validator.ListRelationKind)

### RadixSpec

`RadixSpec` describes one number notation for a
[RadixValidator](#radixvalidator) subclass: the base, the accepted digit
characters, the Python format letter, the public member name, and the
adjective and article used in diagnostics. You need it only when you add a
notation beyond the predefined hexadecimal and octal ones.

Full API:
[`RadixSpec`](api.md#config_as_json.radix_number.RadixSpec)

### MemberProjector

The callable type accepted as the `projector` of
[ProjectedMemberValidator](#projectedmembervalidator). It receives the
config object, the member name, the member value, and the diagnostic
stream, and returns the value to validate.

Full API:
[`config_as_json.projected_validators`](api.md#config_as_json.projected_validators)

### WholeConfigProjector

The callable type accepted as the `projector` of
[ProjectedWholeConfigValidator](#projectedwholeconfigvalidator) and as the
`a_projector` and `b_projector` of
[ListRelationValidator](#listrelationvalidator). It receives the config
object and the diagnostic stream, and returns the value to validate.

Full API:
[`config_as_json.projected_validators`](api.md#config_as_json.projected_validators)

### CsvDialectConfig

The `TypedDict` describing the shape of a CSV dialect configuration member:
a mandatory `name` and the optional `delimiter`, `quoting`, `quotechar`,
`lineterminator`, and `escapechar`. Declare your member with this type so
that the code and
[CsvDialectValidator](#csvdialectvalidator) agree about the shape.

Full API:
[`CsvDialectConfig`](api.md#config_as_json.csv_dialect.CsvDialectConfig)

### accept_all_keys

The ready-made key predicate for [DictRule](#dictrule). It returns `True`
for every key, so a rule using it applies its validators to every key
present in the dict. Use it when the keys are chosen by the user and only
the values have a policy.

Full API:
[`accept_all_keys`](api.md#config_as_json.dict_validators.accept_all_keys)

### public_attrs_to_dict

The ready-made `to_dict` callable for
[AsDictViewValidator](#asdictviewvalidator). It projects every non-callable
public instance attribute of an object into a shallow dictionary, which is
the right view whenever an application class stores its configuration data
in ordinary public attributes.

Full API:
[`public_attrs_to_dict`](api.md#config_as_json.as_dict_view_validator.public_attrs_to_dict)

## Validation helper functions

These functions are not validators and do not go into a `ValidationPlan`.
They solve validation-adjacent problems in ordinary application code, and
they are listed here because they are frequently what a programmer looking
for a validator actually needs.

### valid_char_encoding

Returns `True` when a string names a text encoding Python recognizes, and
`False` otherwise. Use it when your code needs to branch on the answer.
Inside a validation plan, use
[CharEncodingValidator](#charencodingvalidator) instead.

Full API:
[`valid_char_encoding`](api.md#config_as_json.char_encoding.valid_char_encoding)

### check_char_encoding

Writes a diagnostic and raises `SystemExit` when a string does not name a
recognized text encoding. This is the fail-fast form for command-line
arguments and other input that is not part of the configuration object.
Inside a validation plan, use
[CharEncodingValidator](#charencodingvalidator) instead, because a plan
should raise `InvalidConfiguration` rather than terminate the program.

Full API:
[`check_char_encoding`](api.md#config_as_json.char_encoding.check_char_encoding)

### file_must_exist

Stops the job with a helpful message naming the missing file, and
optionally describing what the file should have contained. By default it
raises `SystemExit`; with `exit_if_missing=False` it raises
`FileNotFoundError` instead, which is the form to use from library code.
Use it for input files whose existence the configuration implies.

Full API:
[`file_must_exist`](api.md#config_as_json.file_must_exist.file_must_exist)

### fix_file_extension

Returns a filename normalized to the extension the application expects,
optionally stripping another extension first. With `for_reading=True` a
filename that already exists exactly as written is returned unchanged. Use
it to be forgiving about whether the user typed the extension.

Full API:
[`fix_file_extension`](api.md#config_as_json.file_extension.fix_file_extension)

### string_best_match

Matches a string against a sequence of allowed values, accepting common
case variants and then a unique case-insensitive prefix, and raises
`InvalidConfigurationValue` when nothing matches uniquely. This is the
matching logic behind [StrValidator](#strvalidator) with
`best_match=True`, exposed for use in your own validators and in
command-line handling.

Full API:
[`string_best_match`](api.md#config_as_json.validator.string_best_match)

### string_to_enum_best_match

Returns the member of an enum class whose name best matches a string,
accepting case variants and then a unique case-insensitive prefix, and
raising `KeyError` when nothing matches uniquely. It is the usual
implementation of a `ParseConverter` for an enum member, and it is also
useful when normalizing old configuration files.

Full API:
[`string_to_enum_best_match`](api.md#config_as_json.str_to_enum.string_to_enum_best_match)

### get_csv_dialect

Builds a `csv.Dialect` from the serialized fields of a validated CSV
dialect member. Call it in application code after
[CsvDialectValidator](#csvdialectvalidator) has accepted the member, and
give it the six fields of [CsvDialectConfig](#csvdialectconfig).

Full API:
[`get_csv_dialect`](api.md#config_as_json.csv_dialect.get_csv_dialect)

## Combination recipes

Each recipe below is a problem that no single predefined validator solves,
and the combination that does solve it. They are also worth reading as
examples of the two composition tools that come up again and again:
[MemberValidatorSequence](#membervalidatorsequence) for several rules on
one member, and
[ListForEachValidator](#listforeachvalidator) or
[DictForEachValidator](#dictforeachvalidator) for descending into a
container.

### An integer between 0 and 15 that is not a bool

`IntFloatValidator` checks the range with `isinstance`, and in Python
`bool` is a subclass of `int`. A configuration file holding `true` would
therefore pass an `int` range check as the value 1. When JSON `true` must
not be silently accepted as a number, put a
[ValueTypeValidator](#valuetypevalidator) that forbids `bool` in front of
the range check.

````python
from config_as_json import IntFloatValidator, MemberValidatorSequence, \
    ValueTypeValidator

nibble = MemberValidatorSequence(
    validators=[ValueTypeValidator(value_type=int, not_allowed_type=bool),
                IntFloatValidator(min_value=0, max_value=15,
                                  allowed_values=None)])
````

`ValueTypeValidator(value_type=int, strict=True)` also rejects `True`,
because strict mode compares `type(value)` exactly. Prefer
`not_allowed_type=bool` when you want to name the intent, and `strict=True`
when no `int` subclass at all should be accepted.

The same pattern applies to every list element by wrapping it in a
[ListForEachValidator](#listforeachvalidator), and to one dict key by
putting the sequence in a [DictRule](#dictrule).

### An optional value that has rules when it is set

Most predefined validators reject `None` rather than ignoring it, which is
correct for a mandatory member and wrong for an optional one. Wrap the
rules in [OptionalMemberValidator](#optionalmembervalidator); a list of
validators is accepted and wrapped in a sequence for you.

````python
from config_as_json import OptionalMemberValidator, StrLenValidator, \
    StrValidator

# None, or one of the known palettes, spelled canonically.
palette = OptionalMemberValidator(
    validator=[StrLenValidator(min_length=1, max_length=32),
               StrValidator(allowed_values=['dark', 'light', 'high-contrast'],
                            ignore_case=True, normalize=True)])
````

### Accept forgiving input and store a canonical value

Users edit configuration files by hand, so `"8080"`, `8080.0`, and `8080`
all turn up in the same member. Convert first with
[ValueAsTypeValidator](#valueastypevalidator), then apply the real rule to
the converted value. The order matters: the range check must run on the
`int`, not on the string.

````python
from config_as_json import IntFloatValidator, MemberValidatorSequence, \
    ValueAsTypeValidator

port = MemberValidatorSequence(
    validators=[ValueAsTypeValidator(value_type=int,
                                     direct_types=[str, float]),
                IntFloatValidator(min_value=1, max_value=65535,
                                  allowed_values=None)])
````

The string equivalent is
[StrCaseChangeValidator](#strcasechangevalidator) followed by
[StrValidator](#strvalidator), which lowercases the value before testing
membership.

### A list of records with mandatory keys and validated values

This is the most common composite shape in real configurations. It takes
three steps, and separating them is what keeps the error messages precise.
[ListSizeValidator](#listsizevalidator) checks how many records there are,
[ListOfDictsKeysValidator](#listofdictskeysvalidator) checks that each
record carries the right keys, and
[ListForEachValidator](#listforeachvalidator) with an inner
[DictForEachValidator](#dictforeachvalidator) checks the values behind
those keys.

````python
from config_as_json import DictForEachValidator, DictRule, \
    IntFloatValidator, ListForEachValidator, ListOfDictsKeysValidator, \
    ListSizeValidator, MemberValidationStep, StrLenValidator

name_rule = DictRule(keys=['name'],
                     validators=[StrLenValidator(min_length=1,
                                                 max_length=40)])
width_rule = DictRule(keys=['width'],
                      validators=[IntFloatValidator(min_value=1,
                                                    max_value=200,
                                                    allowed_values=None)])
values = ListForEachValidator(
    element_validators=[DictForEachValidator(rules=[name_rule, width_rule])],
    element_type=dict)
plan = [MemberValidationStep(member_names=['columns'],
                             validator=ListSizeValidator(min_size=1,
                                                         max_size=64)),
        MemberValidationStep(
            member_names=['columns'],
            validator=ListOfDictsKeysValidator(mandatory_keys=['name',
                                                               'width'],
                                               allowed_keys=['align'])),
        MemberValidationStep(member_names=['columns'], validator=values)]
````

### Records that must have unique names

Uniqueness of a field across a list of records is not a property of any one
element, so no element validator can express it. Project the field out of
every record with
[ProjectedMemberValidator](#projectedmembervalidator) and let
[ListIsOrderedValidator](#listisorderedvalidator) do the duplicate check on
the projected list. Set `is_ordered=False`, because the records themselves
need not be sorted.

````python
from typing import TextIO
from config_as_json import Config, ListIsOrderedValidator, \
    ProjectedMemberValidator


def _names(config: Config, member_name: str, member_value: object,
           stderr_file: TextIO) -> object:
    """Project the name field of every record to a list of names."""
    _ = config, member_name, stderr_file
    assert isinstance(member_value, list)
    return [record['name'] for record in member_value]


unique_names = ProjectedMemberValidator(
    projector=_names,
    validators=[ListIsOrderedValidator(element_type=str, is_ordered=False,
                                       unique_values=True)])
````

If duplicates should be removed rather than reported, use
[ListKeyOrderingValidator](#listkeyorderingvalidator) with
`keep_only_unique=True` instead. Run a key-set validator first so the
projection can rely on the field being there.

### Values that must be chosen from another part of the configuration

When one member lists names that must exist in another member, no member
validator can see both. Use
[ListRelationValidator](#listrelationvalidator) with
`ListRelationKind.SUBSET`, projecting the dict keys of the defining member
into a list.

````python
from typing import TextIO
from config_as_json import Config, ListRelationKind, \
    ListRelationValidator, WholeConfigValidationStep


def _defined_keys(config: Config, stderr_file: TextIO) -> object:
    """Project the keys of the defined-columns dict to a list."""
    _ = stderr_file
    return list(config.defined_columns.keys())


step = WholeConfigValidationStep(validator=ListRelationValidator(
    kind=ListRelationKind.SUBSET, member_a_name='selected_columns',
    member_b_name='defined columns', b_projector=_defined_keys))
````

`ListRelationKind.DISJOINT` expresses the opposite rule, such as input and
output field names that may not overlap.

### A dict whose keys the user chooses

When the keys are user-defined and only the values have a policy, a fixed
key list cannot be written. Give the [DictRule](#dictrule) a key predicate
instead of a key sequence; [accept_all_keys](#accept_all_keys) is the
predicate that selects every key present.

````python
from config_as_json import accept_all_keys, DictForEachValidator, \
    DictRule, IntFloatValidator

weights = DictForEachValidator(
    rules=[DictRule(keys=accept_all_keys,
                    validators=[IntFloatValidator(min_value=0.0,
                                                  max_value=1.0,
                                                  allowed_values=None)])])
````

For the simpler case where both the key type and the value type are
uniform, [DictKeyValueTypesValidator](#dictkeyvaluetypesvalidator) says the
same thing in one line. Remember to list the member in `_unchecked_dicts`
on your configuration class when the base-class key check would reject the
user's keys.

### One thing configured in several kinds

An output that is a file needs a `path`; an output that is a database needs
a `dsn` and a `table`. Model it as a discriminated dict rather than as one
dict with every key optional, so that the wrong combination is actually
rejected. Wrap it in a
[ListForEachValidator](#listforeachvalidator) when the configuration holds
several such outputs.

````python
from config_as_json import DictRule, DictVariant, \
    DiscriminatedDictValidator, ListForEachValidator, StrLenValidator, \
    StrValidator

path_rule = DictRule(keys=['path'],
                     validators=[StrLenValidator(min_length=1,
                                                 max_length=None)])
one_output = DiscriminatedDictValidator(
    discriminator_key='kind',
    variants={'file': DictVariant(mandatory_keys=['path'],
                                  rules=[path_rule]),
              'database': DictVariant(mandatory_keys=['dsn', 'table'])},
    discriminator_validator=StrValidator(
        allowed_values=['file', 'database'], ignore_case=True,
        best_match=True))
outputs = ListForEachValidator(element_validators=[one_output],
                               element_type=dict)
````

### Check the size of a list after it has been normalized

Because each step sees what the previous step returned, the position of
[ListSizeValidator](#listsizevalidator) relative to a normalizing validator
changes what it means. Placed first it measures what the user wrote; placed
after [ListOrderingValidator](#listorderingvalidator) with
`keep_only_unique=True` it measures the deduplicated list, so `[12, 12]`
fails a `min_size=2` check. Decide which of the two you mean, and order the
steps accordingly.

````python
from config_as_json import ListOrderingValidator, ListSizeValidator, \
    ListValueValidator, MemberValidationStep

plan = [
    # 1. Reject impossible hours, reported against what the user wrote.
    MemberValidationStep(member_names=['run_hours_utc'],
                         validator=ListValueValidator(min_value=0,
                                                      max_value=23,
                                                      allowed_values=None)),
    # 2. Sort and deduplicate for the user.
    MemberValidationStep(
        member_names=['run_hours_utc'],
        validator=ListOrderingValidator(element_type=int,
                                        keep_only_unique=True)),
    # 3. Check the size of the list the application will actually use.
    MemberValidationStep(member_names=['run_hours_utc'],
                         validator=ListSizeValidator(min_size=1,
                                                     max_size=24))]
````

Worked example:
[e08_combined_list_validators.py](../example/src/example/e08_combined_list_validators.py)

## Related documentation

- [Public API reference](api.md)
- [Example programs](../example/src/example/README.md)
- [Repository overview](../README.md)
- [Package overview](../README_pypi.md)
