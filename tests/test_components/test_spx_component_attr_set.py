# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
from spx_sdk.components.component import SpxComponent


class CustomLeaf(SpxComponent):
    """
    A simple leaf component that has no children initially but has a predefined attribute.
    """
    def __init__(self, name, parent=None, definition=None):
        super().__init__(name=name, parent=parent, definition=definition)
        # Set a default attribute
        self.some_attr = 123
        self.extra = None  # Another attribute to test setting/getting


class CustomParent(SpxComponent):
    """
    A component that will hold children to test normal dict-like behavior.
    """
    def __init__(self, name, parent=None, definition=None):
        super().__init__(name=name, parent=parent, definition=definition)


class TestSpxComponentDictAccess(unittest.TestCase):
    def test_get_set_item_with_children(self):
        parent = CustomParent(name="parent")
        # Create a child component
        child = CustomLeaf(name="child", parent=parent, definition={})
        # Ensure child exists and can be retrieved via __getitem__
        retrieved = parent["child"]
        self.assertIs(retrieved, child)

        # Create another child to set via __setitem__
        new_child = CustomLeaf(name="new_child")
        parent["new_child"] = new_child
        self.assertIn("new_child", parent.children)
        self.assertIs(parent.get("new_child"), new_child)
        # Confirm that the child's parent reference is correct
        self.assertIs(new_child.parent, parent)

        # Attempt to set a non-SpxComponent under a component with children should raise ValueError
        with self.assertRaises(ValueError):
            parent["invalid"] = 42  # not an SpxComponent

    def test_get_set_item_on_leaf(self):
        leaf = CustomLeaf(name="leaf")
        # Leaf has no children, so __getitem__ should treat key as attribute
        # Retrieving existing attribute 'some_attr'
        self.assertEqual(leaf["some_attr"], 123)

        # Overwriting existing attribute
        leaf["some_attr"] = 999
        self.assertEqual(leaf.some_attr, 999)
        self.assertEqual(leaf["some_attr"], 999)

        # Attempt to get a nonexistent attribute on leaf should raise KeyError
        with self.assertRaises(KeyError):
            _ = leaf["does_not_exist"]

    def test_nested_hierarchy_get_set(self):
        # Test a deeper hierarchy: parent -> child -> leaf
        root = CustomParent(name="root")
        mid = CustomParent(name="mid", parent=root, definition={})
        leaf = CustomLeaf(name="leaf", parent=mid, definition={})

        # root has children, so retrieving mid by key
        self.assertIs(root["mid"], mid)
        # mid has children, retrieving leaf by key
        self.assertIs(mid["leaf"], leaf)
        # At leaf (no children), retrieving attribute
        self.assertEqual(leaf["some_attr"], 123)

        # Setting attribute on leaf
        leaf["extra"] = 7
        self.assertEqual(leaf.extra, 7)
        self.assertEqual(leaf["extra"], 7)

        # Setting child under root
        new_mid = CustomParent(name="new_mid")
        root["new_mid"] = new_mid
        self.assertIs(root["new_mid"], new_mid)
        self.assertIs(new_mid.parent, root)

    def test_contains_and_len_behavior(self):
        parent = CustomParent(name="p1")
        # No children yet, so __contains__ and __len__ refer to children dict
        self.assertFalse("anything" in parent)
        self.assertEqual(len(parent), 0)

        # Add a child
        child = CustomLeaf(name="c1", parent=parent, definition={})
        self.assertTrue("c1" in parent)
        self.assertEqual(len(parent), 1)

        # Leaf's len is always zero, contains only checks for children
        self.assertFalse("some_attr" in child)
        self.assertEqual(len(child), 0)


if __name__ == "__main__":
    unittest.main()
