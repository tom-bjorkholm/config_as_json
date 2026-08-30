# Dotted member paths in reported names

## What this delivers

A validation failure, and every other diagnostic that names a configuration
value, tells the whole path from the top level configuration down to the
value it is about, such as `outputs[1].section.kind` instead of `kind`.

The path is built as the configuration structure is traversed, on the way
*in*. The top level member name starts the string as a plain name. Going
into a class member appends a dot and the member name. Indexing into a list
or a dict appends the index or key in square brackets.

## Decisions this plan is built on

These were settled in the step 0 review and are not reopened by a later
step.

1. **The path travels down, as a parameter.** `member_name` is threaded
   through the call chain rather than collected on the way out of an
   exception or carried in ambient state. Collecting on the way out needs an
   exception to exist at all, so it cannot name the value in a warning that
   does not stop the validation, and it leaves permanent unwinding code in
   the library. That is why the `breadcrumb_at_nesting` branch is not the
   route taken; see *The branch that is not taken* below.

2. **`member_name` is the path of the Config object itself**, not of one of
   its members. A nested object holding `outputs[1]` receives
   `member_name='outputs[1]'` and reports its own member `kind` as
   `outputs[1].kind` once its own nesting step is added. `None`
   means this object is the top level and not a member of anything, so its
   members are reported by their plain names.

3. **The reported name becomes the path.** `MemberValidator.validate_member`
   receives the path as `member_name`, and
   `InvalidConfigurationValue.member_name` holds the path. The local
   attribute name is not reported separately. This is what makes every one
   of the roughly twenty validator modules report paths without being
   changed at all.

4. **Notation: a dot before a class member, square brackets around a list
   index or a dict key.** `outputs[1].section.kind`, `by_name[main].mode`.
   The bracket part of this is already implemented in
   `list_element_validators`, `dict_validators` and `_config_nesting_io`;
   the dot part is what this plan adds.

5. **The path is text a person reads, not text a program parses back.** A
   dict key holding a dot or a bracket makes an ambiguous path. That is
   accepted and documented rather than escaped.

6. **ROCF path notation is left alone for now.** `rocf_change` prints
   `outputs[0][csv_params][delimiter]` for the same location, because its
   paths address JSON data where an object with attributes looks like a
   dict, and the two notations cannot fully agree. Whether ROCF should align
   where it can is a question for later and is not part of this plan.

## Two other things to notice

**The parse path does not go through `parse_json()`.** A nested Config is
built in [`_config_nesting_io.py`](../src/config_as_json/_config_nesting_io.py)
by calling `nesting.config_type(from_json_data_text=..., ...)` or
`nesting.factory_function(...)`, and that constructor calls `parse_json` and
`validate` on itself. A `member_name` parameter on `parse_json` alone
therefore never reaches a nested object while a configuration is being read,
which is where most validation failures happen. The nested construction
contract — `Config.__init__`, the `ConfigFactory` protocol, and
`config_factory_from_json` — has to carry `member_name` too.

**Three public extension points below `Config` need the path.**
`Config.validate` reaches its members through `ValidationStep.apply`, and a
whole-config validator receives no member name at all. `check_key_match` and
`check_dict_parse` are public static methods with no path context either. So
`ValidationStep.apply`, `WholeConfigValidator.validate`, `check_key_match`
and `check_dict_parse` all take `member_name` as well.

There is also a third traversal beyond parse and validate: **the write
path**. `_item_json_data` calls `member_value.as_json_string()`, which
validates. So `as_json_string` and `read` carry `member_name` too. `write`
does not: a file is always written for a whole configuration, so it passes
`None`.

## Decisions

- **Are the wrappers public or private?** They shall be **private**.
  Naming them `_wrap_parse_json` and `_wrap_validate` means step 12 removes
  private methods rather than public ones, so the removal is not itself
  a breaking change. Steps below use the public names as originally written.

- **Which branch do steps 1 to 5 live on?** Between step 1 and step 6 the
  package is incompatible with existing callers, and `master` is
  publishable at any time. A feature branch merged at step 6 or step 9
  keeps `master` releasable while every step is still separately reviewed
  and committed.
  Feature branch for step 1 to step 5 is **dotted_path_in_member_name**.

## Per-step definition of done

Every step that changes code, tests or build scripts ends with a clean
`./run_clean_build.py`, and every issue it reports repo-wide is fixed.
Steps 1 to 8 are each reviewed and committed before the next one starts.

---

## Step 1 — `member_name` on `Config.parse_json()` and `Config.validate()`

Status: **Implemented and committed**

Plumbing only. Nothing about what is reported changes yet.

- Add `member_name: Optional[str]` **without a default value** to
  `Config.parse_json()`, `Config.validate()`, `Config.read()` and
  `Config.as_json_string()`.
