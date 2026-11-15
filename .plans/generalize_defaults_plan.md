# Generalize the use of default values when parsing

## Why this is done

An application that offers an editor for composing a configuration file
wants to start editing from the default values, and to read an incomplete
file by keeping the defaults for whatever the file leaves out. Version 1.8
has `ok_to_use_defaults` on `parse_json()` and `read()`, but it does not
carry that through:

1. **It stops at a nested `Config`.** A nested object is built by
   `_constructed_by_type` / `_constructed_by_factory` in
   `_config_nesting_io.py`, whose constructor calls `parse_json()` strictly.
   This holds for every nesting kind.
2. **It silences a checked dict without filling it.** `check_dict_parse`
   skips the missing-key check, and `parse_json()` then assigns the JSON
   value as it stands, so a declared key of the default dict that the file
   lacks is gone. Nobody is told.
3. **It is not available on the constructor.** Constructing from JSON with
   defaults needs two steps.
4. **Nothing tells the caller which values were kept.** An editor wants to
   show which values did not come from the file.

## What this delivers

With `ok_to_use_defaults=True`, every key that the JSON data must contain
in strict mode, and that the JSON data lacks, keeps a value instead of
raising. This holds at every nesting level. The new method
`Config.kept_value_paths()` tells which paths were kept.

## Decisions this plan is built on

These were settled in the design discussion and are not reopened by a
later step.

1. **On or off only.** The flag stays a `bool` named `ok_to_use_defaults`.
   No `Enum` and no `Flag`. Points 1 and 2 above are bug fixes of what
   `True` already promises, so `True` means the full behaviour, nesting and
   checked dicts included.
2. **"Keep" means: keep the value held when the parse started.** A missing
   key keeps the current value of the object that holds it. On a freshly
   constructed object that is the default assigned by the constructor; on
   an object parsed a second time it is the value of the previous parse.
3. **The JSON data decides which nested objects exist; defaults only
   complete them.** No nested object is ever created that the JSON data
   does not contain:
   - A list holding nested objects gets exactly the elements of the JSON
     list, no more.
   - A dict holding nested objects (`DICT_VALUE`, `DICT_VALUE_BY_KEY`) gets
     exactly the keys of the JSON dict. A key that the JSON dict lacks is
     not added (see decision 7).
   - An `OPTIONAL_MEMBER` that is JSON `null` stays `None`.
   - A nested member that is absent from the JSON data altogether keeps
     its current value as a whole, like any other absent member (this is
     the 1.8 behaviour).

   What defaults are for is the other case: the JSON data **does** contain
   a nested object, but that object lacks some of its required keys. The
   missing keys are then filled, and the only question is where the values
   come from:
   - **From the current nested object, when there is one at the same
     place.** That is `MEMBER`, an `OPTIONAL_MEMBER` whose current value is
     not `None`, and a dict key (`DICT_VALUE` or `DICT_VALUE_BY_KEY`) whose
     current value is a nested Config. The JSON data is parsed into that
     current object, in place, with `ok_to_use_defaults=True`.
   - **From the defaults of the nested Config class, when there is no
     current nested object at the same place.** That is every element of a
     `LIST_ELEMENT` list (elements have no correspondence by index), a dict
     key that the current dict lacks, and an `OPTIONAL_MEMBER` whose current
     value is `None` while the JSON data has an object for it. The object
     is constructed with `config_type(None, None, ...)`, which gives it the
     class defaults, and the JSON data is then parsed into it with
     `ok_to_use_defaults=True`.
   - A declaration with `factory_function` is never parsed in place, since
     the factory chooses the class from the JSON content. The factory is
     called with `ok_to_use_defaults=True`.
4. **A factory that does not accept `ok_to_use_defaults` parses strictly
   with a warning**, once per factory, through the same signature
   introspection that already serves `member_name`. The introspection only
   happens when the flag is `True`; strict callers see no change and no
   warning.
