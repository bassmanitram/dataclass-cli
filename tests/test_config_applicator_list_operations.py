"""Tests for list index and append operations in ConfigApplicator."""

import pytest

from dataclass_args.config_applicator import ConfigApplicator


class TestListIndexOperations:
    """Test list indexing in set_nested_property."""

    def test_set_list_element_by_index(self):
        target = {"items": ["a", "b", "c"]}
        ConfigApplicator.set_nested_property(target, "items.0", "new_value")
        assert target == {"items": ["new_value", "b", "c"]}

    def test_set_list_element_by_index_negative_index_raises_error(self):
        # Negative indices treated as non-numeric (no negative indexing support)
        target = {"items": ["a", "b", "c"]}
        with pytest.raises(ValueError, match="non-numeric key"):
            ConfigApplicator.set_nested_property(target, "items.-1", "neg_value")

    def test_set_list_element_index_out_of_range(self):
        target = {"items": ["a", "b"]}
        with pytest.raises(ValueError, match="List index out of range"):
            ConfigApplicator.set_nested_property(target, "items.5", "value")

    def test_nested_list_indexing(self):
        target = {"data": [{"name": "old"}, {"name": "older"}]}
        ConfigApplicator.set_nested_property(target, "data.1.name", "new_name")
        assert target == {"data": [{"name": "old"}, {"name": "new_name"}]}

    def test_list_indicates_dict_behavior_unchanged(self):
        # When target is a dict, numeric keys should create string keys, not list indices
        target = {"items": {}}
        ConfigApplicator.set_nested_property(target, "items.0", "value")
        assert target == {"items": {"0": "value"}}

    def test_non_digit_in_list_context_raises_error(self):
        target = {"items": ["a", "b"]}
        with pytest.raises(ValueError, match="non-numeric key"):
            ConfigApplicator.set_nested_property(target, "items.key", "value")

    def test_non_numeric_key_in_list_context_raises_error(self):
        target = {"items": [{"name": "value"}]}
        with pytest.raises(
            ValueError, match="Cannot set list element with non-numeric key"
        ):
            ConfigApplicator.set_nested_property(target, "items.name", "new_value")


class TestListAppendOperations:
    """Test list append operations in set_nested_property."""

    def test_append_to_list(self):
        target = {"items": ["a", "b"]}
        ConfigApplicator.set_nested_property(target, "items.+", "c")
        assert target == {"items": ["a", "b", "c"]}

    def test_append_to_list_with_object(self):
        target = {"items": [{"name": "first"}]}
        ConfigApplicator.set_nested_property(target, "items.+", '{"name": "second"}')
        assert target == {"items": [{"name": "first"}, {"name": "second"}]}

    def test_append_to_empty_list(self):
        target = {"items": []}
        ConfigApplicator.set_nested_property(target, "items.+", "first")
        assert target == {"items": ["first"]}

    def test_plus_on_dict_is_string_key(self):
        # + on a dict is a valid string key, not an error
        target = {"items": {"key": "value"}}
        ConfigApplicator.set_nested_property(target, "items.+", "new")
        assert target == {"items": {"key": "value", "+": "new"}}

    def test_plus_in_intermediate_path_raises_error(self):
        # + is not a valid list index for navigation
        target = {"items": [{"nested": "value"}]}
        with pytest.raises(ValueError, match="non-numeric key"):
            ConfigApplicator.set_nested_property(target, "items.+.nested", "new_value")


class TestMixedDictListOperations:
    """Test mixed dict and list navigation."""

    def test_navigate_dict_to_list(self):
        target = {"outer": {"inner": ["a", "b", "c"]}}
        ConfigApplicator.set_nested_property(target, "outer.inner.1", "b_new")
        assert target == {"outer": {"inner": ["a", "b_new", "c"]}}

    def test_create_dict_then_navigate_to_list(self):
        target = {}
        ConfigApplicator.set_nested_property(target, "parent.child", "[1, 2, 3]")
        assert target == {"parent": {"child": [1, 2, 3]}}

    def test_list_in_dict_with_numeric_keys(self):
        # Verify that dicts still work with numeric-looking keys
        target = {"mixed": {"0": "zero", "1": "one"}}
        ConfigApplicator.set_nested_property(target, "mixed.2", "two")
        assert target == {"mixed": {"0": "zero", "1": "one", "2": "two"}}


class TestBackwardCompatibility:
    """Ensure all existing behavior remains unchanged."""

    def test_original_dict_behavior_unchanged(self):
        target = {}
        ConfigApplicator.set_nested_property(target, "key", "value")
        assert target == {"key": "value"}

    def test_original_nested_dict_behavior_unchanged(self):
        target = {}
        ConfigApplicator.set_nested_property(target, "outer.inner", "value")
        assert target == {"outer": {"inner": "value"}}

    def test_original_creates_intermediate_dicts(self):
        target = {}
        ConfigApplicator.set_nested_property(target, "a.b.c", "value")
        assert target == {"a": {"b": {"c": "value"}}}

    def test_original_non_dict_parent_raises_error(self):
        target = {"key": "string_value"}
        with pytest.raises(ValueError, match="not a dictionary"):
            ConfigApplicator.set_nested_property(target, "key.nested", "value")


class TestApplyPropertyOverridesListSupport:
    """Test list operations through apply_property_overrides."""

    def test_override_list_element(self):
        target = {"items": ["old", "other"]}
        ConfigApplicator.apply_property_overrides(target, ["items.0:new"])
        assert target == {"items": ["new", "other"]}

    def test_override_list_append(self):
        target = {"items": ["a"]}
        ConfigApplicator.apply_property_overrides(target, ["items.+:b"])
        assert target == {"items": ["a", "b"]}

    def test_override_nested_in_list_element(self):
        target = {"data": [{"name": "old"}]}
        ConfigApplicator.apply_property_overrides(target, ["data.0.name:new_name"])
        assert target == {"data": [{"name": "new_name"}]}

    def test_override_dict_with_numeric_key_unchanged(self):
        target = {}
        ConfigApplicator.apply_property_overrides(target, ["items.0:value"])
        assert target == {"items": {"0": "value"}}

    def test_multiple_list_operations(self):
        target = {"items": ["a", "b"], "other": [{"val": 1}]}
        ConfigApplicator.apply_property_overrides(
            target, ["items.0:A", "items.+:c", "other.0.val:2"]
        )
        assert target == {"items": ["A", "b", "c"], "other": [{"val": 2}]}
