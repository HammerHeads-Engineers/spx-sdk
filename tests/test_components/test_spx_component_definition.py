# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
import logging
from dataclasses import dataclass
from spx_sdk.components.component import SpxComponent


class DummyParent(SpxComponent):
    """A no-op subclass just to have a distinct class name in registry/tests."""
    pass


class TestSpxComponent(unittest.TestCase):
    def setUp(self):
        # configure logging for debugging during tests
        logging.basicConfig(level=logging.DEBUG)
        # always start each test with a fresh parent
        self.parent = DummyParent(name="root")

    def test_definition_set_explicitly(self):
        item = SpxComponent("item1", parent=self.parent, definition="foo")
        self.assertEqual(item.name, "item1")
        self.assertEqual(item.definition, "foo")
        self.assertIs(item.parent, self.parent)
        self.assertIn(item, self.parent.get_children_list())

    def test_default_definition_empty(self):
        item = SpxComponent("item2", parent=self.parent)
        self.assertEqual(item.name, "item2")
        self.assertEqual(item.definition, None)

    def test_attached_to_parent(self):
        item = SpxComponent("item3", parent=self.parent, definition=123)
        self.assertIs(item.parent, self.parent)
        self.assertIn(item, self.parent.get_children_list())

    def test_children_property_initially_empty(self):
        item = SpxComponent("leaf", parent=self.parent)
        self.assertEqual(item.get_children_list(), [])

    def test_parent_and_root(self):
        root = DummyParent(name="root2")
        child = SpxComponent("child", parent=root)
        subchild = SpxComponent("sub", parent=child)
        self.assertIs(child.get_parent(), root)
        self.assertIs(subchild.get_root(), root)
        # root.get_root() returns itself
        self.assertIs(root.get_root(), root)

    def test_repr_includes_class_name_and_name(self):
        item = SpxComponent("dataItem", parent=self.parent, definition="data")
        r = repr(item)
        # expect something like "<SpxComponent(name=dataItem)>" or including children count
        self.assertTrue(item.__class__.__name__ in r)
        self.assertIn(f"name='{item.name}'", r)

    def test_prepare_and_stop_propagation(self):
        # test that prepare() and stop() calls propagate to children
        class Recorder(SpxComponent):
            def __init__(self, name, parent=None, definition=None):
                super().__init__(name, parent=parent, definition=definition)
                self.prepared = False
                self.stopped = False

            def prepare(self):
                self.prepared = True

            def stop(self):
                self.stopped = True

        root = DummyParent(name="root3")
        rec = Recorder("rec", parent=root)
        # before calling, flags are False
        self.assertFalse(rec.prepared)
        self.assertFalse(rec.stopped)
        # calling on root should propagate
        root.prepare()
        self.assertTrue(rec.prepared)
        root.stop()
        self.assertTrue(rec.stopped)

    def test_remove_child_and_destroy(self):
        item = SpxComponent("x", parent=self.parent)
        child = SpxComponent("c2", parent=item)
        self.assertIn(child, item.get_children_list())
        # remove child
        item.remove_child(child)
        self.assertNotIn(child, item.children)
        self.assertIsNone(child.parent)
        # test destroy cleans up
        item.destroy()
        self.assertEqual(item.get_children_list(), [])
        self.assertIsNone(item.parent)

    def test_subclass_naming_and_definition(self):
        class MyItem(SpxComponent):
            a = None

        my = MyItem("myNode", parent=self.parent, definition={"a": 1})
        # name is provided explicitly
        self.assertEqual(my.name, "myNode")
        self.assertEqual(my.definition, {"a": 1})
        self.assertIs(my.parent, self.parent)

    def test_plain_subclass_field_population(self):
        # subclass with plain class attributes should get populated from definition
        class PlainItem(SpxComponent):
            a: int = None
            b: str = None
            c = None

        plain = PlainItem("plain", parent=self.parent, definition={"a": 10, "b": "hello"})
        self.assertEqual(plain.a, 10)
        self.assertEqual(plain.b, "hello")
        self.assertEqual(plain.c, None)
        # unspecified fields remain default None
        self.assertIsNone(getattr(plain, "d", None))

    def test_dataclass_subclass_field_population(self):
        # dataclass subclass with fields should get populated from definition
        @dataclass(init=False)
        class DataItem(SpxComponent):
            a: int = 0
            b: str = ""

        data = DataItem("data", parent=self.parent, definition={"a": 5, "b": "world"})
        self.assertEqual(data.a, 5)
        self.assertEqual(data.b, "world")
        # defaults when missing
        data2 = DataItem("data2", parent=self.parent, definition={})
        self.assertEqual(data2.a, 0)
        self.assertEqual(data2.b, "")

    def test_custom_populate_override(self):
        # A subclass overriding _populate to transform definition values
        class SpecialItem(SpxComponent):
            def _populate(self, definition):
                # e.g. store each key uppercased, doubling integers
                for k, v in definition.items():
                    processed = v * 2 if isinstance(v, int) else v
                    setattr(self, k.upper(), processed)

        # Ensure that custom populate runs
        spec = SpecialItem("special", parent=self.parent, definition={"a": 3, "b": "ok"})
        # The override should have set attributes A and B according to our logic
        self.assertEqual(getattr(spec, 'A', None), 6)
        self.assertEqual(getattr(spec, 'B', None), 'ok')


if __name__ == '__main__':
    unittest.main()
