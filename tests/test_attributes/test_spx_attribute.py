# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
from spx_sdk.attributes import (
    type_mapping,
    is_attribute_reference,
    get_attribute_value,
    set_attribute_value,
    SpxAttribute,
)
from spx_sdk.attributes.attribute import StaticAttributeWrapper
from spx_sdk.components.component import SpxComponent


class DummyTrigger:
    def __init__(self):
        self.ran = False

    def run(self):
        self.ran = True


class DummyOwner(SpxComponent):
    """Component with a real property and method to test LinkedProperty."""

    def __init__(self, name="dummy", parent=None):
        super().__init__(name=name, parent=parent)
        self._foo = 0

    @property
    def foo(self):
        return self._foo

    @foo.setter
    def foo(self, v):
        self._foo = v

    def bar(self):
        return 123

    def set_bar(self, v):
        # illustrative setter-as-method
        self._bar = v


class TestSpxAttributeHelpers(unittest.TestCase):

    def test_type_mapping_defaults(self):
        # ensure our type_mapping covers float, bool, int, str
        self.assertEqual(type_mapping["float"]["default"], 0.0)
        self.assertEqual(type_mapping["bool"]["default"], False)
        self.assertEqual(type_mapping["int"]["default"], 0)
        self.assertEqual(type_mapping["str"]["default"], "")

    def test_is_attribute_reference_hash(self):
        # #attr(), #internal(), #external()
        for prefix, expected_type in [
            ("attr", "internal"),
            ("internal", "internal"),
            ("external", "external"),
        ]:
            ref = f"${prefix}(some.attr)"
            is_attr, attr_str, attr_type = is_attribute_reference(ref)
            self.assertTrue(is_attr)
            self.assertEqual(attr_str, "some.attr")
            self.assertEqual(attr_type, expected_type)

        # no prefix but dotted
        is_attr, attr_str, attr_type = is_attribute_reference("inst.attrname")
        self.assertTrue(is_attr)
        self.assertEqual(attr_str, "inst.attrname")
        self.assertEqual(attr_type, "internal")

        # not a reference
        for s in ("just_a_string", "123", "#wrongprefix(x)"):
            is_attr, *_ = is_attribute_reference(s)
            self.assertFalse(is_attr)

    def test_get_and_set_attribute_value(self):
        class Fake:
            def __init__(self):
                self.internal_value = "i"
                self.external_value = "e"

        f = Fake()
        self.assertEqual(get_attribute_value(f, "internal"), "i")
        self.assertEqual(get_attribute_value(f, "external"), "e")

        set_attribute_value(f, "internal", 42)
        self.assertEqual(f.internal_value, 42)
        set_attribute_value(f, "external", 43)
        self.assertEqual(f.external_value, 43)


class TestSpxAttribute(unittest.TestCase):
    def setUp(self):
        self.owner = DummyOwner()
        # minimal node must have Name
        self.node = {"type": "int", "default": 7}
        self.attr = SpxAttribute(name="power", parent=self.owner, definition=self.node)

    def test_initial_fields(self):
        # name taken from definition
        self.assertEqual(self.attr.name, "power")
        # type and initial_value from DataType/InitialValue
        self.assertEqual(self.attr.type, "int")
        self.assertEqual(self.attr.initial_value, 7)
        # internal_value getter returns same when no link
        self.assertEqual(self.attr.internal_value, 7)
        # external_value defaults to internal when not set externally
        self.assertEqual(self.attr.external_value, 7)

    def test_internal_value_setter_and_casting(self):
        # setting internal_value casts to correct type and resets external
        self.attr.type = "bool"
        self.attr.internal_value = 1  # True-ish
        self.assertTrue(isinstance(self.attr.internal_value, bool))
        self.assertTrue(self.attr.internal_value)
        # external reset
        self.assertIsNone(self.attr._external_value)

    def test_external_value_setter_and_casting(self):
        self.attr.type = "float"
        self.attr.external_value = "3.14"
        self.assertIsInstance(self.attr.external_value, float)
        self.assertAlmostEqual(self.attr.external_value, 3.14)

    def test_invalid_type_raises(self):
        self.attr.type = "int"
        with self.assertRaises(TypeError):
            self.attr.internal_value = "not an int"
        with self.assertRaises(TypeError):
            self.attr.external_value = "nope"

    def test_link_to_internal_property(self):
        # link to owner.foo property
        self.attr = SpxAttribute(
            name="foo",
            parent=self.owner,
            definition={"type": "int", "default": 5},
        )
        self.attr.link_to_internal_property(self.owner, "foo")
        # the owner's foo property should be set to initial_value
        self.assertEqual(self.owner.foo, 5)
        # updating attribute.internal_value updates the linked property
        self.attr.internal_value = 42
        self.assertEqual(self.owner.foo, 42)
        # reading attribute.internal_value reflects getter from owner
        self.owner.foo = 99
        self.assertEqual(self.attr.internal_value, 99)

    def test_link_to_external_property(self):
        # no real external property on DummyOwner, but linkage code path covers setting
        # we simulate by monkey-patching DummyOwner.bar setter
        self.owner._bar = None
        # create a property-like setter on DummyOwner for bar
        DummyOwner.bar = property(lambda s: None, lambda s, v: setattr(s, "_bar", v))
        self.attr = SpxAttribute(
            name="bar",
            parent=self.owner,
            definition={"type": "int", "default": 2},
        )
        self.attr.link_to_external_property(self.owner, "bar")
        # initial link sets external via setter
        self.assertEqual(self.owner._bar, 2)
        # updating external_value updates the linked setter
        self.attr.external_value = 7
        self.assertEqual(self.owner._bar, 7)

    def test_link_to_internal_method(self):
        # link via method getter & setter
        # DummyOwner.bar() returns 123; set_bar stores to _bar
        self.attr = SpxAttribute(
            name="bar",
            parent=self.owner,
            definition={"type": "int", "default": 5},
        )
        self.attr.link_to_internal_func(self.owner, "bar", "set_bar")
        # setter invoked with initial_value
        self.assertEqual(self.owner._bar, 5)
        # update attr.internal triggers setter
        self.attr.internal_value = 8
        self.assertEqual(self.owner._bar, 8)

    def test_prepare_and_run_reset_external(self):
        self.attr._external_value = 99
        self.attr.prepare()
        self.assertIsNone(self.attr._external_value)
        self.attr._external_value = 88
        self.attr.run()
        self.assertIsNone(self.attr._external_value)

    def test_internal_wrapper(self):
        """InternalAttributeWrapper should get and set internal_value."""
        # initialize internal to a known value
        self.attr.internal_value = 5
        wrapper = self.attr.internal
        self.assertEqual(wrapper.get(), 5)
        wrapper.set(8)
        self.assertEqual(self.attr.internal_value, 8)
        self.assertEqual(repr(wrapper), f"<Internal {self.attr.name}=8>")

    def test_external_wrapper(self):
        """ExternalAttributeWrapper should get and set external_value."""
        wrapper = self.attr.external
        wrapper.set(15)
        self.assertEqual(self.attr.external_value, 15)
        self.assertEqual(repr(wrapper), f"<External {self.attr.name}=15>")

    def test_static_wrapper(self):
        """StaticAttributeWrapper should wrap plain object attributes."""
        class Dummy:
            pass
        d = Dummy()
        d.value = 1
        sw = StaticAttributeWrapper(d, "value")
        self.assertEqual(sw.get(), 1)
        sw.set(2)
        self.assertEqual(d.value, 2)
        self.assertEqual(repr(sw), "<Static value=2>")


if __name__ == "__main__":
    unittest.main()
