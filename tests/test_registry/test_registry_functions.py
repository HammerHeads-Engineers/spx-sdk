# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
from spx_sdk.registry import (
    register_class,
    get_classes_by_base,
    get_class_names_by_base,
    filter_instances_by_base_class,
    filter_instances_by_base_class_name,
    get_instance,
    get_all_instances,
    get_all_classes,
    clear_registry,
    get_class,
    get_class_base,
    class_registry,
    instance_registry
)


# --- Dummy Classes for Testing ---
class BaseDummy:
    pass


@register_class()
class DummyA(BaseDummy):
    def __init__(self, **kwargs):
        self.params = kwargs


@register_class(name="CustomDummyB")
class DummyB(BaseDummy):
    def __init__(self, **kwargs):
        self.params = kwargs


# --- Unit Test Suite ---
class TestRegistryFunctions(unittest.TestCase):

    def setUp(self):
        # Clear registries before each test to ensure test isolation.
        clear_registry()

    def test_get_classes_by_base(self):
        # Clear and populate the registry.
        clear_registry()
        # Register the base and the subclasses.
        register_class()(BaseDummy)
        register_class()(DummyA)
        register_class()(DummyB)  # DummyB is registered with custom name "CustomDummyB"

        result = get_classes_by_base("BaseDummy")
        self.assertIn("DummyA", result, "DummyA should be registered under its default name.")
        self.assertIn("DummyB", result, "DummyB should be registered as 'CustomDummyB'.")
        self.assertEqual(result["DummyA"], DummyA)
        self.assertEqual(result["DummyB"], DummyB)

    def test_get_class_names_by_base(self):
        clear_registry()
        register_class()(BaseDummy)
        register_class()(DummyA)
        register_class()(DummyB)

        names = get_class_names_by_base("BaseDummy")
        self.assertIn("DummyA", names, "Name 'DummyA' should be in the list.")
        self.assertIn("DummyB", names, "Name 'DummyB' should be in the list.")

    def test_filter_instances_by_base_class(self):
        clear_registry()
        register_class()(BaseDummy)
        register_class()(DummyA)
        register_class()(DummyB)

        # Create dummy instances and add them to the instance registry.
        a = DummyA(foo="bar")
        b = DummyB(hello="world")
        instance_registry["inst_a"] = a
        instance_registry["inst_b"] = b

        filtered = filter_instances_by_base_class(BaseDummy)
        self.assertEqual(len(filtered), 2, "Both DummyA and DummyB instances should be filtered.")
        self.assertIn("inst_a", filtered)
        self.assertIn("inst_b", filtered)

    def test_filter_instances_by_base_class_name(self):
        clear_registry()
        register_class()(BaseDummy)
        register_class()(DummyA)
        register_class()(DummyB)

        a = DummyA(foo="bar")
        b = DummyB(hello="world")
        instance_registry["inst_a"] = a
        instance_registry["inst_b"] = b

        filtered = filter_instances_by_base_class_name("BaseDummy")
        self.assertEqual(len(filtered), 2, "Both instances should be filtered using the base class name 'BaseDummy'.")
        self.assertIn("inst_a", filtered)
        self.assertIn("inst_b", filtered)

    def test_get_instance(self):
        clear_registry()
        register_class()(BaseDummy)
        register_class()(DummyA)

        a = DummyA(foo="bar")
        instance_registry["inst_a"] = a
        # Test that the instance is returned when present.
        self.assertIs(get_instance("inst_a"), a)
        # Test that a ValueError is raised for missing instance.
        with self.assertRaises(ValueError) as context:
            get_instance("nonexistent")
        self.assertIn("Instance nonexistent not found in registry", str(context.exception))

    def test_get_all_instances_and_classes(self):
        clear_registry()
        # Expect empty dictionaries after clearing.
        self.assertEqual(get_all_instances(), {}, "Instance registry should be empty.")
        self.assertEqual(get_all_classes(), {}, "Class registry should be empty.")

        # Add dummy entries.
        a = DummyA(foo="bar")
        instance_registry["inst_a"] = a
        class_registry["DummyA"] = {"class": DummyA, "base_class": "BaseDummy"}

        all_instances = get_all_instances()
        all_classes = get_all_classes()
        self.assertIn("inst_a", all_instances, "inst_a should appear in all instances.")
        self.assertIn("DummyA", all_classes, "DummyA should appear in all classes.")

    def test_clear_registry(self):
        # Populate the registries.
        instance_registry["key1"] = DummyA(foo="a")
        class_registry["DummyA"] = {"class": DummyA, "base_class": "BaseDummy"}
        clear_registry()
        # After clearing, registries should be empty.
        self.assertEqual(instance_registry, {}, "Instance registry should be cleared.")
        self.assertEqual(class_registry, {}, "Class registry should be cleared.")

    def test_get_class_and_get_class_base(self):
        clear_registry()
        register_class()(DummyA)
        cls = get_class("DummyA")
        self.assertIs(cls, DummyA, "get_class should return DummyA for key 'DummyA'.")
        base = get_class_base("DummyA")
        self.assertEqual(base, "BaseDummy", "The base class of DummyA should be 'BaseDummy'.")


class TestRegistryMisc(unittest.TestCase):

    def setUp(self):
        # Clear the global registries before each test.
        clear_registry()

    def test_clear_registry(self):
        # Populate the registries with dummy data.
        class_registry["DummyA"] = {"class": DummyA, "base_class": "BaseDummy"}
        instance_registry["key1"] = DummyA(foo="a")

        # Check that the registries are not empty.
        self.assertNotEqual(class_registry, {}, "Class registry should not be empty before clearing.")
        self.assertNotEqual(instance_registry, {}, "Instance registry should not be empty before clearing.")

        # Clear the registries.
        clear_registry()

        # Verify that both registries are empty.
        self.assertEqual(class_registry, {}, "Class registry should be empty after clearing.")
        self.assertEqual(instance_registry, {}, "Instance registry should be empty after clearing.")

    def test_get_class_valid(self):
        # Register DummyA and test retrieval with get_class.
        register_class()(DummyA)
        cls = get_class("DummyA")
        self.assertIs(cls, DummyA, "get_class should return DummyA for key 'DummyA'.")

    def test_get_class_invalid(self):
        # Test that get_class raises a ValueError if the class is not in the registry.
        with self.assertRaises(ValueError) as context:
            get_class("NonExistentClass")
        self.assertIn("not found in registry", str(context.exception))

    def test_get_class_base_valid(self):
        # Register DummyA and then retrieve its base class using get_class_base.
        register_class()(DummyA)
        base = get_class_base("DummyA")
        self.assertEqual(base, "BaseDummy", "Base class of DummyA should be 'BaseDummy'.")

    def test_get_class_base_invalid(self):
        # Test that get_class_base raises ValueError for a non-registered class.
        with self.assertRaises(ValueError) as context:
            get_class_base("NonExistentClass")
        self.assertIn("not found in registry", str(context.exception))


if __name__ == "__main__":
    unittest.main()
