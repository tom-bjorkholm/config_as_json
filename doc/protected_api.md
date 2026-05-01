# Table of Contents

* [config\_as\_json.validator](#config_as_json.validator)
  * [InvalidConfiguration](#config_as_json.validator.InvalidConfiguration)
    * [\_\_init\_\_](#config_as_json.validator.InvalidConfiguration.__init__)
  * [\_not\_one\_of\_allowed\_values\_message](#config_as_json.validator._not_one_of_allowed_values_message)
  * [not\_one\_of\_allowed\_values](#config_as_json.validator.not_one_of_allowed_values)
  * [InvalidConfigurationValue](#config_as_json.validator.InvalidConfigurationValue)
    * [\_\_init\_\_](#config_as_json.validator.InvalidConfigurationValue.__init__)
  * [WholeConfigValidator](#config_as_json.validator.WholeConfigValidator)
    * [\_\_init\_\_](#config_as_json.validator.WholeConfigValidator.__init__)
    * [validate](#config_as_json.validator.WholeConfigValidator.validate)
  * [MemberValidator](#config_as_json.validator.MemberValidator)
    * [\_\_init\_\_](#config_as_json.validator.MemberValidator.__init__)
    * [validate\_member](#config_as_json.validator.MemberValidator.validate_member)
  * [ValidationStep](#config_as_json.validator.ValidationStep)
    * [apply](#config_as_json.validator.ValidationStep.apply)
  * [WholeConfigValidationStep](#config_as_json.validator.WholeConfigValidationStep)
    * [apply](#config_as_json.validator.WholeConfigValidationStep.apply)
  * [MemberValidationStep](#config_as_json.validator.MemberValidationStep)
    * [apply](#config_as_json.validator.MemberValidationStep.apply)
  * [string\_best\_match](#config_as_json.validator.string_best_match)
  * [StrValidator](#config_as_json.validator.StrValidator)
    * [\_\_init\_\_](#config_as_json.validator.StrValidator.__init__)
    * [validate\_member](#config_as_json.validator.StrValidator.validate_member)
  * [IntFloat](#config_as_json.validator.IntFloat)
  * [ConstraintValue](#config_as_json.validator.ConstraintValue)
  * [\_validate\_and\_get\_constraint\_value\_type](#config_as_json.validator._validate_and_get_constraint_value_type)
  * [\_ensure\_int\_float\_type](#config_as_json.validator._ensure_int_float_type)
  * [IntFloatValidator](#config_as_json.validator.IntFloatValidator)
    * [\_\_init\_\_](#config_as_json.validator.IntFloatValidator.__init__)
    * [validate\_member](#config_as_json.validator.IntFloatValidator.validate_member)
* [config\_as\_json.config\_auto\_change\_hook](#config_as_json.config_auto_change_hook)
  * [ConfigAutoChangeHook](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook)
    * [\_\_init\_\_](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.__init__)
    * [auto\_changed](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.auto_changed)
    * [old\_key\_handled](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.old_key_handled)
    * [rocf\_missing\_value\_provided](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.rocf_missing_value_provided)
    * [all\_autochanges\_done](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.all_autochanges_done)
* [config\_as\_json.config](#config_as_json.config)
  * [RocfKeyRename](#config_as_json.config.RocfKeyRename)
  * [\_ConfigEncoder](#config_as_json.config._ConfigEncoder)
    * [default](#config_as_json.config._ConfigEncoder.default)
  * [ConfigBadJson](#config_as_json.config.ConfigBadJson)
  * [\_over\_ride\_needed](#config_as_json.config._over_ride_needed)
  * [ParseConverter](#config_as_json.config.ParseConverter)
  * [Config](#config_as_json.config.Config)
    * [\_\_init\_\_](#config_as_json.config.Config.__init__)
    * [parse\_converters](#config_as_json.config.Config.parse_converters)
    * [check\_key\_match](#config_as_json.config.Config.check_key_match)
    * [check\_dict\_parse](#config_as_json.config.Config.check_dict_parse)
    * [\_json\_parse\_obj\_hook](#config_as_json.config.Config._json_parse_obj_hook)
    * [\_omit\_none\_from\_json](#config_as_json.config.Config._omit_none_from_json)
    * [\_checked\_omit\_none\_from\_json](#config_as_json.config.Config._checked_omit_none_from_json)
    * [\_rocf\_values\_for\_missing\_json\_keys](#config_as_json.config.Config._rocf_values_for_missing_json_keys)
    * [\_rocf\_apply\_missing\_values](#config_as_json.config.Config._rocf_apply_missing_values)
    * [\_rocf\_get\_json\_key\_renames](#config_as_json.config.Config._rocf_get_json_key_renames)
    * [\_rocf\_rename\_json\_key\_in\_dict](#config_as_json.config.Config._rocf_rename_json_key_in_dict)
    * [\_rocf\_rename\_json\_key\_in\_list](#config_as_json.config.Config._rocf_rename_json_key_in_list)
    * [\_rocf\_rename\_json\_keys](#config_as_json.config.Config._rocf_rename_json_keys)
    * [parse\_json](#config_as_json.config.Config.parse_json)
    * [as\_json\_string](#config_as_json.config.Config.as_json_string)
    * [read](#config_as_json.config.Config.read)
    * [write](#config_as_json.config.Config.write)
    * [check\_array\_keys](#config_as_json.config.Config.check_array_keys)
    * [check\_lst\_dict](#config_as_json.config.Config.check_lst_dict)
    * [check\_lst\_dict\_lst](#config_as_json.config.Config.check_lst_dict_lst)
    * [value\_of\_type](#config_as_json.config.Config.value_of_type)
    * [check\_array\_dicts](#config_as_json.config.Config.check_array_dicts)
    * [get\_converter\_dict](#config_as_json.config.Config.get_converter_dict)
    * [check\_no\_duplicates](#config_as_json.config.Config.check_no_duplicates)
    * [get\_validation\_plan](#config_as_json.config.Config.get_validation_plan)
    * [validate](#config_as_json.config.Config.validate)
* [config\_as\_json.str\_to\_enum](#config_as_json.str_to_enum)
  * [string\_to\_enum\_best\_match](#config_as_json.str_to_enum.string_to_enum_best_match)
* [config\_as\_json.migrate\_cfg](#config_as_json.migrate_cfg)
  * [\_match\_config\_seq](#config_as_json.migrate_cfg._match_config_seq)
  * [migrate\_cfg](#config_as_json.migrate_cfg.migrate_cfg)
* [config\_as\_json.file\_must\_exist](#config_as_json.file_must_exist)
  * [file\_must\_exist](#config_as_json.file_must_exist.file_must_exist)
* [config\_as\_json.migrate\_cfg\_warn\_hook](#config_as_json.migrate_cfg_warn_hook)
  * [MigrateCfgWarnHook](#config_as_json.migrate_cfg_warn_hook.MigrateCfgWarnHook)
    * [migrate\_instructions](#config_as_json.migrate_cfg_warn_hook.MigrateCfgWarnHook.migrate_instructions)
    * [migrate\_warn\_msg](#config_as_json.migrate_cfg_warn_hook.MigrateCfgWarnHook.migrate_warn_msg)
    * [auto\_changed](#config_as_json.migrate_cfg_warn_hook.MigrateCfgWarnHook.auto_changed)
* [config\_as\_json.discriminated\_dict\_validators](#config_as_json.discriminated_dict_validators)
  * [\_validate\_variant\_rules](#config_as_json.discriminated_dict_validators._validate_variant_rules)
  * [DictVariant](#config_as_json.discriminated_dict_validators.DictVariant)
    * [\_\_post\_init\_\_](#config_as_json.discriminated_dict_validators.DictVariant.__post_init__)
  * [\_validate\_discriminator\_key](#config_as_json.discriminated_dict_validators._validate_discriminator_key)
  * [\_validate\_variants](#config_as_json.discriminated_dict_validators._validate_variants)
  * [\_validate\_optional\_discriminator\_validator](#config_as_json.discriminated_dict_validators._validate_optional_discriminator_validator)
  * [\_variant\_mandatory\_keys](#config_as_json.discriminated_dict_validators._variant_mandatory_keys)
  * [\_raise\_missing\_discriminator](#config_as_json.discriminated_dict_validators._raise_missing_discriminator)
  * [\_variant\_for\_discriminator\_value](#config_as_json.discriminated_dict_validators._variant_for_discriminator_value)
  * [DiscriminatedDictValidator](#config_as_json.discriminated_dict_validators.DiscriminatedDictValidator)
    * [\_\_init\_\_](#config_as_json.discriminated_dict_validators.DiscriminatedDictValidator.__init__)
    * [\_validate\_discriminator](#config_as_json.discriminated_dict_validators.DiscriminatedDictValidator._validate_discriminator)
    * [validate\_member](#config_as_json.discriminated_dict_validators.DiscriminatedDictValidator.validate_member)
* [config\_as\_json.csv\_dialect](#config_as_json.csv_dialect)
  * [CsvDialectConfig](#config_as_json.csv_dialect.CsvDialectConfig)
  * [\_csv\_dialect\_from\_name](#config_as_json.csv_dialect._csv_dialect_from_name)
  * [\_csv\_quoting\_from\_name](#config_as_json.csv_dialect._csv_quoting_from_name)
  * [get\_csv\_dialect](#config_as_json.csv_dialect.get_csv_dialect)
  * [\_invalid\_csv\_dialect](#config_as_json.csv_dialect._invalid_csv_dialect)
  * [\_validate\_csv\_dialect\_key](#config_as_json.csv_dialect._validate_csv_dialect_key)
  * [\_validate\_csv\_dialect\_value](#config_as_json.csv_dialect._validate_csv_dialect_value)
  * [\_normalized\_csv\_dialect\_config](#config_as_json.csv_dialect._normalized_csv_dialect_config)
  * [CsvDialectValidator](#config_as_json.csv_dialect.CsvDialectValidator)
    * [validate\_member](#config_as_json.csv_dialect.CsvDialectValidator.validate_member)
* [config\_as\_json.projected\_validators](#config_as_json.projected_validators)
  * [\_validate\_projector](#config_as_json.projected_validators._validate_projector)
  * [\_validate\_optional\_source\_validator](#config_as_json.projected_validators._validate_optional_source_validator)
  * [\_validate\_projected\_validators](#config_as_json.projected_validators._validate_projected_validators)
  * [ProjectedMemberValidator](#config_as_json.projected_validators.ProjectedMemberValidator)
    * [\_\_init\_\_](#config_as_json.projected_validators.ProjectedMemberValidator.__init__)
    * [validate\_member](#config_as_json.projected_validators.ProjectedMemberValidator.validate_member)
* [config\_as\_json.dict\_validators](#config_as_json.dict_validators)
  * [\_validate\_dict\_member\_value](#config_as_json.dict_validators._validate_dict_member_value)
  * [\_validate\_string\_keys](#config_as_json.dict_validators._validate_string_keys)
  * [\_inner\_member\_name](#config_as_json.dict_validators._inner_member_name)
  * [DictKeysValidator](#config_as_json.dict_validators.DictKeysValidator)
    * [\_\_init\_\_](#config_as_json.dict_validators.DictKeysValidator.__init__)
    * [validate\_member](#config_as_json.dict_validators.DictKeysValidator.validate_member)
  * [DictRule](#config_as_json.dict_validators.DictRule)
    * [\_\_post\_init\_\_](#config_as_json.dict_validators.DictRule.__post_init__)
  * [\_validate\_for\_each\_rules](#config_as_json.dict_validators._validate_for_each_rules)
  * [DictForEachValidator](#config_as_json.dict_validators.DictForEachValidator)
    * [\_\_init\_\_](#config_as_json.dict_validators.DictForEachValidator.__init__)
    * [validate\_member](#config_as_json.dict_validators.DictForEachValidator.validate_member)
* [config\_as\_json.file\_extension](#config_as_json.file_extension)
  * [fix\_file\_extension](#config_as_json.file_extension.fix_file_extension)
* [config\_as\_json.char\_encoding](#config_as_json.char_encoding)
  * [valid\_char\_encoding](#config_as_json.char_encoding.valid_char_encoding)
  * [check\_char\_encoding](#config_as_json.char_encoding.check_char_encoding)
  * [CharEncodingValidator](#config_as_json.char_encoding.CharEncodingValidator)
    * [validate\_member](#config_as_json.char_encoding.CharEncodingValidator.validate_member)
* [config\_as\_json.config\_factory](#config_as_json.config_factory)
  * [MatchConfig](#config_as_json.config_factory.MatchConfig)
    * [match\_func](#config_as_json.config_factory.MatchConfig.match_func)
    * [config\_class](#config_as_json.config_factory.MatchConfig.config_class)
  * [\_config\_factory\_get\_text](#config_as_json.config_factory._config_factory_get_text)
  * [\_config\_factory\_exit](#config_as_json.config_factory._config_factory_exit)
  * [JsonValueMatcher](#config_as_json.config_factory.JsonValueMatcher)
    * [\_\_init\_\_](#config_as_json.config_factory.JsonValueMatcher.__init__)
    * [\_\_call\_\_](#config_as_json.config_factory.JsonValueMatcher.__call__)
    * [compare\_value](#config_as_json.config_factory.JsonValueMatcher.compare_value)
  * [config\_factory\_from\_json](#config_as_json.config_factory.config_factory_from_json)
* [config\_as\_json.list\_validators](#config_as_json.list_validators)
  * [Basictype](#config_as_json.list_validators.Basictype)
  * [\_validate\_supported\_list\_element\_type](#config_as_json.list_validators._validate_supported_list_element_type)
  * [\_validate\_list\_size\_bounds](#config_as_json.list_validators._validate_list_size_bounds)
  * [\_validate\_list\_member\_value](#config_as_json.list_validators._validate_list_member_value)
  * [\_validate\_typed\_list\_member](#config_as_json.list_validators._validate_typed_list_member)
  * [\_sort\_list\_values](#config_as_json.list_validators._sort_list_values)
  * [\_unique\_list\_values](#config_as_json.list_validators._unique_list_values)
  * [\_validate\_list\_order](#config_as_json.list_validators._validate_list_order)
  * [\_validate\_unique\_list\_values](#config_as_json.list_validators._validate_unique_list_values)
  * [\_indexed\_not\_one\_of\_allowed\_values](#config_as_json.list_validators._indexed_not_one_of_allowed_values)
  * [\_IndexedInvalidConfigurationValue](#config_as_json.list_validators._IndexedInvalidConfigurationValue)
    * [\_\_init\_\_](#config_as_json.list_validators._IndexedInvalidConfigurationValue.__init__)
  * [ListValueValidator](#config_as_json.list_validators.ListValueValidator)
    * [\_\_init\_\_](#config_as_json.list_validators.ListValueValidator.__init__)
    * [validate\_member](#config_as_json.list_validators.ListValueValidator.validate_member)
  * [ListSizeValidator](#config_as_json.list_validators.ListSizeValidator)
    * [\_\_init\_\_](#config_as_json.list_validators.ListSizeValidator.__init__)
    * [validate\_member](#config_as_json.list_validators.ListSizeValidator.validate_member)
  * [ListIsOrderedValidator](#config_as_json.list_validators.ListIsOrderedValidator)
    * [\_\_init\_\_](#config_as_json.list_validators.ListIsOrderedValidator.__init__)
    * [validate\_member](#config_as_json.list_validators.ListIsOrderedValidator.validate_member)
  * [ListOrderingValidator](#config_as_json.list_validators.ListOrderingValidator)
    * [\_\_init\_\_](#config_as_json.list_validators.ListOrderingValidator.__init__)
    * [validate\_member](#config_as_json.list_validators.ListOrderingValidator.validate_member)
  * [\_validate\_for\_each\_element\_validators](#config_as_json.list_validators._validate_for_each_element_validators)
  * [\_validate\_for\_each\_element\_type](#config_as_json.list_validators._validate_for_each_element_type)
  * [ListForEachValidator](#config_as_json.list_validators.ListForEachValidator)
    * [\_\_init\_\_](#config_as_json.list_validators.ListForEachValidator.__init__)
    * [\_validate\_element\_type](#config_as_json.list_validators.ListForEachValidator._validate_element_type)
    * [validate\_member](#config_as_json.list_validators.ListForEachValidator.validate_member)
* [config\_as\_json.assert\_dict\_equal](#config_as_json.assert_dict_equal)
  * [\_print\_dict\_differs](#config_as_json.assert_dict_equal._print_dict_differs)
  * [assert\_dict\_equal](#config_as_json.assert_dict_equal.assert_dict_equal)

<a id="config_as_json.validator"></a>

# config\_as\_json.validator

Classes to validate a Config object or field in a Config object.

<a id="config_as_json.validator.InvalidConfiguration"></a>

## InvalidConfiguration Objects

```python
class InvalidConfiguration(ValueError)
```

Raised when a validation check on a configuration fails.

<a id="config_as_json.validator.InvalidConfiguration.__init__"></a>

#### \_\_init\_\_

```python
def __init__(message: str) -> None
```

Initialize the exception.

<a id="config_as_json.validator._not_one_of_allowed_values_message"></a>

#### \_not\_one\_of\_allowed\_values\_message

```python
def _not_one_of_allowed_values_message(
        member_name: str,
        member_value: object,
        allowed_values: Sequence[object],
        stderr_file: Optional[TextIO],
        member_index: Optional[int] = None) -> str
```

Construct an allowed-values error message and optionally print it.

**Arguments**:

- `member_name` - The name of the member that has the invalid value.
- `member_value` - The invalid value of the member.
- `allowed_values` - The allowed values for the member.
- `stderr_file` - The file to optionally write error messages to.
  If set to ``None`` explicitly, printing is suppressed.
- `member_index` - Optional index of the invalid element in a list value.


**Returns**:

  A string containing the error message.

<a id="config_as_json.validator.not_one_of_allowed_values"></a>

#### not\_one\_of\_allowed\_values

```python
def not_one_of_allowed_values(member_name: str, member_value: object,
                              allowed_values: Sequence[object],
                              stderr_file: Optional[TextIO]) -> str
```

Construct a message that a value is not one of the allowed values.

If ``stderr_file`` is not ``None``, the message is written to it.

This helper is special: passing ``stderr_file`` as ``None`` explicitly
suppresses printing while still returning the constructed message.

**Arguments**:

- `member_name` - The name of the member that has the invalid value.
- `member_value` - The invalid value of the member.
- `allowed_values` - The allowed values for the member.
- `stderr_file` - The file to optionally write error messages to.
  If set to ``None`` explicitly, printing is suppressed.


**Returns**:

  A string containing the error message.

<a id="config_as_json.validator.InvalidConfigurationValue"></a>

## InvalidConfigurationValue Objects

```python
class InvalidConfigurationValue(InvalidConfiguration)
```

Raised when a configuration value is not one of the allowed values.

<a id="config_as_json.validator.InvalidConfigurationValue.__init__"></a>

#### \_\_init\_\_

```python
def __init__(member_name: str, member_value: object,
             allowed_values: Sequence[object]) -> None
```

Initialize the exception.

<a id="config_as_json.validator.WholeConfigValidator"></a>

## WholeConfigValidator Objects

```python
class WholeConfigValidator(ABC)
```

Base class for validators that validate a complete Config object.

<a id="config_as_json.validator.WholeConfigValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__() -> None
```

Initialize the validator.

<a id="config_as_json.validator.WholeConfigValidator.validate"></a>

#### validate

```python
@abstractmethod
def validate(config: 'Config', stderr_file: TextIO = sys.stderr) -> None
```

Validate an aspect of the entire Config object.

The validate method must be implemented in a derived class.
The validator shall validate the entire Config object. If the
validation check fails, the error message shall be written to
``stderr_file`` before the exception is raised.
This method may mutate the Config object directly if needed
to normalize the configuration.

**Raises**:

- `InvalidConfiguration` - The configuration is invalid.
- `InvalidConfigurationValue` - The value of a configuration member is
  not one of the allowed values.


**Arguments**:

- `config` - The Config object to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  None if the validation check passes, otherwise the exception
  is raised.

<a id="config_as_json.validator.MemberValidator"></a>

## MemberValidator Objects

```python
class MemberValidator(ABC)
```

Base class for validators that validate one Config member.

<a id="config_as_json.validator.MemberValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__() -> None
```

Initialize the validator.

<a id="config_as_json.validator.MemberValidator.validate_member"></a>

#### validate\_member

```python
@abstractmethod
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate an aspect of the Config object for one member.

The validate_member method must be implemented in a derived class.
It shall validate a specific member of the Config object, and
``member_value`` is the value of that member. If the validation check
fails, the error message shall be written to ``stderr_file`` before
the exception is raised.

**Raises**:

- `InvalidConfiguration` - The configuration is invalid.
- `InvalidConfigurationValue` - The value of a configuration member is
  not one of the allowed values.


**Arguments**:

- `config` - The complete Config object (might be needed if the
  validator needs to access other members of the Config
  object).
- `member_name` - The name of the member to validate.
- `member_value` - The value of the member to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  A normalized value if the validation check passes,
  otherwise the exception is raised. This returned value will be
  used as the value of the member in the Config object.
  Return the original value if you only validate and do not want
  to change the value of the member in the Config object.
  The returned value is used as the new member value, even if it is
  ``None``.

<a id="config_as_json.validator.ValidationStep"></a>

## ValidationStep Objects

```python
class ValidationStep(ABC)
```

Base class for one ordered validation step.

<a id="config_as_json.validator.ValidationStep.apply"></a>

#### apply

```python
@abstractmethod
def apply(config: 'Config', stderr_file: TextIO = sys.stderr) -> None
```

Apply the validation step to one Config object.

**Arguments**:

- `config` - The Config object to validate.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `NotImplementedError` - A derived validation step did not implement
  this method.

<a id="config_as_json.validator.WholeConfigValidationStep"></a>

## WholeConfigValidationStep Objects

```python
@dataclass
class WholeConfigValidationStep(ValidationStep)
```

Validation step that applies one whole-config validator.

**Attributes**:

- `validator` - Validator that receives the whole Config object.

<a id="config_as_json.validator.WholeConfigValidationStep.apply"></a>

#### apply

```python
def apply(config: 'Config', stderr_file: TextIO = sys.stderr) -> None
```

Apply the whole-config validator to the Config object.

**Arguments**:

- `config` - The Config object to validate.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - The supplied validator rejects the
  configuration.
- `InvalidConfigurationValue` - The supplied validator rejects one
  configuration value.

<a id="config_as_json.validator.MemberValidationStep"></a>

## MemberValidationStep Objects

```python
@dataclass
class MemberValidationStep(ValidationStep)
```

Validation step that applies one member validator.

**Attributes**:

- `member_names` - Config member names to validate in order.
- `validator` - Validator that receives each named member value.

<a id="config_as_json.validator.MemberValidationStep.apply"></a>

#### apply

```python
def apply(config: 'Config', stderr_file: TextIO = sys.stderr) -> None
```

Apply the member validator to each named member.

**Arguments**:

- `config` - The Config object to validate.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `AttributeError` - One member name is not present on ``config``.
- `InvalidConfiguration` - The supplied validator rejects the
  configuration.
- `InvalidConfigurationValue` - The supplied validator rejects one
  configuration value.

<a id="config_as_json.validator.string_best_match"></a>

#### string\_best\_match

```python
def string_best_match(value: str,
                      allowed_values: Sequence[str],
                      member_name: str,
                      stderr_file: TextIO = sys.stderr) -> str
```

Return the best match for a string value from a list of allowed values.

The helper first accepts a direct match among ``value`` and a few common
case variants. If that fails, it accepts a unique prefix match ignoring
case.

**Arguments**:

- `value` - The value to match.
- `allowed_values` - The allowed values to match against.
- `member_name` - The name of the member to validate used in any
  error message.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The best match for the value from the allowed values.


**Raises**:

- `InvalidConfiguration` - The value is not a string.
- `InvalidConfigurationValue` - The value is not one of the allowed values.

<a id="config_as_json.validator.StrValidator"></a>

## StrValidator Objects

```python
class StrValidator(  # pylint: disable=too-few-public-methods
        MemberValidator)
```

Validate one string member against allowed string values.

<a id="config_as_json.validator.StrValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(allowed_values: Sequence[str] | Callable[[], Sequence[str]],
             ignore_case: bool,
             best_match: bool = False,
             normalize: bool = False) -> None
```

Initialize the validator.

**Arguments**:

- `allowed_values` - The allowed values for the string member.
- `ignore_case` - Whether to ignore case when validating the
  string member.
- `best_match` - Whether to return the best match for the string
  member if the value is not one of the allowed values.
  The best match includes a unique prefix match ignoring
  case. In this case, the returned value from
  validate_member will be the best match (or an
  exception if no best match is found).
- `normalize` - Whether to normalize the string member to one of the
  allowed values.

<a id="config_as_json.validator.StrValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate the aspect of the Config object for a specific str member.

**Raises**:

- `InvalidConfiguration` - The configuration is invalid.
- `InvalidConfigurationValue` - The value of a configuration member is
  not one of the allowed values.


**Arguments**:

- `config` - The Config object to validate.
- `member_name` - The name of the member to validate.
- `member_value` - The value of the member to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  A normalized value if the validation check passes, otherwise
  an exception is raised.
  Returns the original value when only validated and does not want
  to change the value of the member in the Config object.
  When ``best_match`` is used, the returned value is the matched
  entry from ``allowed_values``. This can normalize the member value
  even when ``normalize`` is ``False``.

<a id="config_as_json.validator.IntFloat"></a>

#### IntFloat

Numeric type accepted by IntFloatValidator.

<a id="config_as_json.validator.ConstraintValue"></a>

#### ConstraintValue

Value type used when validating shared constraint arguments.

<a id="config_as_json.validator._validate_and_get_constraint_value_type"></a>

#### \_validate\_and\_get\_constraint\_value\_type

```python
def _validate_and_get_constraint_value_type(
    min_value: Optional[ConstraintValue],
    max_value: Optional[ConstraintValue],
    allowed_values: Optional[Sequence[ConstraintValue]],
    lt_comparator: Callable[[ConstraintValue, ConstraintValue],
                            bool] = lambda x, y: x < y
) -> type[ConstraintValue]
```

Validate shared constructor constraints and return their type.

The helper validates the common constructor arguments used by validators
that support lower bounds, upper bounds, and allowed-values membership.
It infers one runtime type from the provided constraints and verifies
that all provided constraint values are instances of that type.

**Arguments**:

- `min_value` - Optional minimum allowed value.
- `max_value` - Optional maximum allowed value.
- `allowed_values` - Optional allowed values.
- `lt_comparator` - Comparator used when checking that ``min_value`` is
  not greater than ``max_value``.


**Returns**:

  The inferred runtime type shared by all provided constraint values.


**Raises**:

- `ValueError` - If no constraints are provided.
- `ValueError` - If ``allowed_values`` is provided as an empty sequence.
- `ValueError` - If ``min_value`` is greater than ``max_value``.
- `TypeError` - If provided constraints use incompatible runtime types.

<a id="config_as_json.validator._ensure_int_float_type"></a>

#### \_ensure\_int\_float\_type

```python
def _ensure_int_float_type(value_type: type[object]) -> None
```

Reject unsupported runtime types for IntFloatValidator.

<a id="config_as_json.validator.IntFloatValidator"></a>

## IntFloatValidator Objects

```python
class IntFloatValidator(  # pylint: disable=too-few-public-methods
        MemberValidator, Generic[IntFloat])
```

Validate one int or float member against numeric constraints.

<a id="config_as_json.validator.IntFloatValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(min_value: Optional[IntFloat], max_value: Optional[IntFloat],
             allowed_values: Optional[Sequence[IntFloat]]) -> None
```

Initialize the validator.

The validator checks that the member value has one runtime type,
either ``int`` or ``float``. The value must satisfy every configured
constraint: lower bound, upper bound, and allowed-values membership.
At least one of min_value, max_value, or allowed_values must be
provided.

**Arguments**:

- `min_value` - Minimum allowed member value.
  If ``None``, no minimum value is checked.
- `max_value` - Maximum allowed member value.
  If ``None``, no maximum value is checked.
- `allowed_values` - The only allowed values for the member.
  If ``None``, no allowed-values check is done.


**Raises**:

- `ValueError` - If no constraints are provided.
- `ValueError` - If allowed_values is provided as an empty sequence.
- `ValueError` - If min_value is greater than max_value.
- `TypeError` - If unsupported or mixed runtime types are used.

<a id="config_as_json.validator.IntFloatValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate the aspect of the Config object for a specific member.

**Arguments**:

- `config` - The Config object to validate.
- `member_name` - The name of the member to validate.
- `member_value` - The value of the member to validate.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - The configuration is invalid.
- `InvalidConfigurationValue` - The value of a configuration member is
  not one of the allowed values.

**Returns**:

  The member value if the validation check passes, otherwise
  an exception is raised.

<a id="config_as_json.config_auto_change_hook"></a>

# config\_as\_json.config\_auto\_change\_hook

Define callbacks for automatic configuration adjustments.

Hooks let an application learn that configuration input needed help while it
was parsed, for example because a missing optional key received a default
value or because an old key name was transparently mapped to a new one.

<a id="config_as_json.config_auto_change_hook.ConfigAutoChangeHook"></a>

## ConfigAutoChangeHook Objects

```python
class ConfigAutoChangeHook()
```

Collect and report automatic configuration changes during parsing.

Applications that want to react when configuration data is normalized
should derive from this class and pass an instance to ``Config``.

<a id="config_as_json.config_auto_change_hook.ConfigAutoChangeHook.__init__"></a>

#### \_\_init\_\_

```python
def __init__() -> None
```

Initialize empty change tracking state.

<a id="config_as_json.config_auto_change_hook.ConfigAutoChangeHook.auto_changed"></a>

#### auto\_changed

```python
def auto_changed(old_keys_handled: list[str], rocf_vals_handled: list[str],
                 stderr_file: TextIO) -> None
```

React after parsing finished with one or more automatic changes.

Derived classes override this method to log, warn, or otherwise react
when configuration input was normalized.

**Arguments**:

- `old_keys_handled` - Old key names that were accepted and mapped
  onto their current names during Reading an Old Configuration
  File (ROCF).
- `rocf_vals_handled` - Keys that were filled with default values during
  parsing during Reading an Old Configuration File (ROCF).
- `stderr_file` - Stream used for user-facing diagnostics.

<a id="config_as_json.config_auto_change_hook.ConfigAutoChangeHook.old_key_handled"></a>

#### old\_key\_handled

```python
def old_key_handled(old_key: str) -> None
```

Record that one legacy key name was accepted and remapped.

**Arguments**:

- `old_key` - Legacy key name that was handled.

<a id="config_as_json.config_auto_change_hook.ConfigAutoChangeHook.rocf_missing_value_provided"></a>

#### rocf\_missing\_value\_provided

```python
def rocf_missing_value_provided(rocf_val_key: str) -> None
```

Record that parsing supplied a default value for one key.

**Arguments**:

- `rocf_val_key` - Key that was absent from input and received a default
  value during Reading an Old Configuration File (ROCF).

<a id="config_as_json.config_auto_change_hook.ConfigAutoChangeHook.all_autochanges_done"></a>

#### all\_autochanges\_done

```python
def all_autochanges_done(stderr_file: TextIO) -> None
```

Notify the hook once all automatic changes have been collected.

The default implementation calls :meth:`auto_changed` once if at
least one automatic change was recorded.

**Arguments**:

- `stderr_file` - Stream used for user-facing diagnostics.

<a id="config_as_json.config"></a>

# config\_as\_json.config

Implement the core configuration model for config-as-json.

Applications derive from :class:`Config`, create one instance attribute for
each supported configuration setting, and use those attribute values as the
default configuration. Each such configuration setting can also have a value
type of dict or list, or even a nested dict or list.
The base class then provides JSON serialization, parsing, schema-like key
checks, omit-when-None handling, old-file migration helpers, and a collection
of validation helpers for common patterns.

<a id="config_as_json.config.RocfKeyRename"></a>

#### RocfKeyRename

Describe a configuration key rename from an old name to a new name.

Renaming rule for Reading Old Configuration File (ROCF).
Used by derived classes to describe key names in old configuration files
that should be mapped onto their current names during parsing of an old
configuration file.

<a id="config_as_json.config._ConfigEncoder"></a>

## \_ConfigEncoder Objects

```python
class _ConfigEncoder(json.JSONEncoder)
```

Encode configuration objects with enum values stored as names.

<a id="config_as_json.config._ConfigEncoder.default"></a>

#### default

```python
def default(o: object) -> object
```

Serialize enum members using their symbolic names.

**Arguments**:

- `o` - Object supplied by ``json.dumps`` for custom encoding.


**Returns**:

  The JSON-serializable representation of ``o``.


**Raises**:

- `TypeError` - The object cannot be serialized by this encoder or its
  base implementation.

<a id="config_as_json.config.ConfigBadJson"></a>

## ConfigBadJson Objects

```python
class ConfigBadJson(json.JSONDecodeError)
```

Report JSON input that could not be interpreted as configuration.

<a id="config_as_json.config._over_ride_needed"></a>

#### \_over\_ride\_needed

```python
def _over_ride_needed(stri: str) -> Any
```

Act as a placeholder conversion function for incomplete subclasses.

The base :meth:`Config.parse_converters` implementation uses this helper
to make missing converter customization obvious. Subclasses that need to
coerce parsed JSON values should override ``parse_converters`` and return
real conversion recipes.

**Arguments**:

- `stri` - Parsed JSON value that needs conversion.


**Returns**:

  A sentinel value only in the degenerate case where no conversion was
  actually needed.


**Raises**:

- `NotImplementedError` - A subclass relied on the placeholder converter
  for a real conversion.

<a id="config_as_json.config.ParseConverter"></a>

#### ParseConverter

Describe how one parsed JSON value should be converted after loading.

<a id="config_as_json.config.Config"></a>

## Config Objects

```python
class Config()
```

Base class for application-specific JSON-backed configuration models.

A derived class declares the supported configuration schema by assigning
instance attributes before calling ``super().__init__``. Those initial
attribute values form the default configuration. The base class can then
read JSON into the object, write the current values back to JSON, omit
selected ``None`` values, and apply controlled old-file migration helpers.

For each configuration attribute that holds a ``dict``, the base class
recursively checks parsed JSON against the default: unknown keys in the
file are rejected, and (depending on the load path) required keys from the
default may need to be present. That built-in check covers many fixed dict
shapes and avoids extra application code. List a dict member's name in
``_unchecked_dicts`` to skip that check for that member and let validators
such as ``DictKeysValidator`` and ``DictForEachValidator`` define more
flexible or more complex key and value policy instead. See
``DictKeysValidator`` in ``dict_validators`` for how that interacts with
this check.

<a id="config_as_json.config.Config.__init__"></a>

#### \_\_init\_\_

```python
def __init__(from_json_data_text: Optional[str],
             from_json_filename: Optional[PathOrStr],
             auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
             stderr_file: TextIO = sys.stderr) -> None
```

Initialize a derived configuration object.

A derived ``__init__`` is expected to assign every supported
configuration attribute before calling this constructor. If neither
JSON source argument is supplied, those attribute values remain in
place as the default configuration. If a JSON source is supplied, the
parsed data is applied to the same attributes instead.

**Arguments**:

- `from_json_data_text` - Optional JSON text to parse directly.
- `from_json_filename` - Optional path to a JSON file to read.
- `auto_ch_hook` - Hook that is notified about automatic changes such
  as filled values or renamed keys when reading old
  configuration files.
- `stderr_file` - Stream used for user-facing diagnostics.

  Dict-valued members are checked against the default key set by the
  base class unless listed in ``_unchecked_dicts``; see the class
  docstring.


**Raises**:

- `AttributeError` - The derived class did not declare any public
  configuration attributes before calling ``super().__init__``.
- `TypeError` - ``_unchecked_dicts`` exists but is not a list.
- `ValueError` - Both JSON text and a JSON file were supplied.
- `KeyError` - Parsed data is missing required keys or contains
  unexpected keys.
- `ConfigBadJson` - The supplied JSON could not be decoded or converted
  into the expected configuration structure.
- `NotImplementedError` - The derived class did not implement
  ``get_validation_plan``.

<a id="config_as_json.config.Config.parse_converters"></a>

#### parse\_converters

```python
def parse_converters() -> Optional[dict[str, ParseConverter]]
```

Return post-load conversion rules for parsed JSON values.

Derived classes override this method when some keys should accept a
JSON representation that needs conversion into a richer Python type,
for example turning enum names into enum members.

**Returns**:

  A mapping from JSON key name to a :class:`ParseConverter`
  describing the expected parsed type, the conversion callable, and
  keyword arguments passed to that callable.

<a id="config_as_json.config.Config.check_key_match"></a>

#### check\_key\_match

```python
@staticmethod
def check_key_match(expected_keys: list[str],
                    j_keys: list[str],
                    ok_to_use_defaults: bool,
                    stderr_file: TextIO,
                    allowed_missing_keys: Optional[list[str]] = None) -> None
```

Validate that parsed keys match the declared configuration keys.

**Arguments**:

- `expected_keys` - Keys declared by the configuration object.
- `j_keys` - Keys found in parsed JSON data.
- `ok_to_use_defaults` - Whether missing declared keys may fall back to
  defaults supplied by the configuration object.
- `stderr_file` - Stream used for user-facing diagnostics.
- `allowed_missing_keys` - Keys that may be omitted even when
  ``ok_to_use_defaults`` is false.


**Raises**:

- `KeyError` - The JSON data is missing a required key or contains an
  unexpected key.

<a id="config_as_json.config.Config.check_dict_parse"></a>

#### check\_dict\_parse

```python
@staticmethod
def check_dict_parse(self_data: dict[str, Any], json_data: dict[str, Any],
                     key: str, ok_to_use_defaults: bool,
                     unchecked_dicts: list[str], stderr_file: TextIO) -> None
```

Recursively validate nested dictionaries against default values.

**Arguments**:

- `self_data` - Default value currently stored on the configuration
  object.
- `json_data` - Parsed JSON value for the same key.
- `key` - Name of the configuration key being checked.
- `ok_to_use_defaults` - Whether missing nested keys may use defaults.
- `unchecked_dicts` - Keys whose nested dictionary contents should not
  be validated recursively.
- `stderr_file` - Stream used for user-facing diagnostics.


**Raises**:

- `KeyError` - The JSON structure for the key does not match the
  expected dictionary shape.

<a id="config_as_json.config.Config._json_parse_obj_hook"></a>

#### \_json\_parse\_obj\_hook

```python
def _json_parse_obj_hook(indict: dict[str, Any]) -> dict[str, Any]
```

Apply configured post-load conversions to one decoded JSON object.

**Arguments**:

- `indict` - Dictionary produced by ``json.loads``.


**Returns**:

  A copy of ``indict`` where configured keys have been converted to
  their intended Python representation.

<a id="config_as_json.config.Config._omit_none_from_json"></a>

#### \_omit\_none\_from\_json

```python
def _omit_none_from_json() -> list[str]
```

Return keys omitted from JSON when their value is ``None``.

Derived classes override this method when a top-level public
configuration member is intentionally optional. Such members may be
absent from JSON input. They keep their constructor value of ``None``
when absent, explicit JSON ``null`` is read as ``None``, and writing
the configuration omits them while their value is still ``None``.

**Returns**:

  A list of public member names that use omit-when-None behavior.

<a id="config_as_json.config.Config._checked_omit_none_from_json"></a>

#### \_checked\_omit\_none\_from\_json

```python
def _checked_omit_none_from_json(self_keys: list[str],
                                 check_default_values: bool) -> list[str]
```

Return validated omit-when-None member names.

**Arguments**:

- `self_keys` - Public configuration member names on this object.
- `check_default_values` - Whether listed members must currently have
  the value ``None``.


**Returns**:

  The keys returned by :meth:`_omit_none_from_json`.


**Raises**:

- `TypeError` - The hook returned a value with the wrong type.
- `KeyError` - The hook listed an unknown public member.
- `ValueError` - A listed member did not default to ``None``.

<a id="config_as_json.config.Config._rocf_values_for_missing_json_keys"></a>

#### \_rocf\_values\_for\_missing\_json\_keys

```python
def _rocf_values_for_missing_json_keys() -> dict[str, JsonType]
```

Return values for missing JSON keys.

When Reading an Old Configuration File (ROCF), some now existing
and mandatory keys may be missing in the JSON input from the
old configuration file. This method returns the values that should
be supplied for these missing keys.

**Returns**:

  A mapping from missing key name to the value that should
  be supplied when the key is absent from JSON input.

<a id="config_as_json.config.Config._rocf_apply_missing_values"></a>

#### \_rocf\_apply\_missing\_values

```python
def _rocf_apply_missing_values(json_data: dict[str, JsonType]) -> None
```

Apply values for missing JSON keys to the configuration object.

When Reading an Old Configuration File (ROCF), some now existing
and mandatory keys may be missing in the JSON input from the
old configuration file. This method applies the values that should
be supplied for these missing keys to the configuration object.

**Arguments**:

- `json_data` - Parsed JSON object that will be applied to the
  configuration instance.

<a id="config_as_json.config.Config._rocf_get_json_key_renames"></a>

#### \_rocf\_get\_json\_key\_renames

```python
def _rocf_get_json_key_renames() -> list[RocfKeyRename]
```

Return configuration key renames for Reading Old Configuration File.

Derived classes override this method to describe key names
in old configuration files that should be mapped onto their current
names during parsing of an old configuration file.

**Returns**:

  A list of ``RocfKeyRename`` entries describing accepted key
  renames.

<a id="config_as_json.config.Config._rocf_rename_json_key_in_dict"></a>

#### \_rocf\_rename\_json\_key\_in\_dict

```python
@staticmethod
def _rocf_rename_json_key_in_dict(rename: RocfKeyRename,
                                  json_data: dict[str, JsonType],
                                  stderr_file: TextIO = sys.stderr) -> bool
```

Apply one ROCF key rename in a nested dictionary.

**Arguments**:

- `rename` - ROCT old to new key mapping to apply.
- `json_data` - Parsed JSON dictionary to update in place.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  ``True`` if the old key name was found and replaced anywhere in
  ``json_data``, otherwise ``False``.

<a id="config_as_json.config.Config._rocf_rename_json_key_in_list"></a>

#### \_rocf\_rename\_json\_key\_in\_list

```python
@staticmethod
def _rocf_rename_json_key_in_list(rename: RocfKeyRename,
                                  json_data: list[JsonType],
                                  stderr_file: TextIO = sys.stderr) -> bool
```

Apply one ROCF key rename inside nested lists.

**Arguments**:

- `rename` - ROCF old to new key mapping to apply.
- `json_data` - Parsed JSON list to walk recursively.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  ``True`` if the old key name was found and replaced anywhere in
  ``json_data``, otherwise ``False``.

<a id="config_as_json.config.Config._rocf_rename_json_keys"></a>

#### \_rocf\_rename\_json\_keys

```python
def _rocf_rename_json_keys(json_data: dict[str, JsonType],
                           stderr_file: TextIO) -> None
```

Apply all declared ROCF key renames in place.

When Reading an Old Configuration File (ROCF), some key names in the
JSON input from the old configuration file may need to be mapped onto
their current names during parsing of an old configuration file.
This method applies all declared ROCF key renames in place.

**Arguments**:

- `json_data` - Parsed JSON object to normalize before validation.
- `stderr_file` - Stream used for user-facing diagnostics.

<a id="config_as_json.config.Config.parse_json"></a>

#### parse\_json

```python
def parse_json(from_json_text: str,
               ok_to_use_defaults: bool = False,
               stderr_file: TextIO = sys.stderr) -> None
```

Parse JSON text and apply it to the configuration object.

**Arguments**:

- `from_json_text` - JSON document describing configuration values.
- `ok_to_use_defaults` - Whether missing declared keys may remain at
  their already assigned default values.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.


**Raises**:

- `ConfigBadJson` - The text is not valid configuration JSON.
- `KeyError` - The parsed configuration does not match the declared
  keys or nested dictionary structure.
- `NotImplementedError` - A required custom converter was not supplied
  by a derived class.

<a id="config_as_json.config.Config.as_json_string"></a>

#### as\_json\_string

```python
def as_json_string(stderr_file: TextIO) -> str
```

Serialize the current configuration object to formatted JSON.

**Arguments**:

- `stderr_file` - Stream used for user-facing diagnostics during
  validation.


**Returns**:

  A JSON document containing every public, non-callable instance
  attribute on the configuration object.

<a id="config_as_json.config.Config.read"></a>

#### read

```python
def read(from_json_filename: PathOrStr,
         ok_to_use_defaults: bool = False,
         stderr_file: TextIO = sys.stderr) -> None
```

Read configuration JSON from a file and apply it to the object.

**Arguments**:

- `from_json_filename` - File containing configuration JSON.
- `ok_to_use_defaults` - Whether missing declared keys may remain at
  their already assigned default values.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.

<a id="config_as_json.config.Config.write"></a>

#### write

```python
def write(to_json_filename: PathOrStr,
          stderr_file: TextIO = sys.stderr) -> None
```

Write the current configuration to a JSON file.

**Arguments**:

- `to_json_filename` - Destination file that should receive the
  formatted JSON document.
- `stderr_file` - Stream used for user-facing diagnostics during
  validation.

<a id="config_as_json.config.Config.check_array_keys"></a>

#### check\_array\_keys

```python
@staticmethod
def check_array_keys(name_of_cfg: str,
                     array: Sequence[Mapping[str, Any]],
                     mandatory_keys: list[str],
                     allowed_keys: Optional[list[str]] = None,
                     stderr_file: TextIO = sys.stderr) -> None
```

Validate keys in a list of mapping objects.

Every mapping in ``array`` must contain all keys in
``mandatory_keys`` and may only contain those keys plus any keys in
``allowed_keys``.

**Arguments**:

- `name_of_cfg` - Name used in user-facing error messages.
- `array` - Sequence of mappings to validate.
- `mandatory_keys` - Keys that must be present in every mapping.
- `allowed_keys` - Extra optional keys that are accepted in addition to
  the mandatory keys.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.


**Raises**:

- `SystemExit` - One mapping is missing a mandatory key or contains an
  unexpected key.

<a id="config_as_json.config.Config.check_lst_dict"></a>

#### check\_lst\_dict

```python
@staticmethod
def check_lst_dict(paramname: str,
                   inp: Sequence[Mapping[str, Any]],
                   key: str,
                   key_optional: bool,
                   valtype: type,
                   min_size_list: int,
                   stderr_file: TextIO = sys.stderr) -> None
```

Validate a list of mappings that carry one typed value per row.

**Arguments**:

- `paramname` - Configuration parameter name used in diagnostics.
- `inp` - Sequence that should be a list of dictionaries.
- `key` - Key whose value type should be checked in each dictionary.
- `key_optional` - Whether dictionaries may omit ``key``.
- `valtype` - Expected runtime type for the value stored at ``key``.
- `min_size_list` - Minimum allowed number of dictionaries in ``inp``.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.


**Raises**:

- `SystemExit` - ``inp`` is not a list, contains non-dict items, is too
  short, is missing ``key`` when required, or has a value at
  ``key`` with the wrong runtime type.

<a id="config_as_json.config.Config.check_lst_dict_lst"></a>

#### check\_lst\_dict\_lst

```python
@staticmethod
def check_lst_dict_lst(paramname: str,
                       inp: Sequence[Mapping[str, Any]],
                       key: str,
                       key_optional: bool,
                       valtype: type,
                       min_size_outer_list: int,
                       min_size_inner_list: int,
                       stderr_file: TextIO = sys.stderr) -> None
```

Validate a list of mappings whose checked value is itself a list.

**Arguments**:

- `paramname` - Configuration parameter name used in diagnostics.
- `inp` - Sequence that should be a list of dictionaries.
- `key` - Key whose value should be a list of ``valtype`` items.
- `key_optional` - Whether dictionaries may omit ``key``.
- `valtype` - Expected runtime type for each item in the inner list.
- `min_size_outer_list` - Minimum number of dictionaries in ``inp``.
- `min_size_inner_list` - Minimum number of items in each checked inner
  list.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.


**Raises**:

- `SystemExit` - The outer value does not satisfy
  :meth:`check_lst_dict`, one checked inner list is too short,
  or one inner list item has the wrong runtime type.

<a id="config_as_json.config.Config.value_of_type"></a>

#### value\_of\_type

```python
@staticmethod
def value_of_type(input_value: Any, to_type: Any) -> Any
```

Return ``input_value`` as an instance of ``to_type``.

**Arguments**:

- `input_value` - Value to normalize.
- `to_type` - Target runtime type or constructor.


**Returns**:

  ``input_value`` unchanged when it already has the expected type,
  otherwise the result of calling ``to_type(input_value)``.

<a id="config_as_json.config.Config.check_array_dicts"></a>

#### check\_array\_dicts

```python
@staticmethod
def check_array_dicts(name_of_cfg: str,
                      array: list[dict[str, Any]],
                      kind_key: str,
                      kind_type: type,
                      dict_of_templates: Mapping[Keya, Mapping[str, type]],
                      stderr_file: TextIO = sys.stderr) -> None
```

Validate a list of dictionaries against type templates.

Each row in ``array`` selects its expected template through
``kind_key``. The selected template then defines which keys must
exist and which runtime types their values must have.

**Arguments**:

- `name_of_cfg` - Name used in user-facing error messages.
- `array` - List of dictionaries to validate.
- `kind_key` - Key whose value selects the expected template.
- `kind_type` - Type used to normalize the value at ``kind_key``.
- `dict_of_templates` - Mapping from kind value to a dictionary of
  expected keys and value types.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.


**Raises**:

- `KeyError` - ``dict_of_templates`` is not a dictionary of
  dictionaries.
- `SystemExit` - ``array`` is not a list of dictionaries, one row is
  missing a required key, or one row value has the wrong runtime
  type.

<a id="config_as_json.config.Config.get_converter_dict"></a>

#### get\_converter\_dict

```python
@staticmethod
def get_converter_dict(enum_type: Type[Enum]) -> ParseConverter
```

Build a converter recipe for enum-valued configuration fields.

**Arguments**:

- `enum_type` - Enum class that should be reconstructed from text.


**Returns**:

  A ``ParseConverter`` that parses strings with
  :func:`string_to_enum_best_match`.

<a id="config_as_json.config.Config.check_no_duplicates"></a>

#### check\_no\_duplicates

```python
@staticmethod
def check_no_duplicates(expanded_data: list[str] | list[int],
                        param_name: str,
                        stderr_file: TextIO = sys.stderr) -> None
```

Fail if a sequence contains duplicate values.

**Arguments**:

- `expanded_data` - Sequence whose values must be unique.
- `param_name` - Configuration parameter name used in diagnostics.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.


**Raises**:

- `SystemExit` - ``expanded_data`` contains duplicate values.

<a id="config_as_json.config.Config.get_validation_plan"></a>

#### get\_validation\_plan

```python
def get_validation_plan(stderr_file: TextIO) -> ValidationPlan
```

Return the validation plan for the Config object.

The validation plan is used to validate the Config object after it has
been parsed from JSON, and it is also used to validate the Config
object after it has been default constructed.

The derived class shall override this method to return a list of
validation steps describing the validations for the Config object.
This is mandatory even for derived classes that do not currently use
validation and only want to return an empty list.

**Arguments**:

- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  An ordered list of validation steps describing the validations for
  the Config object. The order of the steps in the list is
  significant as a previous validation may normalize or change a
  configuration value that is used in a later validation.

<a id="config_as_json.config.Config.validate"></a>

#### validate

```python
def validate(stderr_file: TextIO) -> None
```

Validate the Config object.

The validation is performed by the validation plan returned by
``get_validation_plan``. The validation plan is applied in the order
of the validation steps in the list. A previous validation may
normalize or change a configuration value that is used in a later
validation.
A member validator returns the value that shall be stored back into the
member, even if that returned value is ``None``.
A whole-config validator may instead mutate the Config object
directly.

**Raises**:

- `InvalidConfiguration` - The Config object is not valid.
- `InvalidConfigurationValue` - The value of a member of the Config
  object is not valid.
- `NotImplementedError` - The derived class did not override
  ``get_validation_plan`` or one of the
  required validation methods.
- `AttributeError` - A member name in the validation plan is not a
  valid member name of the Config object.


**Arguments**:

- `stderr_file` - Stream used for user-facing diagnostics.

<a id="config_as_json.str_to_enum"></a>

# config\_as\_json.str\_to\_enum

Convert strings into enum members using forgiving matching rules.

<a id="config_as_json.str_to_enum.string_to_enum_best_match"></a>

#### string\_to\_enum\_best\_match

```python
def string_to_enum_best_match(inp: str, num_type: type[SomeEnum]) -> SomeEnum
```

Return the enum member whose name best matches ``inp``.

Matching first tries exact name lookups using common case variants. If no
exact name is found, the function accepts a unique prefix match ignoring
case.

**Arguments**:

- `inp` - Text that should name an enum member.
- `num_type` - Enum class to search.


**Returns**:

  The matching enum member.


**Raises**:

- `AssertionError` - ``inp`` is not a string.
- `KeyError` - No enum member matches or the prefix is ambiguous.

<a id="config_as_json.migrate_cfg"></a>

# config\_as\_json.migrate\_cfg

Migrate an older configuration file to the newest supported format.

<a id="config_as_json.migrate_cfg._match_config_seq"></a>

#### \_match\_config\_seq

```python
def _match_config_seq(config_class: object) -> MatchConfigSeq
```

Validate and return matcher/class pairs for configuration selection.

**Arguments**:

- `config_class` - Object supplied as the ``config_class`` argument to
  ``migrate_cfg``.


**Returns**:

  The validated matcher/class pair sequence.


**Raises**:

- `TypeError` - ``config_class`` is not a valid selector.

<a id="config_as_json.migrate_cfg.migrate_cfg"></a>

#### migrate\_cfg

```python
def migrate_cfg(infile: PathOrStr,
                outfile: PathOrStr,
                config_class: type[Config] | MatchConfigSeq,
                stderr_file: TextIO = sys.stderr) -> int
```

Read an old configuration file and write it back in current format.

The input file is parsed through the normal read old configuration file
(ROCF) mechanisms of the registered configuration classes. The normalized
in-memory configuration is then written to ``outfile`` using the current
schema and key names.

The ``config_class`` argument can be either:
- The configuration class to use (when reading ``infile`` and
writing ``outfile``).
- An ordered matcher/class pairs used to choose the correct configuration
class to use (when reading ``infile`` and writing ``outfile``).

The normal case is to use a single configuration class.

When the application supports multiple configuration variants, the
``config_class`` argument can be an ordered sequence of matcher/class
pairs used to choose the correct configuration class for ``infile``.
Multiple variants are for different configuration classes like for
instance Config2D and Config3D for a CAD application.

Multiple variants shall not be confused with multiple versions of the
same variant. A migration is always done between two versions of the
same variant.

**Arguments**:

- `infile` - Existing configuration file to migrate.
- `outfile` - Destination path for the migrated configuration file.
- `config_class` - Either the configuration class to use,
  or an ordered sequence of matcher/class pairs used to
  choose the correct configuration class (for applications
  with multiple configuration variants) to use.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.


**Returns**:

  ``0`` after a successful migration.


**Raises**:

- `SystemExit` - ``infile`` does not exist or ``outfile`` already exists,
  or no matcher accepts ``infile``.
- `TypeError` - ``config_class`` is neither a ``Config`` subclass nor a
  non-empty sequence of ``MatchConfig`` items.

<a id="config_as_json.file_must_exist"></a>

# config\_as\_json.file\_must\_exist

Check that a required input file exists before continuing.

<a id="config_as_json.file_must_exist.file_must_exist"></a>

#### file\_must\_exist

```python
def file_must_exist(filename: PathOrStr,
                    with_content_txt: Optional[str] = None,
                    stderr_file: TextIO = sys.stderr) -> None
```

Terminate with a helpful message when an expected file is missing.

**Arguments**:

- `filename` - Path to the file that must exist.
- `with_content_txt` - Optional human-readable description of the expected
  file contents.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.


**Raises**:

- `SystemExit` - The file does not exist.

<a id="config_as_json.migrate_cfg_warn_hook"></a>

# config\_as\_json.migrate\_cfg\_warn\_hook

Warn users when backward compatibility was needed during parsing.

<a id="config_as_json.migrate_cfg_warn_hook.MigrateCfgWarnHook"></a>

## MigrateCfgWarnHook Objects

```python
class MigrateCfgWarnHook(ConfigAutoChangeHook)
```

Emit a migration warning when automatic compatibility changes occur.

<a id="config_as_json.migrate_cfg_warn_hook.MigrateCfgWarnHook.migrate_instructions"></a>

#### migrate\_instructions

```python
@classmethod
def migrate_instructions(cls) -> str
```

Return instructions for migrating the configuration file.

A derived class in an application is expected to override this
method to return instructions for migrating the configuration file
in a way that is specific to the application.

**Returns**:

  Instructions for migrating the configuration file.

<a id="config_as_json.migrate_cfg_warn_hook.MigrateCfgWarnHook.migrate_warn_msg"></a>

#### migrate\_warn\_msg

```python
@classmethod
def migrate_warn_msg(cls) -> str
```

Return the standard warning shown for old configuration files.

**Returns**:

  Warning text encouraging the user to migrate the configuration to
  the newest supported format.

<a id="config_as_json.migrate_cfg_warn_hook.MigrateCfgWarnHook.auto_changed"></a>

#### auto\_changed

```python
def auto_changed(old_keys_handled: list[str], rocf_vals_handled: list[str],
                 stderr_file: TextIO) -> None
```

Print the standard migration warning.

**Arguments**:

- `old_keys_handled` - Legacy key names accepted during parsing.
- `def_vals_handled` - Keys that were filled with default values during
  parsing.
- `stderr_file` - Stream used for user-facing diagnostics.

<a id="config_as_json.discriminated_dict_validators"></a>

# config\_as\_json.discriminated\_dict\_validators

Implement validators for discriminated dictionary variants.

<a id="config_as_json.discriminated_dict_validators._validate_variant_rules"></a>

#### \_validate\_variant\_rules

```python
def _validate_variant_rules(rules: Sequence[DictRule]) -> None
```

Validate the ``rules`` field of ``DictVariant``.

**Arguments**:

- `rules` - Rules to validate.


**Raises**:

- `TypeError` - If ``rules`` is not a sequence or any entry is not a
  ``DictRule``.

<a id="config_as_json.discriminated_dict_validators.DictVariant"></a>

## DictVariant Objects

```python
@dataclass(frozen=True)
class DictVariant()
```

Describe one allowed dictionary variant.

The discriminator key handled by ``DiscriminatedDictValidator`` is
always mandatory and allowed. The keys in this variant are therefore
the variant-specific keys in addition to that discriminator key.

**Attributes**:

- `mandatory_keys` - Variant-specific keys that must be present.
- `allowed_keys` - Additional variant-specific keys that are allowed but
  not required. ``None`` means no additional optional keys.
- `rules` - Per-key validators to apply after the key set has been
  checked. Rules may include the discriminator key if it should
  also be normalized or checked beyond variant selection.

<a id="config_as_json.discriminated_dict_validators.DictVariant.__post_init__"></a>

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

Validate that the variant description is well-formed.

<a id="config_as_json.discriminated_dict_validators._validate_discriminator_key"></a>

#### \_validate\_discriminator\_key

```python
def _validate_discriminator_key(discriminator_key: str) -> None
```

Validate the discriminator key argument.

**Arguments**:

- `discriminator_key` - Key whose value chooses the dictionary variant.


**Raises**:

- `TypeError` - If ``discriminator_key`` is not a string.
- `ValueError` - If ``discriminator_key`` is empty.

<a id="config_as_json.discriminated_dict_validators._validate_variants"></a>

#### \_validate\_variants

```python
def _validate_variants(variants: Mapping[object, DictVariant]) -> None
```

Validate the variants mapping argument.

**Arguments**:

- `variants` - Mapping from discriminator values to dict variants.


**Raises**:

- `TypeError` - If ``variants`` is not a mapping or one value is not a
  ``DictVariant``.
- `ValueError` - If ``variants`` is empty.

<a id="config_as_json.discriminated_dict_validators._validate_optional_discriminator_validator"></a>

#### \_validate\_optional\_discriminator\_validator

```python
def _validate_optional_discriminator_validator(
        discriminator_validator: Optional[MemberValidator]) -> None
```

Validate the optional discriminator validator argument.

<a id="config_as_json.discriminated_dict_validators._variant_mandatory_keys"></a>

#### \_variant\_mandatory\_keys

```python
def _variant_mandatory_keys(discriminator_key: str,
                            variant: DictVariant) -> list[str]
```

Return mandatory keys including the discriminator key once.

<a id="config_as_json.discriminated_dict_validators._raise_missing_discriminator"></a>

#### \_raise\_missing\_discriminator

```python
def _raise_missing_discriminator(member_name: str, discriminator_key: str,
                                 stderr_file: TextIO) -> None
```

Raise an invalid-configuration error for a missing discriminator.

<a id="config_as_json.discriminated_dict_validators._variant_for_discriminator_value"></a>

#### \_variant\_for\_discriminator\_value

```python
def _variant_for_discriminator_value(discriminator_name: str,
                                     discriminator_value: object,
                                     variants: Mapping[object, DictVariant],
                                     stderr_file: TextIO) -> DictVariant
```

Return the variant selected by one discriminator value.

**Arguments**:

- `discriminator_name` - Name of the discriminator value in diagnostics.
- `discriminator_value` - Normalized discriminator value.
- `variants` - Mapping from discriminator values to variants.
- `stderr_file` - Stream used for diagnostics.


**Returns**:

  The selected variant.


**Raises**:

- `InvalidConfiguration` - If the discriminator value is unhashable or has
  no matching variant.

<a id="config_as_json.discriminated_dict_validators.DiscriminatedDictValidator"></a>

## DiscriminatedDictValidator Objects

```python
class DiscriminatedDictValidator(  # pylint: disable=too-few-public-methods
        MemberValidator)
```

Validate a dictionary using a variant selected by one key.

This validator is intended for dictionaries whose required and allowed
keys depend on a discriminator field such as ``'kind'`` or ``'type'``.
The member must be a dictionary and must contain ``discriminator_key``.
The discriminator value is optionally validated or normalized by
``discriminator_validator`` before variant lookup.

The ``variants`` mapping is keyed by the discriminator values used after
that optional discriminator validation. The selected ``DictVariant``
defines the variant-specific mandatory keys, optional keys, and per-key
validators.

Validation never mutates the input dictionary in place. It returns a new
dictionary carrying any normalized discriminator value and any normalized
per-key values returned by the selected variant rules.

<a id="config_as_json.discriminated_dict_validators.DiscriminatedDictValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(
        discriminator_key: str,
        variants: Mapping[object, DictVariant],
        discriminator_validator: Optional[MemberValidator] = None) -> None
```

Initialize the discriminated dictionary validator.

**Arguments**:

- `discriminator_key` - Key whose value chooses the variant. This key
  is always required and allowed independently of the selected
  variant.
- `variants` - Mapping from normalized discriminator values to the
  variant that applies to that discriminator value.
- `discriminator_validator` - Optional validator applied to the
  discriminator value before variant lookup. It can normalize
  values, for example from user-facing strings to canonical
  strings or enum values.


**Raises**:

- `ValueError` - If ``discriminator_key`` is empty or ``variants`` is
  empty.
- `TypeError` - If ``discriminator_key`` is not a string, if
  ``variants`` is not a mapping, if any variant is not a
  ``DictVariant``, or if ``discriminator_validator`` is not
  ``None`` or a ``MemberValidator``.

<a id="config_as_json.discriminated_dict_validators.DiscriminatedDictValidator._validate_discriminator"></a>

#### \_validate\_discriminator

```python
def _validate_discriminator(
        config: Config, member_name: str, member_value: dict[object, object],
        stderr_file: TextIO) -> tuple[dict[object, object], object]
```

Validate and normalize the discriminator value.

<a id="config_as_json.discriminated_dict_validators.DiscriminatedDictValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one dictionary member using the selected variant.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the dictionary member to validate.
- `member_value` - The dictionary value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  A new dictionary carrying any normalized discriminator value and
  any normalized per-key values returned by the selected variant
  rules.


**Raises**:

- `InvalidConfiguration` - If the member is not a dictionary, the
  discriminator key is missing, the discriminator value has no
  variant, or the selected variant rejects the key set or a
  value.
- `InvalidConfigurationValue` - If an inner validator rejects a value
  because it is not one of its allowed values.

<a id="config_as_json.csv_dialect"></a>

# config\_as\_json.csv\_dialect

Build CSV dialects from JSON-friendly configuration values.

<a id="config_as_json.csv_dialect.CsvDialectConfig"></a>

## CsvDialectConfig Objects

```python
class CsvDialectConfig(TypedDict)
```

Describe serialized ``csv.Dialect`` configuration values.

The ``name`` key is required, and its value may not be ``None``.
The remaining keys are optional when validated through
:class:`CsvDialectValidator`; missing optional keys are
treated as if they were present with value ``None``.

Keys:
    name: Dialect template name, such as ``'csv.excel'``.
    delimiter: Optional field delimiter override.
    quoting: Optional quoting constant name, such as
        ``'csv.quote_minimal'``.
    quotechar: Optional quoting character override.
    lineterminator: Optional line terminator override.
    escapechar: Optional escape character override.

<a id="config_as_json.csv_dialect._csv_dialect_from_name"></a>

#### \_csv\_dialect\_from\_name

```python
def _csv_dialect_from_name(name: str, stderr_file: TextIO) -> csv.Dialect
```

Return the CSV dialect template selected by ``name``.

<a id="config_as_json.csv_dialect._csv_quoting_from_name"></a>

#### \_csv\_quoting\_from\_name

```python
def _csv_quoting_from_name(quoting: Optional[str],
                           stderr_file: TextIO) -> Literal[0, 1, 2, 3, 4, 5]
```

Return the CSV quoting constant selected by ``quoting``.

<a id="config_as_json.csv_dialect.get_csv_dialect"></a>

#### get\_csv\_dialect

```python
def get_csv_dialect(*,
                    name: str,
                    delimiter: Optional[str],
                    quoting: Optional[str],
                    quotechar: Optional[str],
                    lineterminator: Optional[str],
                    escapechar: Optional[str],
                    stderr_file: TextIO = sys.stderr) -> csv.Dialect
```

Build a ``csv.Dialect`` from serialized configuration fields.

**Arguments**:

- `name` - Name of a standard-library dialect template to start from.
- `delimiter` - Optional field delimiter override.
- `quoting` - Optional quoting constant name such as ``'csv.quote_all'``.
- `quotechar` - Optional quoting character override.
- `lineterminator` - Optional line terminator override.
- `escapechar` - Optional escape character override.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.


**Returns**:

  A configured ``csv.Dialect`` instance.


**Raises**:

- `KeyError` - ``name`` or ``quoting`` is not one of the supported
  serialized values.

<a id="config_as_json.csv_dialect._invalid_csv_dialect"></a>

#### \_invalid\_csv\_dialect

```python
def _invalid_csv_dialect(member_name: str, message: str,
                         stderr_file: TextIO) -> NoReturn
```

Raise ``InvalidConfiguration`` for one CSV dialect problem.

<a id="config_as_json.csv_dialect._validate_csv_dialect_key"></a>

#### \_validate\_csv\_dialect\_key

```python
def _validate_csv_dialect_key(member_name: str, key: object,
                              stderr_file: TextIO) -> str
```

Validate and return one key in a CSV dialect member.

<a id="config_as_json.csv_dialect._validate_csv_dialect_value"></a>

#### \_validate\_csv\_dialect\_value

```python
def _validate_csv_dialect_value(member_name: str, key: str, value: object,
                                stderr_file: TextIO) -> Optional[str]
```

Validate and return one value in a CSV dialect member.

<a id="config_as_json.csv_dialect._normalized_csv_dialect_config"></a>

#### \_normalized\_csv\_dialect\_config

```python
def _normalized_csv_dialect_config(member_name: str, member_value: object,
                                   stderr_file: TextIO) -> CsvDialectConfig
```

Validate and normalize one CSV dialect member.

<a id="config_as_json.csv_dialect.CsvDialectValidator"></a>

## CsvDialectValidator Objects

```python
class CsvDialectValidator(MemberValidator)
```

Validate one CSV dialect configuration dictionary.

The member value must be a ``dict[str, Optional[str]]``. No keys other
than ``name``, ``delimiter``, ``quoting``, ``quotechar``,
``lineterminator``, and ``escapechar`` are allowed. The ``name`` key is
mandatory. Missing optional keys are normalized to ``None`` in the value
returned by ``validate_member``.

After the dictionary shape has been checked, the validator calls
:func:`get_csv_dialect` to verify that the values can actually create a
``csv.Dialect``. Any failure from that construction is reported as
:class:`InvalidConfiguration`.

<a id="config_as_json.csv_dialect.CsvDialectValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one CSV dialect member and return a normalized dict.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The member value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  A normalized ``CsvDialectConfig`` with all supported keys present.


**Raises**:

- `InvalidConfiguration` - If the member is not a valid CSV dialect
  configuration dictionary.

<a id="config_as_json.projected_validators"></a>

# config\_as\_json.projected\_validators

Define validators that validate projected member values.

<a id="config_as_json.projected_validators._validate_projector"></a>

#### \_validate\_projector

```python
def _validate_projector(
        projector: Callable[['Config', str, object, TextIO], object]) -> None
```

Validate the projector argument.

**Arguments**:

- `projector` - Callable that computes the value to validate.


**Raises**:

- `TypeError` - If ``projector`` is not callable.

<a id="config_as_json.projected_validators._validate_optional_source_validator"></a>

#### \_validate\_optional\_source\_validator

```python
def _validate_optional_source_validator(
        source_validator: Optional[MemberValidator]) -> None
```

Validate the optional source validator argument.

**Arguments**:

- `source_validator` - Optional validator for the source member value.


**Raises**:

- `TypeError` - If ``source_validator`` is not ``None`` or a
  ``MemberValidator``.

<a id="config_as_json.projected_validators._validate_projected_validators"></a>

#### \_validate\_projected\_validators

```python
def _validate_projected_validators(
        validators: Sequence[MemberValidator]) -> None
```

Validate validators applied to the projected value.

**Arguments**:

- `validators` - Validators to apply to the projected value.


**Raises**:

- `TypeError` - If ``validators`` is not a sequence or one entry is not a
  ``MemberValidator``.
- `ValueError` - If ``validators`` is empty.

<a id="config_as_json.projected_validators.ProjectedMemberValidator"></a>

## ProjectedMemberValidator Objects

```python
class ProjectedMemberValidator(  # pylint: disable=too-few-public-methods
        MemberValidator)
```

Validate a projected value while keeping the original member value.

This validator is intended for configuration members whose natural
validation view is not the stored value itself. A projector function
computes that validation view from the original member value, and a
sequence of inner validators is then applied to the projected value.

``source_validator`` is an optional validator for the source member value
before projection. It is useful when the projector benefits from a
validated or normalized source view. If it is supplied, the value it
returns is passed to ``projector`` instead of the original member value.

Projected validators are applied in order. If one projected validator
returns a normalized or replacement projected value, that returned value
is passed to the next projected validator. The final projected value is
discarded when validation succeeds, and the original member value is
returned.

Returned replacement values from ``source_validator`` and projected
validators affect only this validation chain. They do not replace the
stored member value. The validator does not copy the source or projected
value, though. In-place mutation done by ``source_validator``, by the
projector, or by a projected validator can still affect shared mutable
objects. Validators and projectors that need isolation should return or
work on detached values.

<a id="config_as_json.projected_validators.ProjectedMemberValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(projector: Callable[['Config', str, object, TextIO], object],
             validators: Sequence[MemberValidator],
             source_validator: Optional[MemberValidator] = None) -> None
```

Initialize the projected member validator.

**Arguments**:

- `projector` - Callable that receives the complete config object,
  the member name, the original member value, and the diagnostic
  stream. It returns the projected value to validate.
- `validators` - Validators to apply to the projected value. They are
  applied in declaration order, and each validator receives the
  value returned by the previous validator.
- `source_validator` - Optional validator applied to the original
  member value before projection. Its returned value is passed
  to ``projector``.


**Raises**:

- `ValueError` - If ``validators`` is empty.
- `TypeError` - If ``projector`` is not callable or any validator is
  not a ``MemberValidator``.

<a id="config_as_json.projected_validators.ProjectedMemberValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one member through a projected value.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The original member value.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The original ``member_value`` when validation succeeds. Returned
  normalized source or projected values affect only this validation
  chain, not the stored config member.


**Raises**:

- `InvalidConfiguration` - If the projector or an inner validator
  detects an invalid configuration.
- `InvalidConfigurationValue` - If an inner validator rejects a value
  because it is not one of its allowed values.

<a id="config_as_json.dict_validators"></a>

# config\_as\_json.dict\_validators

Implement dictionary validators for config-as-json.

The ``Config`` base class already checks each dict member's keys against the
default; list a member in ``_unchecked_dicts`` when validators here (for
example ``DictKeysValidator``) should own that member's key or value policy
completely instead. See :class:`DictKeysValidator` for the full picture.

<a id="config_as_json.dict_validators._validate_dict_member_value"></a>

#### \_validate\_dict\_member\_value

```python
def _validate_dict_member_value(member_name: str, member_value: object,
                                stderr_file: TextIO) -> dict[object, object]
```

Validate that one member value is a dict and return it.

**Arguments**:

- `member_name` - The member name used in any error message.
- `member_value` - The value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The validated dict value.


**Raises**:

- `InvalidConfiguration` - If ``member_value`` is not a dict.

<a id="config_as_json.dict_validators._validate_string_keys"></a>

#### \_validate\_string\_keys

```python
def _validate_string_keys(keys: Sequence[str], parameter_name: str) -> None
```

Validate that ``keys`` is a sequence of distinct strings.

**Arguments**:

- `keys` - The sequence to validate.
- `parameter_name` - Name used in error messages.


**Raises**:

- `TypeError` - If any entry of ``keys`` is not a ``str``.
- `ValueError` - If ``keys`` contains a duplicate entry.

<a id="config_as_json.dict_validators._inner_member_name"></a>

#### \_inner\_member\_name

```python
def _inner_member_name(outer: str, key: str) -> str
```

Return the inner member name used for a value at ``key`` of ``outer``.

The convention is ``outer[key]``, mirroring the ``outer[index]`` form
used by ``ListForEachValidator`` for list elements.

**Arguments**:

- `outer` - The member name of the surrounding dict member.
- `key` - The dict key whose value is being validated.


**Returns**:

  The combined inner member name.

<a id="config_as_json.dict_validators.DictKeysValidator"></a>

## DictKeysValidator Objects

```python
class DictKeysValidator(MemberValidator)
```

Validate that a dict's key set conforms to a fixed policy.

The validator accepts only actual dict values. All keys listed in
``mandatory_keys`` must be present in the dict; a missing mandatory key
is reported as an error. Any key in the dict that is neither a
mandatory key nor an additional allowed key is rejected. The set of
permitted keys is the union of ``mandatory_keys`` and ``allowed_keys``;
a key listed in both sequences is harmless.

The validator never modifies the dict and never inspects its values,
so it is the natural first step in a ``ValidationPlan`` that is later
followed by per-key value validators such as ``DictForEachValidator``.

Interaction with :class:`Config` dict checking. The base class
already enforces a key-set policy for each dict member by matching parsed
JSON to the default value (unknown keys in the file are not allowed;
which default keys may be omitted depends on the load path). For a
fixed closed key set, that is often enough and you do not need this
validator. Use ``DictKeysValidator`` and list the member in
``_unchecked_dicts`` on the :class:`Config` when you need optional keys, a
different key policy, or when ``DictForEachValidator`` will validate
values and you must not let the base class reject valid key sets first.

<a id="config_as_json.dict_validators.DictKeysValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(mandatory_keys: Sequence[str],
             allowed_keys: Optional[Sequence[str]] = None) -> None
```

Initialize the validator.

**Arguments**:

- `mandatory_keys` - Keys that must be present in the dict. May be
  empty if the dict is allowed to be empty (or to contain
  only optional keys).
- `allowed_keys` - Additional keys that are permitted but not
  required. ``None`` means no optional keys are allowed; the
  dict must contain exactly the mandatory keys.


**Raises**:

- `TypeError` - If any entry of ``mandatory_keys`` or
  ``allowed_keys`` is not a ``str``.
- `ValueError` - If ``mandatory_keys`` or ``allowed_keys`` contains
  a duplicate entry.

<a id="config_as_json.dict_validators.DictKeysValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one dict member against the configured key set.

Mandatory keys are checked first, in their declared order, so the
first missing mandatory key triggers the error. After that, the
keys in the dict are checked in their insertion order so that the
first unknown key triggers the error.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The dict value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The original dict value if validation succeeds.


**Raises**:

- `InvalidConfiguration` - If the member is not a dict, a mandatory
  key is missing, or an unknown key is present.

<a id="config_as_json.dict_validators.DictRule"></a>

## DictRule Objects

```python
@dataclass(frozen=True)
class DictRule()
```

Bind a sequence of validators to a set of dict keys.

A ``DictRule`` is the data shape that ``DictForEachValidator`` uses to
apply per-key validation. For every key listed in ``keys``, every
validator in ``validators`` is applied in order, threading the
normalized return value forward.

<a id="config_as_json.dict_validators.DictRule.__post_init__"></a>

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

Validate that ``keys`` and ``validators`` are well-formed.

**Raises**:

- `ValueError` - If ``keys`` or ``validators`` is empty, or if
  ``keys`` contains a duplicate entry.
- `TypeError` - If any entry of ``keys`` is not a ``str`` or any
  entry of ``validators`` is not a ``MemberValidator``.

<a id="config_as_json.dict_validators._validate_for_each_rules"></a>

#### \_validate\_for\_each\_rules

```python
def _validate_for_each_rules(rules: Sequence[DictRule]) -> None
```

Validate the ``rules`` argument of DictForEachValidator.

**Arguments**:

- `rules` - Rules to apply per dict key.


**Raises**:

- `ValueError` - If ``rules`` is empty.
- `TypeError` - If any entry of ``rules`` is not a ``DictRule``.

<a id="config_as_json.dict_validators.DictForEachValidator"></a>

## DictForEachValidator Objects

```python
class DictForEachValidator(MemberValidator)
```

Apply per-key validators to specific keys of a dict.

For each ``DictRule`` in ``rules`` (in declaration order), the
validator iterates the rule's ``keys`` (in declaration order) and
applies every validator in the rule's ``validators`` (in declaration
order) to the value at that key. Each validator receives the value
returned by the previous validator, so normalization performed by one
inner validator is visible to the next one. The dict member is never
modified in place; a new dict is returned that carries the per-key
updates.

A rule key that is not present in the dict is silently skipped. This
keeps the validator strictly orthogonal to ``DictKeysValidator``,
which is the dedicated mechanism for enforcing that mandatory keys
are present and that unknown keys are rejected.

Keys that are present in the dict but are not covered by any rule are
copied through unchanged.

Inner validator calls receive ``f'{member_name}[{key}]'`` as the
``member_name``, so error messages stay precise about which key
failed. The same convention is used by ``ListForEachValidator`` with
the index in place of the key.

Order example::

    ra = DictRule(keys=['a', 'b'], validators=[v1, v2])
    rb = DictRule(keys=['a', 'b', 'c'], validators=[v3, v4])
    v = DictForEachValidator(rules=[ra, rb])

For a dict whose keys include at least ``'a'``, ``'b'``, and ``'c'``,
the inner validator calls happen in this order:

    1. ``v1(a)``, ``v2(a)``  -- rule ``ra``, key ``'a'``
    2. ``v1(b)``, ``v2(b)``  -- rule ``ra``, key ``'b'``
    3. ``v3(a)``, ``v4(a)``  -- rule ``rb``, key ``'a'``;
       sees the value left by ``v2(a)``
    4. ``v3(b)``, ``v4(b)``  -- rule ``rb``, key ``'b'``;
       sees the value left by ``v2(b)``
    5. ``v3(c)``, ``v4(c)``  -- rule ``rb``, key ``'c'``

The iteration is rule-major, then key-within-rule, then
validator-within-rule. This mirrors ``ListForEachValidator``'s
iteration shape: outer loop over container children, inner loop over
the validators that apply to each child.

<a id="config_as_json.dict_validators.DictForEachValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(rules: Sequence[DictRule]) -> None
```

Initialize the validator.

**Arguments**:

- `rules` - Non-empty sequence of ``DictRule`` entries to apply.


**Raises**:

- `ValueError` - If ``rules`` is empty.
- `TypeError` - If any entry of ``rules`` is not a ``DictRule``.

<a id="config_as_json.dict_validators.DictForEachValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one dict member by delegating to per-key validators.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the outer dict member to validate.
- `member_value` - The dict value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  A new dict whose values are the values returned by the last
  inner validator for each rule key that was present in the
  input. Keys not covered by any rule are copied through
  unchanged. The new dict preserves the input's key insertion
  order.


**Raises**:

- `InvalidConfiguration` - If the member is not a dict, or a
  supplied validator raised ``InvalidConfiguration``.
- `InvalidConfigurationValue` - If a supplied validator raised
  ``InvalidConfigurationValue``.

<a id="config_as_json.file_extension"></a>

# config\_as\_json.file\_extension

Normalize filenames by removing or appending configured extensions.

<a id="config_as_json.file_extension.fix_file_extension"></a>

#### fix\_file\_extension

```python
def fix_file_extension(filename: str,
                       ext_to_add: str,
                       ext_to_remove: Optional[str] = None,
                       for_reading: bool = False) -> str
```

Return ``filename`` with the desired extension normalization applied.

**Arguments**:

- `filename` - Path text to normalize.
- `ext_to_add` - Extension that should be present in the returned value.
- `ext_to_remove` - Optional extension that should be stripped before
  ``ext_to_add`` is applied.
- `for_reading` - If ``True`` and ``filename`` already exists as written,
  return it unchanged.


**Returns**:

  The normalized filename.

<a id="config_as_json.char_encoding"></a>

# config\_as\_json.char\_encoding

Validate text encoding names used by configuration values.

<a id="config_as_json.char_encoding.valid_char_encoding"></a>

#### valid\_char\_encoding

```python
def valid_char_encoding(enc: str) -> bool
```

Return whether ``enc`` names a valid text encoding.

**Arguments**:

- `enc` - Encoding name to test.


**Returns**:

  ``True`` when Python recognizes ``enc`` as a text encoding, otherwise
  ``False``.

<a id="config_as_json.char_encoding.check_char_encoding"></a>

#### check\_char\_encoding

```python
def check_char_encoding(enc: str, stderr_file: TextIO = sys.stderr) -> None
```

Fail fast when a named character encoding is not recognized.

**Arguments**:

- `enc` - Encoding name to validate.
- `stderr_file` - Stream used for user-facing diagnostics. Defaults to
  ``sys.stderr``.


**Raises**:

- `SystemExit` - ``enc`` is not a recognized text encoding.

<a id="config_as_json.char_encoding.CharEncodingValidator"></a>

## CharEncodingValidator Objects

```python
class CharEncodingValidator(MemberValidator)
```

Validate that one string member names a recognized text encoding.

<a id="config_as_json.char_encoding.CharEncodingValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one character encoding member.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The member value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The original encoding string.


**Raises**:

- `InvalidConfiguration` - If the member value is not a string or does
  not name a recognized text encoding.

<a id="config_as_json.config_factory"></a>

# config\_as\_json.config\_factory

Choose a configuration class by inspecting JSON input.

Applications that support multiple configuration schemas can register matcher
functions together with the corresponding ``Config`` subclasses. This module
then reads JSON from text or file input, selects the first matching schema,
and creates the appropriate configuration object.

<a id="config_as_json.config_factory.MatchConfig"></a>

## MatchConfig Objects

```python
class MatchConfig(NamedTuple)
```

Pair one JSON matcher with the configuration class it selects.

<a id="config_as_json.config_factory.MatchConfig.match_func"></a>

#### match\_func

Function to check if JSON text matches the config class.

**Arguments**:

- `json_text` - The JSON text to check.
- `stderr_file` - File to write error messages to.

**Returns**:

  True if JSON text matches the config class, False otherwise.

<a id="config_as_json.config_factory.MatchConfig.config_class"></a>

#### config\_class

Config class for the case that JSON text matches.

<a id="config_as_json.config_factory._config_factory_get_text"></a>

#### \_config\_factory\_get\_text

```python
def _config_factory_get_text(from_json_text: Optional[str],
                             from_json_filename: Optional[PathOrStr],
                             stderr_file: TextIO) -> str
```

Return configuration JSON from exactly one supported input source.

**Arguments**:

- `from_json_text` - Optional JSON text supplied directly by the caller.
- `from_json_filename` - Optional path to a file containing JSON text.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  The JSON text that should be inspected by the factory.


**Raises**:

- `RuntimeError` - Neither or both input sources were supplied.
- `SystemExit` - The requested file input does not exist.

<a id="config_as_json.config_factory._config_factory_exit"></a>

#### \_config\_factory\_exit

```python
def _config_factory_exit(msg: str, exc: Optional[JSONDecodeError]
                         | Optional[UnicodeDecodeError],
                         stderr_file: TextIO) -> NoReturn
```

Print a fatal factory error message and terminate the process.

**Arguments**:

- `msg` - Main user-facing error message.
- `exc` - Optional decoding exception whose text should be appended.
- `stderr_file` - Stream used for diagnostics.

<a id="config_as_json.config_factory.JsonValueMatcher"></a>

## JsonValueMatcher Objects

```python
class JsonValueMatcher()
```

Match a configuration schema by checking one JSON key/value pair.

<a id="config_as_json.config_factory.JsonValueMatcher.__init__"></a>

#### \_\_init\_\_

```python
def __init__(key: str, value: JsonType) -> None
```

Store the key and reference value used by the matcher.

**Arguments**:

- `key` - JSON object key that identifies the schema.
- `value` - Expected value at ``key`` for this schema.

<a id="config_as_json.config_factory.JsonValueMatcher.__call__"></a>

#### \_\_call\_\_

```python
def __call__(json_text: str, stderr_file: TextIO) -> bool
```

Return whether one JSON document matches this key/value rule.

**Arguments**:

- `json_text` - JSON text to inspect.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  ``True`` when the document is a JSON object containing ``self``
  key with a matching value, otherwise ``False``.

<a id="config_as_json.config_factory.JsonValueMatcher.compare_value"></a>

#### compare\_value

```python
@classmethod
def compare_value(cls, value_at_key: JsonType,
                  expected_value: JsonType) -> bool
```

Compare an observed JSON value with the expected reference value.

Derived classes may override this class method to implement other
matching strategies. The default implementation compares strings
case-insensitively and all other JSON values with ``==``.

**Arguments**:

- `value_at_key` - Value read from the JSON document.
- `expected_value` - Reference value configured on the matcher.


**Returns**:

  ``True`` when the values should be considered equivalent.

<a id="config_as_json.config_factory.config_factory_from_json"></a>

#### config\_factory\_from\_json

```python
def config_factory_from_json(match_configs: MatchConfigSeq,
                             auto_ch_hook: ConfigAutoChangeHook,
                             from_json_filename: Optional[PathOrStr] = None,
                             from_json_data_text: Optional[str] = None,
                             stderr_file: TextIO = sys.stderr) -> Config
```

Create the first configuration class whose matcher accepts the input.

The function is intended for applications that support several related
configuration schemas and want to decide which ``Config`` subclass to use
by inspecting the input document itself.

**Arguments**:

- `match_configs` - Ordered matcher/class pairs. The first matcher that
  returns ``True`` selects the configuration class to instantiate.
- `auto_ch_hook` - Hook that should receive automatic-change callbacks from
  the selected configuration object.
- `from_json_filename` - Optional file containing configuration JSON.
- `from_json_data_text` - Optional configuration JSON supplied directly.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  An instance of the selected ``Config`` subclass populated from the
  supplied JSON.


**Raises**:

- `RuntimeError` - Neither or both JSON input sources were supplied.
- `SystemExit` - The JSON could not be decoded, no matcher accepted it, or
  a referenced input file does not exist.

<a id="config_as_json.list_validators"></a>

# config\_as\_json.list\_validators

Implement list validators for config-as-json.

<a id="config_as_json.list_validators.Basictype"></a>

#### Basictype

Basic scalar type accepted by the list validators.

<a id="config_as_json.list_validators._validate_supported_list_element_type"></a>

#### \_validate\_supported\_list\_element\_type

```python
def _validate_supported_list_element_type(element_type: type[object]) -> None
```

Validate that a list validator uses one supported runtime type.

**Arguments**:

- `element_type` - The element type configured for a list validator.


**Raises**:

- `TypeError` - If ``element_type`` is not exactly ``int``, ``float``,
  ``str``, or ``bool``.

<a id="config_as_json.list_validators._validate_list_size_bounds"></a>

#### \_validate\_list\_size\_bounds

```python
def _validate_list_size_bounds(min_size: int, max_size: int) -> None
```

Validate constructor bounds for ``ListSizeValidator``.

**Arguments**:

- `min_size` - Minimum allowed list size.
- `max_size` - Maximum allowed list size.


**Raises**:

- `TypeError` - If one bound is not exactly an ``int``.
- `ValueError` - If one bound is negative or ``min_size`` exceeds
  ``max_size``.

<a id="config_as_json.list_validators._validate_list_member_value"></a>

#### \_validate\_list\_member\_value

```python
def _validate_list_member_value(member_name: str, member_value: object,
                                stderr_file: TextIO) -> list[object]
```

Validate that one member value is a list and return it.

**Arguments**:

- `member_name` - The member name used in any error message.
- `member_value` - The value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The validated list value.


**Raises**:

- `InvalidConfiguration` - If ``member_value`` is not a list.

<a id="config_as_json.list_validators._validate_typed_list_member"></a>

#### \_validate\_typed\_list\_member

```python
def _validate_typed_list_member(member_name: str, member_value: object,
                                element_type: type[Basictype],
                                stderr_file: TextIO) -> list[Basictype]
```

Validate that a member is a list with elements of one runtime type.

**Arguments**:

- `member_name` - The member name used in any error message.
- `member_value` - The value to validate.
- `element_type` - The required runtime type of each list element.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The validated list value with a narrow element type.


**Raises**:

- `InvalidConfiguration` - If the member is not a list or one element has
  the wrong runtime type.

<a id="config_as_json.list_validators._sort_list_values"></a>

#### \_sort\_list\_values

```python
def _sort_list_values(values: Sequence[Basictype],
                      lt_comparator: Callable[[Basictype, Basictype], bool],
                      reverse: bool) -> list[Basictype]
```

Return a stably sorted list using a less-than comparator.

**Arguments**:

- `values` - The values to sort.
- `lt_comparator` - The less-than comparator used for ordering.
- `reverse` - Whether to reverse the final sort order.


**Returns**:

  A new sorted list.

<a id="config_as_json.list_validators._unique_list_values"></a>

#### \_unique\_list\_values

```python
def _unique_list_values(values: Sequence[Basictype]) -> list[Basictype]
```

Return the first occurrence of each value in the current order.

**Arguments**:

- `values` - The values to deduplicate.


**Returns**:

  A new list with only the first occurrence of each value kept.

<a id="config_as_json.list_validators._validate_list_order"></a>

#### \_validate\_list\_order

```python
def _validate_list_order(member_name: str, values: Sequence[Basictype],
                         is_reversed: bool,
                         lt_comparator: Callable[[Basictype, Basictype], bool],
                         stderr_file: TextIO) -> None
```

Validate that adjacent values are in the requested non-strict order.

**Arguments**:

- `member_name` - The member name used in any error message.
- `values` - The typed list values to validate.
- `is_reversed` - Whether descending order is required.
- `lt_comparator` - The less-than comparator used for ordering.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - If the list is not in the requested order.

<a id="config_as_json.list_validators._validate_unique_list_values"></a>

#### \_validate\_unique\_list\_values

```python
def _validate_unique_list_values(member_name: str, values: Sequence[Basictype],
                                 stderr_file: TextIO) -> None
```

Validate that a list contains no duplicate values.

Duplicate detection uses normal Python equality semantics rather than the
custom ordering comparator.

**Arguments**:

- `member_name` - The member name used in any error message.
- `values` - The typed list values to validate.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - If a duplicate value is found.

<a id="config_as_json.list_validators._indexed_not_one_of_allowed_values"></a>

#### \_indexed\_not\_one\_of\_allowed\_values

```python
def _indexed_not_one_of_allowed_values(member_name: str, member_value: object,
                                       member_index: int,
                                       allowed_values: Sequence[object],
                                       stderr_file: Optional[TextIO]) -> str
```

Construct a message for a list element outside the allowed values.

Construct a message that one element in a list value is not one of the
allowed values. If ``stderr_file`` is not ``None``, the message is
written to it.

**Arguments**:

- `member_name` - The name of the member that has the invalid list value.
- `member_value` - The invalid element value in the list.
- `member_index` - The index of the invalid element in the list.
- `allowed_values` - The allowed values for elements in the list.
- `stderr_file` - The file to optionally write error messages to.
  If set to ``None`` explicitly, printing is suppressed.


**Returns**:

  A string containing the error message.

<a id="config_as_json.list_validators._IndexedInvalidConfigurationValue"></a>

## \_IndexedInvalidConfigurationValue Objects

```python
class _IndexedInvalidConfigurationValue(InvalidConfigurationValue)
```

Raised when a list element value is not one of the allowed values.

<a id="config_as_json.list_validators._IndexedInvalidConfigurationValue.__init__"></a>

#### \_\_init\_\_

```python
def __init__(member_name: str, member_value: object, member_index: int,
             allowed_values: Sequence[object]) -> None
```

Initialize the exception.

<a id="config_as_json.list_validators.ListValueValidator"></a>

## ListValueValidator Objects

```python
class ListValueValidator(  # pylint: disable=too-few-public-methods
        MemberValidator, Generic[Basictype])
```

Validate values in a list of basic scalar values.

<a id="config_as_json.list_validators.ListValueValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(
    min_value: Optional[Basictype],
    max_value: Optional[Basictype],
    allowed_values: Optional[Sequence[Basictype]],
    lt_comparator: Callable[[Basictype, Basictype], bool] = lambda x, y: x < y
) -> None
```

Initialize the validator.

The validator checks that the member value is a list containing only
values of the inferred scalar runtime type. Each element value must
satisfy every configured constraint: lower bound, upper bound, and
allowed-values membership.
At least one of min_value, max_value, or allowed_values must be
provided.

**Arguments**:

- `min_value` - Minimum allowed member element value.
  If ``None``, no minimum value is checked.
- `max_value` - Maximum allowed member element value.
  If ``None``, no maximum value is checked.
- `allowed_values` - The only allowed values for the elements of
  the member.
  If ``None``, no allowed-values check is done.
- `lt_comparator` - Comparator function for the element values.
  Defaults to the < operator.


**Raises**:

- `ValueError` - If no constraints are provided.
- `ValueError` - If allowed_values is provided as an empty sequence.
- `ValueError` - If min_value is greater than max_value.
- `TypeError` - If incompatible or mixed runtime types are used.

<a id="config_as_json.list_validators.ListValueValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one list member against elementwise constraints.

The validator accepts only actual list values. Each element in the
list must be an instance of the inferred constraint type and must
satisfy every configured constraint. The custom comparator is used
only for lower-bound and upper-bound checks. Membership in
``allowed_values`` uses the normal equality semantics of ``in``.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The list value to validate.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - The member is not a list or one element does
  not satisfy type or range constraints.
- `InvalidConfigurationValue` - One element is not one of the allowed
  values.


**Returns**:

  The original list value if the validation check passes.

<a id="config_as_json.list_validators.ListSizeValidator"></a>

## ListSizeValidator Objects

```python
class ListSizeValidator(MemberValidator)
```

Validate that a list length stays within mandatory size bounds.

<a id="config_as_json.list_validators.ListSizeValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(min_size: int, max_size: int) -> None
```

Initialize the validator.

The validator accepts only actual list values. The list length must be
between ``min_size`` and ``max_size``, inclusive.

**Arguments**:

- `min_size` - Minimum allowed size of the list.
- `max_size` - Maximum allowed size of the list.


**Raises**:

- `TypeError` - If one bound is not exactly an ``int``.
- `ValueError` - If one bound is negative or ``min_size`` exceeds
  ``max_size``.

<a id="config_as_json.list_validators.ListSizeValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one list member against the configured size bounds.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The list value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The original list value if validation succeeds.


**Raises**:

- `InvalidConfiguration` - If the member is not a list or its size is
  outside the allowed range.

<a id="config_as_json.list_validators.ListIsOrderedValidator"></a>

## ListIsOrderedValidator Objects

```python
class ListIsOrderedValidator(
        MemberValidator,  # pylint: disable=too-few-public-methods # noqa: E501
        Generic[Basictype])
```

Validate list element types, optional ordering, and uniqueness.

<a id="config_as_json.list_validators.ListIsOrderedValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(
    element_type: type[Basictype],
    is_ordered: bool = True,
    is_reversed: bool = False,
    unique_values: bool = False,
    lt_comparator: Callable[[Basictype, Basictype], bool] = lambda x, y: x < y
) -> None
```

Initialize the validator.

The validator always checks that the member value is a list and that
every element is an instance of ``element_type`` using normal
``isinstance`` semantics. This means, for example, that ``True`` is
accepted when ``element_type`` is ``int``.

If ``is_ordered`` is true, the list must be in non-strict ascending
order by default, or in non-strict descending order when
``is_reversed`` is true. Equal adjacent values are therefore allowed
unless ``unique_values`` is also true.

If ``unique_values`` is true, duplicate detection uses normal Python
equality semantics rather than the custom ordering comparator.

**Arguments**:

- `element_type` - The type of the elements in the list. Must be one
  of the supported basic scalar types.
- `is_ordered` - Whether to validate element order.
- `is_reversed` - Whether ordered lists must be descending instead of
  ascending.
- `unique_values` - Whether duplicate values are rejected.
- `lt_comparator` - Comparator function for the element values.
  Defaults to the < operator.


**Raises**:

- `TypeError` - If ``element_type`` is unsupported.
- `ValueError` - If ``is_reversed`` is true while ``is_ordered`` is
  false.

<a id="config_as_json.list_validators.ListIsOrderedValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one list member against order and uniqueness rules.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The list value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The original list value if validation succeeds.


**Raises**:

- `InvalidConfiguration` - If the member is not a list, an element has
  the wrong type, the list order is wrong, or
  duplicates are present when forbidden.

<a id="config_as_json.list_validators.ListOrderingValidator"></a>

## ListOrderingValidator Objects

```python
class ListOrderingValidator(
        MemberValidator,  # pylint: disable=too-few-public-methods # noqa: E501
        Generic[Basictype])
```

Normalize one list by ordering, reversing, and deduplicating it.

<a id="config_as_json.list_validators.ListOrderingValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(
    element_type: type[Basictype],
    order: bool = True,
    reverse: bool = False,
    keep_only_unique: bool = False,
    lt_comparator: Callable[[Basictype, Basictype], bool] = lambda x, y: x < y
) -> None
```

Initialize the validator.

The validator always checks that the member value is a list and that
every element is an instance of ``element_type`` using normal
``isinstance`` semantics. This means, for example, that ``True`` is
accepted when ``element_type`` is ``int``.

If ``order`` is true, the list is stably sorted with
``lt_comparator``. If ``reverse`` is also true, the sorted result is
descending.

If ``order`` is false and ``reverse`` is true, the original list order
is reversed first.

If ``keep_only_unique`` is true, duplicate removal happens after any
ordering or reversing. Duplicate removal is stable in the current
order, so the first occurrence in the current order is kept and later
equal values are removed. Duplicate detection uses normal Python
equality semantics rather than the custom ordering comparator.

**Arguments**:

- `element_type` - The type of the elements in the list. Must be one
  of the supported basic scalar types.
- `order` - Whether to sort the list.
- `reverse` - Whether to reverse the sort order, or to reverse the
  original list when ``order`` is false.
- `keep_only_unique` - Whether to remove later duplicate values after
  ordering or reversing.
- `lt_comparator` - Comparator function for the element values.
  Defaults to the < operator.


**Raises**:

- `TypeError` - If ``element_type`` is unsupported.

<a id="config_as_json.list_validators.ListOrderingValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate and normalize one list member.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The list value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  A reordered or deduplicated list. If no normalization is
  configured, the original list value is returned unchanged.


**Raises**:

- `InvalidConfiguration` - If the member is not a list or one element
  has the wrong runtime type.

<a id="config_as_json.list_validators._validate_for_each_element_validators"></a>

#### \_validate\_for\_each\_element\_validators

```python
def _validate_for_each_element_validators(
        element_validators: Sequence[MemberValidator]) -> None
```

Validate the ``element_validators`` argument of ListForEachValidator.

**Arguments**:

- `element_validators` - Validators to apply to each list element.


**Raises**:

- `ValueError` - If ``element_validators`` is empty.
- `TypeError` - If any entry is not a ``MemberValidator``.

<a id="config_as_json.list_validators._validate_for_each_element_type"></a>

#### \_validate\_for\_each\_element\_type

```python
def _validate_for_each_element_type(
        element_type: Optional[type[object]]) -> None
```

Validate the ``element_type`` argument of ListForEachValidator.

**Arguments**:

- `element_type` - Optional required runtime type of each list element.


**Raises**:

- `TypeError` - If ``element_type`` is not ``None`` and not a ``type``.

<a id="config_as_json.list_validators.ListForEachValidator"></a>

## ListForEachValidator Objects

```python
class ListForEachValidator(MemberValidator)
```

Apply a sequence of inner validators to each element of a list.

This validator is the general composition mechanism for list members.
It iterates the outer list and delegates all per-element work to the
``element_validators`` sequence. It has no opinion about what an
element is: every inner validator is a ``MemberValidator`` and can
therefore be any of the built-in validators or a user-defined one.

Typical use cases include, but are not restricted to:

- Lists of lists (a matrix) where each inner list is checked with
  other list validators such as ``ListSizeValidator`` or
  ``ListValueValidator``.
- Lists of dicts where each element is checked with the built-in
  ``DictKeysValidator`` and ``DictForEachValidator`` (or any
  user-defined ``MemberValidator``) used as inner element
  validators.
- Lists of scalar values where each element is checked or normalized
  by a user-defined validator. For example a custom ``MemberValidator``
  may spell-check each string, convert each string to upper case, or
  apply any other per-element rule that the built-in scalar list
  validators do not cover.

Because ``ListForEachValidator`` is itself a ``MemberValidator``, one
instance can be an element validator of another, so nesting is not
limited to a single inner layer.

The member value must be a list. For each element, in order:

1. If ``element_type`` was provided, the element must be an instance of
   that type.
2. Every validator in ``element_validators`` is invoked on the element,
   in order. Each validator receives the value returned by the previous
   validator, so normalization performed by one inner validator is
   visible to the next one.
3. The final value returned for that element is collected into a new
   list that is returned from ``validate_member``.

When an inner validator is invoked, ``member_name`` is the outer member
name with the element index appended in square brackets, for example
``'matrix[3]'``. The validator's error messages therefore stay precise
about which element failed.

List-level size or ordering checks are intentionally not part of this
class. Use a separate ``ListSizeValidator`` (or any other list
validator) as an earlier or later step in the ``ValidationPlan``.

<a id="config_as_json.list_validators.ListForEachValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(element_validators: Sequence[MemberValidator],
             element_type: Optional[type[object]] = None) -> None
```

Initialize the validator.

**Arguments**:

- `element_validators` - Non-empty sequence of validators to apply
  to each list element, in order. Each entry must be a
  ``MemberValidator``.
- `element_type` - Optional required runtime type of each list
  element. If ``None``, the type check is skipped and the
  inner validators are solely responsible for type checks.


**Raises**:

- `ValueError` - If ``element_validators`` is empty.
- `TypeError` - If any entry of ``element_validators`` is not a
  ``MemberValidator``, or if ``element_type`` is not ``None``
  and not a ``type``.

<a id="config_as_json.list_validators.ListForEachValidator._validate_element_type"></a>

#### \_validate\_element\_type

```python
def _validate_element_type(member_name: str, index: int, element: object,
                           stderr_file: TextIO) -> None
```

Check one element's type when ``element_type`` is configured.

**Arguments**:

- `member_name` - The outer member name used in error messages.
- `index` - The index of the element in the outer list.
- `element` - The element to type-check.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - If ``element`` is not an instance of
  ``self.element_type``.

<a id="config_as_json.list_validators.ListForEachValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one list member by delegating to the inner validators.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the outer list member to validate.
- `member_value` - The list value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  A new list whose elements are the values returned by the last
  inner validator for each element. The caller's list is never
  modified in place.


**Raises**:

- `InvalidConfiguration` - If the member is not a list, an element
  has the wrong runtime type, or a supplied validator raised
  ``InvalidConfiguration``.
- `InvalidConfigurationValue` - If a supplied validator raised
  ``InvalidConfigurationValue``.

<a id="config_as_json.assert_dict_equal"></a>

# config\_as\_json.assert\_dict\_equal

Compare mapping objects while ignoring selected keys.

This primarily exists as a tool for developers of applications that use
configuration classes derived from ``Config``.
It is also useful in test code that wants a readable failure message
before asserting equality of configuration objects in applications that
use the library.

<a id="config_as_json.assert_dict_equal._print_dict_differs"></a>

#### \_print\_dict\_differs

```python
def _print_dict_differs(msg: str,
                        lhs: Mapping[str, object],
                        rhs: Mapping[str, object],
                        stderr_file: TextIO = sys.stderr) -> None
```

Print a detailed mismatch report to standard error.

**Arguments**:

- `msg` - Summary of the mismatch that was detected.
- `lhs` - Left-hand mapping after any ignored keys were removed.
- `rhs` - Right-hand mapping after any ignored keys were removed.
- `stderr_file` - Stream used for diagnostics. Defaults to ``sys.stderr``.

<a id="config_as_json.assert_dict_equal.assert_dict_equal"></a>

#### assert\_dict\_equal

```python
def assert_dict_equal(lhs: Mapping[str, object],
                      rhs: Mapping[str, object],
                      ignorekeys: list[str],
                      stderr_file: TextIO = sys.stderr) -> None
```

Assert that two mappings are equal after ignoring selected keys.

The function makes defensive copies, removes any keys listed in
``ignorekeys`` from both sides, prints a readable difference report when
a mismatch is detected, and finally raises ``AssertionError`` through the
normal ``assert`` statements.

**Arguments**:

- `lhs` - Left-hand mapping to compare.
- `rhs` - Right-hand mapping to compare.
- `ignorekeys` - Keys to drop from both mappings before comparison.
- `stderr_file` - Stream used for diagnostics. Defaults to ``sys.stderr``.


**Raises**:

- `AssertionError` - The mappings do not match after ignored keys have been
  removed.