- Add `Config._wrap_parse_json()` and `Config._wrap_validate()` with the same
  argument lists as the methods they wrap. At this stage they only forward.
  Every call the library makes to `parse_json` or `validate` on a Config
  object goes through a wrapper from here on.
- `Config.write()` keeps its signature and passes `member_name=None` to
  `as_json_string`.
- Document in every one of those docstrings that `member_name` is the dotted
  and indexed path for reaching this object by traversing nested attributes
  from the top level of the complete `validate()` or `parse_json()`
  operation, and that `None` means this object is the top level.
- Update every call site in `src/`, `test/` and `example/` to pass
  `member_name` explicitly. Everything passes `None` in this step.

**Verifies:** the build is clean and the whole test suite passes unchanged.
No reported name has moved yet.

## Step 2 — `member_name` on the validation extension points

Status: **Implemented and committed**

Plumbing only.

- Add `member_name: Optional[str]` without a default to
  `ValidationStep.apply()`, `WholeConfigValidationStep.apply()`,
  `MemberValidationStep.apply()` and `WholeConfigValidator.validate()`.
- Add it to `Config.check_key_match()` and `Config.check_dict_parse()`.
- Update the built-in whole-config validators that name members in their
  messages: `ProjectedWholeConfigValidator`, `ListRelationValidator`,
  `CallingWholeConfigValidator` and the one in `radix_number`.
- Update the whole-config validators written in `test/` and in
  `example/src/example/` (`e05_custom_validator.py` and the validators in
  `test_nested_config.py`, `test_config_2.py`, `test_validator.py`,
  `config_excel_list_transform_validated.py`).
- `Config.validate()` forwards its own `member_name` to every step.
- `MemberValidationStep.apply()` keeps using the **local** member name for
  `hasattr`, `getattr` and `setattr`. Only what it hands to the validator
  will become a path, in step 4.

**Verifies:** the build is clean, the test suite passes unchanged.

## Step 3 — `member_name` on the nested construction contract

Status: **Implemented and committed**

Plumbing only.

- Add `member_name: Optional[str]` without a default to `Config.__init__()`,
  forwarded to `parse_json`, `read` and `validate`.
- Add it to the `ConfigFactory` protocol in `config_nesting.py` and to
  `config_factory_from_json()` in `config_factory.py`.
- Update the class docstring of `Config` and the docstring of
  `ConfigNesting`, which both document the constructor keyword contract for
  nested classes.
- `_config_nesting_io._constructed_nested` (new small helper, or the
  existing branch in `_item_from_json`) passes `member_name` to the type or
  to the factory.
- Update every nested Config class and every factory in `test/` and
  `example/src/example/`. That is `e33` through `e39` and `e41` for nested
  classes, `e32` for the factory, and the twelve test modules that declare
  `nested_configs` plus `test_nested_config_factory.py` and
  `test_migrate_cfg.py` for the factories.

**Verifies:** the build is clean, the test suite passes unchanged. This is
the largest mechanical step; nothing about behaviour has changed yet.

What was decided while implementing this step:

- `Config.__init__()`, the `ConfigFactory` protocol and
  `config_factory_from_json()` take `member_name` without a default, which is
  what forces every call site to be visited. Every other constructor that
  gained the parameter took it with the default `None`: the roughly 140
  `Config` derived classes in `test/` and `example/`, `RadixNumber`, and the
  factories. Their own call sites therefore did not have to change.
- The scope was wider than the classes listed above. A required parameter on
  `Config.__init__()` means that every `Config` derived class in `src/`,
  `test/` and `example/` has to pass `member_name` on to
  `super().__init__()`, not only the ones that are used as nested configs.
- `_constructed_nested()` hands the nested object the name that
  `_item_from_json()` already computes, rather than `None`. No reported name
  moves, because nothing builds a reported name out of `member_name` before
  step 4. Step 5 therefore only has to make that computed name a whole path.
- `_config_initial_data._wrap_one_value()` and `migrate_cfg()` pass `None`.
  An auto-wrapped bridge default is replaced by the parsed object before any
  path matters, and a migration reads a whole configuration file.
- `SingleMemberValidationConfig` in `validator_test_helpers.py` already had a
  parameter named `member_name` holding the local attribute name of its one
  member. That parameter is now called `attr_name`.
- Four new `duplicate-code` reports appeared, because the added
  `member_name=member_name` line makes constructor boilerplate in unrelated
  test modules four lines alike. They are suppressed with block local
  `# pylint: disable=duplicate-code` in one module of each pair, the way the
  repository already handles that kind of accidental similarity.

## Step 4 — Build the path on the `validate()` traversal

Status: **Implemented and committed**, and it absorbed parts of step 5

The first step where reported names move.

