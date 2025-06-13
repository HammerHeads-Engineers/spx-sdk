# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest

from spx_sdk.registry import clear_registry, register_class
from spx_sdk.components import SpxComponent
from spx_sdk.attributes import SpxAttributes, SpxAttribute


@register_class()
class DummyComponent(SpxComponent):
    """A simple component to act as parent for SpxAttributes in tests."""
    pass


class TestSpxAttributes(unittest.TestCase):
    def setUp(self):
        # wipe any previous registrations/instances
        clear_registry()
        # register SpxAttribute and SpxAttributes so SpxContainer can see them
        register_class()(SpxAttribute)
        register_class()(SpxAttributes)
        # make a dummy parent component
        self.parent = DummyComponent(name="root", parent=None)

        # our sample definition: two attributes, one with explicit initial value
        self.definition = {
            "power": {"name": "power", "type": "int", "default": 5},
            "temp":  {}  # uses default DataType=float, InitialValue=0.0
        }
        # instantiate
        self.attrs = SpxAttributes(
            name="attributes",
            definition=self.definition,
            parent=self.parent
        )

    def test_children_are_attributes(self):
        # Should have exactly two children, both SpxAttribute instances
        self.assertEqual(len(self.attrs.children), 2)
        for child in self.attrs.children.values():
            self.assertIsInstance(child, SpxAttribute)
            # parent of each child is our SpxAttributes container
            self.assertIs(child.parent, self.attrs)

    def test_names_and_definition(self):
        # attribute names should match dict keys
        names = set(self.attrs.children.keys())
        self.assertEqual(names, {"power", "temp"})
        # each child's .definition matches the original dict given
        defs = {name: attr.definition for name, attr in self.attrs.children.items()}
        self.assertEqual(defs["power"]["name"], "power")

    def test_internal_default_and_initial(self):
        # access via __getitem__ uses internal view
        # 'power' was int with InitialValue=5
        self.assertEqual(self.attrs.internal["power"], 5)
        # 'temp' had no InitialValue so uses default float 0.0
        self.assertEqual(self.attrs.internal["temp"], 0.0)

    def test_set_internal_updates_underlying(self):
        # set new internal value
        self.attrs.internal["temp"] = 3.14
        self.assertEqual(self.attrs.internal["temp"], 3.14)
        # underlying attribute internal_value property
        attr_temp = self.attrs.get("temp")
        self.assertEqual(attr_temp.internal_value, 3.14)

    def test_external_view_and_reset(self):
        # Set external value directly
        self.attrs.external["power"] = 12
        self.assertEqual(self.attrs.external["power"], 12)
        # Underlying attribute external_value is updated
        attr_power: SpxAttribute = self.attrs.get("power")
        self.assertEqual(attr_power.external_value, 12)
        # Changing internal should not reset external value
        self.attrs.internal["power"] = 7
        self.assertEqual(self.attrs.internal["power"], 7)
        self.assertEqual(self.attrs.external["power"], 7)

    def test_len_and_get_attribute(self):
        self.assertEqual(len(self.attrs), 2)
        a = self.attrs.get("power")
        self.assertIsInstance(a, SpxAttribute)
        with self.assertRaises(KeyError):
            _ = self.attrs["missing"]

    def test_unknown_internal_key_raises(self):
        with self.assertRaises(KeyError):
            _ = self.attrs.internal["no_such"]

    def test_unknown_external_key_raises(self):
        with self.assertRaises(KeyError):
            self.attrs.external["no_such"] = 1

    def test_registry_integration(self):
        # ensure both classes got registered
        from spx_sdk.registry import class_registry
        self.assertIn("SpxAttribute", class_registry)
        self.assertIn("SpxAttributes", class_registry)

    def test_attached_to_parent(self):
        # SpxAttributes container itself should be child of the parent component
        self.assertIn("attributes", self.parent)
        self.assertIs(self.parent.children["attributes"], self.attrs)
        self.assertIs(self.attrs.parent, self.parent)

    def test_contains_and_len(self):
        # __contains__ and __len__ support
        self.assertIn("power", self.attrs)
        self.assertNotIn("missing", self.attrs)
        self.assertEqual(len(self.attrs), 2)


if __name__ == "__main__":
    unittest.main()
