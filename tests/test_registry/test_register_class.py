# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest

# Import everything we need from registry.py
from spx_sdk.registry import (
    class_registry,
    register_class,
)


# Define a base dummy class for testing purposes.
class BaseDummy:
    pass


class TestRegisterClass(unittest.TestCase):
    def setUp(self):
        # Clear the global registry before each test.
        class_registry.clear()

    def test_register_class_default_name(self):
        # Register a class without providing a custom name.
        @register_class()
        class DummyA(BaseDummy):
            pass

        self.assertIn("DummyA", class_registry, "DummyA should be registered under its default name.")
        self.assertEqual(class_registry["DummyA"]["class"], DummyA, "Registered class should be DummyA.")
        # Check that the base_class is correctly set to the first base of DummyA.
        self.assertEqual(class_registry["DummyA"]["base_class"], "BaseDummy")

    def test_register_class_custom_name(self):
        # Register a class with a provided custom name.
        @register_class(name="CustomDummyB")
        class DummyB(BaseDummy):
            pass

        self.assertIn("CustomDummyB", class_registry, "DummyB should be registered as 'CustomDummyB'.")
        self.assertEqual(class_registry["CustomDummyB"]["class"], DummyB, "Registered class should be DummyB.")
        self.assertEqual(class_registry["CustomDummyB"]["base_class"], "BaseDummy")

    def test_register_class_decorator(self):
        # Test decorator behavior when register_class is called without a class.
        decorator = register_class(name="LambdaDummy")
        self.assertTrue(callable(decorator), "register_class should return a callable decorator when no class is provided.")

        @decorator
        class DummyC(BaseDummy):
            pass

        self.assertIn("LambdaDummy", class_registry, "DummyC should be registered as 'LambdaDummy'.")
        self.assertEqual(class_registry["LambdaDummy"]["class"], DummyC, "Registered class should be DummyC.")
        self.assertEqual(class_registry["LambdaDummy"]["base_class"], "BaseDummy")


if __name__ == "__main__":
    unittest.main()
