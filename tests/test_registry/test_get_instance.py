# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
from spx_sdk.registry import get_instance, instance_registry


# A simple dummy class for our test.
class Dummy:
    def __init__(self, value):
        self.value = value


class TestGetInstance(unittest.TestCase):
    def setUp(self):
        # Clear the instance registry before each test.
        instance_registry.clear()

    def test_get_instance_exists(self):
        # Create a dummy instance and register it.
        dummy_instance = Dummy("test value")
        instance_registry["inst_a"] = dummy_instance

        # Ensure get_instance returns our dummy instance.
        self.assertIs(get_instance("inst_a"), dummy_instance)

    def test_get_instance_not_found(self):
        # Check that get_instance raises an error when the instance is not in the registry.
        with self.assertRaises(ValueError) as context:
            get_instance("nonexistent")
        self.assertIn("Instance nonexistent not found in registry", str(context.exception))


if __name__ == "__main__":
    unittest.main()
