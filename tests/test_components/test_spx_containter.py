# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
import logging

from copy import deepcopy
from spx_sdk.components import SpxComponent, SpxContainer
from spx_sdk.registry import register_class, clear_registry


class DummyParent(SpxComponent):
    """Just a distinct SpxComponent subclass to attach containers to."""
    pass


# Register three SpxComponent subclasses: A, B and C.
@register_class
class A(SpxComponent):
    def _populate(self, definition):
        self.x = None
        self.z = None
        self.nested = None
        return super()._populate(definition)


@register_class
class B(SpxComponent):
    def _populate(self, definition):
        self.y = None
        self.z = None
        return super()._populate(definition)


@register_class(name="C")
class CItem(SpxComponent):
    pass


class TestSpxContainerGeneric(unittest.TestCase):
    def setUp(self):
        clear_registry()
        register_class()(A)
        register_class()(B)
        register_class(name="C")(CItem)
        self.parent = DummyParent(name="root")

    def test_generic_dict_instantiates_every_key(self):
        cont = SpxContainer(
            name="container",
            definition={"A": {"x": 1}, "C": "foo"},
            parent=self.parent
        )
        # two children: one A, one CItem
        self.assertEqual(len(cont.get_children_list()), 2)
        types = {type(ch) for ch in cont.get_children_list()}
        self.assertEqual(types, {A, CItem})
        # check each one's definition
        for ch in cont.get_children_list():
            if isinstance(ch, A):
                self.assertEqual(ch.definition, {"x": 1})
            else:
                self.assertEqual(ch.definition, "foo")

        # Also test __len__ and __contains__ interfaces
        self.assertEqual(len(cont), 2)
        self.assertIn('A', cont)
        self.assertIn('C', cont)

    def test_generic_list_mixed_nodes(self):
        register_class()(SpxComponent)
        cont = SpxContainer(
            name="container",
            definition=[{"A": {"x": 1}}, {"B": {"y": 2}}, "scalar"],
            parent=self.parent,
            type=SpxComponent
        )
        # A, B, and raw SpxComponent for "scalar"
        # Also test __len__ interface
        self.assertEqual(len(cont), 3)

        self.assertEqual(len(cont.get_children_list()), 3)

        a, b, s = cont.get_children_list()
        self.assertIsInstance(a, A)
        self.assertEqual(a.definition, {"x": 1})

        self.assertIsInstance(b, B)
        self.assertEqual(b.definition, {"y": 2})

        self.assertIsInstance(s, SpxComponent)
        self.assertEqual(s.definition, None)

    def test_generic_list_multikey_dict_wraps_to_root_and_children(self):
        register_class()(SpxComponent)
        invalid = [{"A": 1, "B": 2}]
        cont = SpxContainer(name="container", definition=invalid, parent=self.parent, type=SpxComponent)
        # Only one root child created
        self.assertEqual(len(cont.get_children_list()), 1)
        root_child = cont.get_children_list()[0]
        # First key 'A' becomes the root child
        self.assertIsInstance(root_child, A)
        self.assertEqual(root_child.definition, 1)

        # Subsequent key 'B' becomes a child of the root
        subchildren = root_child.get_children_list()
        self.assertEqual(len(subchildren), 1)
        subchild = subchildren[0]
        self.assertIsInstance(subchild, B)
        self.assertEqual(subchild.definition, 2)

    def test_generic_dict_unknown_class_raises(self):
        with self.assertRaises(AttributeError):
            SpxContainer(name="", definition={"Unknown": {}}, parent=self.parent)

    def test_generic_list_unknown_class_raises(self):
        with self.assertRaises(ValueError):
            SpxContainer(name="", definition=[{"Unknown": {}}], parent=self.parent)

    def test_generic_single_dict_node(self):
        # dict with one registered key instantiates that class
        cont = SpxContainer(
            name="container",
            definition={"B": {"z": 3}},
            parent=self.parent
        )
        self.assertEqual(len(cont.get_children_list()), 1)
        child = cont.get_children_list()[0]
        self.assertIsInstance(child, B)
        self.assertEqual(child.definition, {"z": 3})
        # child.name should reflect the class key
        self.assertEqual(child.name, "B")


