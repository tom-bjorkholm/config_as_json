# Dotted member paths in reported names

## Why this is done

A complete configuration for an application very often have several nested
Config classes as members of other Config classes, or in list or dicts that
are members of of another Config class. When such a leaf Config reports
an error or warning about its configuration, it has to tell the user
the name of the problematic configuation parameter including the path
to it. Telling the user only that Config member `port` has an invalid
value is a slap in the face of the user who has a configuration consisting
of many Service Config objects, each with a member `port`.

Thus it is of outmost importance that the all error messages, warning messages
and similar messages include information that is as specific as possible
about both the Config member name but also include the complete path
through the nested Config object to where this member is.

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

Status: **Implemented and committed, with pending review comments to fix**

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

What was decided while implementing this step:

- The source of this step was already in place, because step 4 absorbed it.
  What this step adds is the comprehensive proof, and the one gap that the
  proof found.
- The sweep is built on a **recording tree**
  (`test/test_config_as_json/member_path_deep_tree.py`). Every level nests
  one child in each of the five nesting kinds, three levels deep, which is
  31 Config objects holding every kind inside every other kind. Validators
  that accept every value and only record the path they were given report
  to one recorder. Every traversal compares the whole recorded list with an
  explicitly written expected list, so a path that is wrong, missing, or
  reported where none was expected is caught even though nothing fails.
- **Placeholder defaults had to be marked.** A Config constructor builds its
  declared defaults before it parses anything, and each of those objects
  validates itself. The tree builds them with `member_name='#defaults'` and
  the recorder drops what they record. Without the marker their paths, which
  are relative to the placeholder, could not be told apart from real ones.
- `validate()` is compared as a multiset, so each path must be reported
  exactly once. The parse, read, `as_json_string` and `write` traversals
  validate a nested object more than once by design, because a nested
  constructor validates itself and `as_json_string` validates every object
  it serializes. Those are therefore compared as sets.
- Every traversal is also started from a path that is not `None`, which is
  what an editor such as edit-cfg-json does when it validates one subtree.
- **One gap was found and fixed.** `MemberValidationStep.apply()` named a
  member missing from the Config object by its local attribute name, so a
  validation plan naming a member that does not exist said nothing about
  which nested object it was about. It now names the path. At the top level
  `member_path(None, local)` is the local name, so no existing message
  changed.
- `CallingMemberValidator` names no member at all in its own diagnostics
  (`Method check_count returned False.`), so there is no name there to turn
  into a path. What it hands to the application method under
  `arg_name_member_name` is the path, and that is what the new test checks.
  **This is a major bug that must be corrected.**
- `Leaf` in `member_path_test_configs.py` gained a `deep` member holding a
  dictionary inside a dictionary, because the recursion in
  `check_dict_parse` composes `[key]` steps and nothing tested that
  composition. `check_key_match` and `check_dict_parse` are also called
  directly, as the public static methods they are.
- `test_nested_config_io_private.py` is now parametrized over
  `parent_path`, so each of the ten shape and type messages of
  `_config_nesting_io` is checked both at the top level and below a holder.
- `test_nested_config_factory.py`'s `TrackingFactory` already recorded the
  `member_name` it was called with, and nothing asserted it. It now does,
  for all five nesting kinds, and a factory returning the wrong type is
  named by its path.
- The deliberate `None` spots of step 3 were left alone.
  `_config_initial_data._wrap_one_value()` names the local member in
  `Cannot wrap {name} as {type}`, and that message is about bridging default
  values before any parse, where step 3 decided the path is `None`.
  **We need to think about the user, this is an internal step but for
  the user this data is in the config object we are constructing from
  it so we really should report the path that we are constructing even
  if it is not yet fully constructed.**
**New test files:** `member_path_deep_tree.py`,
`test_member_path_sweep.py`, `test_member_path_validators.py` and
`test_member_path_factory.py`.

What the review of this step changed:

- The review called the missing path in `CallingMemberValidator` a fatal
  bug rather than an oddity, and asked for a careful scan for the same kind
  of bug. The rule the scan applied: **a diagnostic that a traversal emits
  about a configuration value, member, or object has to say where that
  value is**. Five places failed that rule.
- `CallingMemberValidator` now names the member in all four of its
  diagnostics: the method not found, the method not callable, the method
  returning `False`, and the method returning something else.
  `_get_config_method` and `_check_validation_only_method_result` take the
  ready phrased `where` text instead of a path. `_for_member` phrases it as
  ` for {path}` for a member call and `_at_path` phrases it as ` at {path}`
  for a whole-config call, and both now sit directly after the method name,
  which reads well for both. **A top level member call message changes**:
  `Method check_count returned False.` becomes `Method check_count for count
  returned False.` That is the point of the fix, because the message named
  no member at all before. Every top level whole-config message is
  unchanged, because `_at_path(None)` is empty text.
- `_config_initial_data` composes the whole path of the member the wrapped
  value ends up at, so `Cannot wrap items[0] as MySection` becomes
  `Cannot wrap outputs[1].items[0] as MySection` for a nested object. The
  bridge that is built is also constructed with that path, so its own
  construction-time validation reports paths too. This reverses the step 3
  misconception that auto-wrapping passes `None`: the end user thinks of that
  neutral value by the path of the member it is the value of.