5. **The library never passes `ok_to_use_defaults` to a class constructor.**
   Wherever the library knows the class (nested type declarations and
   `config_factory_from_json`), it constructs from class defaults and then
   calls `parse_json()` with the flag through `wrap_parse_json`. So no
   derived class has to change its `__init__`, and no constructor needs a
   deprecation warning. The keyword on `Config.__init__` is a convenience
   for applications and for factory authors.
6. **`parse_json()`, `read()`, `check_key_match()` and `check_dict_parse()`
   keep their signatures.** The existing bool already says what is needed.
7. **What is never filled.** Unchecked dicts (`_unchecked_dicts`), missing
   keys of a `DICT_VALUE` dict, and missing keys of a `DICT_VALUE_BY_KEY`
   dict. In all three a missing key is accepted in strict mode, so its
   absence is likely deliberate. Lists are never merged.
8. **`kept_value_paths()` reports `JsonPath` tuples, outermost absent key
   only.** A wholly absent member is one path, e.g. `('section',)`. A
   filled leaf inside a present member is its own path, e.g.
   `('section', 'limits', 'max')`. The values below an absent key are not
   listed. Paths of nested objects are prefixed by their path in the
   parent, the way `_located_nested` already prefixes exceptions. Strict
   mode, an object constructed without JSON, and a parse that kept nothing
   all give an empty list. The order of the list is not part of the
   contract.
9. **Values supplied by ROCF are not kept values.** ROCF runs first; a key
   it fills is present when the keep logic runs, and ROCF reports it
   through the automatic-change hook as before.

## The docstring of `kept_value_paths()`

Decision 2 must leave no ambiguity in the docstring. Proposed text:

```text
Return the paths of the values that the most recent parse kept.

A value is kept when a parse with ``ok_to_use_defaults`` true finds no
value in the JSON data for a key that strict parsing requires. The key
then keeps the value that it had when that parse started:

- On an object constructed without JSON data, that is the default value
  assigned by the constructor.
- On an object that is parsed a second time, that is the value from the
  previous parse, not the constructor default.
- In a nested Config that the JSON data contains but that had no current
  nested object at the same place to be parsed into (any list element, a
  dict key that the current dict lacked, or an optional member that was
  None), that is the default value of the nested Config class.

Defaults only complete nested objects that the JSON data contains. No
list element, dict key or optional member is ever added because of them.

A kept value is not an error. Each path is a JsonPath from the root of
the JSON data of this object. A path names the outermost absent key: when
a whole member is absent, only the path of that member is reported, not
the paths of the values inside it.

Missing keys of dicts listed in ``_unchecked_dicts``, and of dicts holding
nested Config objects by key, are not required in strict parsing. They
are not filled and never reported.

Returns:
    A new list of paths, in no guaranteed order. It is empty after a
    strict parse, after construction without JSON data, and after a parse
    that found every required key.
```

## Per-step definition of done

Every step that changes code, tests or build scripts ends with a clean
`./run_clean_build.py`, and every issue it reports repo-wide is fixed. The
whole test suite passes after every step. Each step is reviewed and
committed before the next one starts.

The estimate under each step counts hand-written lines changed (source,
tests, example, hand-written docs), not lines moved and not the
regenerated `doc/api.md` / `doc/protected_api.md`.

Steps 1 to 6 are done on the feature branch **generalize_defaults**, which
is merged into `master` after step 6. Every step leaves the API additive,
so `master` stays releasable either way.

---

## Step 1 — Make room in `config.py`

Status: **Not started**

Refactoring only. No behaviour changes.

- `config.py` is at 946 lines and pylint allows 1000. The later steps add
  roughly 100 lines of logic around parsing. Move the bodies of
  `check_key_match` and `check_dict_parse` into a new private module
  `_config_key_check.py`. The public static methods stay on `Config` with
  their docstrings and delegate, so the public API does not change.
- Split the body of `parse_json()` into small named private functions
  (decode and ROCF, key check, assigning the members), so later steps
  change one small function each instead of growing `parse_json()`.