class TestSpxContainerFiltered(unittest.TestCase):
    def setUp(self):
        clear_registry()
        register_class()(A)
        register_class()(B)
        register_class(name="C")(CItem)
        self.parent = DummyParent(name="root")

    def test_filtered_dict_only_SpxComponent_subclasses(self):
        register_class(SpxComponent)
        cont = SpxContainer(
            name="container",
            definition={"A": {"x": 1}, "C": "foo", "Unknown": {}},
            parent=self.parent,
            type=SpxComponent
        )
        self.assertEqual({type(ch) for ch in cont.get_children_list()}, {A, CItem, SpxComponent})

    def test_filtered_list_picks_first_subclass_each_node(self):
        # setup: register three SpxComponent‐derived types A, B, CItem
        clear_registry()
        register_class(SpxComponent)  # ensure base is in registry

        @register_class()
        class A(SpxComponent):
            pass

        @register_class()
        class B(A):
            pass

        @register_class()
        class CItem(SpxComponent):
            pass

        parent = DummyParent(name="root")
        nodes = ["one", {"x": 9}, "123"]

        cont = SpxContainer(
            name="container",
            definition=deepcopy(nodes),
            parent=parent,
            type=SpxComponent
        )

        # we get exactly one child per node
        self.assertEqual(len(cont.get_children_list()), len(nodes))
        # by registration order, A is first subclass, so every child is A
        self.assertTrue(all(isinstance(ch, SpxComponent) for ch in cont.get_children_list()))
        # each child's definition must match the original node
        one, two, three = cont.get_children_list()

        self.assertEqual(one.definition, None)
        self.assertEqual(two.definition,  9)
        self.assertEqual(three.definition, None)

        self.assertEqual(cont["one"].definition, None)
        self.assertEqual(cont["x"].definition, 9)
        self.assertEqual(cont["123"].definition, None)

        self.assertIsInstance(cont.get("one", None), SpxComponent)
        self.assertEqual(cont.get("blebvla", None), None)

    def test_filtered_scalar_fallback_to_base(self):
        # filtered scalar should create base type
        register_class()(SpxComponent)
        parent = DummyParent(name="root")
        cont = SpxContainer(
            name="container",
            definition="foo",
            parent=parent,
            type=SpxComponent
        )
        self.assertEqual(len(cont.get_children_list()), 1)
        child = cont.get_children_list()[0]
        self.assertIsInstance(child, SpxComponent)
        self.assertEqual(child.definition, "foo")
        self.assertIs(child.parent, cont)

    def test_filtered_dict_unknown_fallback(self):
        # unknown key in filtered dict falls back to base type
        register_class()(SpxComponent)
        cont = SpxContainer(
            name="container",
            definition={"Unknown": {"name": "abcdefg"}},
            parent=self.parent,
            type=SpxComponent
        )
        self.assertEqual(len(cont.get_children_list()), 1)
        child = cont.get_children_list()[0]
        self.assertIsInstance(child, SpxComponent)
        self.assertIs(child.parent, cont)

    def test_runtime_add_new_child_via_dict(self):
        register_class()(SpxComponent)
        cont = SpxContainer(name="ct", definition={}, parent=self.parent, type=SpxComponent)
        cont["new_child"] = {}
        self.assertIn("new_child", cont)
        child = cont["new_child"]
        self.assertIsInstance(child, SpxComponent)
        self.assertEqual(child.definition, {})
        self.assertIs(child.parent, cont)

    def test_runtime_override_existing_child_definition(self):
        register_class()(SpxComponent)
        cont = SpxContainer(name="ct", definition={"A": {"x": 1}}, parent=self.parent, type=SpxComponent)
        cont["A"] = {"x": 5}
        self.assertEqual(cont["A"].definition, {"x": 5})

    def test_runtime_replace_child_with_component(self):
        register_class()(SpxComponent)
        cont = SpxContainer(name="ct", definition={"A": {"x": 1}}, parent=self.parent, type=SpxComponent)
        new_a = A(name="A")
        cont["A"] = new_a
        self.assertIs(cont["A"], new_a)
        self.assertIs(new_a.parent, cont)

    def test_runtime_remove_and_delete(self):
        register_class()(SpxComponent)
        cont = SpxContainer(name="ct", definition={"A": {"x": 1}}, parent=self.parent, type=SpxComponent)
        cont.remove("A")
        self.assertNotIn("A", cont)
        new_c = CItem(name="C")
        cont["C"] = new_c
        self.assertIn("C", cont)
        del cont["C"]
        self.assertNotIn("C", cont)

    def test_runtime_setitem_invalid_type_raises(self):
        register_class()(SpxComponent)
        cont = SpxContainer(name="ct", definition={}, parent=self.parent, type=SpxComponent)
        with self.assertRaises(ValueError):
            cont["invalid"] = object()