- `config_factory_from_json` names the member it was building when no
  matcher accepts the data: `No matching config class found for
  outputs[1].part`.
- `Config._decoded_json_object` names the object the JSON was meant for,
  which is what an editor validating one subtree needs: `Config.parse_json
  for outputs[1] failed to load JSON from string/file.` and `Configuration
  JSON root for outputs[1] must be a JSON object.`
- `json_write_hooks` reports its places as the path of the Config object
  whose data is being written with the place inside that data appended, so
  `Value at limits[cpu] has non-JSON type set` becomes `Value at
  outputs[1].limits[cpu] has non-JSON type set`. Its `_append_path_text`
  already used the member-name convention, so only the root of the walk had
  to change, in the new `_reported_at`. The `path_text` handed to an
  application converter function stays relative to the object's own data,
  because a selector is relative to it too, and `<root>` is still what a
  place in the top level configuration is called. `apply_serialize_converters`
  therefore took `member_name` as a keyword argument without a default, like
  the rest of steps 1 to 3.

What the scan deliberately left alone, and why:

- **Diagnostics about a class declaration**, not about a value: the checks
  in `Config.__init__`, in `_config_nesting_decl`, and the selector checks
  in `json_write_hooks`. They report a mistake in the application's Config
  class or in its converter declarations, and the class, not a path, is
  what locates such a mistake. They are also raised for every instance of
  that class, wherever it sits.
- **ROCF diagnostics** (`RocfConflictError`, `RocfIncompatiblePathError`).
  Decision 6 defers ROCF notation, and these report a conflict between the
  migration rules a class declares rather than a configuration value. Adding
  the path there means `ReadOldConfiguration.process_json` taking
  `member_name`, which is a public extension point and a decision of its own.
- `RadixNumber.get()` and `RadixNumber.set()` outside a validation, which
  keep the local written-member name because there is no traversal and so no
  path. This is documented and tested.
- `string_to_enum_best_match`, a utility an application calls from its own
  parse converter. It has no member context in its API at all.

## Step 6 — Backward compatibility for existing applications

Status: **Implemented, waiting for review**

The package becomes compatible with unchanged application code again,
but issues a deprication warning for unchanged application code.
(This is in fact not such a big problem as you might think, as most
 application code never override the changed APIs, and most application
 code never call the methods in the changed API directly.)

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

What was decided while implementing this step:

- **The compatibility layer is asked about the signature, not about the
  override.** `_deprecated_support.accepts_member_name()` reads
  `inspect.signature` and answers whether the callable has a `member_name`
  parameter, or a `**kwargs` that any keyword argument reaches. Asking
  whether the method is overridden at all, the way the renamed-hook shim
  does, would have called an override that does accept the argument without
  it. A callable whose signature cannot be read is assumed to accept it,
  which is the behaviour it had before this step.
- The answer is remembered in a dict keyed by the function, the method
  function, or the class, so a class is read once per process rather than
  once per validated object. A callable object whose class defines
  `__call__` in Python is remembered by that `__call__`, which is what makes
  `RadixNumber.factory()`'s returned object cached correctly. Anything else,
  such as a `functools.partial`, has no key that is safe to keep a reference
  to and is read every time.
- `use_member_name()` warns **once per function and per class**, keyed the
  same way, so an application that has to change two methods is told about
  both. The tests therefore declare each old-style class inside the test
  function that is about it.
- **The warning is meant to be seen in pytest, and only there, at this
  stage.** It is issued with a fixed `stacklevel` that names a line in this
  package, which has two consequences that are both wanted. A pytest session
  shows it, whether the old-style object is built in a test body, while a
  test module is imported, or while a `conftest.py` is loaded, because pytest
  replaces the warning filters with `always`; it takes an explicit
  `ignore::DeprecationWarning`, or `-p no:warnings`, to turn it off, and a
  `filterwarnings = error` setting turns it into a failing test. An
  application in production stays silent, because a `DeprecationWarning` is
  ignored by default and the `__main__` exception of PEP 565 does not apply
  to a warning attributed to a library file. Attributing it to the
  application instead, which `warnings.warn(skip_file_prefixes=...)` can do
  from Python 3.12 on, was therefore deliberately **not** done: an
  application developer tests, and that is where the warning belongs until
  step 10 makes it visible to the ones who do not.
- **Nine call sites are guarded, not the six this step first listed.** The
  rule applied: every place where the library itself calls a method, a
  constructor or a factory of the application with `member_name`. Beyond the
  six, those are `config_factory_from_json` constructing the matched class,
  `migrate_cfg` constructing the class it migrates, `_config_initial_data`
  constructing an auto-wrap bridge, and `_RadixFactory` constructing its
  written-number class. Leaving any of them out would have broken an old
  application that never wrote a nested Config at all.