- Remove the duplicate `_nesting_by_key` (in both `_config_nesting_io.py`
  and `_config_initial_data.py`); keep one and import it.

**Verifies:** the build is clean, the test suite passes unchanged.

**Estimate:** about 60 new or changed lines, plus about 150 moved.

## Step 2 — Fill missing keys of checked dicts

Status: **Not started**

The first bug fix (point 2 above).

- New private function in `_config_key_check.py`, given the current value,
  the JSON value and the unchecked-dict names, returning the JSON value
  with missing keys filled from **deep copies** of the current value
  (recursively, for dicts inside checked dicts). Deep copies, because a
  module-level default dict assigned by reference must never become shared
  with, or changed through, the parsed value.
- The same name-based rule decides "unchecked" as in `check_dict_parse`
  (the key name is looked up in `_unchecked_dicts` at every depth), so a
  dict that is not checked is also not filled.
- Called only when `ok_to_use_defaults` is true, after the key check.
- The function also returns the `JsonPath` of every key it filled. Step 3
  uses that; here it is only covered by tests.
- Fix the `check_dict_parse` docstring that already promises this.

**New tests** (parametrized): a missing key at depth 1 and depth 2; a
missing key whose default is itself a dict (one filled path); an unchecked
dict and a dict inside it are not filled; strict mode unchanged; the
filled value is a copy (changing it leaves the default untouched); the
existing `ok_to_use_defaults=True` tests in `test_config.py` still pass.

**Estimate:** about 60 source, 150 test lines.

## Step 3 — `kept_value_paths()` for one level

Status: **Not started**

- `Config.kept_value_paths()` with the docstring above. The list is
  stored in a private attribute set in `__init__` and cleared at the start
  of `parse_json()`, next to the clearing of the automatic-change hook.
- Recorded in `parse_json()` when `ok_to_use_defaults` is true:
  - every public member absent from the JSON data, omit-None members
    included: `(key,)`;
  - every key filled by the function of step 2.
- Nothing is recorded in strict mode.
- `__init__` gains keyword-only `ok_to_use_defaults: bool = False` after
  the `*`, forwarded to `wrap_parse_json` / `wrap_read`. Docstring of
  `__init__` and of the class updated. Since the library never passes it
  to a constructor (decision 5), no derived class has to change.

**New tests:** absent direct member; absent omit-None member; filled dict
leaf; absent nested member as one path (nested objects themselves come in
step 4); strict mode and construction without JSON give `[]`; a second
parse reports only what the second JSON lacked; the list is a new list each
call; the constructor keyword with text and with a file.

**Estimate:** about 70 source, 180 test lines.

## Step 4 — Carry the flag into nested objects declared by type

Status: **Not started**

The second bug fix (point 1 above), for declarations without
`factory_function`.

- `_nested_config_from_json` and the four functions below it
  (`_item_from_json`, `_list_from_json`, `_dict_from_json`,
  `_dict_by_key_from_json`) take `ok_to_use_defaults` and the current
  value of the member.
- With the flag false, nothing changes: construction exactly as in 1.8.
- With the flag true, per decision 3:
  - for each nested object that the JSON data contains, when a current
    nested object exists at the same place: `wrap_parse_json(current,
    text, True, ...)` in place;
  - for each nested object that the JSON data contains, when there is no
    current nested object at the same place: `config_type(None, None, ...)`
    with `member_name`, then `wrap_parse_json(new, text, True, ...)`;
  - the list elements, the dict keys, and `None` for JSON `null` are
    exactly those of the JSON data. Nothing is added.
- `_located_nested` keeps prefixing `json_path` of a `ConfigParseError`
  for both routes.
- After each nested object is parsed, its `kept_value_paths()` are added
  to the parent's list with the nested object's `json_path` in front,
  next to the existing `merge_nested` of the automatic-change hook.
- A parse that fails inside a nested object parsed in place leaves that
  object partly updated. That is the same as what a failing top level
  `parse_json()` already does to its own object; document it, do not add
  rollback.