class TestSpxContainerComplex(unittest.TestCase):
    def setUp(self):
        clear_registry()
        register_class()(SpxComponent)
        register_class()(A)
        register_class()(B)
        register_class(name="C")(CItem)
        self.parent = DummyParent(name="root")

    def test_generic_complex_nested_dict(self):
        """
        Even if one of the config values is itself a dict or list,
        we only load the top‐level keys. Nested structures stay inside .definition.
        """
        definition = {
            "A": {
                "x": 1,
                "nested": [
                    {"B": {"y": 2}},
                    "plain"
                ]
            },
            "C": "foo",
            "scalar": 123
        }
        cont = SpxContainer(
            name="complex",
            definition=deepcopy(definition),
            parent=self.parent,
            type=SpxComponent
        )

        # Top‐level keys: A, CItem, and SpxComponent(scalar)
        types = {type(ch) for ch in cont.get_children_list()}
        self.assertEqual(types, {A, CItem, SpxComponent})

        # Check that A got the full dict, including nested list
        a = next(ch for ch in cont.get_children_list() if isinstance(ch, A))
        self.assertEqual(a.definition["x"], 1)
        self.assertIsInstance(a.definition["nested"], list)
        # but we did NOT recursively instantiate B here:
        self.assertNotIn("y", getattr(a, 'children', []))

    def test_generic_list_with_multilevel_dicts(self):
        """
        A list entry that is a dict but with multiple keys becomes a raw SpxComponent,
        preserving its entire dict.
        """
        definition = [
            {"A": {"x": 1}},
            {"B": {"y": 2}, "C": "oops"},
            {"Unknown": {}},
            42
        ]
        # Unknown in generic list should raise, but only when it's a single‐key dict;
        # multi‐key dict is wrapped instead:
        with self.assertRaises(ValueError):
            SpxContainer(name="bad", definition=definition, parent=self.parent)

        # drop the truly unknown and see wrapping
        clean = [
            {"A": {"x": 1}},
            {"B": {"y": 2}, "C": "oops"},
            42
        ]
        cont = SpxContainer(name="mix", definition=clean, parent=self.parent, type=SpxComponent)
        self.assertEqual(len(cont.get_children_list()), 3)

        a, b_child, forty_two = cont.get_children_list()
        self.assertIsInstance(a, A)
        self.assertEqual(a.definition, {"x": 1})

        # Multi-key dict: first key 'B' becomes B instance
        self.assertIsInstance(b_child, B)
        self.assertEqual(b_child.definition, {"y": 2})
        # Its child should be CItem for key 'C'
        sub = b_child.get_children_list()
        self.assertEqual(len(sub), 1)
        c_item = sub[0]
        self.assertIsInstance(c_item, CItem)
        self.assertEqual(c_item.definition, "oops")

        # Scalar entry becomes a raw SpxComponent with definition 42
        self.assertIsInstance(forty_two, SpxComponent)
        self.assertEqual(forty_two.definition, 42)

    def test_filtered_complex_dict_and_list(self):
        """
        In filtered mode we fall back to base type (SpxComponent) when
        no subclass matches, but sub‐dicts still become individual children.
        """
        # register the base type itself
        register_class()(SpxComponent)

        definition = {
            "A": {"x": 1},
            "Unknown1": {"name": "bar"},
        }
        cont = SpxContainer(
            name="filt",
            definition=deepcopy(definition),
            parent=self.parent,
            type=SpxComponent
        )
        # one A, one SpxComponent fallback
        types = [type(ch) for ch in cont.get_children_list()]
        self.assertCountEqual(types, [A, SpxComponent])
        # check definitions round‐trip
        self.assertEqual(cont.get_children_list()[0].definition, {"x": 1})
        self.assertEqual(cont.get_children_list()[1].definition, {"name": "bar"})

        # now mixed list
        nodes = [
            {"x": 9},   # dict → base type
            "plain",    # scalar → base
            {"A": {"z": 3}},  # matches subclass A
        ]
        cont2 = SpxContainer(
            name="filt2",
            definition=nodes,
            parent=self.parent,
            type=SpxComponent
        )
        # should produce exactly 3 children
        self.assertEqual(len(cont2.get_children_list()), 3)
        # first two are SpxComponent (fallback), last is A
        self.assertTrue(isinstance(cont2.get_children_list()[0], SpxComponent))
        self.assertTrue(isinstance(cont2.get_children_list()[1], SpxComponent))
        self.assertTrue(isinstance(cont2.get_children_list()[2], A))
        self.assertEqual(cont2.get_children_list()[2].definition, {"z": 3})

    def test_filtered_missing_base_class_error(self):
        """
        If you ask for a filtered mode on an unregistered base,
        we should error immediately.
        """
        # clear_registry() was called already, but we must not register SpxComponent now.
        with self.assertRaises(ValueError):
            SpxContainer(
                name="fail",
                definition={"A": {}},
                parent=self.parent,
                type=DummyParent  # not in registry at all
            )

    def test_getitem_child_access_on_container(self):
        definition = {"A": {"x": 1}, "C": "foo", "scalar": 123}
        cont = SpxContainer(
            name="container",
            definition=definition,
            parent=self.parent,
            type=SpxComponent
        )
        # Access children by key via __getitem__
        self.assertEqual(cont["A"].definition, {"x": 1})
        self.assertEqual(cont["C"].definition, "foo")
        self.assertEqual(cont["scalar"].definition, 123)

    def test_setitem_replace_child_on_container(self):
        definition = {"A": {"x": 1}}
        cont = SpxContainer(
            name="container",
            definition=definition,
            parent=self.parent,
            type=SpxComponent
        )
        # Create a new component to replace existing
        new_comp = A(name="A")
        cont["A"] = new_comp
        self.assertIs(cont["A"], new_comp)
        self.assertIs(new_comp.get_parent(), cont)
        # Setting a non-SpxComponent should raise
        with self.assertRaises(ValueError):
            cont["nonexistent"] = object()

    def test_duplicate_keys_get_indexed_names(self):
        # Create a container with duplicate keys in the definition
        # This is only possible via a list of dicts, as Python dicts can't have duplicate keys
        definition = [
            {"A": {"x": 1}},
            {"A": {"x": 2}},
            {"A": {"x": 3}},
            {"B": {"y": 4}},
            {"B": {"y": 5}},
        ]
        cont = SpxContainer(
            name="container",
            definition=definition,
            parent=self.parent
        )
        children = cont.get_children_list()
        # There should be 5 children
        self.assertEqual(len(children), 5)
        # Their names should be A, A_1, A_2, B, B_1
        names = [ch.name for ch in children]
        self.assertEqual(names, ["A", "A_1", "A_2", "B", "B_1"])
        # Their types and definitions should be correct
        self.assertIsInstance(children[0], A)
        self.assertEqual(children[0].definition, {"x": 1})
        self.assertIsInstance(children[1], A)
        self.assertEqual(children[1].definition, {"x": 2})
        self.assertIsInstance(children[2], A)
        self.assertEqual(children[2].definition, {"x": 3})
        self.assertIsInstance(children[3], B)
        self.assertEqual(children[3].definition, {"y": 4})
        self.assertIsInstance(children[4], B)
        self.assertEqual(children[4].definition, {"y": 5})

    def test_duplicate_keys_get_indexed_names_filtered(self):
        # Create a container with duplicate keys in the definition
        # This is only possible via a list of dicts, as Python dicts can't have duplicate keys
        definition = [
            {"A": {"x": 1}},
            {"A": {"x": 2}},
            {"A": {"x": 3}},
            {"B": {"y": 4}},
            {"B": {"y": 5}},
        ]
        cont = SpxContainer(
            name="container",
            definition=definition,
            parent=self.parent,
            type=SpxComponent
        )
        children = cont.get_children_list()
        # There should be 5 children
        self.assertEqual(len(children), 5)
        # Their names should be A, A_1, A_2, B, B_1
        names = [ch.name for ch in children]
        self.assertEqual(names, ["A", "A_1", "A_2", "B", "B_1"])
        # Their types and definitions should be correct
        self.assertIsInstance(children[0], A)
        self.assertEqual(children[0].definition, {"x": 1})
        self.assertIsInstance(children[1], A)
        self.assertEqual(children[1].definition, {"x": 2})
        self.assertIsInstance(children[2], A)
        self.assertEqual(children[2].definition, {"x": 3})
        self.assertIsInstance(children[3], B)
        self.assertEqual(children[3].definition, {"y": 4})
        self.assertIsInstance(children[4], B)
        self.assertEqual(children[4].definition, {"y": 5})


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