- `check_key_match` and `check_dict_parse` got the default but no guard.
  They are static methods that the library calls on itself, and an
  application that overrides a static method of `Config` is a case this
  step deliberately does not serve.
- `apply_serialize_converters()` keeps requiring `member_name`, because it
  was added in step 5 and this step is about what steps 1 to 3 changed.
- **The wrappers moved out of `config.py`**, which had grown past the
  1000 line limit. They are now the module-level functions `wrap_parse_json`,
  `wrap_validate`, `wrap_read`, `wrap_as_json_string` and `wrap_apply` in the
  new private module `_config_call_wrappers.py`, each taking the object to
  call as its first argument. Two wrappers are new here: the library calls
  `read` from `Config.__init__` and `as_json_string` from
  `_item_json_data` and from `write`, so an old-style override of either of
  those had to be served too. Step 12 now deletes one file instead of
  removing methods, and `_config_nesting_io` no longer reaches into a
  protected method of the object it validates.
- Adding the default to `WholeConfigValidator.validate` and to
  `ValidationStep.apply` forced the same default onto every override of them,
  in `src/`, `test/` and `example/`: an override may not require what the
  base class defaults. That is twelve mechanical edits and one mypy rule
  worth remembering for step 12.
- The two contract docstrings that say a nested class must accept
  `member_name` now say that it should, and what it loses when it does not.
- One `duplicate-code` report appeared, because the nested Config
  boilerplate of the new test helper module is four lines like the one in
  `test_nested_config.py`. It is suppressed block locally in the new module,
  the way the repository already handles that kind of accidental similarity.

## Step 7 — Documentation and a teaching example

Status: **Implemented, committed**

- `README.md` and `README_pypi.md`: what a reported name looks like now.
- A new `example/src/example/e42_nested_member_paths.py` and its test,
  showing a failure inside a list of nested objects and the path it reports.
  Explanatory comments, as teaching examples require.
- `example/src/example/README.md`: the section for the new example.
- `doc/api.md` and `doc/protected_api.md` regenerate from docstrings during
  the build; check that what they say about `member_name` reads well.

What was decided while implementing this step:

- **The example teaches the path by having the same member name twice.**
  `ExampleConfig42` has a `port` of its own and a `backends` list whose
  elements each have a `port`. One single validator, `port_validator()`,
  validates both, so the two diagnostics differ only by the path: `Value
  99999 for port ...` and `Value 99999 for backends[1].port ...`. A member
  name that exists in only one place would have proved nothing, because a
  plain name would have been enough for it.
- The example is deliberately *not* a second `e34`. It takes its backends
  as `host=port` command line tokens rather than as one JSON value, so it
  needed no JSON parsing helpers and does not repeat e34's code.
- One `duplicate-code` report appeared, because the `set` and `print`
  helper shape that every example in the directory shares is four lines
  like the one in `e14`. It is suppressed block locally in the new module,
  the way the repository already handles that kind of accidental
  similarity. Factoring that shape out would work against the teaching,
  because each example has to be readable on its own.
- **The `README_pypi.md` snippets had drifted from their tested sources.**
  `test_simple_readme_example.py`,
  `test_dataclass_readme_example.py` and
  `test_validated_dataclass_readme_example.py` gained `member_name` in step
  1, and the README text they are copied into did not. All three snippets
  are now verbatim copies of the tested modules again, and the same two
  snippets in `example/src/example/README.md` were synchronized with them.
- `example/src/example/README.md` still documented the pre-step-3 nested
  contract, with three constructor keywords and no `member_name`. It never
  received the step 3 update that `README_pypi.md` got. It now says the
  same thing as `README_pypi.md`.
- `README_pypi.md` gained the section *Names in diagnostics are paths*,
  which is the one place that states the notation, what carries it, that it
  is text for a person and not for a parser, and what an application that
  never adopted `member_name` loses. `README.md` states the same in two
  lines, because it is the maintainer facing readme.
- `doc/predefined_validators.md` said that a reported name carries the
  index or the key of a list or dict element. It now also says that the
  reported name is the whole path, which is what makes the roughly twenty
  validator modules report paths without being changed.
- **Fifty validator docstrings said `member_name` was "the name of the
  member".** They are the text that `doc/api.md` shows at each validator,
  which is where a reader looks, so all of them now say that it is the
  reported path. Left alone were the names that really are local: the
  declared `member_names` of a validation plan, the declared
  `pseudo_member_name`, `written_member_name`, `arg_name_member_name`, and
  the `Public parent member` arguments of `_config_nesting_io`, which step
  4 deliberately kept local while `parent_path` carries the path.
- `test_e41_hex_and_octal.py` claimed in a docstring that the diagnostic
  names `oct_str` and *not* the member holding the nested value. That
  stopped being true in step 4; the message says `file_mode.oct_str`. The
  docstring is corrected and the assertion now checks the whole path, which
  it did not before.

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

- Delete `_config_call_wrappers.py`; the calls to `parse_json`, `validate`,
  `read`, `as_json_string` and `apply` are direct again.
- Remove the introspection and the deprecation warnings for all nine call
  sites, and the `member_name` part of `_deprecated_support`.
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