- Add the joining helper — one small module, one function:
  `member_path(prefix: Optional[str], name: str) -> str`, returning `name`
  when `prefix` is `None` and `f'{prefix}.{name}'` otherwise. Export it, so
  an application writing a whole-config validator can build its own member
  paths the same way.
- `Config._validate_nested_configs()` passes `member_path(member_name, key)`
  down for each declared nested member.
- `_validate_item`, `_validate_list`, `_validate_dict` and
  `_validate_dict_by_key` already append `[index]` and `[key]` to the name
  they are given. They now pass that name on as the nested object's
  `member_name` when they call `validate()`.
- `MemberValidationStep.apply()` passes `member_path(member_name, local)` to
  the validator while still using `local` for the attribute access.
- `WholeConfigValidationStep.apply()` forwards `member_name` unchanged.
- The built-in whole-config validators build their reported names with
  `member_path`, including `ProjectedWholeConfigValidator`'s
  `pseudo_member_name`.

**New tests** (`test/test_config_as_json/test_member_path.py`):

- One reported path per `ConfigNestingKind`: `MEMBER`, `OPTIONAL_MEMBER`,
  `LIST_ELEMENT`, `DICT_VALUE`, `DICT_VALUE_BY_KEY`.
- Nesting two levels deep, so a path has two dots.
- A list of nested objects inside a nested object: `a.b[2].c`.
- A dict key that holds a dot, asserting the documented ambiguous result.
- `InvalidConfigurationValue.member_name` holding the path.
- A member validator, a whole-config validator, and `ListForEachValidator`
  and `DictForEachValidator` on a member of a nested object, each reporting
  the path.
- A top level `validate()` still reporting plain names.
- The path reaching a diagnostic that is **printed without raising**, which
  is the case the discarded design could not serve.

What was decided while implementing this step:

- The joining helper lives in the new module `member_path.py`. It holds the
  exported `member_path()` and, next to it, the private `_indexed_path()`
  that `config.py` had as `_dict_value_path()`. The rename is because list
  indices use it too, and using it for them removed about ten copies of the
  same `f'{name}[{index}]'` in `_config_nesting_io.py`. Keeping the two
  notations in one module means a reader finds the whole notation in one
  place, and only one of the two is public.
- **`_config_nesting_io` could not simply pass the whole path down.** Its
  `_item_from_json` uses the name it computes for two different things: the
  nested object's `member_name`, and the `path_prefix` for
  `auto_ch_hook.merge_nested`. The automatic-change paths address JSON data,
  they use their own bracket notation, and `rocf_change._absolute_path`
  composes them one nesting level at a time. Handing that a dotted path
  would have corrupted every automatic-change path below two nesting levels.
  So all three traversals in that module keep `member_name` as the local
  name and take the reported path of the holding object as a new
  `parent_path` argument. `test_rocf_own_notation` locks that down. This also keeps decision 6 true.
- `check_key_match` serves two callers with two notations: the keys of a
  configuration object are reported after a dot, and the keys of a plain
  dictionary in square brackets. It therefore took one more keyword argument,
  `dict_keys: bool = False`, rather than guessing.
- `CallingMemberValidator` needed no change at all. Its
  `arg_name_member_name` is the *name of the keyword argument* in the call to
  the application's method; the value handed under that name is
  `validate_member`'s `member_name`, which becomes the path by the same rule
  as for every other validator.
- `CallingWholeConfigValidator` names the Config object it is about with a
  ` at {path}` suffix built by `validator._at_path`, so that the four
  messages are unchanged for a top level configuration.
- `RadixNumber.get()` gave up its cache rebuild to a new protected
  `_rebuild_cache(reported_name, stderr_file)`, so that `_RadixCacheBuilder`
  can rebuild the cache naming the whole path. `written_member_name()` is a
  new classmethod, because the cache builder needs that name to join.
- Of the existing tests only `test_nested_config_io_private.py` needed
  changing, and only because it calls the private traversal helpers
  directly. No existing test asserted a reported name inside a nested
  object, which is why the new test modules carry the whole proof.

## Step 5 — Build the path on the parse and write traversals

Status: **Mostly imlemented tests remaining to do.**

- `_item_from_json`, `_list_from_json`, `_dict_from_json` and
  `_dict_by_key_from_json` pass the name they already compute into the
  nested constructor or factory as `member_name`.
- `_item_json_data`, `_list_json_data`, `_dict_json_data` and
  `_dict_by_key_json_data` do the same for `as_json_string`.
- The `Nested Config member {member_name} must be ...` messages in
  `_config_nesting_io` name the path.
- `check_key_match` and `check_dict_parse` name the path in their unknown
  key and missing key messages.

**New tests:** a validation failure inside a nested object during
`parse_json`, during `read`, and during `as_json_string`/`write`, each
reporting the whole path; an unknown key and a missing key inside a nested
object reporting the path; a nested object two levels down failing while
being parsed.

