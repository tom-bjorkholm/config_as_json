# Table of Contents

* [config\_as\_json.str\_validators](#config_as_json.str_validators)
  * [\_validate\_str\_value](#config_as_json.str_validators._validate_str_value)
  * [\_validate\_static\_len\_bound](#config_as_json.str_validators._validate_static_len_bound)
  * [\_length\_bound](#config_as_json.str_validators._length_bound)
  * [\_validate\_len\_bounds](#config_as_json.str_validators._validate_len_bounds)
  * [StrLenValidator](#config_as_json.str_validators.StrLenValidator)
    * [\_\_init\_\_](#config_as_json.str_validators.StrLenValidator.__init__)
    * [validate\_member](#config_as_json.str_validators.StrLenValidator.validate_member)
  * [StrCaseSpec](#config_as_json.str_validators.StrCaseSpec)
    * [LOWER](#config_as_json.str_validators.StrCaseSpec.LOWER)
    * [UPPER](#config_as_json.str_validators.StrCaseSpec.UPPER)
    * [ORIGINAL](#config_as_json.str_validators.StrCaseSpec.ORIGINAL)
  * [StrPositionSpec](#config_as_json.str_validators.StrPositionSpec)
    * [FIRST\_IN\_STRING](#config_as_json.str_validators.StrPositionSpec.FIRST_IN_STRING)
    * [FIRST\_IN\_WORD](#config_as_json.str_validators.StrPositionSpec.FIRST_IN_WORD)
    * [FIRST\_IN\_SENTENCE](#config_as_json.str_validators.StrPositionSpec.FIRST_IN_SENTENCE)
    * [EVERY\_CHARACTER](#config_as_json.str_validators.StrPositionSpec.EVERY_CHARACTER)
  * [\_validate\_case\_args](#config_as_json.str_validators._validate_case_args)
  * [\_word\_position\_flags](#config_as_json.str_validators._word_position_flags)
  * [\_sentence\_position\_flags](#config_as_json.str_validators._sentence_position_flags)
  * [\_position\_flags](#config_as_json.str_validators._position_flags)
  * [\_case\_spec\_for\_flag](#config_as_json.str_validators._case_spec_for_flag)
  * [\_is\_case\_match](#config_as_json.str_validators._is_case_match)
  * [\_case\_spec\_text](#config_as_json.str_validators._case_spec_text)
  * [\_raise\_case\_error](#config_as_json.str_validators._raise_case_error)
  * [\_change\_case](#config_as_json.str_validators._change_case)
  * [StrCaseValidator](#config_as_json.str_validators.StrCaseValidator)
    * [\_\_init\_\_](#config_as_json.str_validators.StrCaseValidator.__init__)
    * [validate\_member](#config_as_json.str_validators.StrCaseValidator.validate_member)
  * [StrCaseChangeValidator](#config_as_json.str_validators.StrCaseChangeValidator)
    * [\_\_init\_\_](#config_as_json.str_validators.StrCaseChangeValidator.__init__)
    * [validate\_member](#config_as_json.str_validators.StrCaseChangeValidator.validate_member)
  * [StrValidator](#config_as_json.str_validators.StrValidator)
    * [\_\_init\_\_](#config_as_json.str_validators.StrValidator.__init__)
    * [validate\_member](#config_as_json.str_validators.StrValidator.validate_member)
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
  * [\_validate\_type\_argument](#config_as_json.validator._validate_type_argument)
  * [\_validate\_non\_empty\_str\_argument](#config_as_json.validator._validate_non_empty_str_argument)
  * [ValidationStep](#config_as_json.validator.ValidationStep)
    * [apply](#config_as_json.validator.ValidationStep.apply)
  * [WholeConfigValidationStep](#config_as_json.validator.WholeConfigValidationStep)
    * [apply](#config_as_json.validator.WholeConfigValidationStep.apply)
  * [MemberValidationStep](#config_as_json.validator.MemberValidationStep)
    * [apply](#config_as_json.validator.MemberValidationStep.apply)
  * [string\_best\_match](#config_as_json.validator.string_best_match)
  * [IntFloat](#config_as_json.validator.IntFloat)
  * [ConstraintValue](#config_as_json.validator.ConstraintValue)
  * [\_validated\_constraint\_vtype](#config_as_json.validator._validated_constraint_vtype)
  * [\_get\_allowed\_values\_type](#config_as_json.validator._get_allowed_values_type)
  * [\_validate\_allowed\_values\_sequence](#config_as_json.validator._validate_allowed_values_sequence)
  * [\_values\_for\_type](#config_as_json.validator._values_for_type)
  * [\_get\_allowed\_values](#config_as_json.validator._get_allowed_values)
  * [\_ensure\_int\_float\_type](#config_as_json.validator._ensure_int_float_type)
  * [IntFloatValidator](#config_as_json.validator.IntFloatValidator)
    * [\_\_init\_\_](#config_as_json.validator.IntFloatValidator.__init__)
    * [validate\_member](#config_as_json.validator.IntFloatValidator.validate_member)
  * [\_copy\_method\_other\_args](#config_as_json.validator._copy_method_other_args)
  * [\_get\_config\_method](#config_as_json.validator._get_config_method)
  * [\_check\_validation\_only\_method\_result](#config_as_json.validator._check_validation_only_method_result)
  * [CallingMemberValidator](#config_as_json.validator.CallingMemberValidator)
    * [\_\_init\_\_](#config_as_json.validator.CallingMemberValidator.__init__)
    * [validate\_member](#config_as_json.validator.CallingMemberValidator.validate_member)
  * [CallingWholeConfigValidator](#config_as_json.validator.CallingWholeConfigValidator)
    * [\_\_init\_\_](#config_as_json.validator.CallingWholeConfigValidator.__init__)
    * [validate](#config_as_json.validator.CallingWholeConfigValidator.validate)
  * [MemberValidatorSequence](#config_as_json.validator.MemberValidatorSequence)
    * [\_\_init\_\_](#config_as_json.validator.MemberValidatorSequence.__init__)
    * [validate\_member](#config_as_json.validator.MemberValidatorSequence.validate_member)
* [config\_as\_json.optional\_validator](#config_as_json.optional_validator)
  * [\_validate\_mvalidator](#config_as_json.optional_validator._validate_mvalidator)
  * [OptionalMemberValidator](#config_as_json.optional_validator.OptionalMemberValidator)
    * [\_\_init\_\_](#config_as_json.optional_validator.OptionalMemberValidator.__init__)
    * [validate\_member](#config_as_json.optional_validator.OptionalMemberValidator.validate_member)
* [config\_as\_json.\_config\_nesting\_io](#config_as_json._config_nesting_io)
  * [\_NestedConfigEncoder](#config_as_json._config_nesting_io._NestedConfigEncoder)
    * [default](#config_as_json._config_nesting_io._NestedConfigEncoder.default)
  * [\_item\_from\_json](#config_as_json._config_nesting_io._item_from_json)
  * [\_list\_from\_json](#config_as_json._config_nesting_io._list_from_json)
  * [\_dict\_from\_json](#config_as_json._config_nesting_io._dict_from_json)
  * [\_nesting\_by\_key](#config_as_json._config_nesting_io._nesting_by_key)
  * [\_dict\_by\_key\_from\_json](#config_as_json._config_nesting_io._dict_by_key_from_json)
  * [\_is\_dict\_value\_by\_key](#config_as_json._config_nesting_io._is_dict_value_by_key)
  * [\_single\_nesting](#config_as_json._config_nesting_io._single_nesting)
  * [\_nested\_config\_from\_json](#config_as_json._config_nesting_io._nested_config_from_json)
  * [\_item\_json\_data](#config_as_json._config_nesting_io._item_json_data)
  * [\_list\_json\_data](#config_as_json._config_nesting_io._list_json_data)
  * [\_dict\_json\_data](#config_as_json._config_nesting_io._dict_json_data)
  * [\_is\_config\_object](#config_as_json._config_nesting_io._is_config_object)
  * [\_dict\_by\_key\_json\_data](#config_as_json._config_nesting_io._dict_by_key_json_data)
  * [\_nested\_config\_json\_data](#config_as_json._config_nesting_io._nested_config_json_data)
  * [\_validate\_item](#config_as_json._config_nesting_io._validate_item)
  * [\_validate\_list](#config_as_json._config_nesting_io._validate_list)
  * [\_validate\_dict](#config_as_json._config_nesting_io._validate_dict)
  * [\_validate\_dict\_by\_key](#config_as_json._config_nesting_io._validate_dict_by_key)
  * [\_validate\_nested\_config](#config_as_json._config_nesting_io._validate_nested_config)
* [config\_as\_json.config\_auto\_change\_hook](#config_as_json.config_auto_change_hook)
  * [ConfigAutoChangeHook](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook)
    * [\_\_init\_\_](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.__init__)
    * [auto\_changed](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.auto_changed)
    * [old\_key\_handled](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.old_key_handled)
    * [rocf\_missing\_value\_provided](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.rocf_missing_value_provided)
    * [old\_path\_moved](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.old_path_moved)
    * [all\_autochanges\_done](#config_as_json.config_auto_change_hook.ConfigAutoChangeHook.all_autochanges_done)
* [config\_as\_json.config](#config_as_json.config)
  * [ConfigBadJson](#config_as_json.config.ConfigBadJson)
  * [\_over\_ride\_needed](#config_as_json.config._over_ride_needed)
  * [ParseConverter](#config_as_json.config.ParseConverter)
  * [Config](#config_as_json.config.Config)
    * [\_\_init\_\_](#config_as_json.config.Config.__init__)
    * [parse\_converters](#config_as_json.config.Config.parse_converters)
    * [serialize\_converters](#config_as_json.config.Config.serialize_converters)
    * [nested\_configs](#config_as_json.config.Config.nested_configs)
    * [\_get\_read\_old\_configuration](#config_as_json.config.Config._get_read_old_configuration)
    * [check\_key\_match](#config_as_json.config.Config.check_key_match)
    * [check\_dict\_parse](#config_as_json.config.Config.check_dict_parse)
    * [\_json\_parse\_obj\_hook](#config_as_json.config.Config._json_parse_obj_hook)
    * [\_omit\_none\_from\_json](#config_as_json.config.Config._omit_none_from_json)
    * [\_checked\_omit\_none\_from\_json](#config_as_json.config.Config._checked_omit_none_from_json)
    * [\_check\_config\_nesting](#config_as_json.config.Config._check_config_nesting)
    * [\_checked\_config\_nesting\_list](#config_as_json.config.Config._checked_config_nesting_list)
    * [\_check\_config\_nesting\_kinds](#config_as_json.config.Config._check_config_nesting_kinds)
    * [\_checked\_nested\_configs](#config_as_json.config.Config._checked_nested_configs)
    * [\_value\_has\_config](#config_as_json.config.Config._value_has_config)
    * [\_check\_nested\_config\_members](#config_as_json.config.Config._check_nested_config_members)
    * [\_validate\_nested\_configs](#config_as_json.config.Config._validate_nested_configs)
    * [copy\_initial\_data](#config_as_json.config.Config.copy_initial_data)
    * [\_auto\_wrap\_nested\_defaults](#config_as_json.config.Config._auto_wrap_nested_defaults)
    * [parse\_json](#config_as_json.config.Config.parse_json)
    * [\_child\_owned\_paths](#config_as_json.config.Config._child_owned_paths)
    * [as\_json\_string](#config_as_json.config.Config.as_json_string)
    * [read](#config_as_json.config.Config.read)
    * [write](#config_as_json.config.Config.write)
    * [value\_of\_type](#config_as_json.config.Config.value_of_type)
    * [get\_converter\_dict](#config_as_json.config.Config.get_converter_dict)
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
* [config\_as\_json.list\_relation\_validator](#config_as_json.list_relation_validator)
  * [\_validate\_relation\_kind](#config_as_json.list_relation_validator._validate_relation_kind)
  * [\_validate\_member\_name](#config_as_json.list_relation_validator._validate_member_name)
  * [\_validate\_optional\_projector](#config_as_json.list_relation_validator._validate_optional_projector)
  * [\_validate\_comparator](#config_as_json.list_relation_validator._validate_comparator)
  * [\_print\_and\_raise\_type\_error](#config_as_json.list_relation_validator._print_and_raise_type_error)
  * [\_print\_and\_raise\_key\_error](#config_as_json.list_relation_validator._print_and_raise_key_error)
  * [\_print\_and\_raise\_invalid](#config_as_json.list_relation_validator._print_and_raise_invalid)
  * [\_materialized\_sequence](#config_as_json.list_relation_validator._materialized_sequence)
  * [\_contains\_equal](#config_as_json.list_relation_validator._contains_equal)
  * [\_is\_distinct\_subset](#config_as_json.list_relation_validator._is_distinct_subset)
  * [\_is\_multiset\_equal](#config_as_json.list_relation_validator._is_multiset_equal)
  * [\_is\_disjoint](#config_as_json.list_relation_validator._is_disjoint)
  * [ListRelationKind](#config_as_json.list_relation_validator.ListRelationKind)
    * [EQUAL](#config_as_json.list_relation_validator.ListRelationKind.EQUAL)
    * [MULTISET\_EQUAL](#config_as_json.list_relation_validator.ListRelationKind.MULTISET_EQUAL)
    * [SET\_EQUAL](#config_as_json.list_relation_validator.ListRelationKind.SET_EQUAL)
    * [SUBSET](#config_as_json.list_relation_validator.ListRelationKind.SUBSET)
    * [DISJOINT](#config_as_json.list_relation_validator.ListRelationKind.DISJOINT)
  * [ListRelationValidator](#config_as_json.list_relation_validator.ListRelationValidator)
    * [\_\_init\_\_](#config_as_json.list_relation_validator.ListRelationValidator.__init__)
    * [\_relation\_value](#config_as_json.list_relation_validator.ListRelationValidator._relation_value)
    * [\_relation\_holds](#config_as_json.list_relation_validator.ListRelationValidator._relation_holds)
    * [validate](#config_as_json.list_relation_validator.ListRelationValidator.validate)
* [config\_as\_json.projected\_validators](#config_as_json.projected_validators)
  * [\_validate\_projector](#config_as_json.projected_validators._validate_projector)
  * [\_validate\_pseudo\_member\_name](#config_as_json.projected_validators._validate_pseudo_member_name)
  * [\_validate\_optional\_source\_validator](#config_as_json.projected_validators._validate_optional_source_validator)
  * [\_validate\_projected\_validators](#config_as_json.projected_validators._validate_projected_validators)
  * [ProjectedMemberValidator](#config_as_json.projected_validators.ProjectedMemberValidator)
    * [\_\_init\_\_](#config_as_json.projected_validators.ProjectedMemberValidator.__init__)
    * [validate\_member](#config_as_json.projected_validators.ProjectedMemberValidator.validate_member)
  * [ProjectedWholeConfigValidator](#config_as_json.projected_validators.ProjectedWholeConfigValidator)
    * [\_\_init\_\_](#config_as_json.projected_validators.ProjectedWholeConfigValidator.__init__)
    * [validate](#config_as_json.projected_validators.ProjectedWholeConfigValidator.validate)
* [config\_as\_json.type\_validators](#config_as_json.type_validators)
  * [\_validate\_type\_spec](#config_as_json.type_validators._validate_type_spec)
  * [\_copy\_type\_spec](#config_as_json.type_validators._copy_type_spec)
  * [\_format\_type\_names](#config_as_json.type_validators._format_type_names)
  * [\_matches\_type\_spec](#config_as_json.type_validators._matches_type_spec)
  * [\_validate\_strict](#config_as_json.type_validators._validate_strict)
  * [\_validate\_allowed\_denied](#config_as_json.type_validators._validate_allowed_denied)
  * [\_type\_is\_denied](#config_as_json.type_validators._type_is_denied)
  * [\_raise\_type\_error](#config_as_json.type_validators._raise_type_error)
  * [\_raise\_denied\_error](#config_as_json.type_validators._raise_denied_error)
  * [\_matching\_type](#config_as_json.type_validators._matching_type)
  * [\_type\_rank](#config_as_json.type_validators._type_rank)
  * [\_validate\_convert\_map](#config_as_json.type_validators._validate_convert_map)
  * [\_validate\_no\_overlap](#config_as_json.type_validators._validate_no_overlap)
  * [\_raise\_conversion\_error](#config_as_json.type_validators._raise_conversion_error)
  * [\_validate\_converted\_value](#config_as_json.type_validators._validate_converted_value)
  * [InvalidConfigurationType](#config_as_json.type_validators.InvalidConfigurationType)
  * [ValueTypeValidator](#config_as_json.type_validators.ValueTypeValidator)
    * [\_\_init\_\_](#config_as_json.type_validators.ValueTypeValidator.__init__)
    * [validate\_member](#config_as_json.type_validators.ValueTypeValidator.validate_member)
  * [ValueAsTypeValidator](#config_as_json.type_validators.ValueAsTypeValidator)
    * [\_\_init\_\_](#config_as_json.type_validators.ValueAsTypeValidator.__init__)
    * [validate\_member](#config_as_json.type_validators.ValueAsTypeValidator.validate_member)
    * [\_conversion\_input\_types](#config_as_json.type_validators.ValueAsTypeValidator._conversion_input_types)
    * [\_use\_direct](#config_as_json.type_validators.ValueAsTypeValidator._use_direct)
    * [\_convert\_direct](#config_as_json.type_validators.ValueAsTypeValidator._convert_direct)
    * [\_convert\_with\_func](#config_as_json.type_validators.ValueAsTypeValidator._convert_with_func)
* [config\_as\_json.commontypes](#config_as_json.commontypes)
  * [json\_types](#config_as_json.commontypes.json_types)
* [config\_as\_json.dict\_validators](#config_as_json.dict_validators)
  * [\_validate\_dict\_member\_value](#config_as_json.dict_validators._validate_dict_member_value)
  * [\_validate\_string\_keys](#config_as_json.dict_validators._validate_string_keys)
  * [\_validate\_hashable\_keys](#config_as_json.dict_validators._validate_hashable_keys)
  * [\_validate\_bool\_argument](#config_as_json.dict_validators._validate_bool_argument)
  * [\_validate\_hashable\_type](#config_as_json.dict_validators._validate_hashable_type)
  * [\_inner\_member\_name](#config_as_json.dict_validators._inner_member_name)
  * [DictKeysValidator](#config_as_json.dict_validators.DictKeysValidator)
    * [\_\_init\_\_](#config_as_json.dict_validators.DictKeysValidator.__init__)
    * [validate\_member](#config_as_json.dict_validators.DictKeysValidator.validate_member)
  * [accept\_all\_keys](#config_as_json.dict_validators.accept_all_keys)
  * [DictRule](#config_as_json.dict_validators.DictRule)
    * [\_\_post\_init\_\_](#config_as_json.dict_validators.DictRule.__post_init__)
  * [\_validate\_for\_each\_rules](#config_as_json.dict_validators._validate_for_each_rules)
  * [DictForEachValidator](#config_as_json.dict_validators.DictForEachValidator)
    * [\_\_init\_\_](#config_as_json.dict_validators.DictForEachValidator.__init__)
    * [\_run\_rule\_on\_key](#config_as_json.dict_validators.DictForEachValidator._run_rule_on_key)
    * [validate\_member](#config_as_json.dict_validators.DictForEachValidator.validate_member)
  * [DictKeyValueTypesValidator](#config_as_json.dict_validators.DictKeyValueTypesValidator)
    * [\_\_init\_\_](#config_as_json.dict_validators.DictKeyValueTypesValidator.__init__)
    * [validate\_member](#config_as_json.dict_validators.DictKeyValueTypesValidator.validate_member)
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
  * [\_validate\_list\_element\_type](#config_as_json.list_validators._validate_list_element_type)
  * [\_validate\_list\_size\_bounds](#config_as_json.list_validators._validate_list_size_bounds)
  * [\_validate\_list\_member\_value](#config_as_json.list_validators._validate_list_member_value)
  * [\_validate\_typed\_list\_member](#config_as_json.list_validators._validate_typed_list_member)
  * [\_sort\_list\_values](#config_as_json.list_validators._sort_list_values)
  * [\_unique\_list\_values](#config_as_json.list_validators._unique_list_values)
  * [\_validate\_list\_order](#config_as_json.list_validators._validate_list_order)
  * [\_validate\_unique\_list\_values](#config_as_json.list_validators._validate_unique_list_values)
  * [\_indexed\_not\_allowed\_message](#config_as_json.list_validators._indexed_not_allowed_message)
  * [\_IndexedInvalidConfigurationValue](#config_as_json.list_validators._IndexedInvalidConfigurationValue)
    * [\_\_init\_\_](#config_as_json.list_validators._IndexedInvalidConfigurationValue.__init__)
  * [ListValueValidator](#config_as_json.list_validators.ListValueValidator)
    * [\_\_init\_\_](#config_as_json.list_validators.ListValueValidator.__init__)
    * [validate\_member](#config_as_json.list_validators.ListValueValidator.validate_member)
  * [ListSizeValidator](#config_as_json.list_validators.ListSizeValidator)
    * [\_\_init\_\_](#config_as_json.list_validators.ListSizeValidator.__init__)
    * [validate\_member](#config_as_json.list_validators.ListSizeValidator.validate_member)
  * [ListValueTypeValidator](#config_as_json.list_validators.ListValueTypeValidator)
    * [\_\_init\_\_](#config_as_json.list_validators.ListValueTypeValidator.__init__)
    * [validate\_member](#config_as_json.list_validators.ListValueTypeValidator.validate_member)
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
  * [ListOfDictsKeysValidator](#config_as_json.list_validators.ListOfDictsKeysValidator)
    * [\_\_init\_\_](#config_as_json.list_validators.ListOfDictsKeysValidator.__init__)
    * [validate\_member](#config_as_json.list_validators.ListOfDictsKeysValidator.validate_member)
* [config\_as\_json.assert\_dict\_equal](#config_as_json.assert_dict_equal)
  * [\_print\_dict\_differs](#config_as_json.assert_dict_equal._print_dict_differs)
  * [assert\_dict\_equal](#config_as_json.assert_dict_equal.assert_dict_equal)
* [config\_as\_json.read\_old\_configuration](#config_as_json.read_old_configuration)
  * [RocfKeyMove](#config_as_json.read_old_configuration.RocfKeyMove)
  * [RocfKeyRename](#config_as_json.read_old_configuration.RocfKeyRename)
  * [RocfConflictError](#config_as_json.read_old_configuration.RocfConflictError)
  * [RocfIncompatiblePathError](#config_as_json.read_old_configuration.RocfIncompatiblePathError)
  * [\_MovedValue](#config_as_json.read_old_configuration._MovedValue)
  * [\_MoveContext](#config_as_json.read_old_configuration._MoveContext)
  * [\_as\_dict](#config_as_json.read_old_configuration._as_dict)
  * [\_as\_list](#config_as_json.read_old_configuration._as_list)
  * [\_path\_text](#config_as_json.read_old_configuration._path_text)
  * [\_validate\_path](#config_as_json.read_old_configuration._validate_path)
  * [\_list\_marker\_count](#config_as_json.read_old_configuration._list_marker_count)
  * [\_validate\_move](#config_as_json.read_old_configuration._validate_move)
  * [\_conflict\_diag](#config_as_json.read_old_configuration._conflict_diag)
  * [\_remove\_key\_recursive](#config_as_json.read_old_configuration._remove_key_recursive)
  * [\_rename\_key\_recursive](#config_as_json.read_old_configuration._rename_key_recursive)
  * [\_collect\_path\_values](#config_as_json.read_old_configuration._collect_path_values)
  * [\_target\_path](#config_as_json.read_old_configuration._target_path)
  * [\_delete\_path](#config_as_json.read_old_configuration._delete_path)
  * [\_path\_exists](#config_as_json.read_old_configuration._path_exists)
  * [\_path\_is\_prefix](#config_as_json.read_old_configuration._path_is_prefix)
  * [\_paths\_overlap](#config_as_json.read_old_configuration._paths_overlap)
  * [\_wrap\_prefix](#config_as_json.read_old_configuration._wrap_prefix)
  * [\_get\_existing\_value](#config_as_json.read_old_configuration._get_existing_value)
  * [\_container\_for](#config_as_json.read_old_configuration._container_for)
  * [\_require\_dict](#config_as_json.read_old_configuration._require_dict)
  * [\_require\_list](#config_as_json.read_old_configuration._require_list)
  * [\_write\_path](#config_as_json.read_old_configuration._write_path)
  * [\_remove\_path](#config_as_json.read_old_configuration._remove_path)
  * [\_apply\_missing](#config_as_json.read_old_configuration._apply_missing)
  * [ReadOldConfiguration](#config_as_json.read_old_configuration.ReadOldConfiguration)
    * [process\_json](#config_as_json.read_old_configuration.ReadOldConfiguration.process_json)
    * [\_remove\_keys\_recursively](#config_as_json.read_old_configuration.ReadOldConfiguration._remove_keys_recursively)
    * [\_remove\_keys\_by\_path](#config_as_json.read_old_configuration.ReadOldConfiguration._remove_keys_by_path)
    * [\_rename\_json\_keys](#config_as_json.read_old_configuration.ReadOldConfiguration._rename_json_keys)
    * [\_move\_json\_keys](#config_as_json.read_old_configuration.ReadOldConfiguration._move_json_keys)
    * [\_move\_one\_path](#config_as_json.read_old_configuration.ReadOldConfiguration._move_one_path)
    * [\_target\_is\_current](#config_as_json.read_old_configuration.ReadOldConfiguration._target_is_current)
    * [\_apply\_missing\_values](#config_as_json.read_old_configuration.ReadOldConfiguration._apply_missing_values)
    * [get\_json\_key\_moves](#config_as_json.read_old_configuration.ReadOldConfiguration.get_json_key_moves)
    * [get\_keys\_to\_remove\_recursively](#config_as_json.read_old_configuration.ReadOldConfiguration.get_keys_to_remove_recursively)
    * [get\_keys\_to\_remove](#config_as_json.read_old_configuration.ReadOldConfiguration.get_keys_to_remove)
    * [get\_values\_for\_missing\_json\_keys](#config_as_json.read_old_configuration.ReadOldConfiguration.get_values_for_missing_json_keys)
    * [get\_json\_key\_renames](#config_as_json.read_old_configuration.ReadOldConfiguration.get_json_key_renames)
    * [pre\_process\_json](#config_as_json.read_old_configuration.ReadOldConfiguration.pre_process_json)
    * [post\_process\_json](#config_as_json.read_old_configuration.ReadOldConfiguration.post_process_json)
* [config\_as\_json.\_config\_initial\_data](#config_as_json._config_initial_data)
  * [\_public\_items\_of](#config_as_json._config_initial_data._public_items_of)
  * [\_public\_items\_of\_mapping](#config_as_json._config_initial_data._public_items_of_mapping)
  * [\_public\_items\_of\_object](#config_as_json._config_initial_data._public_items_of_object)
  * [copy\_initial\_data\_impl](#config_as_json._config_initial_data.copy_initial_data_impl)
  * [\_wrap\_one\_value](#config_as_json._config_initial_data._wrap_one_value)
  * [\_wrap\_optional\_or\_member](#config_as_json._config_initial_data._wrap_optional_or_member)
  * [\_wrap\_list\_elements](#config_as_json._config_initial_data._wrap_list_elements)
  * [\_wrap\_dict\_values](#config_as_json._config_initial_data._wrap_dict_values)
  * [\_wrap\_dict\_value\_by\_key](#config_as_json._config_initial_data._wrap_dict_value_by_key)
  * [\_nesting\_by\_key](#config_as_json._config_initial_data._nesting_by_key)
  * [\_auto\_wrap\_one\_member](#config_as_json._config_initial_data._auto_wrap_one_member)
  * [auto\_wrap\_nested\_defaults\_impl](#config_as_json._config_initial_data.auto_wrap_nested_defaults_impl)
* [config\_as\_json.as\_dict\_view\_validator](#config_as_json.as_dict_view_validator)
  * [public\_attrs\_to\_dict](#config_as_json.as_dict_view_validator.public_attrs_to_dict)
  * [\_validate\_non\_dict\_type](#config_as_json.as_dict_view_validator._validate_non_dict_type)
  * [\_validate\_to\_dict](#config_as_json.as_dict_view_validator._validate_to_dict)
  * [\_validate\_rules](#config_as_json.as_dict_view_validator._validate_rules)
  * [\_validate\_validators](#config_as_json.as_dict_view_validator._validate_validators)
  * [\_ensure\_work\_exists](#config_as_json.as_dict_view_validator._ensure_work_exists)
  * [\_raise\_invalid\_member\_type](#config_as_json.as_dict_view_validator._raise_invalid_member_type)
  * [\_validate\_projected\_dict](#config_as_json.as_dict_view_validator._validate_projected_dict)
  * [\_validate\_dict\_view\_step](#config_as_json.as_dict_view_validator._validate_dict_view_step)
  * [\_validation\_chain](#config_as_json.as_dict_view_validator._validation_chain)
  * [AsDictViewValidator](#config_as_json.as_dict_view_validator.AsDictViewValidator)
    * [\_\_init\_\_](#config_as_json.as_dict_view_validator.AsDictViewValidator.__init__)
    * [\_validate\_dict\_view](#config_as_json.as_dict_view_validator.AsDictViewValidator._validate_dict_view)
    * [validate\_member](#config_as_json.as_dict_view_validator.AsDictViewValidator.validate_member)
* [config\_as\_json.json\_write\_hooks](#config_as_json.json_write_hooks)
  * [SerializeConverter](#config_as_json.json_write_hooks.SerializeConverter)
  * [JsonWriteHookError](#config_as_json.json_write_hooks.JsonWriteHookError)
  * [SerializeSelectorError](#config_as_json.json_write_hooks.SerializeSelectorError)
  * [\_is\_path\_selector](#config_as_json.json_write_hooks._is_path_selector)
  * [\_selector\_repr](#config_as_json.json_write_hooks._selector_repr)
  * [\_validate\_one\_selector](#config_as_json.json_write_hooks._validate_one_selector)
  * [\_split\_selectors](#config_as_json.json_write_hooks._split_selectors)
  * [\_check\_rec\_vs\_path\_conflicts](#config_as_json.json_write_hooks._check_rec_vs_path_conflicts)
  * [\_path\_matches\_or\_extends](#config_as_json.json_write_hooks._path_matches_or_extends)
  * [\_check\_child\_boundaries](#config_as_json.json_write_hooks._check_child_boundaries)
  * [\_append\_path\_text](#config_as_json.json_write_hooks._append_path_text)
  * [\_check\_json\_compatible](#config_as_json.json_write_hooks._check_json_compatible)
  * [\_apply\_one\_converter](#config_as_json.json_write_hooks._apply_one_converter)
  * [\_builtin\_fallback](#config_as_json.json_write_hooks._builtin_fallback)
  * [\_is\_inside\_child\_owned](#config_as_json.json_write_hooks._is_inside_child_owned)
  * [\_has\_path\_inside](#config_as_json.json_write_hooks._has_path_inside)
  * [\_WalkContext](#config_as_json.json_write_hooks._WalkContext)
  * [\_convert\_dict](#config_as_json.json_write_hooks._convert_dict)
  * [\_convert\_list](#config_as_json.json_write_hooks._convert_list)
  * [\_passthrough\_child](#config_as_json.json_write_hooks._passthrough_child)
  * [\_convert\_value](#config_as_json.json_write_hooks._convert_value)
  * [apply\_serialize\_converters](#config_as_json.json_write_hooks.apply_serialize_converters)
* [config\_as\_json.config\_nesting](#config_as_json.config_nesting)
  * [ConfigNestingKind](#config_as_json.config_nesting.ConfigNestingKind)
  * [ConfigFactory](#config_as_json.config_nesting.ConfigFactory)
    * [\_\_call\_\_](#config_as_json.config_nesting.ConfigFactory.__call__)
  * [ConfigNesting](#config_as_json.config_nesting.ConfigNesting)

<a id="config_as_json.str_validators"></a>

# config\_as\_json.str\_validators

Validate strings.

<a id="config_as_json.str_validators._validate_str_value"></a>

#### \_validate\_str\_value

```python
def _validate_str_value(member_name: str, member_value: object,
                        stderr_file: TextIO) -> str
```

Validate and return one string member value.

<a id="config_as_json.str_validators._validate_static_len_bound"></a>

#### \_validate\_static\_len\_bound

```python
def _validate_static_len_bound(value: object, parameter_name: str) -> None
```

Validate one static string length bound or callable placeholder.

<a id="config_as_json.str_validators._length_bound"></a>

#### \_length\_bound

```python
def _length_bound(value: Optional[int] | Callable[[], Optional[int]],
                  parameter_name: str) -> Optional[int]
```

Return one dynamic length bound after runtime validation.

<a id="config_as_json.str_validators._validate_len_bounds"></a>

#### \_validate\_len\_bounds

```python
def _validate_len_bounds(min_length: Optional[int],
                         max_length: Optional[int]) -> None
```

Validate the relationship between two active length bounds.

<a id="config_as_json.str_validators.StrLenValidator"></a>

## StrLenValidator Objects

```python
class StrLenValidator(MemberValidator)
```

Validate length of a string member.

<a id="config_as_json.str_validators.StrLenValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(min_length: Optional[int] | Callable[[], Optional[int]],
             max_length: Optional[int] | Callable[[], Optional[int]]) -> None
```

Initialize the validator.

A validator that validates the length of a string member.

**Arguments**:

- `min_length` - The minimum length of the string member.
  If a callable is provided, it will be called
  at validation time to get the minimum length.
  A callable may return ``None`` to skip this bound.
- `max_length` - The maximum length of the string member.
  If a callable is provided, it will be called
  at validation time to get the maximum length.
  A callable may return ``None`` to skip this bound.


**Raises**:

- `TypeError` - If a static bound is not an int, None, or callable.
- `ValueError` - If a static bound is negative, if static bounds are
  ordered incorrectly, or if both static bounds are None.

<a id="config_as_json.str_validators.StrLenValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate the length of a string member.

**Arguments**:

- `config` - The configuration object to validate.
- `member_name` - The name of the member to validate.
- `member_value` - The value of the member to validate, which is a
  string.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - The configuration is invalid.
- `InvalidConfiguration` - The member value is not a string.


**Returns**:

  The member value unchanged if the validation passes, otherwise
  an exception is raised.

<a id="config_as_json.str_validators.StrCaseSpec"></a>

## StrCaseSpec Objects

```python
class StrCaseSpec(Enum)
```

Specification for string case.

<a id="config_as_json.str_validators.StrCaseSpec.LOWER"></a>

#### LOWER

Character(s) in the position shall be lowercase.

<a id="config_as_json.str_validators.StrCaseSpec.UPPER"></a>

#### UPPER

Character(s) in the position shall be uppercase.

<a id="config_as_json.str_validators.StrCaseSpec.ORIGINAL"></a>

#### ORIGINAL

Character(s) in the position shall be original case.

When converting this means no conversion is performed.
When validating/checking this means any case is allowed.

<a id="config_as_json.str_validators.StrPositionSpec"></a>

## StrPositionSpec Objects

```python
class StrPositionSpec(Enum)
```

Specification for string position.

<a id="config_as_json.str_validators.StrPositionSpec.FIRST_IN_STRING"></a>

#### FIRST\_IN\_STRING

First character in the string.

<a id="config_as_json.str_validators.StrPositionSpec.FIRST_IN_WORD"></a>

#### FIRST\_IN\_WORD

First character in every word.

This is the first non-whitespace character in the string, and the first
non-whitespace character after a whitespace character.

<a id="config_as_json.str_validators.StrPositionSpec.FIRST_IN_SENTENCE"></a>

#### FIRST\_IN\_SENTENCE

First character in every sentence.

This is the first non-whitespace character in the string, and the first
non-whitespace character after a period, exclamation mark, or question
mark.

<a id="config_as_json.str_validators.StrPositionSpec.EVERY_CHARACTER"></a>

#### EVERY\_CHARACTER

Every character in the string.

<a id="config_as_json.str_validators._validate_case_args"></a>

#### \_validate\_case\_args

```python
def _validate_case_args(special_position: StrPositionSpec,
                        special_position_case: StrCaseSpec,
                        other_position_case: StrCaseSpec) -> None
```

Validate constructor arguments for string case validators.

<a id="config_as_json.str_validators._word_position_flags"></a>

#### \_word\_position\_flags

```python
def _word_position_flags(value: str) -> list[bool]
```

Return flags for first non-whitespace characters in words.

<a id="config_as_json.str_validators._sentence_position_flags"></a>

#### \_sentence\_position\_flags

```python
def _sentence_position_flags(value: str) -> list[bool]
```

Return flags for first non-whitespace characters in sentences.

<a id="config_as_json.str_validators._position_flags"></a>

#### \_position\_flags

```python
def _position_flags(value: str,
                    special_position: StrPositionSpec) -> list[bool]
```

Return flags for the positions selected by one position spec.

<a id="config_as_json.str_validators._case_spec_for_flag"></a>

#### \_case\_spec\_for\_flag

```python
def _case_spec_for_flag(is_special: bool, special_position_case: StrCaseSpec,
                        other_position_case: StrCaseSpec) -> StrCaseSpec
```

Return the case specification for one position flag.

<a id="config_as_json.str_validators._is_case_match"></a>

#### \_is\_case\_match

```python
def _is_case_match(character: str, case_spec: StrCaseSpec) -> bool
```

Return whether one character matches one case specification.

<a id="config_as_json.str_validators._case_spec_text"></a>

#### \_case\_spec\_text

```python
def _case_spec_text(case_spec: StrCaseSpec) -> str
```

Return a human-readable name for one case specification.

<a id="config_as_json.str_validators._raise_case_error"></a>

#### \_raise\_case\_error

```python
def _raise_case_error(member_name: str, character: str, index: int,
                      case_spec: StrCaseSpec, stderr_file: TextIO) -> None
```

Raise a validation error for one incorrectly cased character.

<a id="config_as_json.str_validators._change_case"></a>

#### \_change\_case

```python
def _change_case(character: str, case_spec: StrCaseSpec) -> str
```

Return one character converted according to a case specification.

<a id="config_as_json.str_validators.StrCaseValidator"></a>

## StrCaseValidator Objects

```python
class StrCaseValidator(MemberValidator)
```

Validate (upper/lower) case of a string member.

<a id="config_as_json.str_validators.StrCaseValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(special_position: StrPositionSpec,
             special_position_case: StrCaseSpec,
             other_position_case: StrCaseSpec) -> None
```

Initialize the validator.

A validator that validates the (upper/lower) case of a string member.

**Arguments**:

- `special_position` - The position of the special characters.
  To what position(s) in the string shall
  the special_position_case apply?
- `special_position_case` - The case of the special characters.
  The case that the character(s) in the special
  position(s) (as specified by special_position)
  shall have.
- `other_position_case` - The case of the other characters.
  The case that the character(s) in the other
  position(s) (that is every position not matching
  the special_position) shall have.


**Raises**:

- `TypeError` - If one argument is not the expected enum type.

<a id="config_as_json.str_validators.StrCaseValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate the (upper/lower) case of a string member.

The validation is performed by checking the case of the characters in
the special position(s) and the other position(s).

**Arguments**:

- `config` - The configuration object to validate.
- `member_name` - The name of the member to validate.
- `member_value` - The value of the member to validate, which is a
  string.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - The configuration is invalid. One or more
  characters in the string do not match the case specification.
- `InvalidConfiguration` - The member value is not a string.


**Returns**:

  The member value unchanged if the validation passes, otherwise
  an exception is raised.

<a id="config_as_json.str_validators.StrCaseChangeValidator"></a>

## StrCaseChangeValidator Objects

```python
class StrCaseChangeValidator(MemberValidator)
```

Change the (upper/lower) case of a string member.

<a id="config_as_json.str_validators.StrCaseChangeValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(special_position: StrPositionSpec,
             special_position_case: StrCaseSpec,
             other_position_case: StrCaseSpec) -> None
```

Initialize the validator.

A validator that changes the (upper/lower) case of a string member.

**Arguments**:

- `special_position` - The position of the special characters.
  To what position(s) in the string shall
  the special_position_case apply?
- `special_position_case` - The case of the special characters.
  The case that the character(s) in the special
  position(s) (as specified by special_position)
  shall be changed to.
- `other_position_case` - The case of the other characters.
  The case that the character(s) in the other
  position(s) (that is every position not matching
  the special_position) shall be changed to.


**Raises**:

- `TypeError` - If one argument is not the expected enum type.

<a id="config_as_json.str_validators.StrCaseChangeValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Change the (upper/lower) case of a string member.

The change is performed by converting the case of the characters in
the special position(s) and the other position(s).

**Arguments**:

- `config` - The configuration object to validate.
- `member_name` - The name of the member to validate.
- `member_value` - The value of the member to validate, which is a
  string.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - The member value is not a string.


**Returns**:

  The member value changed to the new case if the validation passes,
  otherwise an exception is raised.

<a id="config_as_json.str_validators.StrValidator"></a>

## StrValidator Objects

```python
class StrValidator(MemberValidator)
```

Validate one string member against allowed string values.

<a id="config_as_json.str_validators.StrValidator.__init__"></a>

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

<a id="config_as_json.str_validators.StrValidator.validate_member"></a>

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

<a id="config_as_json.validator._validate_type_argument"></a>

#### \_validate\_type\_argument

```python
def _validate_type_argument(value_type: object,
                            parameter_name: str) -> type[object]
```

Validate and return one runtime type argument.

**Arguments**:

- `value_type` - Value supplied as a runtime type argument.
- `parameter_name` - Name used in the error message.


**Returns**:

  ``value_type`` after it has been proven to be a type.


**Raises**:

- `TypeError` - ``value_type`` is not a type.

<a id="config_as_json.validator._validate_non_empty_str_argument"></a>

#### \_validate\_non\_empty\_str\_argument

```python
def _validate_non_empty_str_argument(value: object,
                                     parameter_name: str) -> str
```

Validate and return one non-empty string argument.

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

<a id="config_as_json.validator.IntFloat"></a>

#### IntFloat

Numeric type accepted by IntFloatValidator.

<a id="config_as_json.validator.ConstraintValue"></a>

#### ConstraintValue

Value type used when validating shared constraint arguments.

<a id="config_as_json.validator._validated_constraint_vtype"></a>

#### \_validated\_constraint\_vtype

```python
def _validated_constraint_vtype(
    min_value: Optional[ConstraintValue],
    max_value: Optional[ConstraintValue],
    allowed_values: Optional[Sequence[ConstraintValue]],
    lt_comparator: Callable[[ConstraintValue, ConstraintValue],
                            bool] = operator_lt
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

<a id="config_as_json.validator._get_allowed_values_type"></a>

#### \_get\_allowed\_values\_type

```python
def _get_allowed_values_type(allowed_values: object) -> type[ConstraintValue]
```

Return the type of the first value in a non-empty sequence.

<a id="config_as_json.validator._validate_allowed_values_sequence"></a>

#### \_validate\_allowed\_values\_sequence

```python
def _validate_allowed_values_sequence(
        allowed_values: object,
        value_type: type[ConstraintValue]) -> Sequence[ConstraintValue]
```

Validate allowed-values sequence shape and element type.

<a id="config_as_json.validator._values_for_type"></a>

#### \_values\_for\_type

```python
def _values_for_type(
    min_value: Optional[ConstraintValue], max_value: Optional[ConstraintValue],
    allowed_values: Optional[Sequence[ConstraintValue]
                             | Callable[[], Sequence[ConstraintValue]]]
) -> Optional[Sequence[ConstraintValue]]
```

Return allowed values needed for constructor type inference.

<a id="config_as_json.validator._get_allowed_values"></a>

#### \_get\_allowed\_values

```python
def _get_allowed_values(
        allowed_values: Optional[Sequence[ConstraintValue]
                                 | Callable[[], Sequence[ConstraintValue]]],
        value_type: type[ConstraintValue]
) -> Optional[Sequence[ConstraintValue]]
```

Return the allowed values to use for the current validation.

<a id="config_as_json.validator._ensure_int_float_type"></a>

#### \_ensure\_int\_float\_type

```python
def _ensure_int_float_type(value_type: type[object]) -> None
```

Reject unsupported runtime types for IntFloatValidator.

<a id="config_as_json.validator.IntFloatValidator"></a>

## IntFloatValidator Objects

```python
class IntFloatValidator(MemberValidator, Generic[IntFloat])
```

Validate one int or float member against numeric constraints.

<a id="config_as_json.validator.IntFloatValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(
    min_value: Optional[IntFloat], max_value: Optional[IntFloat],
    allowed_values: Optional[Sequence[IntFloat]
                             | Callable[[], Sequence[IntFloat]]]
) -> None
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
  If a callable, it is called to get the allowed values.


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

<a id="config_as_json.validator._copy_method_other_args"></a>

#### \_copy\_method\_other\_args

```python
def _copy_method_other_args(
        other_args: Optional[Mapping[str, object]]) -> dict[str, object]
```

Validate and copy additional keyword arguments for a method call.

<a id="config_as_json.validator._get_config_method"></a>

#### \_get\_config\_method

```python
def _get_config_method(config: 'Config', method_name: str,
                       stderr_file: TextIO) -> Callable[..., object]
```

Return one callable method from a Config object.

<a id="config_as_json.validator._check_validation_only_method_result"></a>

#### \_check\_validation\_only\_method\_result

```python
def _check_validation_only_method_result(method_name: str, result: object,
                                         stderr_file: TextIO) -> None
```

Validate the return value from a validation-only method call.

<a id="config_as_json.validator.CallingMemberValidator"></a>

## CallingMemberValidator Objects

```python
class CallingMemberValidator(MemberValidator)
```

Validate one member by calling a method of the Config object.

The validator calls a method of the Config object with the given arguments.
The method must accept all arguments as keyword arguments. The method is
expected to validate the member value. This validator is most useful when
the configuration class is multiply derived from Config and from a class
in a third-party library, and the class in the third-party library has
validation logic.

The method may indicate that the member value is invalid by raising an
exception, or in validation-only mode by returning False. In
validation-only mode, a return value of None or True is considered valid
and the original member value is kept. In normalizing mode, the method is
expected to return the validated and normalized value.

<a id="config_as_json.validator.CallingMemberValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(method_name: str,
             arg_name_value: str,
             arg_name_member_name: Optional[str] = None,
             other_args: Optional[Mapping[str, object]] = None,
             normalizing: bool = False) -> None
```

Initialize the validator.

The validator calls a method of the Config object with the given
arguments. The method must accept all arguments as keyword arguments.

The method may indicate that the member value is invalid by raising an
exception, or in validation-only mode by returning False. In
validation-only mode, a return value of None or True indicates a valid
member value and the original member value is kept. In normalizing
mode, the method is expected to return the validated and normalized
value.

**Arguments**:

- `method_name` - The name of the method to call on the Config object.
  The method must accept all arguments as keyword
  arguments.
- `arg_name_value` - The name of the argument to the method that
  contains the value passed in to be validated.
- `arg_name_member_name` - The name of the argument to the method that
  contains the name of the member that is
  being validated. If ``None``, the member name
  is not passed to the method.
- `other_args` - Other arguments to the method. If ``None``, no other
  arguments are passed to the method.
- `normalizing` - Whether the method returns a normalized member value.
  If ``False``, the method is expected to return None
  or True if valid, and to return False if invalid.
  If ``True``, the method is expected to return the
  validated and normalized value.


**Raises**:

- `TypeError` - If one constructor argument has an invalid type.
- `ValueError` - If one argument name is empty or would overwrite
  another generated argument.

<a id="config_as_json.validator.CallingMemberValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one member by calling a method of the Config object.

**Arguments**:

- `config` - The Config object to validate.
- `member_name` - The name of the member to validate.
- `member_value` - The value of the member to validate.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - The configuration is invalid.
- `InvalidConfigurationValue` - The value of a configuration member is
  not one of the allowed values.
  Any exception raised by the method in the Config object.


**Returns**:

  The original member value in validation-only mode, or the
  validated and normalized value in normalizing mode.

<a id="config_as_json.validator.CallingWholeConfigValidator"></a>

## CallingWholeConfigValidator Objects

```python
class CallingWholeConfigValidator(WholeConfigValidator)
```

Validate complete Config by calling a method of the Config object.

The validator calls a method of the Config object with the given arguments.
The method must accept all arguments as keyword arguments. The method is
expected to validate the configuration. This validator is most useful when
the configuration class is multiply derived from Config and from a class
in a third-party library, and the class in the third-party library has
validation logic.

The method may indicate that the configuration is invalid by raising an
exception, or by returning False.
The method is expected to return None or True if the configuration is
valid.

<a id="config_as_json.validator.CallingWholeConfigValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(method_name: str,
             other_args: Optional[Mapping[str, object]] = None) -> None
```

Initialize the validator.

The validator calls a method of the Config object with the given
arguments. The method must accept all arguments as keyword arguments.

The method may indicate that the configuration is invalid by raising an
exception, or by returning False.
A return value of None or True is indicating a valid configuration.

The method may mutate the Config object directly if needed to
normalize the configuration.

**Arguments**:

- `method_name` - The name of the method to call on the Config object.
  The method must accept all arguments as keyword
  arguments.
- `other_args` - Other arguments to the method. If ``None``, no other
  arguments are passed to the method.


**Raises**:

- `TypeError` - If one constructor argument has an invalid type.
- `ValueError` - If one argument name is empty.

<a id="config_as_json.validator.CallingWholeConfigValidator.validate"></a>

#### validate

```python
def validate(config: 'Config', stderr_file: TextIO = sys.stderr) -> None
```

Validate the entire Config object by calling a method in it.

**Arguments**:

- `config` - The Config object to validate.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfiguration` - The configuration is invalid.
  Any exception raised by the method in the Config object.

<a id="config_as_json.validator.MemberValidatorSequence"></a>

## MemberValidatorSequence Objects

```python
class MemberValidatorSequence(MemberValidator)
```

Validate one member by applying a sequence of validators.

The validator applies a sequence of validators to the member value.
The sequence is applied in order, and the output of each validator is
passed as the input to the next validator.

This is useful when several validators need to be applied to the
same member value, before moving on to the next member.
When validating several member values with ValidationPlan the natural
order is to apply the same validator to several member values before
moving on to the next ValidationStep that has another validator.
MemberValidatorSequence thus has a natural order that is different from
the order easily specified by ValidationPlan.

<a id="config_as_json.validator.MemberValidatorSequence.__init__"></a>

#### \_\_init\_\_

```python
def __init__(validators: Sequence[MemberValidator]) -> None
```

Initialize the validator.

**Arguments**:

- `validators` - The sequence of validators to apply.


**Raises**:

- `TypeError` - If ``validators`` is not a sequence or one entry is not
  a ``MemberValidator``.
- `ValueError` - If ``validators`` is empty.

<a id="config_as_json.validator.MemberValidatorSequence.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one member by applying a sequence of validators.

**Arguments**:

- `config` - The Config object to validate.
- `member_name` - The name of the member to validate.
- `member_value` - The value of the member to validate.
- `stderr_file` - The file to write error messages to.

<a id="config_as_json.optional_validator"></a>

# config\_as\_json.optional\_validator

Optional validator.

<a id="config_as_json.optional_validator._validate_mvalidator"></a>

#### \_validate\_mvalidator

```python
def _validate_mvalidator(
        validator: MemberValidator | list[MemberValidator]) -> MemberValidator
```

Validate a MemberValidator or list of MemberValidators.

<a id="config_as_json.optional_validator.OptionalMemberValidator"></a>

## OptionalMemberValidator Objects

```python
class OptionalMemberValidator(MemberValidator)
```

Validate an optional member.

<a id="config_as_json.optional_validator.OptionalMemberValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(validator: MemberValidator | list[MemberValidator]) -> None
```

Construct validator for an optional member.

**Arguments**:

- `validator` - Validator or list of validators to use for the
  value if it is not None.

**Raises**:

- `TypeError` - If ``validator`` is not a MemberValidator or
  list of MemberValidators.
- `ValueError` - If ``validator`` is an empty list.

<a id="config_as_json.optional_validator.OptionalMemberValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one member if it is not None.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The member value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  None if ``member_value`` is None. Otherwise, the result of
  validating ``member_value`` using the supplied validator(s),
  that may normalize the value.


**Raises**:

  The same exceptions as the supplied validator(s).

<a id="config_as_json._config_nesting_io"></a>

# config\_as\_json.\_config\_nesting\_io

Read, write, and validate nested Config declarations.

<a id="config_as_json._config_nesting_io._NestedConfigEncoder"></a>

## \_NestedConfigEncoder Objects

```python
class _NestedConfigEncoder(json.JSONEncoder)
```

Encode nested configuration JSON data with enum names.

<a id="config_as_json._config_nesting_io._NestedConfigEncoder.default"></a>

#### default

```python
def default(o: object) -> object
```

Serialize enum members using their symbolic names.

<a id="config_as_json._config_nesting_io._item_from_json"></a>

#### \_item\_from\_json

```python
def _item_from_json(name: str, json_data: object, nesting: ConfigNesting,
                    stderr_file: TextIO) -> 'Config'
```

Construct one nested Config from one parsed JSON object.

**Arguments**:

- `name` - Diagnostic name for the nested Config.
- `json_data` - Parsed JSON object for the nested Config.
- `nesting` - Nested Config declaration for the member.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  A new nested Config instance.


**Raises**:

- `KeyError` - JSON data is not a dictionary for a nested Config.
- `TypeError` - The factory returned the wrong Config type.

<a id="config_as_json._config_nesting_io._list_from_json"></a>

#### \_list\_from\_json

```python
def _list_from_json(member_name: str, json_data: object,
                    nesting: ConfigNesting,
                    stderr_file: TextIO) -> list['Config']
```

Construct a list of nested Config objects from parsed JSON.

**Arguments**:

- `member_name` - Public parent member receiving the nested list.
- `json_data` - Parsed JSON value for the member.
- `nesting` - Nested Config declaration for the list elements.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  A list containing one nested Config for each JSON element.


**Raises**:

- `KeyError` - JSON data is not a list of dictionaries.

<a id="config_as_json._config_nesting_io._dict_from_json"></a>

#### \_dict\_from\_json

```python
def _dict_from_json(member_name: str, json_data: object,
                    nesting: ConfigNesting,
                    stderr_file: TextIO) -> dict[str, 'Config']
```

Construct a dict of nested Config objects from parsed JSON.

**Arguments**:

- `member_name` - Public parent member receiving the nested dict.
- `json_data` - Parsed JSON value for the member.
- `nesting` - Nested Config declaration for the dict values.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  A dict containing one nested Config for each JSON value.


**Raises**:

- `KeyError` - JSON data is not a dict of dictionaries.

<a id="config_as_json._config_nesting_io._nesting_by_key"></a>

#### \_nesting\_by\_key

```python
def _nesting_by_key(nestings: list[ConfigNesting]) -> dict[str, ConfigNesting]
```

Return DICT_VALUE_BY_KEY declarations keyed by discriminator_key.

<a id="config_as_json._config_nesting_io._dict_by_key_from_json"></a>

#### \_dict\_by\_key\_from\_json

```python
def _dict_by_key_from_json(member_name: str, json_data: object,
                           nestings: list[ConfigNesting],
                           stderr_file: TextIO) -> dict[str, object]
```

Construct selected dict values as nested Config objects.

**Arguments**:

- `member_name` - Public parent member receiving the nested dict.
- `json_data` - Parsed JSON value for the member.
- `nestings` - Nested Config declarations for selected dict keys.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  A dictionary where declared keys contain nested Config objects and
  undeclared keys keep their parsed JSON values.


**Raises**:

- `KeyError` - JSON data is not a dictionary or a declared key does not
  contain a JSON object.

<a id="config_as_json._config_nesting_io._is_dict_value_by_key"></a>

#### \_is\_dict\_value\_by\_key

```python
def _is_dict_value_by_key(nestings: list[ConfigNesting]) -> bool
```

Return whether the declarations describe keyed dict values.

<a id="config_as_json._config_nesting_io._single_nesting"></a>

#### \_single\_nesting

```python
def _single_nesting(nestings: list[ConfigNesting]) -> ConfigNesting
```

Return the single declaration for non-keyed nesting kinds.

<a id="config_as_json._config_nesting_io._nested_config_from_json"></a>

#### \_nested\_config\_from\_json

```python
def _nested_config_from_json(member_name: str, json_data: object,
                             nestings: list[ConfigNesting],
                             stderr_file: TextIO) -> object
```

Construct nested Config data from parsed JSON data.

**Arguments**:

- `member_name` - Public parent member receiving the nested data.
- `json_data` - Parsed JSON value for the member.
- `nestings` - Nested Config declarations for the member.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  A nested Config, ``None`` for optional JSON null, a list of nested
  Config objects, or a dict of nested Config objects.

<a id="config_as_json._config_nesting_io._item_json_data"></a>

#### \_item\_json\_data

```python
def _item_json_data(member_name: str, member_value: object,
                    nesting: ConfigNesting,
                    stderr_file: TextIO) -> dict[str, JsonType]
```

Return JSON data for one nested Config object.

**Arguments**:

- `member_name` - Diagnostic name for the nested Config.
- `member_value` - Current nested Config value.
- `nesting` - Nested Config declaration for the member.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  A JSON-compatible dictionary.


**Raises**:

- `TypeError` - The member value is not a valid nested Config object.

<a id="config_as_json._config_nesting_io._list_json_data"></a>

#### \_list\_json\_data

```python
def _list_json_data(member_name: str, member_value: object,
                    nesting: ConfigNesting,
                    stderr_file: TextIO) -> list[JsonType]
```

Return JSON data for a list of nested Config objects.

**Arguments**:

- `member_name` - Public parent member being serialized.
- `member_value` - Current nested list value.
- `nesting` - Nested Config declaration for the list elements.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  A JSON-compatible list.


**Raises**:

- `TypeError` - The member value is not a list of nested Config objects.

<a id="config_as_json._config_nesting_io._dict_json_data"></a>

#### \_dict\_json\_data

```python
def _dict_json_data(member_name: str, member_value: object,
                    nesting: ConfigNesting,
                    stderr_file: TextIO) -> dict[str, JsonType]
```

Return JSON data for a dict of nested Config objects.

**Arguments**:

- `member_name` - Public parent member being serialized.
- `member_value` - Current nested dict value.
- `nesting` - Nested Config declaration for the dict values.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  A JSON-compatible dict.


**Raises**:

- `TypeError` - The member value is not a dict of nested Config objects.

<a id="config_as_json._config_nesting_io._is_config_object"></a>

#### \_is\_config\_object

```python
def _is_config_object(value: object) -> bool
```

Return whether value is a Config object without import-time cycles.

<a id="config_as_json._config_nesting_io._dict_by_key_json_data"></a>

#### \_dict\_by\_key\_json\_data

```python
def _dict_by_key_json_data(member_name: str, member_value: object,
                           nestings: list[ConfigNesting],
                           stderr_file: TextIO) -> dict[str, JsonType]
```

Return JSON data for a dict with selected nested Config values.

**Arguments**:

- `member_name` - Public parent member being serialized.
- `member_value` - Current nested dict value.
- `nestings` - Nested Config declarations for selected dict keys.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  A JSON-compatible dict.


**Raises**:

- `TypeError` - The member value is not a dict, a key is not a string, or
  an undeclared key stores a Config object.

<a id="config_as_json._config_nesting_io._nested_config_json_data"></a>

#### \_nested\_config\_json\_data

```python
def _nested_config_json_data(member_name: str, member_value: object,
                             nestings: list[ConfigNesting],
                             stderr_file: TextIO) -> JsonType
```

Return JSON data for one nested Config declaration.

**Arguments**:

- `member_name` - Public parent member being serialized.
- `member_value` - Current value of that member.
- `nestings` - Nested Config declarations for the member.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  JSON-compatible data for the configured nesting kind.

<a id="config_as_json._config_nesting_io._validate_item"></a>

#### \_validate\_item

```python
def _validate_item(member_name: str, member_value: object,
                   nesting: ConfigNesting, stderr_file: TextIO) -> None
```

Validate one nested Config object.

**Arguments**:

- `member_name` - Diagnostic name for the nested Config.
- `member_value` - Current nested Config value.
- `nesting` - Nested Config declaration for the member.
- `stderr_file` - Stream used for user-facing diagnostics.


**Raises**:

- `TypeError` - The member value is not a valid nested Config object.

<a id="config_as_json._config_nesting_io._validate_list"></a>

#### \_validate\_list

```python
def _validate_list(member_name: str, member_value: object,
                   nesting: ConfigNesting, stderr_file: TextIO) -> None
```

Validate a list of nested Config objects.

**Arguments**:

- `member_name` - Public parent member containing the nested list.
- `member_value` - Current nested list value.
- `nesting` - Nested Config declaration for the list elements.
- `stderr_file` - Stream used for user-facing diagnostics.


**Raises**:

- `TypeError` - The member value is not a list of nested Config objects.

<a id="config_as_json._config_nesting_io._validate_dict"></a>

#### \_validate\_dict

```python
def _validate_dict(member_name: str, member_value: object,
                   nesting: ConfigNesting, stderr_file: TextIO) -> None
```

Validate a dict of nested Config objects.

**Arguments**:

- `member_name` - Public parent member containing the nested dict.
- `member_value` - Current nested dict value.
- `nesting` - Nested Config declaration for the dict values.
- `stderr_file` - Stream used for user-facing diagnostics.


**Raises**:

- `TypeError` - The member value is not a dict of nested Config objects.

<a id="config_as_json._config_nesting_io._validate_dict_by_key"></a>

#### \_validate\_dict\_by\_key

```python
def _validate_dict_by_key(member_name: str, member_value: object,
                          nestings: list[ConfigNesting],
                          stderr_file: TextIO) -> None
```

Validate a dict with selected nested Config values.

**Arguments**:

- `member_name` - Public parent member containing the nested dict.
- `member_value` - Current nested dict value.
- `nestings` - Nested Config declarations for selected dict keys.
- `stderr_file` - Stream used for user-facing diagnostics.


**Raises**:

- `TypeError` - The member value is not a dict, a key is not a string, an
  undeclared key stores a Config object, or a declared key has the
  wrong nested Config type.

<a id="config_as_json._config_nesting_io._validate_nested_config"></a>

#### \_validate\_nested\_config

```python
def _validate_nested_config(member_name: str, member_value: object,
                            nestings: list[ConfigNesting],
                            stderr_file: TextIO) -> None
```

Validate one nested Config declaration.

**Arguments**:

- `member_name` - Public parent member containing the nested data.
- `member_value` - Current value of that member.
- `nestings` - Nested Config declarations for the member.
- `stderr_file` - Stream used for user-facing diagnostics.


**Raises**:

- `TypeError` - The member value does not match the nesting kind.

<a id="config_as_json.config_auto_change_hook"></a>

# config\_as\_json.config\_auto\_change\_hook

Define callbacks for automatic configuration adjustments.

Hooks let an application learn that configuration input needed help while it
was parsed, for example because old-file compatibility renamed a key, moved a
path, removed an obsolete key, or supplied a missing current value.

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

- `old_keys_handled` - Old keys or paths that were accepted during
  Reading an Old Configuration File (ROCF), for example by
  mapping them onto current names, moving them to current paths,
  or removing keys no longer used. Moved paths are reported here
  as ``old.path -> new.path`` strings.
- `rocf_vals_handled` - Current paths that received values during
  Reading an Old Configuration File (ROCF) because old input did
  not contain them.
- `stderr_file` - Stream used for user-facing diagnostics.

<a id="config_as_json.config_auto_change_hook.ConfigAutoChangeHook.old_key_handled"></a>

#### old\_key\_handled

```python
def old_key_handled(old_key: str) -> None
```

Record that one legacy key name was accepted and handled.

**Arguments**:

- `old_key` - Legacy key name that was handled by renaming or removal.

<a id="config_as_json.config_auto_change_hook.ConfigAutoChangeHook.rocf_missing_value_provided"></a>

#### rocf\_missing\_value\_provided

```python
def rocf_missing_value_provided(rocf_val_key: str) -> None
```

Record that parsing supplied a compatibility value for one key.

**Arguments**:

- `rocf_val_key` - Key that was absent from input and received a value
  during Reading an Old Configuration File (ROCF).

<a id="config_as_json.config_auto_change_hook.ConfigAutoChangeHook.old_path_moved"></a>

#### old\_path\_moved

```python
def old_path_moved(old_path: str, new_path: str) -> None
```

Record that one old path was moved to a current path.

**Arguments**:

- `old_path` - Actual old path that was accepted and removed.
- `new_path` - Actual current path that received the old value, or
  already had a current value that won.

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
checks, omit-when-None handling, old-file migration helpers, and validation
plan integration.

<a id="config_as_json.config.ConfigBadJson"></a>

## ConfigBadJson Objects

```python
class ConfigBadJson(json.JSONDecodeError)
```

Report JSON input that could not be interpreted as configuration.

<a id="config_as_json.config._over_ride_needed"></a>

#### \_over\_ride\_needed

```python
def _over_ride_needed(value: object) -> int
```

Act as a placeholder conversion function for incomplete subclasses.

The base :meth:`Config.parse_converters` implementation uses this helper
to make missing converter customization obvious. Subclasses that need to
coerce parsed JSON values should override ``parse_converters`` and return
real conversion recipes.

**Arguments**:

- `value` - Parsed JSON value that needs conversion.


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

A derived class can also declare nested configuration sections by
overriding :meth:`nested_configs`. ``MEMBER`` and ``OPTIONAL_MEMBER``
describe direct members, ``LIST_ELEMENT`` describes a list whose elements
are nested Config objects, ``DICT_VALUE`` describes a dict whose values
are nested Config objects, and ``DICT_VALUE_BY_KEY`` describes selected
keys inside a dict whose values are nested Config objects. Use a direct
``ConfigNesting`` value for one declaration. Use a list only when every
list element has kind ``DICT_VALUE_BY_KEY`` and the entries describe
selected keys inside the same dict member.
Nested config classes must accept the constructor keyword arguments
``from_json_data_text``,
``from_json_filename``, and ``stderr_file`` because those are used when
nested JSON objects are parsed. As an alternative construction path, a
``ConfigNesting`` declaration may provide ``factory_function`` with the
same keyword-argument contract. The returned object must be an instance of
the declared ``config_type``.

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
  as filled, renamed, moved, or removed values when reading old
  configuration files.
- `stderr_file` - Stream used for user-facing diagnostics.

  Dict-valued members are checked against the default key set by the
  base class unless listed in ``_unchecked_dicts``; see the class
  docstring.


**Raises**:

- `AttributeError` - The derived class did not declare any public
  configuration attributes before calling ``super().__init__``.
- `TypeError` - ``_unchecked_dicts`` exists but is not a list, or
  ``nested_configs`` returns invalid declarations.
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

<a id="config_as_json.config.Config.serialize_converters"></a>

#### serialize\_converters

```python
def serialize_converters() -> SerializeConverters
```

Return write-side conversion rules for rich Python values.

Derived classes override this method when some configuration values
need explicit conversion into JSON-compatible data before
``json.dumps()`` is called. The motivating case is ``IntEnum``,
which Python's JSON encoder treats as ``int`` and never offers to
``default()``; an explicit converter sidesteps that problem.

The returned dictionary maps selectors to converters. A selector
may be either a recursive key-name string (matches every
dictionary member with that name in data owned by this object) or
an absolute ``ConfigPath`` (matches one specific path). Path
selectors use the same rules as ROCF paths.

Converters apply only to data owned by this object. Declared
nested ``Config`` objects serialize themselves and apply their own
converters; the parent's converters never reach into those
subtrees.

Explicit converters override built-in fallback conversions. The
initial built-in fallbacks are limited to ``Enum`` and ``IntEnum``
members, which are converted to their member names.

Returning the same key with both a recursive key selector and a
path selector that ends in or passes through that key is a
declaration error; ``apply_serialize_converters`` raises
``SerializeSelectorError`` in that case.

**Returns**:

  Write-side conversion rules. The base class returns an empty
  dictionary; override and return non-empty rules when explicit
  conversions are needed.

<a id="config_as_json.config.Config.nested_configs"></a>

#### nested\_configs

```python
def nested_configs() -> NestedConfigs
```

Return nested Config declarations for this configuration.

Override this for public members that contain nested :class:`Config`
objects. Return :class:`NestedConfigs` mapping member names to
:class:`ConfigNesting` declarations. Use ``@override`` so static type
checkers can catch a misspelled method name.

The override should only return stable declarative metadata: no
parsing, validation, mutation, diagnostics, or other side effects.
Values should be constant from the time ``super().__init__`` is
called. Every nested Config object needs a declaration.

<a id="config_as_json.config.Config._get_read_old_configuration"></a>

#### \_get\_read\_old\_configuration

```python
def _get_read_old_configuration() -> ReadOldConfiguration
```

Return the object that normalizes old configuration data.

Derived classes override this method when they need to accept old
configuration file shapes. The default object leaves parsed data
unchanged.

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
def check_dict_parse(self_data: object, json_data: object, key: str,
                     ok_to_use_defaults: bool, unchecked_dicts: list[str],
                     stderr_file: TextIO) -> None
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
def _json_parse_obj_hook(indict: dict[str, object]) -> dict[str, object]
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
absent from JSON input. In strict reads, absent listed members become
``None``; when ``ok_to_use_defaults`` is true, absent members keep
their constructor defaults. Explicit JSON ``null`` is read as
``None``, and writing the configuration omits listed members while
their value is still ``None``.

**Returns**:

  A list of public member names that use omit-when-None behavior.

<a id="config_as_json.config.Config._checked_omit_none_from_json"></a>

#### \_checked\_omit\_none\_from\_json

```python
def _checked_omit_none_from_json(self_keys: list[str]) -> list[str]
```

Return validated omit-when-None member names.

**Arguments**:

- `self_keys` - Public configuration member names on this object.


**Returns**:

  The keys returned by :meth:`_omit_none_from_json`.


**Raises**:

- `TypeError` - The hook returned a value with the wrong type.
- `KeyError` - The hook listed an unknown public member.

<a id="config_as_json.config.Config._check_config_nesting"></a>

#### \_check\_config\_nesting

```python
@staticmethod
def _check_config_nesting(key: str, nesting: ConfigNesting) -> None
```

Validate one nested Config declaration.

**Arguments**:

- `key` - Public member name described by ``nesting``.
- `nesting` - Nested configuration declaration to validate.


**Raises**:

- `TypeError` - The declaration has the wrong runtime type.
- `ValueError` - ``discriminator_key`` is used with the wrong kind.

<a id="config_as_json.config.Config._checked_config_nesting_list"></a>

#### \_checked\_config\_nesting\_list

```python
@staticmethod
def _checked_config_nesting_list(key: str,
                                 nesting_raw: object) -> list[ConfigNesting]
```

Return the checked declaration list for one nested member.

**Arguments**:

- `key` - Public member name described by the declarations.
- `nesting_raw` - Raw value from :meth:`nested_configs`.


**Returns**:

  One or more checked ``ConfigNesting`` declarations.


**Raises**:

- `TypeError` - The raw value or a list entry has the wrong type.
- `ValueError` - The list shape is not valid for the declared kinds.

<a id="config_as_json.config.Config._check_config_nesting_kinds"></a>

#### \_check\_config\_nesting\_kinds

```python
@staticmethod
def _check_config_nesting_kinds(key: str, nestings: list[ConfigNesting],
                                list_form: bool) -> None
```

Validate combinations of nested Config declaration kinds.

**Arguments**:

- `key` - Public member name described by the declarations.
- `nestings` - Checked declarations for one public member.
- `list_form` - Whether the declarations used list syntax.


**Raises**:

- `ValueError` - The declarations combine incompatible nesting kinds.

<a id="config_as_json.config.Config._checked_nested_configs"></a>

#### \_checked\_nested\_configs

```python
def _checked_nested_configs(
        self_keys: list[str]) -> dict[str, list[ConfigNesting]]
```

Return validated and normalized nested Config declarations.

<a id="config_as_json.config.Config._value_has_config"></a>

#### \_value\_has\_config

```python
@staticmethod
def _value_has_config(value: object) -> bool
```

Return whether a default value visibly contains a Config object.

<a id="config_as_json.config.Config._check_nested_config_members"></a>

#### \_check\_nested\_config\_members

```python
def _check_nested_config_members(
        self_keys: list[str],
        nested_configs: dict[str, list[ConfigNesting]]) -> None
```

Validate that visible nested Config defaults are declared.

<a id="config_as_json.config.Config._validate_nested_configs"></a>

#### \_validate\_nested\_configs

```python
def _validate_nested_configs(stderr_file: TextIO) -> None
```

Validate all direct nested Config members before this object.

**Arguments**:

- `stderr_file` - Stream used for user-facing diagnostics.

<a id="config_as_json.config.Config.copy_initial_data"></a>

#### copy\_initial\_data

```python
@staticmethod
def copy_initial_data(source: object, target: 'Config') -> None
```

Copy public attributes from ``source`` onto a Config ``target``.

Use this helper from a derived Config constructor when the
configuration defaults come from a separate framework-neutral data
class that the derived class wants to bridge to. The neutral data
class can be a plain object, a dataclass instance, or a
``Mapping`` such as a ``dict``. Private names (those starting with
``_``) and bound method-like callables are not copied.

When ``target`` already exposes at least one public attribute, the
helper enforces that every public attribute in ``source`` is also
declared on ``target``; an unexpected attribute on ``source``
therefore raises immediately with a clear diagnostic message. This
covers two practical cases: the common multiple-inheritance
pattern where the neutral base class constructor on ``target`` has
already established the schema, and the internal wrap path used
when nested neutral defaults are turned into bridge instances.

When ``target`` has not yet had its schema established, the helper
simply copies every public attribute from ``source`` onto
``target`` and the source's set of names becomes the bridge's
schema. This covers the pattern used when the neutral class
constructor takes required arguments that the bridge does not
duplicate; the application constructs the neutral instance and
hands it to the bridge.

**Arguments**:

- `source` - Object, dataclass instance, or mapping whose public
  attributes describe the desired initial values.
- `target` - Config instance whose attributes should be assigned.


**Raises**:

- `TypeError` - ``source`` cannot be read, a mapping key is not a
  string, or ``target`` has a declared public schema and
  ``source`` exposes a public attribute that ``target`` does
  not declare.

<a id="config_as_json.config.Config._auto_wrap_nested_defaults"></a>

#### \_auto\_wrap\_nested\_defaults

```python
def _auto_wrap_nested_defaults(stderr_file: TextIO) -> None
```

Wrap nested member defaults that are not yet bridge-typed.

Scans the validated nested-config declarations and replaces any
default value that is not already an instance of the declared
``config_type`` with a freshly constructed bridge instance whose
public attributes were copied from the original neutral value.
Already-wrapped values are left untouched, and ``None`` is left
in place for ``OPTIONAL_MEMBER`` declarations.

**Arguments**:

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

<a id="config_as_json.config.Config._child_owned_paths"></a>

#### \_child\_owned\_paths

```python
def _child_owned_paths() -> list[ConfigPath]
```

Return paths to nested ``Config`` subtrees owned by children.

Used by :meth:`as_json_string` to tell
:func:`apply_serialize_converters` which parts of the assembled
JSON data have already been produced by a child ``Config``'s own
``as_json_string()`` and must not be touched by this object's
write-side converters.

The literal ``'['`` step in a returned path means "every list
element or every dictionary value at this position", which lets
``LIST_ELEMENT`` and ``DICT_VALUE`` declarations share the same
notation.

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

<a id="config_as_json.config.Config.value_of_type"></a>

#### value\_of\_type

```python
@staticmethod
def value_of_type(input_value: object, to_type: type[_T]) -> _T
```

Return ``input_value`` as an instance of ``to_type``.

**Arguments**:

- `input_value` - Value to normalize.
- `to_type` - Target runtime type.


**Returns**:

  ``input_value`` unchanged when it already has the expected type,
  otherwise the result of calling ``to_type(input_value)``.

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
- `rocf_vals_handled` - Current paths that received values during
  old-file compatibility processing.
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
- `allow_extra_dict_keys` - Whether keys not listed for this variant
  should be accepted.

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
class DiscriminatedDictValidator(MemberValidator)
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
  variant that applies to that discriminator value. Each variant
  also decides whether extra keys are accepted for that selected
  shape.
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

<a id="config_as_json.list_relation_validator"></a>

# config\_as\_json.list\_relation\_validator

Validate that one list-like value has a relation to another.

The validator is used to validate that a list-like value (which may be
a projected value) has the specified relation to another list-like value
(which might also be a projected value).

<a id="config_as_json.list_relation_validator._validate_relation_kind"></a>

#### \_validate\_relation\_kind

```python
def _validate_relation_kind(kind: object) -> 'ListRelationKind'
```

Validate and return one list relation kind.

**Arguments**:

- `kind` - Relation kind supplied to the constructor.


**Returns**:

  ``kind`` after it has been proven to be a ``ListRelationKind``.


**Raises**:

- `TypeError` - If ``kind`` is not a ``ListRelationKind``.

<a id="config_as_json.list_relation_validator._validate_member_name"></a>

#### \_validate\_member\_name

```python
def _validate_member_name(member_name: object, parameter_name: str) -> str
```

Validate and return one relation member or pseudo-member name.

**Arguments**:

- `member_name` - Name supplied to the constructor.
- `parameter_name` - Parameter name used in error messages.


**Returns**:

  ``member_name`` after it has been proven to be non-empty str.


**Raises**:

- `TypeError` - If ``member_name`` is not a str.
- `ValueError` - If ``member_name`` is empty.

<a id="config_as_json.list_relation_validator._validate_optional_projector"></a>

#### \_validate\_optional\_projector

```python
def _validate_optional_projector(
        projector: Optional[WholeConfigProjector],
        parameter_name: str) -> Optional[WholeConfigProjector]
```

Validate and return an optional whole-config projector.

**Arguments**:

- `projector` - Optional projector supplied to the constructor.
- `parameter_name` - Parameter name used in error messages.


**Returns**:

  ``projector`` after it has been proven to be ``None`` or callable.


**Raises**:

- `TypeError` - If ``projector`` is not ``None`` and not callable.

<a id="config_as_json.list_relation_validator._validate_comparator"></a>

#### \_validate\_comparator

```python
def _validate_comparator(
        comparator: object,
        parameter_name: str) -> Callable[[object, object], bool]
```

Validate and return one relation element comparator.

**Arguments**:

- `comparator` - Comparator supplied to the constructor.
- `parameter_name` - Parameter name used in error messages.


**Returns**:

  ``comparator`` after it has been proven to be callable.


**Raises**:

- `TypeError` - If ``comparator`` is not callable.

<a id="config_as_json.list_relation_validator._print_and_raise_type_error"></a>

#### \_print\_and\_raise\_type\_error

```python
def _print_and_raise_type_error(message: str, stderr_file: TextIO) -> None
```

Print one type error message and raise ``TypeError``.

**Arguments**:

- `message` - Message to print and raise.
- `stderr_file` - Stream used for user-facing diagnostics.


**Raises**:

- `TypeError` - Always raised with ``message``.

<a id="config_as_json.list_relation_validator._print_and_raise_key_error"></a>

#### \_print\_and\_raise\_key\_error

```python
def _print_and_raise_key_error(message: str, stderr_file: TextIO) -> None
```

Print one key error message and raise ``KeyError``.

**Arguments**:

- `message` - Message to print and raise.
- `stderr_file` - Stream used for user-facing diagnostics.


**Raises**:

- `KeyError` - Always raised with ``message``.

<a id="config_as_json.list_relation_validator._print_and_raise_invalid"></a>

#### \_print\_and\_raise\_invalid

```python
def _print_and_raise_invalid(message: str, stderr_file: TextIO) -> None
```

Print one invalid-configuration message and raise it.

**Arguments**:

- `message` - Message to print and raise.
- `stderr_file` - Stream used for user-facing diagnostics.


**Raises**:

- `InvalidConfiguration` - Always raised with ``message``.

<a id="config_as_json.list_relation_validator._materialized_sequence"></a>

#### \_materialized\_sequence

```python
def _materialized_sequence(member_name: str, value: object,
                           stderr_file: TextIO) -> list[object]
```

Validate and materialize one relation value as a list.

**Arguments**:

- `member_name` - Name used in diagnostics.
- `value` - Value to validate and materialize.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  The relation value as a newly materialized list.


**Raises**:

- `TypeError` - If ``value`` is not a sequence, or if it is ``str``,
  ``bytes``, or ``bytearray``.

<a id="config_as_json.list_relation_validator._contains_equal"></a>

#### \_contains\_equal

```python
def _contains_equal(values: list[object], value: object,
                    eq_comparator: Callable[[object, object], bool]) -> bool
```

Return whether ``values`` contains an equal value.

**Arguments**:

- `values` - Values to search.
- `value` - Value to find.
- `eq_comparator` - Function used to compare values.


**Returns**:

  ``True`` if an equal value was found.

<a id="config_as_json.list_relation_validator._is_distinct_subset"></a>

#### \_is\_distinct\_subset

```python
def _is_distinct_subset(
        values_a: list[object], values_b: list[object],
        eq_comparator: Callable[[object, object], bool]) -> bool
```

Return whether distinct values in A are found in B.

**Arguments**:

- `values_a` - Candidate subset values.
- `values_b` - Candidate superset values.
- `eq_comparator` - Function used to compare values.


**Returns**:

  ``True`` if every distinct value in ``values_a`` occurs in
  ``values_b``.

<a id="config_as_json.list_relation_validator._is_multiset_equal"></a>

#### \_is\_multiset\_equal

```python
def _is_multiset_equal(
        values_a: list[object], values_b: list[object],
        eq_comparator: Callable[[object, object], bool]) -> bool
```

Return whether two values contain equal values with equal counts.

**Arguments**:

- `values_a` - First value sequence.
- `values_b` - Second value sequence.
- `eq_comparator` - Function used to compare values.


**Returns**:

  ``True`` if every value in ``values_a`` can be paired with exactly
  one equal value in ``values_b``.

<a id="config_as_json.list_relation_validator._is_disjoint"></a>

#### \_is\_disjoint

```python
def _is_disjoint(values_a: list[object], values_b: list[object],
                 eq_comparator: Callable[[object, object], bool]) -> bool
```

Return whether no value from A occurs in B.

**Arguments**:

- `values_a` - First value sequence.
- `values_b` - Second value sequence.
- `eq_comparator` - Function used to compare values.


**Returns**:

  ``True`` if no value in one sequence is equal to a value in the
  other sequence.

<a id="config_as_json.list_relation_validator.ListRelationKind"></a>

## ListRelationKind Objects

```python
class ListRelationKind(Enum)
```

Relation to require between two list-like values.

<a id="config_as_json.list_relation_validator.ListRelationKind.EQUAL"></a>

#### EQUAL

The two values must be equal as ordered sequences.

The sequences must have the same length. For each position, the value in
sequence A must be equal to the value in the same position in sequence B
according to the supplied equality comparator.

<a id="config_as_json.list_relation_validator.ListRelationKind.MULTISET_EQUAL"></a>

#### MULTISET\_EQUAL

The two values must contain the same elements with the same counts.

Order is ignored, but duplicates are significant. For example,
``['a', 'a', 'b']`` and ``['a', 'b', 'a']`` satisfy this relation, while
``['a', 'b']`` and ``['a', 'a', 'b']`` do not.

<a id="config_as_json.list_relation_validator.ListRelationKind.SET_EQUAL"></a>

#### SET\_EQUAL

Each distinct value in either sequence must occur in the other.

Order and duplicates are ignored. For example, ``['a', 'a']`` and
``['a']`` satisfy this relation.

<a id="config_as_json.list_relation_validator.ListRelationKind.SUBSET"></a>

#### SUBSET

Each distinct value in sequence A must occur in sequence B.

Order and duplicates are ignored. Sequence B may contain additional
values. For example, ``['a', 'a']`` is a subset of ``['a', 'b']``.

<a id="config_as_json.list_relation_validator.ListRelationKind.DISJOINT"></a>

#### DISJOINT

No value in sequence A may also occur in sequence B.

Order and duplicates inside either sequence are ignored. The relation
fails if any value in one sequence is equal to a value in the other
sequence.

<a id="config_as_json.list_relation_validator.ListRelationValidator"></a>

## ListRelationValidator Objects

```python
class ListRelationValidator(WholeConfigValidator)
```

Validate that one list-like value has a relation to another.

Each side of the relation is either read from a named ``Config`` member or
computed by a projector. A value read from a config member is expected to
be a finite sequence represented by that member, but not a ``str``,
``bytes``, or ``bytearray``. A projected value may be any finite
sequence except ``str``, ``bytes``, or ``bytearray``. The validator
conceptually materializes both values as lists before applying the
relation.

All element comparisons use ``eq_comparator``. ``lt_comparator`` is
used for relation kinds or diagnostics that need a stable ordering
of values.

<a id="config_as_json.list_relation_validator.ListRelationValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(
    kind: ListRelationKind,
    member_a_name: str,
    member_b_name: str,
    *,
    a_projector: Optional[WholeConfigProjector] = None,
    b_projector: Optional[WholeConfigProjector] = None,
    eq_comparator: Callable[[object, object], bool] = eq,
    lt_comparator: Callable[[object, object], bool] = _DEFAULT_LT_COMPARATOR
) -> None
```

Initialize a list relation validator.

**Arguments**:

- `kind` - Relation to require between the two values.
- `member_a_name` - Name of the first member to compare.
  If ``a_projector`` is not supplied, this is the name of a
  member in the ``Config`` object whose value is sequence A.
  If ``a_projector`` is supplied, this is the pseudo-member
  name of the projected value. The name is used for error
  messages.
- `member_b_name` - Name of the second member to compare.
  If ``b_projector`` is not supplied, this is the name of a
  member in the ``Config`` object whose value is sequence B.
  If ``b_projector`` is supplied, this is the pseudo-member
  name of the projected value. The name is used for error
  messages.
- `a_projector` - Optional projector for sequence A.
- `b_projector` - Optional projector for sequence B.
- `eq_comparator` - Function used to decide whether two element values
  are equal. The default is the equality operator.
- `lt_comparator` - Function used when a relation or diagnostic needs
  to order element values. The default is the less-than
  operator.


**Raises**:

- `TypeError` - If a constructor argument has an invalid type.
- `ValueError` - If a member name is empty.

<a id="config_as_json.list_relation_validator.ListRelationValidator._relation_value"></a>

#### \_relation\_value

```python
def _relation_value(config: 'Config', member_name: str,
                    projector: Optional[WholeConfigProjector],
                    stderr_file: TextIO) -> list[object]
```

Return one materialized relation value.

**Arguments**:

- `config` - The Config object to validate.
- `member_name` - Real member name or pseudo-member name.
- `projector` - Optional projector for the relation value.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  The relation value as a list.


**Raises**:

- `KeyError` - The member is missing and no projector was supplied.
- `TypeError` - The relation value is not a sequence, or it is
  ``str``, ``bytes``, or ``bytearray``.

<a id="config_as_json.list_relation_validator.ListRelationValidator._relation_holds"></a>

#### \_relation\_holds

```python
def _relation_holds(values_a: list[object], values_b: list[object]) -> bool
```

Return whether the configured relation holds.

**Arguments**:

- `values_a` - Sequence A materialized as a list.
- `values_b` - Sequence B materialized as a list.


**Returns**:

  ``True`` if the configured relation holds.

<a id="config_as_json.list_relation_validator.ListRelationValidator.validate"></a>

#### validate

```python
def validate(config: 'Config', stderr_file: TextIO = sys.stderr) -> None
```

Validate the configured relation between two list-like values.

If no projector is supplied for a side, that side is read from the
named ``Config`` member. If a projector is supplied, the projector
receives the complete ``Config`` object and the diagnostic stream, and
its returned value is used as that side of the relation.

Both relation values must be finite sequences, but not ``str``,
``bytes``, or ``bytearray``. Rejecting those scalar text and binary
types keeps accidental character-by-character comparison from being
treated as a valid configuration relation.

**Arguments**:

- `config` - The Config object to validate.
- `stderr_file` - Stream used for user-facing diagnostics.


**Raises**:

- `KeyError` - A side has no projector and the named member is not
  present in ``config``.
- `TypeError` - One relation value is not a sequence, or it is
  ``str``, ``bytes``, or ``bytearray``.
- `InvalidConfiguration` - The relation does not hold.

<a id="config_as_json.projected_validators"></a>

# config\_as\_json.projected\_validators

Define validators that validate projected member values.

<a id="config_as_json.projected_validators._validate_projector"></a>

#### \_validate\_projector

```python
def _validate_projector(projector: object) -> None
```

Validate the projector argument.

**Arguments**:

- `projector` - Callable that computes the value to validate.


**Raises**:

- `TypeError` - If ``projector`` is not callable.

<a id="config_as_json.projected_validators._validate_pseudo_member_name"></a>

#### \_validate\_pseudo\_member\_name

```python
def _validate_pseudo_member_name(pseudo_member_name: object) -> str
```

Validate and return one pseudo-member name.

**Arguments**:

- `pseudo_member_name` - Name used when inner validators report errors.


**Returns**:

  ``pseudo_member_name`` after it has been proven to be non-empty str.


**Raises**:

- `TypeError` - If ``pseudo_member_name`` is not a str.
- `ValueError` - If ``pseudo_member_name`` is empty.

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
class ProjectedMemberValidator(MemberValidator)
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
def __init__(projector: MemberProjector,
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

<a id="config_as_json.projected_validators.ProjectedWholeConfigValidator"></a>

## ProjectedWholeConfigValidator Objects

```python
class ProjectedWholeConfigValidator(WholeConfigValidator)
```

Validate a projected value that is computed from the entire config.

This validator is intended for configuration aspects whose natural
validation view is not the stored values themselves. A projector function
computes that validation view from the original member values, and a
sequence of inner validators is then applied to the projected value.

The projector function receives the complete Config object and the
diagnostic stream. It returns the projected value to validate,
and the returned value will be given a pseudo-member name,
and will be validated by the inner validators that are of type
MemberValidator.

Projected validators are applied in order. If one projected validator
returns a normalized or replacement projected value, that returned value
is passed to the next projected validator. The final projected value is
discarded when validation succeeds.

Returned replacement values from the projector and projected
validators affect only this validation chain. They do not replace the
stored Config object. The validator does not copy the Config object or
projected value, though. In-place mutation done by the
projector, or by a projected validator can still affect shared mutable
objects. Validators and projectors that need isolation should return or
work on detached values.

<a id="config_as_json.projected_validators.ProjectedWholeConfigValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(projector: WholeConfigProjector, pseudo_member_name: str,
             validators: Sequence[MemberValidator]) -> None
```

Initialize the projected whole-config validator.

**Arguments**:

- `projector` - Callable that receives the complete config object,
  and the diagnostic stream. It returns the projected value to
  validate.
- `pseudo_member_name` - The name of the pseudo-member to validate.
  This name will be used to identify the pseudo-member
  (that is the projected value) in the error messages.
- `validators` - Validators to apply to the projected value. They are
  applied in declaration order, and each validator receives the
  value returned by the previous validator.


**Raises**:

- `ValueError` - If ``validators`` is empty.
- `TypeError` - If ``projector`` is not callable or any validator is
  not a ``MemberValidator``.

<a id="config_as_json.projected_validators.ProjectedWholeConfigValidator.validate"></a>

#### validate

```python
def validate(config: 'Config', stderr_file: TextIO = sys.stderr) -> None
```

Validate an aspect of the entire Config object.

The validator computes the projected value from the entire Config
object, and then validates the projected value using the inner
validators that are of type MemberValidator in order. If one
projected validator returns a normalized or replacement projected
value, that returned value is passed to the next projected validator.
The final projected value is discarded when validation succeeds.

The inner validators are called with these arguments:
- config: The Config object to validate.
- member_name: The name (which is the pseudo-member name) of the
member to validate (which is the projected value).
- member_value: The projected value to validate.
- stderr_file: The file to write error messages to.

**Raises**:

- `InvalidConfiguration` - If the projector or an inner validator
  detects an invalid configuration.
- `InvalidConfigurationValue` - If an inner validator rejects a value
  because it is not one of its allowed values.


**Arguments**:

- `config` - The Config object to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  None if the validation check passes, otherwise the exception
  is raised.

<a id="config_as_json.type_validators"></a>

# config\_as\_json.type\_validators

Implement type validators for configuration data.

<a id="config_as_json.type_validators._validate_type_spec"></a>

#### \_validate\_type\_spec

```python
def _validate_type_spec(type_spec: object, parameter_name: str,
                        allow_empty: bool) -> tuple[type[object], ...]
```

Validate a type or list of types and return it as a tuple.

**Arguments**:

- `type_spec` - Constructor argument to validate.
- `parameter_name` - Name used in error messages.
- `allow_empty` - Whether an empty list is accepted.


**Returns**:

  The validated runtime types as a tuple.


**Raises**:

- `TypeError` - If ``type_spec`` is not a type or list of types.
- `ValueError` - If ``type_spec`` is an empty list and empty is rejected.

<a id="config_as_json.type_validators._copy_type_spec"></a>

#### \_copy\_type\_spec

```python
def _copy_type_spec(
    value_types: tuple[type[object],
                       ...]) -> type[object] | list[type[object]]
```

Return the public representation for one validated type spec.

**Arguments**:

- `value_types` - Validated type tuple.


**Returns**:

  The only type directly, or a list when there are several types.

<a id="config_as_json.type_validators._format_type_names"></a>

#### \_format\_type\_names

```python
def _format_type_names(value_types: tuple[type[object], ...]) -> str
```

Return a short human-readable list of runtime type names.

**Arguments**:

- `value_types` - Runtime types to include in the text.


**Returns**:

  A comma-separated list with ``or`` before the last type.

<a id="config_as_json.type_validators._matches_type_spec"></a>

#### \_matches\_type\_spec

```python
def _matches_type_spec(member_value: object, value_types: tuple[type[object],
                                                                ...],
                       strict: bool) -> bool
```

Return whether ``member_value`` matches the configured types.

**Arguments**:

- `member_value` - Value to check.
- `value_types` - Runtime types to check against.
- `strict` - Whether exact type matching should be used.


**Returns**:

  ``True`` when the value matches one of the runtime types.

<a id="config_as_json.type_validators._validate_strict"></a>

#### \_validate\_strict

```python
def _validate_strict(strict: bool) -> None
```

Validate the strict-mode constructor argument.

**Arguments**:

- `strict` - Value supplied as the strict-mode flag.


**Raises**:

- `TypeError` - If ``strict`` is not a ``bool``.

<a id="config_as_json.type_validators._validate_allowed_denied"></a>

#### \_validate\_allowed\_denied

```python
def _validate_allowed_denied(allowed: tuple[type[object], ...],
                             denied: tuple[type[object],
                                           ...], strict: bool) -> None
```

Reject allowed types that are completely denied.

**Arguments**:

- `allowed` - Accepted runtime types.
- `denied` - Runtime types that are rejected after the allowed check.
- `strict` - Whether exact type matching should be used.


**Raises**:

- `ValueError` - If one allowed type can never pass the denied check.

<a id="config_as_json.type_validators._type_is_denied"></a>

#### \_type\_is\_denied

```python
def _type_is_denied(allowed_type: type[object], denied_type: type[object],
                    strict: bool) -> bool
```

Return whether one allowed type is rejected by one denied type.

**Arguments**:

- `allowed_type` - Candidate allowed type.
- `denied_type` - Candidate denied type.
- `strict` - Whether exact type matching should be used.


**Returns**:

  ``True`` when the constructor arguments contradict each other.

<a id="config_as_json.type_validators._raise_type_error"></a>

#### \_raise\_type\_error

```python
def _raise_type_error(member_name: str, member_value: object,
                      value_types: tuple[type[object],
                                         ...], stderr_file: TextIO) -> None
```

Print and raise an invalid-type error for one member value.

**Arguments**:

- `member_name` - Name of the member being validated.
- `member_value` - Invalid member value.
- `value_types` - Runtime types accepted by the validator.
- `stderr_file` - Stream used for diagnostics.


**Raises**:

- `InvalidConfigurationType` - Always.

<a id="config_as_json.type_validators._raise_denied_error"></a>

#### \_raise\_denied\_error

```python
def _raise_denied_error(member_name: str, member_value: object,
                        denied_types: tuple[type[object],
                                            ...], stderr_file: TextIO) -> None
```

Print and raise an error for one explicitly denied type.

**Arguments**:

- `member_name` - Name of the member being validated.
- `member_value` - Invalid member value.
- `denied_types` - Runtime types rejected by the validator.
- `stderr_file` - Stream used for diagnostics.


**Raises**:

- `InvalidConfigurationType` - Always.

<a id="config_as_json.type_validators._matching_type"></a>

#### \_matching\_type

```python
def _matching_type(
        member_value: object,
        value_types: tuple[type[object], ...]) -> Optional[type[object]]
```

Return the closest matching type for ``member_value``.

**Arguments**:

- `member_value` - Value to match against the candidate types.
- `value_types` - Candidate runtime types.


**Returns**:

  The candidate type nearest to the value type, or ``None``.

<a id="config_as_json.type_validators._type_rank"></a>

#### \_type\_rank

```python
def _type_rank(member_type: type[object], value_type: type[object]) -> int
```

Return how close ``value_type`` is in ``member_type``'s MRO.

**Arguments**:

- `member_type` - Runtime type of the value being converted.
- `value_type` - Candidate base type.


**Returns**:

  Lower numbers mean a more specific match.

<a id="config_as_json.type_validators._validate_convert_map"></a>

#### \_validate\_convert\_map

```python
def _validate_convert_map(
    convertable_types: Optional[dict[type[object], Callable[[object], T]]]
) -> dict[type[object], Callable[[object], T]]
```

Validate conversion functions keyed by runtime type.

**Arguments**:

- `convertable_types` - Optional conversion mapping.


**Returns**:

  A shallow copy of the validated conversion mapping.


**Raises**:

- `TypeError` - If the mapping, keys, or values are invalid.

<a id="config_as_json.type_validators._validate_no_overlap"></a>

#### \_validate\_no\_overlap

```python
def _validate_no_overlap(
        direct_types: tuple[type[object], ...],
        convertable_types: dict[type[object], Callable[[object], T]]) -> None
```

Reject exact type overlap between direct and callable conversion.

**Arguments**:

- `direct_types` - Types converted with the target constructor.
- `convertable_types` - Types converted with custom callables.


**Raises**:

- `ValueError` - If a type is present in both conversion sets.

<a id="config_as_json.type_validators._raise_conversion_error"></a>

#### \_raise\_conversion\_error

```python
def _raise_conversion_error(member_name: str, member_value: object,
                            target_type: type[object], stderr_file: TextIO,
                            cause: Exception) -> None
```

Print and raise an error when conversion fails.

**Arguments**:

- `member_name` - Name of the member being validated.
- `member_value` - Member value that could not be converted.
- `target_type` - Runtime type the value should convert to.
- `stderr_file` - Stream used for diagnostics.
- `cause` - Exception raised by the conversion.


**Raises**:

- `InvalidConfigurationType` - Always.

<a id="config_as_json.type_validators._validate_converted_value"></a>

#### \_validate\_converted\_value

```python
def _validate_converted_value(member_name: str, converted_value: object,
                              target_type: type[object],
                              stderr_file: TextIO) -> None
```

Validate that a conversion returned the target runtime type.

**Arguments**:

- `member_name` - Name of the member being validated.
- `converted_value` - Result returned from the conversion.
- `target_type` - Required runtime type after conversion.
- `stderr_file` - Stream used for diagnostics.


**Raises**:

- `InvalidConfigurationType` - If the result has the wrong type.

<a id="config_as_json.type_validators.InvalidConfigurationType"></a>

## InvalidConfigurationType Objects

```python
class InvalidConfigurationType(InvalidConfiguration)
```

Raised when a member value has an invalid runtime type.

<a id="config_as_json.type_validators.ValueTypeValidator"></a>

## ValueTypeValidator Objects

```python
class ValueTypeValidator(MemberValidator)
```

Validate that one member value has the configured runtime type.

The validator accepts either one runtime type or a list of runtime types.
Normal mode uses ``isinstance`` semantics, so subclasses are accepted.
Strict mode uses exact ``type(value)`` matching. Optional denied types
are checked with the same strictness as the allowed types.

<a id="config_as_json.type_validators.ValueTypeValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(value_type: type[object] | list[type[object]],
             not_allowed_type: Optional[type[object]
                                        | list[type[object]]] = None,
             strict: bool = False) -> None
```

Initialize the validator.

**Arguments**:

- `value_type` - Required runtime type or types for the member value.
- `not_allowed_type` - Optional runtime types that are not allowed.
- `strict` - Whether to require exact runtime type matches.


**Raises**:

- `TypeError` - If a type specification is invalid.
- `TypeError` - If ``strict`` is not a boolean.
- `ValueError` - If ``value_type`` is an empty list.
- `ValueError` - If allowed and denied types contradict each other.

<a id="config_as_json.type_validators.ValueTypeValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one member's runtime type.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The member value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The original member value if validation succeeds.


**Raises**:

- `InvalidConfigurationType` - If ``member_value`` does not match the
  allowed types, or if it matches a denied type.

<a id="config_as_json.type_validators.ValueAsTypeValidator"></a>

## ValueAsTypeValidator Objects

```python
class ValueAsTypeValidator(ValueTypeValidator, Generic[T])
```

Normalize one member value to the configured runtime type.

Values already matching ``value_type`` are returned unchanged. Other
accepted values are converted either by calling ``value_type(value)`` for
direct types, or by a custom conversion function for convertable types.

<a id="config_as_json.type_validators.ValueAsTypeValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(
    value_type: type[T],
    direct_types: Optional[type[object] | list[type[object]]] = None,
    convertable_types: Optional[dict[type[object], Callable[[object],
                                                            T]]] = None
) -> None
```

Initialize the validator.

**Arguments**:

- `value_type` - Runtime type to normalize the member value to.
- `direct_types` - Runtime types converted with ``value_type(value)``.
- `convertable_types` - Runtime types converted with custom callables.


**Raises**:

- `TypeError` - If any constructor argument has an invalid shape.
- `ValueError` - If one type is both direct and convertable.

<a id="config_as_json.type_validators.ValueAsTypeValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Normalize the member value to the configured runtime type.

If both a direct type and a convertable type match, the type closest
to ``type(member_value)`` in the MRO decides which conversion path is
used.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The member value to validate.
- `stderr_file` - The file to write error messages to.


**Raises**:

- `InvalidConfigurationType` - If the value is not accepted, if
  conversion fails, or if conversion returns the wrong type.


**Returns**:

  The original or normalized member value if validation succeeds.

<a id="config_as_json.type_validators.ValueAsTypeValidator._conversion_input_types"></a>

#### \_conversion\_input\_types

```python
def _conversion_input_types() -> tuple[type[object], ...]
```

Return all accepted input types for diagnostics.

**Returns**:

  Target, direct, and convertable runtime types in check order.

<a id="config_as_json.type_validators.ValueAsTypeValidator._use_direct"></a>

#### \_use\_direct

```python
def _use_direct(member_value: object, direct_type: Optional[type[object]],
                conv_type: Optional[type[object]]) -> bool
```

Return whether direct constructor conversion should be used.

**Arguments**:

- `member_value` - Value being converted.
- `direct_type` - Matching direct type, if any.
- `conv_type` - Matching callable-conversion type, if any.


**Returns**:

  ``True`` when the direct constructor path should be used.

<a id="config_as_json.type_validators.ValueAsTypeValidator._convert_direct"></a>

#### \_convert\_direct

```python
def _convert_direct(member_name: str, member_value: object,
                    stderr_file: TextIO) -> T
```

Convert a value with the target type constructor.

**Arguments**:

- `member_name` - Name of the member being validated.
- `member_value` - Value to convert.
- `stderr_file` - Stream used for diagnostics.


**Returns**:

  Converted value.


**Raises**:

- `InvalidConfigurationType` - If conversion fails or returns a
  value with the wrong runtime type.

<a id="config_as_json.type_validators.ValueAsTypeValidator._convert_with_func"></a>

#### \_convert\_with\_func

```python
def _convert_with_func(member_name: str, member_value: object,
                       conv_type: type[object], stderr_file: TextIO) -> T
```

Convert a value with a configured conversion function.

**Arguments**:

- `member_name` - Name of the member being validated.
- `member_value` - Value to convert.
- `conv_type` - Matching key in ``convertable_types``.
- `stderr_file` - Stream used for diagnostics.


**Returns**:

  Converted value.


**Raises**:

- `InvalidConfigurationType` - If conversion fails or returns a
  value with the wrong runtime type.

<a id="config_as_json.commontypes"></a>

# config\_as\_json.commontypes

Collect shared type aliases and typing helpers for the package.

The aliases in this module describe JSON-compatible values and path-like
input.

<a id="config_as_json.commontypes.json_types"></a>

#### json\_types

Tuple of all JSON-compatible types for use in isinstance checks.

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
                                stderr_file: TextIO) -> dict[Hashable, object]
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

<a id="config_as_json.dict_validators._validate_hashable_keys"></a>

#### \_validate\_hashable\_keys

```python
def _validate_hashable_keys(keys: Sequence[Hashable],
                            parameter_name: str) -> None
```

Validate that ``keys`` is a sequence of distinct hashable values.

**Arguments**:

- `keys` - The sequence to validate.
- `parameter_name` - Name used in error messages.


**Raises**:

- `TypeError` - If any entry of ``keys`` is not hashable.
- `ValueError` - If ``keys`` contains a duplicate entry.

<a id="config_as_json.dict_validators._validate_bool_argument"></a>

#### \_validate\_bool\_argument

```python
def _validate_bool_argument(value: bool, parameter_name: str) -> None
```

Validate that a constructor argument is a bool.

**Arguments**:

- `value` - Value to validate.
- `parameter_name` - Name used in the error message.


**Raises**:

- `TypeError` - If ``value`` is not a bool.

<a id="config_as_json.dict_validators._validate_hashable_type"></a>

#### \_validate\_hashable\_type

```python
def _validate_hashable_type(value_type: object,
                            parameter_name: str) -> type[Hashable]
```

Validate and return one runtime type for dict keys.

**Arguments**:

- `value_type` - Value supplied as a runtime type argument.
- `parameter_name` - Name used in the error message.


**Returns**:

  ``value_type`` after it has been proven to be a hashable type.


**Raises**:

- `TypeError` - If ``value_type`` is not a type or is not hashable.

<a id="config_as_json.dict_validators._inner_member_name"></a>

#### \_inner\_member\_name

```python
def _inner_member_name(outer: str, key: Hashable) -> str
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
is reported as an error. By default, any key in the dict that is neither
a mandatory key nor an additional allowed key is rejected. The set of
permitted keys is the union of ``mandatory_keys`` and ``allowed_keys``;
a key listed in both sequences is harmless.

When ``allow_extra_dict_keys`` is ``True``, unknown keys are accepted
after all mandatory keys have been found. This is useful for open
dictionary shapes where validators should require or validate only a
selected subset of keys and pass application-specific extras through.

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
             allowed_keys: Optional[Sequence[str]] = None,
             allow_extra_dict_keys: bool = False) -> None
```

Initialize the validator.

**Arguments**:

- `mandatory_keys` - Keys that must be present in the dict. May be
  empty if the dict is allowed to be empty (or to contain
  only optional keys).
- `allowed_keys` - Additional keys that are permitted but not
  required. ``None`` means no optional keys are allowed; the
  dict must contain exactly the mandatory keys unless
  ``allow_extra_dict_keys`` is ``True``.
- `allow_extra_dict_keys` - Whether keys not listed in
  ``mandatory_keys`` or ``allowed_keys`` should be accepted.


**Raises**:

- `TypeError` - If any entry of ``mandatory_keys`` or
  ``allowed_keys`` is not a ``str``, or if
  ``allow_extra_dict_keys`` is not a bool.
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
  key is missing, or an unknown key is present while
  ``allow_extra_dict_keys`` is ``False``.

<a id="config_as_json.dict_validators.accept_all_keys"></a>

#### accept\_all\_keys

```python
def accept_all_keys(key: Hashable) -> bool
```

Return ``True`` for all keys.

**Arguments**:

- `key` - The key to check.


**Returns**:

  ``True`` for all keys.

<a id="config_as_json.dict_validators.DictRule"></a>

## DictRule Objects

```python
@dataclass(frozen=True)
class DictRule()
```

Bind a sequence of validators to a set of dict keys.

A ``DictRule`` is the data shape that ``DictForEachValidator`` uses to
apply per-key validation. The ``keys`` is either a sequence of hashable
key values or a callable that receives one key and returns a truthy value
when the rule should apply.

If ``keys`` is a sequence, for every key listed in ``keys``,
every validator in ``validators`` is applied in order, threading the
normalized return value forward.
If ``keys`` is a callable, it is called for each key that is present in
the dict. If the callable returns a truthy value, the validators are
applied in order to the value at that key, threading the normalized
return value forward. If the callable returns a falsey value, the
validators are not applied to the value at that key.

<a id="config_as_json.dict_validators.DictRule.__post_init__"></a>

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

Validate that ``keys`` and ``validators`` are well-formed.

**Raises**:

- `ValueError` - If ``keys`` or ``validators`` is empty, or if
  ``keys`` contains a duplicate entry.
- `TypeError` - If any entry of ``keys`` is not hashable or any
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
validator finds that rule's matching keys and applies every validator
in the rule's ``validators`` (in declaration order) to the value at
each matching key. A fixed key sequence is iterated in declaration
order. A key predicate is called for each present dict key, in the
dict's insertion order, and truthy predicate results select the key.
Each validator receives the value returned by the previous validator,
so normalization performed by one inner validator is visible to the
next one. The dict member is never modified in place; a new dict is
returned that carries the per-key updates.

A rule key that is not present in the dict is silently skipped. This
keeps the validator strictly orthogonal to ``DictKeysValidator``,
which is the dedicated mechanism for enforcing that mandatory keys
are present and that unknown keys are rejected.

Keys that are present in the dict but are not covered by any rule are
copied through unchanged.

Inner validator calls receive ``f'{member_name}[{key}]'`` as the
``member_name``, so error messages stay precise about which key
failed. The same convention is used by ``ListForEachValidator`` with
the index in place of the key. The ``member_name`` is built as the
configuration structure is traversed. The top level member name starts
the string as a plain string. When "indexing" into a list or dict the
index is appended in square brackets. When going into a class member
a dot and the member name is appended.

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

<a id="config_as_json.dict_validators.DictForEachValidator._run_rule_on_key"></a>

#### \_run\_rule\_on\_key

```python
def _run_rule_on_key(rule: DictRule, config: Config, member_name: str,
                     member_value: dict[Hashable, object], key: Hashable,
                     stderr_file: TextIO) -> Optional[object]
```

Run a single rule on a dict member.

**Arguments**:

- `rule` - The rule to run.
- `config` - The Config object that owns the member.
- `member_name` - The name of the outer dict member to validate.
- `member_value` - The dict value to validate.
- `key` - The key to validate.
- `stderr_file` - The file to write error messages to.

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

<a id="config_as_json.dict_validators.DictKeyValueTypesValidator"></a>

## DictKeyValueTypesValidator Objects

```python
class DictKeyValueTypesValidator(MemberValidator)
```

Validate the key and value runtime types of a uniform dict.

This validator is a compact way to validate dicts whose keys all have
one type and whose values all have one type, such as ``dict[str, int]``
or ``dict[str, list[float]]``. It cannot describe non-uniform dicts
such as a ``TypedDict``-like shape where different keys have different
value policies. For those cases, use ``DictKeysValidator`` together
with ``DictForEachValidator`` and one or more ``DictRule`` objects.

The outer member must be a dict. Every key is checked with
``isinstance(key, key_type)`` and every value is checked with
``isinstance(value, value_type)``. If ``value_validator`` is supplied,
it is then applied to each value through ``DictForEachValidator``.
That hook is intended for validating the inside of composite values,
for example ``dict[str, list[float]]``. A validator that performs
unrelated value checks is allowed, but it makes application code harder
to understand; prefer ``DictForEachValidator`` for those richer rules.

An empty dict is considered valid.

<a id="config_as_json.dict_validators.DictKeyValueTypesValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(key_type: type[Hashable],
             value_type: type[object],
             value_validator: Optional[MemberValidator] = None) -> None
```

Initialize the validator.

**Arguments**:

- `key_type` - The type of the keys. The type is checked using
  isinstance.
- `value_type` - The type of the values. The type is checked using
  isinstance.
- `value_validator` - The validator to apply to each value. This
  validator is not needed for simple value types such as
  int, float, str, bool, etc. It is needed for when the
  value is a dict, list, or other type that needs to be
  traversed to be validated.


**Raises**:

- `TypeError` - If ``key_type`` is not a hashable type,
  ``value_type`` is not a type, or ``value_validator`` is not
  a ``MemberValidator`` or ``None``.

<a id="config_as_json.dict_validators.DictKeyValueTypesValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one dict member against the configured value types.

The type of the member itself is checked to be a dict using isinstance.
Then the types of all keys and values are checked using isinstance.
Optionally, the types inside the value are checked using the
value_validator. An empty dict is considered valid.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The dict value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The original dict value if validation succeeds without
  ``value_validator``. When ``value_validator`` is supplied, a new
  dict is returned with any value normalizations from that inner
  validator.


**Raises**:

- `InvalidConfiguration` - If the member is not a dict, or the types of
  the keys or values are not as expected, or a supplied
  validator raised ``InvalidConfiguration``.
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

<a id="config_as_json.list_validators._validate_list_element_type"></a>

#### \_validate\_list\_element\_type

```python
def _validate_list_element_type(element_type: type[object]) -> None
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

<a id="config_as_json.list_validators._indexed_not_allowed_message"></a>

#### \_indexed\_not\_allowed\_message

```python
def _indexed_not_allowed_message(member_name: str, member_value: object,
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
class ListValueValidator(MemberValidator, Generic[Basictype])
```

Validate values in a list of basic scalar values.

<a id="config_as_json.list_validators.ListValueValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(
    min_value: Optional[Basictype],
    max_value: Optional[Basictype],
    allowed_values: Optional[Sequence[Basictype]
                             | Callable[[], Sequence[Basictype]]],
    lt_comparator: Callable[[Basictype, Basictype],
                            bool] = operator_lt) -> None
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
  If a callable, it is called at validation time
  to get the allowed values.
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

<a id="config_as_json.list_validators.ListValueTypeValidator"></a>

## ListValueTypeValidator Objects

```python
class ListValueTypeValidator(MemberValidator)
```

Validate that a member is a list with one element runtime type.

<a id="config_as_json.list_validators.ListValueTypeValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(element_type: type[object]) -> None
```

Initialize the validator.

**Arguments**:

- `element_type` - Required runtime type for each list element.


**Raises**:

- `TypeError` - If ``element_type`` is not a type.

<a id="config_as_json.list_validators.ListValueTypeValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one list member's element types.

The element checks use normal ``isinstance`` semantics. For example,
``ListValueTypeValidator(int)`` accepts ``True`` because ``bool`` is
a subclass of ``int`` in Python.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the member to validate.
- `member_value` - The list value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The original list value if validation succeeds.


**Raises**:

- `InvalidConfiguration` - If the member is not a list or one element
  is not an instance of ``element_type``.

<a id="config_as_json.list_validators.ListIsOrderedValidator"></a>

## ListIsOrderedValidator Objects

```python
class ListIsOrderedValidator(MemberValidator, Generic[Basictype])
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
    lt_comparator: Callable[[Basictype, Basictype],
                            bool] = operator_lt) -> None
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
class ListOrderingValidator(MemberValidator, Generic[Basictype])
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
    lt_comparator: Callable[[Basictype, Basictype],
                            bool] = operator_lt) -> None
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
about which element failed. The ``member_name`` is built as the
configuration structure is traversed. The top level member name starts
the string as a plain string. When "indexing" into a list or dict the
index is appended in square brackets. When going into a class member
a dot and the member name is appended.

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

<a id="config_as_json.list_validators.ListOfDictsKeysValidator"></a>

## ListOfDictsKeysValidator Objects

```python
class ListOfDictsKeysValidator(MemberValidator)
```

Validate the keys of every dict element in a list member.

This is the dedicated predefined validator for the common "list of
dictionaries with a fixed key policy" shape. It is equivalent to using a
``ListForEachValidator`` with ``element_type=dict`` and one inner
``DictKeysValidator``. Pass ``allow_extra_dict_keys=True`` for an open
dict shape where each element must contain selected mandatory keys but
may also carry application-specific extra keys.

<a id="config_as_json.list_validators.ListOfDictsKeysValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(mandatory_keys: Sequence[str],
             allowed_keys: Optional[Sequence[str]] = None,
             allow_extra_dict_keys: bool = False) -> None
```

Initialize the validator.

**Arguments**:

- `mandatory_keys` - Keys that must be present in every dict element.
- `allowed_keys` - Additional keys that are permitted but not required.
- `allow_extra_dict_keys` - Whether keys not listed in
  ``mandatory_keys`` or ``allowed_keys`` should be accepted.


**Raises**:

- `TypeError` - If any key entry is not a string.
- `ValueError` - If a key sequence contains duplicates.

<a id="config_as_json.list_validators.ListOfDictsKeysValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: Config,
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one list-of-dicts member against the configured keys.

**Arguments**:

- `config` - The Config object that owns the member.
- `member_name` - The name of the list member to validate.
- `member_value` - The list value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  A new list containing the validated dict elements.


**Raises**:

- `InvalidConfiguration` - If the member is not a list, one element is
  not a dict, one dict misses a mandatory key, or one dict has
  an unknown key while ``allow_extra_dict_keys`` is ``False``.

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

<a id="config_as_json.read_old_configuration"></a>

# config\_as\_json.read\_old\_configuration

Support read old configuration file (ROCF) normalization rules.

Application code derives from :class:`ReadOldConfiguration` and returns small
rule objects from its methods. The config_as_json library applies those rules
while reading JSON, before validation and nested ``Config`` conversion.

<a id="config_as_json.read_old_configuration.RocfKeyMove"></a>

## RocfKeyMove Objects

```python
class RocfKeyMove(NamedTuple)
```

Declare that an old value belongs at a current path.

Application subclasses return ``RocfKeyMove`` objects from
:meth:`ReadOldConfiguration.get_json_key_moves` when an old configuration
file used a different JSON structure from the current configuration class.
``old_path`` says where old files may contain the value. ``new_path`` says
where the same value belongs in the current JSON shape.

The library validates both paths before applying a rule. Empty paths are
illegal, and ``old_path`` and ``new_path`` must not be equal.

If ``old_path`` is missing, the rule is a no-op because the input may
already use the current schema. If traversal of ``old_path`` reaches a
value with the wrong container type, the rule is also a no-op. Normal
current-schema parsing later decides whether the remaining data is valid.

If the library needs to create an intermediate dictionary or list below
``new_path`` and an incompatible value already exists there, processing
fails with :class:`RocfIncompatiblePathError`.

If both the old value and the current-shape target value exist in one
input file, the current-shape value wins. The library deletes the old
value, writes a diagnostic to the ``stderr_file`` supplied to
:meth:`ReadOldConfiguration.process_json`, and reports the handled old path
to the automatic-change hook.

List handling is intentionally narrow so application rules stay
predictable:

- A path without ``'['`` uses only dictionary traversal.
- If old and new paths contain the same number of ``'['`` elements, list
elements are paired by index. For example,
``RocfKeyMove(old_path=('outputs', '[', 'encoding'),
new_path=('outputs', '[', 'char_encoding'))`` renames a member in every
existing list element.
- If the new path contains one ``'['`` and the old path contains none, the
old value is wrapped into a single-element list when the current list is
absent. If the current list already exists, it wins.
- If the old path contains more ``'['`` elements than the new path, the
move is undefined in this declarative API. Use pre-processing or
post-processing for many-to-one migrations.
- Moving only one selected list element is not supported in this version.

Moving a whole old object into a list element is preferred when changing an
object-valued member into a list-valued current member. For example,
``RocfKeyMove(old_path=('output',), new_path=('outputs', '['))`` turns the
old ``output`` object into the first and only element of ``outputs``.

Moves whose old and new paths overlap are legal. The library reads the old
value first, removes the old path, and then writes the new path.
Overlapping moves are order-sensitive, so application code should avoid
them unless the migration really needs them.

If an old file really contains a dictionary key that starts with ``'['``,
handle that file in :meth:`ReadOldConfiguration.pre_process_json` or
:meth:`ReadOldConfiguration.post_process_json` instead of a declarative
ROCF path rule.

**Attributes**:

- `old_path` - Absolute path to the old value in the root configuration
  data object.
- `new_path` - Absolute path where the value belongs in the current
  configuration data object.

<a id="config_as_json.read_old_configuration.RocfKeyRename"></a>

#### RocfKeyRename

Describe a configuration key rename from an old name to a new name.

Application subclasses return these from
:meth:`ReadOldConfiguration.get_json_key_renames` when reading old
configuration files (ROCF). The library recursively changes dictionary members
named ``old`` to ``new`` in dictionaries and lists. If both names exist in the
same dictionary, the current name wins and the old value is discarded.

<a id="config_as_json.read_old_configuration.RocfConflictError"></a>

## RocfConflictError Objects

```python
class RocfConflictError(InvalidConfiguration)
```

Raised when several old-file move rules write one current path.

Application code may declare several :class:`RocfKeyMove` rules with the
same ``new_path`` when one current configuration version can read files
from more than one older version. The library raises this exception only
if more than one rule actually writes to the same current target while
processing one input file.

<a id="config_as_json.read_old_configuration.RocfIncompatiblePathError"></a>

## RocfIncompatiblePathError Objects

```python
class RocfIncompatiblePathError(InvalidConfiguration)
```

Raised when the library cannot create a declared current path.

Declarative read old configuration file (ROCF) processing raises this when
a move or missing-value rule needs an intermediate dictionary or list, but
the input data already has an incompatible value at that location.

<a id="config_as_json.read_old_configuration._MovedValue"></a>

## \_MovedValue Objects

```python
class _MovedValue(NamedTuple)
```

One existing old value found by expanding a move rule.

<a id="config_as_json.read_old_configuration._MoveContext"></a>

## \_MoveContext Objects

```python
class _MoveContext(NamedTuple)
```

Library state shared while applying one batch of move rules.

<a id="config_as_json.read_old_configuration._as_dict"></a>

#### \_as\_dict

```python
def _as_dict(value: object) -> Optional[dict[str, object]]
```

Return ``value`` as a JSON-object dictionary if possible.

<a id="config_as_json.read_old_configuration._as_list"></a>

#### \_as\_list

```python
def _as_list(value: object) -> Optional[list[object]]
```

Return ``value`` as a JSON-array list if possible.

<a id="config_as_json.read_old_configuration._path_text"></a>

#### \_path\_text

```python
def _path_text(path: Sequence[str | int]) -> str
```

Return the path text used in diagnostics and hook callbacks.

The first dictionary key is rendered as a plain string. Every later
step (dictionary key or list index) is wrapped in square brackets, so
a JSON path renders as ``outputs[2][csv_params][delimiter]``. ROCF
only traverses plain JSON dictionaries and lists, so there is no
``.member`` dot syntax here: that style is reserved for cases where a
path step is known to address a class attribute (for instance inside
a nested ``Config`` object), which ROCF does not do.

<a id="config_as_json.read_old_configuration._validate_path"></a>

#### \_validate\_path

```python
def _validate_path(path: ConfigPath, name: str) -> None
```

Validate a path returned by an application ROCF method.

<a id="config_as_json.read_old_configuration._list_marker_count"></a>

#### \_list\_marker\_count

```python
def _list_marker_count(path: ConfigPath) -> int
```

Return the number of each-list wildcards in ``path``.

<a id="config_as_json.read_old_configuration._validate_move"></a>

#### \_validate\_move

```python
def _validate_move(move: RocfKeyMove) -> None
```

Validate one application-supplied move rule before applying it.

<a id="config_as_json.read_old_configuration._conflict_diag"></a>

#### \_conflict\_diag

```python
def _conflict_diag(old_path: str, new_path: str, stderr_file: TextIO) -> None
```

Write the user-facing diagnostic for a current value winning.

<a id="config_as_json.read_old_configuration._remove_key_recursive"></a>

#### \_remove\_key\_recursive

```python
def _remove_key_recursive(data: object, key: str) -> bool
```

Remove an old key name from every dictionary below ``data``.

<a id="config_as_json.read_old_configuration._rename_key_recursive"></a>

#### \_rename\_key\_recursive

```python
def _rename_key_recursive(rename: RocfKeyRename, data: object,
                          stderr_file: TextIO) -> bool
```

Apply one recursive old-name to current-name rename rule.

<a id="config_as_json.read_old_configuration._collect_path_values"></a>

#### \_collect\_path\_values

```python
def _collect_path_values(data: object, path: ConfigPath,
                         actual: list[str | int],
                         indexes: list[int]) -> list[_MovedValue]
```

Collect old values reached by expanding one move-rule path.

<a id="config_as_json.read_old_configuration._target_path"></a>

#### \_target\_path

```python
def _target_path(new_path: ConfigPath, indexes: list[int]) -> list[str | int]
```

Return the current target path for one collected old value.

<a id="config_as_json.read_old_configuration._delete_path"></a>

#### \_delete\_path

```python
def _delete_path(data: object, path: Sequence[str | int]) -> None
```

Delete an old actual path after it has been handled.

<a id="config_as_json.read_old_configuration._path_exists"></a>

#### \_path\_exists

```python
def _path_exists(data: object, path: Sequence[str | int]) -> bool
```

Return whether a current actual path already exists.

<a id="config_as_json.read_old_configuration._path_is_prefix"></a>

#### \_path\_is\_prefix

```python
def _path_is_prefix(first: Sequence[str | int],
                    second: Sequence[str | int]) -> bool
```

Return whether ``first`` is an ancestor path of ``second``.

<a id="config_as_json.read_old_configuration._paths_overlap"></a>

#### \_paths\_overlap

```python
def _paths_overlap(first: Sequence[str | int],
                   second: Sequence[str | int]) -> bool
```

Return whether either actual path is an ancestor of the other.

<a id="config_as_json.read_old_configuration._wrap_prefix"></a>

#### \_wrap\_prefix

```python
def _wrap_prefix(move: RocfKeyMove,
                 target: list[str | int]) -> Optional[list[str | int]]
```

Return the current-list path for an object-to-list move.

<a id="config_as_json.read_old_configuration._get_existing_value"></a>

#### \_get\_existing\_value

```python
def _get_existing_value(data: object,
                        path: Sequence[str | int]) -> tuple[bool, object]
```

Return whether an actual path exists and its current value.

<a id="config_as_json.read_old_configuration._container_for"></a>

#### \_container\_for

```python
def _container_for(next_part: str | int) -> object
```

Return the empty container needed before ``next_part``.

<a id="config_as_json.read_old_configuration._require_dict"></a>

#### \_require\_dict

```python
def _require_dict(value: object,
                  path: Sequence[str | int]) -> dict[str, object]
```

Return a dict or raise when a rule needs a dict path.

<a id="config_as_json.read_old_configuration._require_list"></a>

#### \_require\_list

```python
def _require_list(value: object, path: Sequence[str | int]) -> list[object]
```

Return a list or raise when a rule needs a list path.

<a id="config_as_json.read_old_configuration._write_path"></a>

#### \_write\_path

```python
def _write_path(data: object, path: Sequence[str | int],
                value: object) -> None
```

Write a moved or missing value, creating current containers.

<a id="config_as_json.read_old_configuration._remove_path"></a>

#### \_remove\_path

```python
def _remove_path(data: object, path: ConfigPath,
                 actual: list[str | int]) -> list[str]
```

Apply one old-path remove rule and return removed path texts.

<a id="config_as_json.read_old_configuration._apply_missing"></a>

#### \_apply\_missing

```python
def _apply_missing(data: object, path: ConfigPath, value: object,
                   actual: list[str | int]) -> list[str]
```

Apply one current missing-value rule and return changed paths.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration"></a>

## ReadOldConfiguration Objects

```python
class ReadOldConfiguration()
```

Base class for application-specific old-file compatibility.

Applications derive from this class when the current ``Config`` subclass
should accept configuration files written by older application versions.
The current ``Config`` subclass normally returns that derived object from
``_get_read_old_configuration()``.

The config_as_json library calls this object while reading every
configuration file. It has already decoded JSON text and may already have
applied ``parse_converters()`` to scalar leaf values. It has not yet
validated the data or converted dictionaries into nested ``Config``
objects.

A subclass should describe only the differences between old files and the
current JSON shape. Current-format input should therefore pass through
unchanged when no old names, old paths or missing current values are
present.

Application-specific subclasses should normally override only declarative
methods:

- :meth:`get_keys_to_remove_recursively`
- :meth:`get_keys_to_remove`
- :meth:`get_json_key_renames`
- :meth:`get_json_key_moves`
- :meth:`get_values_for_missing_json_keys`

Unusual migrations can override :meth:`pre_process_json` or
:meth:`post_process_json`. See ``example/src`` for complete examples.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration.process_json"></a>

#### process\_json

```python
def process_json(json_data: dict[str,
                                 object], auto_ch_hook: ConfigAutoChangeHook,
                 stderr_file: TextIO) -> dict[str, object]
```

Let the library normalize parsed data to the current shape.

Application code normally does not call this method directly.
``Config.parse_json()`` calls it after JSON decoding and before normal
validation. Subclasses customize the result by overriding the rule
methods called below.

The library applies rules in this order:

1. :meth:`pre_process_json`
2. remove keys from :meth:`get_keys_to_remove_recursively`
3. remove keys from :meth:`get_keys_to_remove`
4. rename keys from :meth:`get_json_key_renames`
5. move paths from :meth:`get_json_key_moves`
6. add values from :meth:`get_values_for_missing_json_keys`
7. :meth:`post_process_json`

Missing values are applied after renames and moves so old values get a
chance to populate the current shape before fallback values are
supplied.

This method may mutate ``json_data`` in place. The caller must use the
returned object because overrides may return another dictionary.

The library reports actual performed compatibility changes to
``auto_ch_hook``. A wildcard move over three list elements is therefore
reported as three individual moved paths. Moved paths use the same
text style as member names used by member validators, for example
``outputs[2][csv_params][delimiter]``. ROCF traverses plain JSON
dictionaries and lists, so every step after the top-level key is
rendered with ``[...]``; the ``.member`` dot syntax is reserved for
paths through class attributes and is not used here.

Current-shape values win over old-shape values if both are present.
In that case the library removes the old value, writes a diagnostic to
``stderr_file``, and reports that the old value was handled.

**Arguments**:

- `json_data` - Parsed root object to normalize. The object has not yet
  been validated or converted to nested ``Config`` objects.
- `auto_ch_hook` - Hook that records automatic compatibility changes.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  Parsed configuration data matching the current JSON schema.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration._remove_keys_recursively"></a>

#### \_remove\_keys\_recursively

```python
def _remove_keys_recursively(json_data: dict[str, object],
                             auto_ch_hook: ConfigAutoChangeHook) -> None
```

Apply application-declared recursive key removals.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration._remove_keys_by_path"></a>

#### \_remove\_keys\_by\_path

```python
def _remove_keys_by_path(json_data: dict[str, object],
                         auto_ch_hook: ConfigAutoChangeHook) -> None
```

Apply application-declared path-based key removals.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration._rename_json_keys"></a>

#### \_rename\_json\_keys

```python
def _rename_json_keys(json_data: dict[str, object],
                      auto_ch_hook: ConfigAutoChangeHook,
                      stderr_file: TextIO) -> None
```

Apply application-declared recursive key renames.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration._move_json_keys"></a>

#### \_move\_json\_keys

```python
def _move_json_keys(json_data: dict[str, object],
                    auto_ch_hook: ConfigAutoChangeHook,
                    stderr_file: TextIO) -> None
```

Apply application-declared path moves in declaration order.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration._move_one_path"></a>

#### \_move\_one\_path

```python
def _move_one_path(context: _MoveContext, move: RocfKeyMove,
                   moved_value: _MovedValue) -> None
```

Move one collected old value or discard it if current wins.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration._target_is_current"></a>

#### \_target\_is\_current

```python
def _target_is_current(context: _MoveContext, moved_value: _MovedValue,
                       wrap_prefix: Optional[list[str | int]],
                       target: list[str | int]) -> bool
```

Return whether the current-shape value exists and wins.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration._apply_missing_values"></a>

#### \_apply\_missing\_values

```python
def _apply_missing_values(json_data: dict[str, object],
                          auto_ch_hook: ConfigAutoChangeHook) -> None
```

Apply application-declared current missing-value rules.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration.get_json_key_moves"></a>

#### get\_json\_key\_moves

```python
def get_json_key_moves() -> list[RocfKeyMove]
```

Return old paths whose values should move to current paths.

Application subclasses override this when an old file stores a value
in one JSON structure and the current configuration expects the same
value in another structure. Return ``RocfKeyMove`` entries in the order
they should be applied.

The library ignores a rule when the old path is absent. If the old
value exists and the current target does not, the library moves the
value and removes the old path. If both old and current values exist,
the current value wins, the old path is removed, and a diagnostic is
written.

Several rules may declare the same target path so one current version
can read several older file shapes. During one file read, only one
rule may actually write a given current target. Rules that overlap by
ancestor or descendant paths are legal but order-sensitive.

**Example**:

  ``RocfKeyMove(old_path=('output',), new_path=('outputs', '['))``
  moves an old direct ``output`` object into the first element of the
  current ``outputs`` list.


**Returns**:

  Move rules to apply in list order while reading old files.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration.get_keys_to_remove_recursively"></a>

#### get\_keys\_to\_remove\_recursively

```python
def get_keys_to_remove_recursively() -> list[str]
```

Return old key names to remove recursively.

Application subclasses override this when old configuration files may
contain a member name that no longer exists anywhere in the current
configuration.

The library removes each returned name from every dictionary it finds
below the root object, including dictionaries inside lists. New code
should usually prefer :meth:`get_keys_to_remove` for precise
path-based removal unless this recursive name-based behavior is really
intended.

**Example**:

  Returning ``['debug_trace']`` removes ``debug_trace`` wherever an
  old file contains it.


**Returns**:

  Old dictionary member names that should be accepted and removed.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration.get_keys_to_remove"></a>

#### get\_keys\_to\_remove

```python
def get_keys_to_remove() -> list[ConfigPath]
```

Return old paths to remove while reading old files.

Application subclasses override this when old configuration files may
contain a value at a known path that no longer exists in the current
configuration.

The library removes each returned path when it exists. Missing paths
are ignored. If traversal reaches a value with the wrong container
type, that path is ignored because the input may already use the
current schema.

**Example**:

  Returning ``[('sections', '[', 'stale')]`` removes the old
  ``stale`` key from every object in the ``sections`` list.


**Returns**:

  Old paths that should be accepted and removed from the input data.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration.get_values_for_missing_json_keys"></a>

#### get\_values\_for\_missing\_json\_keys

```python
def get_values_for_missing_json_keys() -> dict[ConfigPath, object]
```

Return values for missing current-schema paths.

Application subclasses override this when old configuration files lack
a value that is mandatory in the current configuration. Return current
paths and the values that should be inserted when those paths are
absent.

The library applies these values after removals, renames and moves.
This gives old values a chance to populate the current shape before
fallback values are supplied. The value is deep-copied before it is
inserted so later changes to one inserted container do not affect
another.

Intermediate dictionaries may be created as needed. If the path
contains the list wildcard ``'['``, the value is supplied inside
existing list elements only. To supply an empty list that is itself
missing, use the path to the list member, for example
``{('outputs',): []}``.

If an incompatible value already exists while creating the path,
the library raises :class:`RocfIncompatiblePathError`.

**Example**:

  Returning ``{('format_version',): 2}`` inserts
  ``format_version`` only when the input file does not contain it.


**Returns**:

  A mapping from current paths to values supplied when absent.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration.get_json_key_renames"></a>

#### get\_json\_key\_renames

```python
def get_json_key_renames() -> list[RocfKeyRename]
```

Return old dictionary member names mapped to current names.

Application subclasses override this when old files used different key
names for values that still live in the same relative JSON structure.

The library applies these renames recursively through dictionaries and
lists. If both the old and current names exist in the same dictionary,
the current value wins, the old value is removed, and a diagnostic is
written.

Use :meth:`get_json_key_moves` instead when the migration depends on a
precise path or changes the JSON structure.

**Example**:

  Returning ``[RocfKeyRename(old='title', new='report_name')]``
  accepts old files that used ``title`` and converts them to the
  current ``report_name`` key before validation.


**Returns**:

  Accepted old-name to current-name rename rules.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration.pre_process_json"></a>

#### pre\_process\_json

```python
def pre_process_json(json_data: dict[str, object],
                     auto_ch_hook: ConfigAutoChangeHook,
                     stderr_file: TextIO) -> dict[str, object]
```

Pre-process data before declarative old-file handling.

Application subclasses override this only for old-file migrations that
cannot be expressed with removals, renames, moves or missing values.
Prefer the declarative methods when they are enough, because the
library can then handle reporting, current-value conflicts and path
validation consistently.

The library calls this before any declarative rules. The override may
mutate ``json_data`` in place or return a replacement dictionary. It
should report any compatibility changes it performs through
``auto_ch_hook`` and write user-facing diagnostics to ``stderr_file``
when needed.

**Arguments**:

- `json_data` - Parsed root object to normalize. The data is not yet
  validated, and dictionaries have not yet been converted to
  nested ``Config`` objects.
- `auto_ch_hook` - Hook that records automatic compatibility changes.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  Data to pass to the declarative old-file processing steps.

<a id="config_as_json.read_old_configuration.ReadOldConfiguration.post_process_json"></a>

#### post\_process\_json

```python
def post_process_json(json_data: dict[str, object],
                      auto_ch_hook: ConfigAutoChangeHook,
                      stderr_file: TextIO) -> dict[str, object]
```

Post-process data after declarative old-file handling.

Application subclasses override this only for old-file migrations that
need to inspect or adjust the result of the declarative processing.
Prefer declarative rules when possible.

The library calls this after removals, renames, moves and missing
values. The override may mutate ``json_data`` in place or return a
replacement dictionary. It should report any compatibility changes it
performs through ``auto_ch_hook`` and write user-facing diagnostics to
``stderr_file`` when needed.

**Arguments**:

- `json_data` - Current-shape data after declarative processing steps
  in ReadOldConfiguration. The data is not yet validated, and
  dictionaries have not yet been converted to nested ``Config``
  objects.
- `auto_ch_hook` - Hook that records automatic compatibility changes.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  Data matching the current configuration schema. This data is now
  ready to be validated and converted to nested Config objects.

<a id="config_as_json._config_initial_data"></a>

# config\_as\_json.\_config\_initial\_data

Copy neutral initial data into Config defaults and auto-wrap nesting.

This private module implements two related operations:

- ``copy_initial_data_impl`` copies public attribute values from a neutral
  data source (plain object, dataclass instance, or mapping) onto a Config
  target. It is the workhorse behind ``Config.copy_initial_data``.

- ``auto_wrap_nested_defaults_impl`` is called from ``Config.__init__``
  after the nested-config declarations have been validated. It walks the
  declared nested members and replaces any default value that is not yet
  an instance of its declared bridge ``config_type`` with a freshly
  constructed bridge-typed value whose public attributes were copied from
  the original neutral value.

Together these two operations let a derived Config inherit defaults from a
framework-neutral data class without copying every public attribute by
hand and without losing the bridge-typed schema for nested sections.

<a id="config_as_json._config_initial_data._public_items_of"></a>

#### \_public\_items\_of

```python
def _public_items_of(source: object) -> Iterator[tuple[str, object]]
```

Yield ``(name, value)`` pairs for public attributes of ``source``.

The source may be a :class:`collections.abc.Mapping` (typically a
:class:`dict`), or any object with a ``__dict__`` (plain object or a
dataclass instance). Names starting with ``_`` and callable values are
skipped so that helper methods and private bookkeeping never leak into
the copy.

**Arguments**:

- `source` - Object or mapping to read public attributes from.


**Yields**:

  Tuples of ``(attribute name, attribute value)`` in the source's
  own iteration order.


**Raises**:

- `TypeError` - ``source`` exposes no readable public attributes, or a
  mapping key is not a string.

<a id="config_as_json._config_initial_data._public_items_of_mapping"></a>

#### \_public\_items\_of\_mapping

```python
def _public_items_of_mapping(
        source: Mapping[object, object]) -> Iterator[tuple[str, object]]
```

Yield public ``(name, value)`` pairs for a Mapping source.

<a id="config_as_json._config_initial_data._public_items_of_object"></a>

#### \_public\_items\_of\_object

```python
def _public_items_of_object(source: object) -> Iterator[tuple[str, object]]
```

Yield public ``(name, value)`` pairs for an object source.

<a id="config_as_json._config_initial_data.copy_initial_data_impl"></a>

#### copy\_initial\_data\_impl

```python
def copy_initial_data_impl(source: object, target: 'Config') -> None
```

Copy public attributes from ``source`` onto a Config ``target``.

The check for "extra" source attributes is enforced only when
``target`` already exposes at least one public attribute. That covers
the common multiple-inheritance pattern where the neutral base class
constructor has already created the schema on ``target``, and it also
covers the internal wrap path where a freshly constructed bridge is
being populated. When ``target`` has no public attributes yet (the
pattern used when the neutral constructor takes required arguments
that the bridge does not duplicate), the source's public attributes
become the target's schema and no comparison can be made.

**Arguments**:

- `source` - Plain object, mapping, or dataclass instance whose public
  attributes describe the desired default values.
- `target` - Config instance whose attributes should be assigned.


**Raises**:

- `TypeError` - ``source`` cannot be read, or ``target`` has a known
  public schema and ``source`` exposes a public attribute that
  ``target`` does not declare.

<a id="config_as_json._config_initial_data._wrap_one_value"></a>

#### \_wrap\_one\_value

```python
def _wrap_one_value(source: object, config_type: 'type[Config]', name: str,
                    stderr_file: TextIO) -> 'Config'
```

Build a bridge Config instance whose values come from ``source``.

**Arguments**:

- `source` - Neutral value (plain object, mapping, or dataclass).
- `config_type` - Bridge Config-derived class to construct.
- `name` - Diagnostic member name used in error messages.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  A new bridge Config instance with attributes copied from
  ``source`` and any further nested neutrals wrapped recursively.


**Raises**:

- `TypeError` - ``source`` cannot be read or describes attributes that
  ``config_type`` does not declare.

<a id="config_as_json._config_initial_data._wrap_optional_or_member"></a>

#### \_wrap\_optional\_or\_member

```python
def _wrap_optional_or_member(current_value: object,
                             config_type: 'type[Config]', name: str,
                             allow_none: bool, stderr_file: TextIO) -> object
```

Compute the auto-wrapped value for one direct nested member.

<a id="config_as_json._config_initial_data._wrap_list_elements"></a>

#### \_wrap\_list\_elements

```python
def _wrap_list_elements(current_value: object, config_type: 'type[Config]',
                        name: str, stderr_file: TextIO) -> object
```

Compute the auto-wrapped list for a LIST_ELEMENT nested member.

<a id="config_as_json._config_initial_data._wrap_dict_values"></a>

#### \_wrap\_dict\_values

```python
def _wrap_dict_values(current_value: object, config_type: 'type[Config]',
                      name: str, stderr_file: TextIO) -> object
```

Compute the auto-wrapped dict for a DICT_VALUE nested member.

<a id="config_as_json._config_initial_data._wrap_dict_value_by_key"></a>

#### \_wrap\_dict\_value\_by\_key

```python
def _wrap_dict_value_by_key(current_value: object,
                            nestings: list[ConfigNesting], name: str,
                            stderr_file: TextIO) -> object
```

Compute the auto-wrapped dict for DICT_VALUE_BY_KEY nestings.

<a id="config_as_json._config_initial_data._nesting_by_key"></a>

#### \_nesting\_by\_key

```python
def _nesting_by_key(nestings: list[ConfigNesting]) -> dict[str, ConfigNesting]
```

Return DICT_VALUE_BY_KEY declarations keyed by discriminator_key.

<a id="config_as_json._config_initial_data._auto_wrap_one_member"></a>

#### \_auto\_wrap\_one\_member

```python
def _auto_wrap_one_member(member_name: str, current_value: object,
                          nestings: list[ConfigNesting],
                          stderr_file: TextIO) -> object
```

Compute the auto-wrapped value for one declared nested member.

<a id="config_as_json._config_initial_data.auto_wrap_nested_defaults_impl"></a>

#### auto\_wrap\_nested\_defaults\_impl

```python
def auto_wrap_nested_defaults_impl(target: 'Config',
                                   nested_decls: dict[str,
                                                      list[ConfigNesting]],
                                   stderr_file: TextIO) -> None
```

Wrap any nested member defaults that are not yet bridge-typed.

**Arguments**:

- `target` - Config instance whose declared nested members should be
  scanned and possibly replaced with bridge-typed wrappers.
- `nested_decls` - Validated nested-config declarations for ``target``.
- `stderr_file` - Stream used for user-facing diagnostics.

<a id="config_as_json.as_dict_view_validator"></a>

# config\_as\_json.as\_dict\_view\_validator

Validate a member value through a dictionary-shaped view.

<a id="config_as_json.as_dict_view_validator.public_attrs_to_dict"></a>

#### public\_attrs\_to\_dict

```python
def public_attrs_to_dict(config: 'Config', member_name: str,
                         member_value: object,
                         stderr_file: TextIO) -> dict[Hashable, object]
```

Project public object attributes to a dictionary.

This helper is the explicit opt-in conversion for the common case where
an application class stores its configuration data in normal public
instance attributes. The intended dictionary view contains every
non-callable entry in ``vars(member_value)`` whose name does not start
with ``'_'``.

The projected dictionary is intended to be a shallow copy. Replacing a
value in the projected dictionary should not replace the corresponding
attribute on ``member_value``. If an attribute value is itself mutable,
validators that mutate that shared value in place may still affect the
original object.

**Arguments**:

- `config` - The configuration object that owns ``member_name``.
- `member_name` - The name of the member being projected.
- `member_value` - The non-dict object to project.
- `stderr_file` - The stream used for diagnostics.


**Returns**:

  A dictionary-shaped validation view of ``member_value``.


**Raises**:

- `InvalidConfiguration` - If ``member_value`` cannot be projected from
  public attributes.

<a id="config_as_json.as_dict_view_validator._validate_non_dict_type"></a>

#### \_validate\_non\_dict\_type

```python
def _validate_non_dict_type(non_dict_type: object) -> type[object]
```

Validate and return the accepted non-dict runtime type.

<a id="config_as_json.as_dict_view_validator._validate_to_dict"></a>

#### \_validate\_to\_dict

```python
def _validate_to_dict(
    to_dict: object
) -> Callable[['Config', str, object, TextIO], dict[Hashable, object]]
```

Validate and return the dictionary-view projector.

<a id="config_as_json.as_dict_view_validator._validate_rules"></a>

#### \_validate\_rules

```python
def _validate_rules(rules: object) -> list[DictRule]
```

Validate and return dictionary rules for the view.

<a id="config_as_json.as_dict_view_validator._validate_validators"></a>

#### \_validate\_validators

```python
def _validate_validators(
        validators: Optional[Sequence[MemberValidator]]
) -> list[MemberValidator]
```

Validate and return whole-dict validators for the view.

<a id="config_as_json.as_dict_view_validator._ensure_work_exists"></a>

#### \_ensure\_work\_exists

```python
def _ensure_work_exists(rules: Sequence[DictRule],
                        validators: Sequence[MemberValidator]) -> None
```

Validate that the validator has at least one operation to run.

<a id="config_as_json.as_dict_view_validator._raise_invalid_member_type"></a>

#### \_raise\_invalid\_member\_type

```python
def _raise_invalid_member_type(member_name: str, member_value: object,
                               non_dict_type: type[object],
                               stderr_file: TextIO) -> None
```

Raise an invalid-configuration error for an unsupported value type.

<a id="config_as_json.as_dict_view_validator._validate_projected_dict"></a>

#### \_validate\_projected\_dict

```python
def _validate_projected_dict(member_name: str, projected: object,
                             stderr_file: TextIO) -> dict[Hashable, object]
```

Validate and return one projected dictionary view.

<a id="config_as_json.as_dict_view_validator._validate_dict_view_step"></a>

#### \_validate\_dict\_view\_step

```python
def _validate_dict_view_step(validator: MemberValidator, config: 'Config',
                             member_name: str, member_value: dict[Hashable,
                                                                  object],
                             stderr_file: TextIO) -> dict[Hashable, object]
```

Run one dict-view validator and require a dict result.

<a id="config_as_json.as_dict_view_validator._validation_chain"></a>

#### \_validation\_chain

```python
def _validation_chain(
        rules: Sequence[DictRule],
        validators: Sequence[MemberValidator]) -> list[MemberValidator]
```

Return the complete validation chain for one dictionary view.

<a id="config_as_json.as_dict_view_validator.AsDictViewValidator"></a>

## AsDictViewValidator Objects

```python
class AsDictViewValidator(MemberValidator)
```

Validate a member value through a dictionary-shaped view.

``AsDictViewValidator`` handles a member whose runtime value may be either
a real ``dict`` or one application-defined object type that can be
projected to a ``dict``. The same dictionary validators and dictionary
rules are applied to both representations, so application code can define
one validation policy for the dictionary-shaped data.

The class is a convenience adapter for the common case where dictionary
validation mainly consists of a list of ``DictRule`` objects. Conceptually
it branches on the member value type, uses ``to_dict`` only for the
non-dict representation, applies the optional whole-dict validators, and
finally applies a ``DictForEachValidator`` built from ``rules``.

The member value must be either an actual ``dict`` or an instance of
``non_dict_type``. Other mapping implementations are not accepted by this
validator. Keeping the contract limited to ``dict`` avoids ambiguity
about how replacement values from validators should be stored.

If the member value is a ``dict``, validators and rules are applied to the
dictionary value. Replacement values returned by validators and rules are
returned from ``validate_member`` and are therefore stored back into the
configuration member by ``MemberValidationStep``.

If the member value is an instance of ``non_dict_type``, ``to_dict`` is
called to produce a dictionary view, and validators and rules are applied
to that view. Replacement values returned while validating the projected
view are used only inside this validation chain. The original object is
returned from ``validate_member`` and remains the stored configuration
member. In-place mutation may still affect shared mutable objects if the
projector exposes them.

<a id="config_as_json.as_dict_view_validator.AsDictViewValidator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(non_dict_type: type[object],
             rules: Sequence[DictRule],
             to_dict: Callable[['Config', str, object, TextIO], dict[Hashable,
                                                                     object]],
             validators: Optional[Sequence[MemberValidator]] = None) -> None
```

Initialize the as-dict-view validator.

**Arguments**:

- `non_dict_type` - The accepted application-defined object type when
  the member value is not a ``dict``. This type may not be
  ``dict`` or a subclass of ``dict``.
- `rules` - Dictionary rules applied to the dictionary view after
  ``validators`` have run. This keeps the common
  ``DictForEachValidator`` use case concise.
- `to_dict` - Callable that receives the complete config object, the
  member name, the non-dict member value, and the diagnostic
  stream. It returns the dictionary view to validate.
  ``public_attrs_to_dict`` is a candidate when the view should
  be the object's public instance attributes.
- `validators` - Optional sequence of whole-dict validators to apply
  to the dictionary view before applying ``rules``. Each
  validator receives the value returned by the previous
  validator.


**Raises**:

- `TypeError` - If ``non_dict_type`` is not a type, is ``dict`` or a
  subclass of ``dict``, if ``to_dict`` is not callable, or if
  any validator is not a ``MemberValidator``.
- `ValueError` - If both ``rules`` is empty and ``validators`` is None
  or empty.

<a id="config_as_json.as_dict_view_validator.AsDictViewValidator._validate_dict_view"></a>

#### \_validate\_dict\_view

```python
def _validate_dict_view(config: 'Config', member_name: str,
                        dict_view: dict[Hashable, object],
                        stderr_file: TextIO) -> Optional[object]
```

Validate one dictionary view and return its normalized value.

<a id="config_as_json.as_dict_view_validator.AsDictViewValidator.validate_member"></a>

#### validate\_member

```python
def validate_member(config: 'Config',
                    member_name: str,
                    member_value: object,
                    stderr_file: TextIO = sys.stderr) -> Optional[object]
```

Validate one member through a dictionary-shaped view.

**Arguments**:

- `config` - The configuration object that owns ``member_name``.
- `member_name` - The name of the member to validate.
- `member_value` - The member value to validate.
- `stderr_file` - The file to write error messages to.


**Returns**:

  The normalized dictionary if ``member_value`` is a ``dict``.
  The original ``member_value`` if it is an instance of
  ``non_dict_type`` and its dictionary view validates.


**Raises**:

- `InvalidConfiguration` - If ``member_value`` is neither a ``dict``
  nor an instance of ``non_dict_type``, if projection fails, if
  the projector does not return a ``dict``, or if a validator
  rejects the dictionary view.
- `InvalidConfigurationValue` - If an inner validator rejects a value
  because it is not one of its allowed values.

<a id="config_as_json.json_write_hooks"></a>

# config\_as\_json.json\_write\_hooks

Implement the public write-side JSON conversion hook API.

A ``Config`` subclass overrides ``serialize_converters()`` to declare how
selected Python values should be converted into JSON-compatible data before
``json.dumps()`` is called. ``Config.as_json_string()`` invokes
:func:`apply_serialize_converters` once the data dictionary owned by the
current Config object has been assembled and all declared nested Config
objects have already serialized themselves.

The implementation is intentionally small: built-in fallback conversions
cover only ``Enum`` and ``IntEnum`` members (converted to their member
names). Everything else is the responsibility of explicit converters
declared by the application. The motivating problem case is ``IntEnum``,
which Python's JSON encoder treats as ``int`` and therefore never offers to
``default()``; the write-side hook runs before ``json.dumps()`` and
sidesteps that issue.

<a id="config_as_json.json_write_hooks.SerializeConverter"></a>

## SerializeConverter Objects

```python
class SerializeConverter(NamedTuple)
```

Describe one write-side conversion from Python data to JSON data.

A converter is selected by a ``SerializeSelector`` returned from
``serialize_converters()``. Explicit converters override built-in
conversions such as enum-name serialization.

``None`` values pass through unchanged. This lets validation and
omit-when-None handling decide whether ``None`` is allowed or omitted.

If ``value_type`` is not ``None``, every matched non-``None`` value must
be an instance of that type before ``func`` is called. If the value has
another type, serialization should raise a path-aware
``JsonWriteHookError``. This rule applies to both absolute path selectors
and recursive key-name selectors.

If ``value_type`` is ``None``, no pre-conversion type check is performed
and the conversion function is responsible for accepting the matched
value.

The conversion function is called with the matched value, the current
path text, the current ``stderr_file``, and the keyword arguments from
``args``. The intended call shape is
``func(value, path_text=path_text, stderr_file=stderr_file, **args)``.

``path_text`` is for diagnostics and should not be parsed as a selector.
It uses the same style as member names passed to member validators: list
indexes and dictionary keys are appended in square brackets, for example
``matrix[3]`` and ``csv_params[delimiter]``.

The conversion result must be recursively JSON-compatible. Valid output
is ``None``, ``int``, ``float``, ``str``, ``bool``, a list of valid
values, or a dictionary with string keys and valid values. Invalid output
raises a path-aware ``JsonWriteHookError`` before ``json.dumps()`` is
called. Explicit converter output is checked as-is. Built-in fallback
conversions are not applied to the converter return value, so returning
``{'mode': SomeEnum.FAST}`` is invalid. Return a JSON-compatible value
such as ``{'mode': 'FAST'}`` instead.

If ``func`` raises ``JsonWriteHookError``, it propagates unchanged.
Other exceptions from ``func`` are wrapped in ``JsonWriteHookError``
with selector and path context.

**Attributes**:

- `value_type` - Optional expected Python type before conversion.
- `func` - Callable that converts a Python value to JSON-compatible data.
- `args` - Keyword arguments passed to ``func``.

<a id="config_as_json.json_write_hooks.JsonWriteHookError"></a>

## JsonWriteHookError Objects

```python
class JsonWriteHookError(InvalidConfiguration)
```

Raised when write-side JSON conversion cannot produce valid JSON.

<a id="config_as_json.json_write_hooks.SerializeSelectorError"></a>

## SerializeSelectorError Objects

```python
class SerializeSelectorError(ValueError)
```

Raised when write-side conversion selectors are not valid together.

This exception reports programming errors in ``serialize_converters()``
declarations, such as invalid selector types, invalid ``ConfigPath``
syntax, or a recursive key selector that conflicts with a path selector
ending in or passing through the same dictionary key. It also reports
selectors that would cross child-owned nested ``Config`` ownership
boundaries.

Selector declarations are checked before conversion starts as far as
possible. Data-dependent traversal errors, such as a path selector that
reaches a list where it needs a dictionary, are detected while traversing
the actual data and also raise this exception.

<a id="config_as_json.json_write_hooks._is_path_selector"></a>

#### \_is\_path\_selector

```python
def _is_path_selector(selector: SerializeSelector) -> bool
```

Return whether ``selector`` is a path (tuple), not a recursive key.

<a id="config_as_json.json_write_hooks._selector_repr"></a>

#### \_selector\_repr

```python
def _selector_repr(selector: SerializeSelector) -> str
```

Return a human-friendly representation of one selector.

<a id="config_as_json.json_write_hooks._validate_one_selector"></a>

#### \_validate\_one\_selector

```python
def _validate_one_selector(selector: SerializeSelector) -> None
```

Validate the shape of one selector returned from the hook.

Recursive key selectors must be non-empty strings that do not start with
``'['``. Path selectors follow the same rules as ROCF paths: non-empty
tuple of strings, first element must be a dictionary key, intermediate
``'['`` markers are allowed, and any other element starting with ``'['``
is reserved.

<a id="config_as_json.json_write_hooks._split_selectors"></a>

#### \_split\_selectors

```python
def _split_selectors(
    converters: SerializeConverters
) -> tuple[_RecKeyConverters, _PathConverters]
```

Validate selectors and split them into rec-key and path mappings.

<a id="config_as_json.json_write_hooks._check_rec_vs_path_conflicts"></a>

#### \_check\_rec\_vs\_path\_conflicts

```python
def _check_rec_vs_path_conflicts(rec_key: _RecKeyConverters,
                                 paths: _PathConverters) -> None
```

Reject recursive-key vs path selector conflicts.

A path selector may neither end with a key that is also a recursive-key
selector, nor pass through such a key in an intermediate step.

<a id="config_as_json.json_write_hooks._path_matches_or_extends"></a>

#### \_path\_matches\_or\_extends

```python
def _path_matches_or_extends(p: _SelectorPath,
                             reference: _SelectorPath) -> bool
```

Return whether ``p`` is equal to or a descendant of ``reference``.

In ``reference``, the literal ``'['`` step matches either ``'['`` in
``p`` (list iteration) or any non-``'['`` dictionary key in ``p`` (a
dictionary value). This extended meaning is only used when matching a
traversal selector path against a child-owned-path boundary. Plain
path-selector matching uses identical tuple equality.

<a id="config_as_json.json_write_hooks._check_child_boundaries"></a>

#### \_check\_child\_boundaries

```python
def _check_child_boundaries(paths: _PathConverters,
                            child_owned: Sequence[ConfigPath]) -> None
```

Reject path selectors that cross child-owned subtree boundaries.

<a id="config_as_json.json_write_hooks._append_path_text"></a>

#### \_append\_path\_text

```python
def _append_path_text(prefix: str, step: str | int) -> str
```

Append one dict-key or list-index step to a path-text string.

Returns the top-level name unchanged when ``prefix`` is empty and the
step is a string. For all other cases the step is wrapped in square
brackets, matching the member-name convention used by the member
validators.

<a id="config_as_json.json_write_hooks._check_json_compatible"></a>

#### \_check\_json\_compatible

```python
def _check_json_compatible(value: object, path_text: str) -> None
```

Recursively verify that a value is JSON-compatible.

Accepted leaf types are ``None``, ``bool``, ``int``, ``float`` and
``str``. Containers must be a ``list`` of compatible values or a
``dict`` with string keys mapping to compatible values. A
``JsonWriteHookError`` is raised on the first violation.

``bool`` is intentionally accepted as a leaf even though it is a
subclass of ``int``; ``json.dumps`` writes booleans as ``true``/
``false`` and we treat them as JSON-native.

<a id="config_as_json.json_write_hooks._apply_one_converter"></a>

#### \_apply\_one\_converter

```python
def _apply_one_converter(value: object, converter: SerializeConverter,
                         path_text: str, selector: SerializeSelector,
                         stderr_file: TextIO) -> JsonType
```

Apply one converter to ``value`` and wrap unexpected errors.

``None`` always passes through unchanged. The optional ``value_type``
pre-check raises ``JsonWriteHookError`` instead of trusting the user
converter to be defensive.

<a id="config_as_json.json_write_hooks._builtin_fallback"></a>

#### \_builtin\_fallback

```python
def _builtin_fallback(value: object) -> object
```

Apply the built-in fallback conversion to one value.

Only Enum/IntEnum members are converted, to their symbolic ``name``.
Other values are returned unchanged.

<a id="config_as_json.json_write_hooks._is_inside_child_owned"></a>

#### \_is\_inside\_child\_owned

```python
def _is_inside_child_owned(selector_path: _SelectorPath,
                           child_owned: Sequence[ConfigPath]) -> bool
```

Return whether ``selector_path`` is at or below a child-owned path.

<a id="config_as_json.json_write_hooks._has_path_inside"></a>

#### \_has\_path\_inside

```python
def _has_path_inside(selector_path: _SelectorPath,
                     paths: _PathConverters) -> tuple[bool, bool]
```

Return whether any path selector targets inside ``selector_path``.

The two booleans say whether such a path expects a dict next or a list
next at ``selector_path``. They are used to raise
``SerializeSelectorError`` when the actual data has the wrong container
type at this point.

<a id="config_as_json.json_write_hooks._WalkContext"></a>

## \_WalkContext Objects

```python
class _WalkContext(NamedTuple)
```

Bundle the read-only walk parameters threaded through traversal.

<a id="config_as_json.json_write_hooks._convert_dict"></a>

#### \_convert\_dict

```python
def _convert_dict(value: dict[str, object], selector_path: _SelectorPath,
                  path_text: str, ctx: _WalkContext) -> dict[str, JsonType]
```

Convert one parent-owned dictionary value.

<a id="config_as_json.json_write_hooks._convert_list"></a>

#### \_convert\_list

```python
def _convert_list(value: list[object], selector_path: _SelectorPath,
                  path_text: str, ctx: _WalkContext) -> list[JsonType]
```

Convert one parent-owned list value.

<a id="config_as_json.json_write_hooks._passthrough_child"></a>

#### \_passthrough\_child

```python
def _passthrough_child(value: object) -> JsonType
```

Return a child-owned value as-is after a JSON-compatibility check.

Child-owned subtrees have already been produced by the child object's
own ``as_json_string()``, so they must already be JSON-compatible. The
check protects us against programming mistakes and produces a clear
error rather than a cryptic ``json.dumps`` failure.

<a id="config_as_json.json_write_hooks._convert_value"></a>

#### \_convert\_value

```python
def _convert_value(value: object, selector_path: _SelectorPath, path_text: str,
                   ctx: _WalkContext) -> JsonType
```

Convert one value, recursing into containers as needed.

<a id="config_as_json.json_write_hooks.apply_serialize_converters"></a>

#### apply\_serialize\_converters

```python
def apply_serialize_converters(
    data: dict[str, object],
    converters: SerializeConverters,
    stderr_file: TextIO,
    child_owned_paths: Sequence[ConfigPath] = ()
) -> dict[str, JsonType]
```

Return JSON-compatible data after write-side conversions.

``Config.as_json_string()`` should call this function after validation
and after nested ``Config`` members have been converted to their own
JSON data, but before calling ``json.dumps()``. The function owns
selector checking, converter dispatch, built-in fallback conversions
such as enum-name serialization, and recursive JSON-compatibility
checks.

The function returns a new converted tree. The passed-in tree is never
mutated.

The initial built-in fallback conversions are ``Enum`` and ``IntEnum``
members to their member names. Everything else outside explicit
converters must already be JSON-compatible.

A path selector that reaches a missing dictionary key is a no-op. A
path selector that reaches the wrong container type raises
``SerializeSelectorError``. For example, expecting a dictionary key
where the actual data has a list is an error, while an absent key in an
existing dictionary is not.

A recursive key-name selector walks parent-owned dictionaries and
lists. It skips child-owned subtrees automatically because the walk
never descends into them.

``child_owned_paths`` describes nested ``Config`` subtrees that are
present in ``data`` only because the child object already serialized
itself. The function passes those subtrees through unchanged. In a
child-owned path the literal ``'['`` step matches either a list
element or a dictionary value at that point, which lets a parent
describe ``LIST_ELEMENT`` and ``DICT_VALUE`` nested-config kinds with
the same notation.

Dictionary keys that start with ``'['`` are rejected. ``'['`` is
reserved by ``ConfigPath`` for list iteration and is not allowed as a
literal data key.

**Arguments**:

- `data` - Root data dictionary owned by the current ``Config`` object.
- `converters` - Explicit converters returned by
  ``Config.serialize_converters()``.
- `stderr_file` - Stream passed through to converter functions.
- `child_owned_paths` - Paths to nested ``Config`` subtrees owned by
  child objects. Selectors that would convert those subtrees,
  their descendants, or an ancestor container containing them
  are invalid.


**Returns**:

  A JSON-compatible dictionary ready to pass to ``json.dumps()``.


**Raises**:

- `SerializeSelectorError` - The selector declarations are invalid or
  ambiguous, or a selector crosses a child-owned path boundary.
- `JsonWriteHookError` - A matched value has the wrong type, a
  converter raises an error that should be wrapped with path
  context, or a conversion result is not JSON-compatible.

<a id="config_as_json.config_nesting"></a>

# config\_as\_json.config\_nesting

Describe nested Config declarations.

<a id="config_as_json.config_nesting.ConfigNestingKind"></a>

## ConfigNestingKind Objects

```python
class ConfigNestingKind(Enum)
```

Describe where a nested Config object is stored.

``MEMBER`` describes a mandatory public member containing one nested
Config object. ``OPTIONAL_MEMBER`` describes a public member that may be
``None`` or one nested Config object. ``LIST_ELEMENT`` describes a public
member that stores a list where every element is a nested Config object.
``DICT_VALUE`` describes a public member that stores a dict where every
value is a nested Config object and every key must be a string.
``DICT_VALUE_BY_KEY`` describes one configured key inside a public dict
member. The value stored at ``discriminator_key`` is a nested Config
object. Other keys in the same public dict keep their ordinary JSON
values unless they are declared by another ``DICT_VALUE_BY_KEY`` entry.

<a id="config_as_json.config_nesting.ConfigFactory"></a>

## ConfigFactory Objects

```python
class ConfigFactory(Protocol)
```

Construct one nested Config object from JSON input.

<a id="config_as_json.config_nesting.ConfigFactory.__call__"></a>

#### \_\_call\_\_

```python
def __call__(*,
             from_json_data_text: Optional[str] = None,
             from_json_filename: Optional[PathOrStr] = None,
             stderr_file: TextIO = sys.stderr) -> 'Config'
```

Construct one nested Config object.

**Arguments**:

- `from_json_data_text` - Optional JSON text to parse directly.
- `from_json_filename` - Optional path to a JSON file to read.
- `stderr_file` - Stream used for user-facing diagnostics.


**Returns**:

  The constructed nested Config object.

<a id="config_as_json.config_nesting.ConfigNesting"></a>

## ConfigNesting Objects

```python
class ConfigNesting(NamedTuple)
```

Describe one nested Config declaration.

The nested class must derive from :class:`Config` and must be
constructible with keyword arguments ``from_json_data_text``,
``from_json_filename``, and ``stderr_file``. This is the constructor
shape used by the base class when it reads a nested JSON object. If
``factory_function`` is set, that callable is used instead of the
``config_type`` constructor. The factory must accept the same keyword
arguments and must return an instance of ``config_type`` or a subclass.

**Attributes**:

- `kind` - Where the nested configuration object is stored.
- `config_type` - Config-derived type expected for this member.
- `discriminator_key` - Dict key used by ``DICT_VALUE_BY_KEY``.
- `factory_function` - Optional callable used to construct JSON objects.

