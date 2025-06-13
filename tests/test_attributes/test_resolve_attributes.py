# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest

from spx_sdk.attributes.resolve_attribute import resolve_attribute_reference_hierarchical

from spx_sdk.registry import register_class
from spx_sdk.components import SpxComponent
from spx_sdk.attributes.resolve_attribute import (
    is_attribute_reference,
    find_attribute,
    resolve_attribute_reference,
    get_attribute_value,
    set_attribute_value,
    resolve_reference,
    substitute_attribute_references_hierarchical,
)
from spx_sdk.attributes import SpxAttributes
from spx_sdk.attributes.attribute import InternalAttributeWrapper, ExternalAttributeWrapper


class DummyAttributeNode(dict):
    """A very minimal dict-like node for Attribute construction."""
    pass


@register_class()
class DummyComponentA(SpxComponent):
    """A simple component to act as parent for SpxAttributes in tests."""
    pass


@register_class()
class DummyComponentB(SpxComponent):
    """A simple component to act as parent for SpxAttributes in tests."""
    pass


class TestResolveAttributeFunctions(unittest.TestCase):
    def setUp(self):
        self.system = DummyComponentA(name="system", parent=None)
        self.parent = DummyComponentB(name="root", parent=self.system)
        # Build an Attributes container with two attributes
        # – 'a' (default float 0.0) and 'b' (override initial to 5)
        nodes = {
            "a": {},
            "b": {"default": 5, "type": "int"},
        }
        self.attrs = SpxAttributes(name="attributes", definition=nodes, parent=self.parent)
        # grab the underlying Attribute objects
        self.attr_a = self.attrs.get("a")
        self.attr_b = self.attrs.get("b")

    def test_is_attribute_reference(self):
        cases = [
            ("$attr(x)", (True, "x", "internal")),
            ("$internal(y)", (True, "y", "internal")),
            ("$external(z)", (True, "z", "external")),
            ("foo.bar", (True, "foo.bar", "internal")),
            ("not_a_ref", (False, "not_a_ref", None)),
            ("$wrong", (False, "$wrong", None)),
        ]
        for ref, expected in cases:
            with self.subTest(ref=ref):
                self.assertEqual(is_attribute_reference(ref), expected)

    def test_find_attribute_simple(self):
        # direct name
        found = find_attribute(self.parent, "a")
        self.assertIs(found, self.attr_a)
        # dotted name – we ignore instance‐prefix, drop it
        found2 = find_attribute(self.system, "root.b")
        self.assertIs(found2, self.attr_b)

    def test_resolve_attribute_reference(self):
        # existing key without prefix returns None
        wrapper = resolve_attribute_reference(self.parent, "b")
        self.assertIsNone(wrapper)

        # via #attr() syntax → internal wrapper
        wrapper2 = resolve_attribute_reference(self.parent, "$attr(a)")
        self.assertIsInstance(wrapper2, InternalAttributeWrapper)
        self.assertIs(wrapper2._attribute, self.attr_a)

        # external marker → external wrapper
        wrapper3 = resolve_attribute_reference(self.parent, "$external(a)")
        self.assertIsInstance(wrapper3, ExternalAttributeWrapper)
        self.assertIs(wrapper3._attribute, self.attr_a)

        # non-attribute returns None
        wrapper4 = resolve_attribute_reference(self.parent, "nothing")
        self.assertIsNone(wrapper4)

    def test_get_and_set_attribute_value(self):
        # initial internal values:
        self.assertEqual(get_attribute_value(self.attr_a, "internal"), 0.0)
        self.assertEqual(get_attribute_value(self.attr_b, "internal"), 5)
        # set internal
        set_attribute_value(self.attr_a, "internal", 3.14)
        self.assertEqual(self.attr_a.internal_value, 3.14)
        # external_value getter falls back to internal if no external set
        self.assertEqual(get_attribute_value(self.attr_a, "external"), 3.14)
        # set external (type casting to attribute type)
        set_attribute_value(self.attr_b, "external", "7")
        # external_value should now reflect the cast (int("7") -> 7)
        self.assertEqual(self.attr_b.external_value, 7)
        self.assertEqual(get_attribute_value(self.attr_b, "external"), 7)

    def test_resolve_reference(self):
        # numeric literal isn't an attr → returned verbatim
        self.assertEqual(resolve_reference(self.attrs, "hello"), "hello")
        # attribute internal
        set_attribute_value(self.attr_a, "internal", 9.9)
        self.assertEqual(resolve_reference(self.parent, "$attr(a)"), 9.9)
        # attribute external
        set_attribute_value(self.attr_a, "external", 42)
        self.assertEqual(resolve_reference(self.parent, "$external(a)"), 42)

    def test_resolve_attribute_reference_hierarchical_found(self):
        # Create a deeper nested component under self.parent
        nested = DummyComponentB(name="nested", parent=self.parent)
        # Resolve via hierarchical search: attribute 'a' lives in self.attrs
        wrapper = resolve_attribute_reference_hierarchical(nested, "$attr(a)")
        self.assertIsNotNone(wrapper)
        # Should be the same internal wrapper for attr_a
        self.assertEqual(wrapper._attribute, self.attr_a)
        self.assertTrue(isinstance(wrapper, InternalAttributeWrapper))

    def test_find_attribute_deep_nested(self):
        """Nested find_attribute should locate attributes in deeper child containers."""
        # Create a deeper nested component under self.parent
        nested2 = DummyComponentB(name="nested2", parent=self.parent)
        # Add its own attributes container with 'c'
        attrs2 = SpxAttributes(name="attributes", definition={"c": {}}, parent=nested2)
        attr_c = attrs2.get("c")
        # Resolve via dotted path from the top-level system
        found = find_attribute(self.system, "root.nested2.c")
        self.assertIs(found, attr_c)

    def test_resolve_attribute_reference_with_dots(self):
        """resolve_attribute_reference should handle dotted attribute names."""
        # For attr_b under 'root', test from system level with #attr(root.b)
        wrapper = resolve_attribute_reference(self.system, "$attr(root.b)")
        self.assertIsInstance(wrapper, InternalAttributeWrapper)
        self.assertIs(wrapper._attribute, self.attr_b)

    def test_resolve_reference_literal_and_dotted(self):
        """resolve_reference should return literal or dotted attribute value."""
        # Set an internal value on b
        set_attribute_value(self.attr_b, "internal", 123)
        # Numeric or non-ref strings return verbatim
        self.assertEqual(resolve_reference(self.parent, "foo.bar"), "foo.bar")
        # Dotted #attr ref should resolve internal b
        self.assertEqual(resolve_reference(self.system, "$attr(root.b)"), 123)

    def test_substitute_attribute_references_hierarchical_basic(self):
        """All attribute references in a string should be replaced with their values."""
        # Set internal and external values
        set_attribute_value(self.attr_a, "internal", 3.5)
        set_attribute_value(self.attr_b, "external", 7)
        text = "A is $attr(a), B is $external(b)."
        result = substitute_attribute_references_hierarchical(self.parent, text)
        self.assertIn("3.5", result)
        self.assertIn("7", result)
        # No leftover reference tokens
        self.assertNotIn("$attr(a)", result)
        self.assertNotIn("$external(b)", result)

    def test_substitute_attribute_references_hierarchical_unknown(self):
        """Unknown references or malformed refs remain unchanged."""
        set_attribute_value(self.attr_a, "internal", 2)
        text = "Known: $attr(a), Unknown: $attr(z)."
        result = substitute_attribute_references_hierarchical(self.parent, text)
        # Known replaced
        self.assertIn("2", result)
        # Unknown remains as literal token
        self.assertIn("$attr(z)", result)


if __name__ == "__main__":
    unittest.main()