**New tests** (parametrized over the five kinds where they apply):

- partial `MEMBER` parsed into the current instance (identity kept,
  customised parent default kept);
- `OPTIONAL_MEMBER`: JSON `null` stays `None`; a partial JSON object while
  the current value is `None` is completed from class defaults;
- `LIST_ELEMENT`: the result has exactly the JSON elements, also when the
  current list is longer or shorter; each partial element is completed
  from class defaults, even when the current list has an element at that
  index;
- `DICT_VALUE`: the result has exactly the JSON keys; a partial value at
  an existing key is parsed in place, at a new key it is completed from
  class defaults; a key missing from the JSON is not added;
- `DICT_VALUE_BY_KEY`: a partial declared value is parsed in place; a key
  missing from the JSON is not added;
- two levels deep with prefixed kept paths;
- strict mode unchanged for every kind;
- a nested parse error still carries the full `json_path`.

**Estimate:** about 110 source, 280 test lines.

## Step 5 — Factories and `config_factory_from_json`

Status: **Not started**

- Generalise the signature check in `_deprecated_support.py` from
  `member_name` to any keyword name (`accepts_keyword(func, name)`), with
  the same per-callable cache. `use_member_name` keeps its behaviour on
  top of it.
- `ConfigFactory` protocol: keyword `ok_to_use_defaults: bool = False`,
  docstring and the `ConfigNesting` docstring updated.
- `_constructed_by_factory`: with the flag true, a factory that accepts it
  gets it; one that does not is called without it (strict) and a
  `DeprecationWarning` is issued once per factory, saying that the factory
  cannot keep default values until it accepts and forwards the keyword.
- `config_factory_from_json` gains keyword-only `ok_to_use_defaults: bool =
  False`. With it true, `_constructed_match` constructs the selected class
  from class defaults and then calls `wrap_parse_json(..., True, ...)`
  (decision 5), so the selected class needs no change.
- Update the factory in `e32` and the test factories only where a test
  needs them to accept the keyword; the rest keep working unchanged.

**New tests:** a factory that accepts the flag keeps values; a factory
that does not parses strictly and warns once; no warning and no
introspection when the flag is false; `config_factory_from_json` with the
flag, with text and with a file; kept paths through a factory-built nested
object.

**Estimate:** about 90 source, 200 test lines.

## Step 6 — Documentation and a teaching example

Status: **Not started**

- New `example/src/example/e43_editor_defaults.py` and its test: an
  editor-style start from defaults, reading an incomplete file that has a
  nested member and a list of nested objects, and printing
  `kept_value_paths()` to show which values the editor should mark as not
  coming from the file. Explanatory comments, as teaching examples
  require.
- `example/src/example/README.md`: the section for the new example.
- `README.md` and `README_pypi.md`: what `ok_to_use_defaults` now covers,
  and the bug fixes.
- `doc/api.md` and `doc/protected_api.md` regenerate from docstrings
  during the build; check that what they say about `ok_to_use_defaults`
  and `kept_value_paths()` reads well.

**Estimate:** about 200 example, 100 test, 40 documentation lines.

## Step 7 — Verify the downstream libraries

Status: **Not started**

`edit-cfg-json`, `edit-cfg-json-tk` and `edit-cfg-json-textual` are the
intended users. Build them against this version, check that nothing
changed for them in strict mode, and record whether they want to adopt
`ok_to_use_defaults` and `kept_value_paths()`. Decide whether any of it
changes this plan. No release before this is done.

## Step 8 — Release

Status: **Not started**

- Run the tests with Python 3.12, 3.13, 3.14 and 3.15.
- Version bump in `setup.py`. The API change is additive and the
  behaviour changes are bug fixes of what `ok_to_use_defaults=True`
  promises, so this is a minor release. The release notes name the two
  bug fixes, since an application that relied on missing dict keys being
  dropped will see them filled.
- Whether a factory without `ok_to_use_defaults` stops being supported is
  decided together with step 12 of `planned_steps.md` (2.0.0), not here.
