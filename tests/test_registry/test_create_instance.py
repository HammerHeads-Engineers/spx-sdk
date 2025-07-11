# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
from spx_sdk.registry import (
    register_class,
    create_instance,
    dynamic_import,
    class_registry
)


# Dummy base class for testing registration.
class BaseDummy:
    def __init__(self, **kwargs):
        self.params = kwargs


# Dummy class to be registered.
class DummyRegistered(BaseDummy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TestCreateInstanceAndDynamicImport(unittest.TestCase):
    def setUp(self):
        # Clear the registry before each test.
        class_registry.clear()

    def test_create_instance_with_registered_class(self):
        """
        Test creating an instance when the class is already registered.
        """
        # Register the dummy class using its default name.
        register_class()(DummyRegistered)
        # Create an instance via create_instance.
        instance = create_instance("DummyRegistered", foo="bar")
        self.assertIsInstance(instance, DummyRegistered)
        self.assertEqual(instance.params.get("foo"), "bar")

    def test_create_instance_dynamic_import_success(self):
        """
        Test that create_instance uses dynamic_import when the class is not registered.
        Here we use a standard library class, such as json.JSONDecoder.
        """
        # Ensure the registry is empty (so dynamic_import gets called)
        # Create an instance for a known class in the standard library.
        instance = create_instance("json.JSONDecoder")
        from json import JSONDecoder
        self.assertIsInstance(instance, JSONDecoder)

    def test_create_instance_dynamic_import_failure(self):
        """
        Test that create_instance raises a ValueError when neither the registry
        nor dynamic import can find the class.
        """
        with self.assertRaises(ValueError) as context:
            create_instance("non.existent.ModuleClass")
        self.assertIn("not found and could not be imported", str(context.exception))

    def test_dynamic_import_success(self):
        """
        Test dynamic_import with a valid module path from the standard library.
        """
        cls = dynamic_import("json.JSONDecoder")
        from json import JSONDecoder
        self.assertIsNotNone(cls)
        self.assertEqual(cls, JSONDecoder)

    def test_dynamic_import_failure(self):
        """
        Test dynamic_import returns None if the module path is invalid.
        """
        cls = dynamic_import("non.existent.ModuleClass")
        self.assertIsNone(cls)

    def test_create_instance_template_only(self):
        """
        Test that create_instance applies a template when no definition is provided.
        """
        # Register a template entry pointing to BaseDummy with a template dict
        class_registry['Templated'] = {
            'class': BaseDummy,
            'template': {'a': 1, 'b': 2}
        }
        # Create instance without explicit 'definition'
        instance = create_instance('Templated', foo='bar')
        # Should be an instance of BaseDummy
        self.assertIsInstance(instance, BaseDummy)
        # 'definition' kwarg should equal the template
        self.assertIn('definition', instance.params)
        self.assertEqual(instance.params['definition'], {'a': 1, 'b': 2})
        # Other parameters should also be preserved
        self.assertEqual(instance.params.get('foo'), 'bar')

    def test_create_instance_template_merging(self):
        """
        Test that create_instance merges the registry template with provided definition.
        """
        class_registry['Templated'] = {
            'class': BaseDummy,
            'template': {'x': 10, 'y': 20}
        }
        # Provide overlapping 'definition' that overrides 'y' and adds 'z'
        instance = create_instance('Templated', definition={'y': 99, 'z': 5})
        self.assertIsInstance(instance, BaseDummy)
        # Merged definition: template x=10, y overridden to 99, plus z=5
        expected = {'x': 10, 'y': 99, 'z': 5}
        self.assertEqual(instance.params['definition'], expected)


if __name__ == '__main__':
    unittest.main()