The way the previous work was split into steps (adding arguments without
passing values or without handling the received values) means that
there is huge risk that we have forgotten to pass or handle member path
values  in some scenario. Therefore, we must create a really
comprehensive test suite to check that for every node or leaf being
validated the dotted path member_name really has the correct value.
This is a big test effort that must be done thoroughly.

## Step 6 — Backward compatibility for existing applications

Status: **Not done yet**

The package becomes compatible with unchanged application code again.

- Give every `member_name` parameter added in steps 1 to 3 the default value
  `None`, meaning this object is the top level and not a member of anything.
  Old code that calls `parse_json`, `validate`, `read`, `as_json_string` or
  a Config constructor without `member_name` keeps working unchanged and
  keeps reporting plain names.
- `Config._wrap_parse_json()` and `Config._wrap_validate()` inspect the
  derived class. When the override accepts `member_name` it is passed on;
  when it does not, a `DeprecationWarning` is issued and the override is
  called without it. Cache the introspection result per class rather than
  inspecting on every call.
- The same introspection guards the other four places where the library
  calls into application code with the new argument:
  `ValidationStep.apply`, `WholeConfigValidator.validate`, the nested
  `config_type.__init__`, and `factory_function`.
- The existing `_deprecated_support` module is the place for this; extend it
  rather than starting a second mechanism.

**New tests:** an old-style derived class overriding `parse_json` and
`validate` without `member_name` still works and warns exactly once per
class; an old-style nested Config class and an old-style factory still work
and warn; a new-style class does not warn; the warning text names what to
change.

## Step 7 — Documentation and a teaching example

Status: **Not done yet**

- `README.md` and `README_pypi.md`: what a reported name looks like now.
- A new `example/src/example/e42_nested_member_paths.py` and its test,
  showing a failure inside a list of nested objects and the path it reports.
  Explanatory comments, as teaching examples require.
- `example/src/example/README.md`: the section for the new example.
- `doc/api.md` and `doc/protected_api.md` regenerate from docstrings during
  the build; check that what they say about `member_name` reads well.

## Step 8 — Verify the downstream libraries

Status: **Not done yet**

`edit-cfg-json`, `edit-cfg-json-tk` and `edit-cfg-json-textual` call
`Config.parse_json` and `Config.validate` directly and attribute a refusal
to the member it is about. Decision 3 changes what
`InvalidConfigurationValue.member_name` holds, from a local name to a path,
so their attribution needs checking against this build before it is
released. Also worth checking is whether their `tree.path_text`, which joins
every step with a dot, should be reconciled with the notation here.

Build the three against this version, record what needs changing there, and
decide whether any of it changes this plan. No release before this is done.

## Step 9 — Release

Status: **Not done yet**

- Version bump in `setup.py`. Steps 1 to 6 leave the public API
  additive, so this is a minor release.
- `README.md` test summary refreshed by the clean build.
- Delete the `breadcrumb_at_nesting` branch, locally and on `origin`, now
  that this design has proved itself.

## Step 10 — Six months after step 9: the warning becomes visible

Status: **Not done yet**

An override that does not accept `member_name` raises both a
`DeprecationWarning` and an end user visible message printed to
`stderr_file`, so that an application that suppresses warnings still learns
that a path is missing from its diagnostics.

Tests for the printed message, and for it appearing once rather than once
per validated member.

## Step 11 — Release

Status: **Not done yet**

Version bump.

## Step 12 — Four months after step 11: remove the compatibility layer

Status: **Not done yet**

- Remove `Config._wrap_parse_json()` and `Config._wrap_validate()`; the calls
  to `parse_json` and `validate` are direct again.
- Remove the introspection and the deprecation warnings for all five call
  sites.
- Decide then whether the `member_name` defaults stay at `None` or become
  required again. Keeping the default is the smaller change and keeps a top
  level call reading well.
- Version bump to 2.0.0, since an application that never adopted
  `member_name` stops working here.

## The branch that is not taken

`origin/breadcrumb_at_nesting` (commit `81d8576`, a child of `28a30ef`)
implements the same goal the other way round: `InvalidConfiguration` carries
`config_path`, each nesting boundary catches and calls `prepend_path`, and a
breadcrumb line is printed per level. It needs no API change at all, and it
comes with 205 lines of tests in `test_nested_diagnostics.py`.

It is not the route taken for two reasons. It needs an exception to carry
anything, so it cannot name a value in a warning that does not stop the
validation. And the catching and re-raising at every boundary is permanent
workaround code that would stay in the library for good, where the parameter
threading leaves nothing behind after step 12.

The branch stays unmerged until this design has proved itself, and is
deleted in step 9. Its tests are worth reading as a source of cases for the
step 4 and step 5 test files.
