# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import os
import unittest
import tempfile
import shutil

from spx_sdk.registry import (
    clear_registry,
    load_instances_from_yaml,
    load_instances_from_yaml_data,
    instance_registry,
    register_class
)


# --- Dummy Classes for Testing ---

class BaseDummy:
    pass


# --- Unittest Module for Instance Loading Functions ---

class TestLoadInstances(unittest.TestCase):
    def setUp(self):
        # Clear the instance registry before each test.
        clear_registry()

        @register_class()
        class DummyA(BaseDummy):
            def __init__(self, **kwargs):
                self.params = kwargs

        @register_class()
        class DummyB(BaseDummy):
            def __init__(self, **kwargs):
                self.params = kwargs
        pass

    def test_load_instances_from_yaml_data_valid(self):
        """
        Test loading instances from a YAML string.
        """
        yaml_data = """
instance1:
  class: DummyA
  parameters:
    foo: "bar"
instance2:
  class: DummyB
  parameters:
    hello: "world"
"""
        load_instances_from_yaml_data(yaml_data)
        # Check that both instances are created.
        self.assertIn("instance1", instance_registry)
        self.assertIn("instance2", instance_registry)
        inst1 = instance_registry["instance1"]
        inst2 = instance_registry["instance2"]
        self.assertEqual(inst1.params.get("foo"), "bar")
        self.assertEqual(inst2.params.get("hello"), "world")

    def test_load_instances_from_yaml_file_valid(self):
        """
        Test loading instances from an actual YAML file.
        """
        tmp_dir = tempfile.mkdtemp()
        try:
            file_path = os.path.join(tmp_dir, "instances.yaml")
            yaml_content = """
instance1:
  class: DummyA
  parameters:
    foo: "bar"
instance2:
  class: DummyB
  parameters:
    hello: "world"
"""
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(yaml_content)
            load_instances_from_yaml(file_path)
            self.assertIn("instance1", instance_registry)
            self.assertIn("instance2", instance_registry)
            inst1 = instance_registry["instance1"]
            inst2 = instance_registry["instance2"]
            self.assertEqual(inst1.params.get("foo"), "bar")
            self.assertEqual(inst2.params.get("hello"), "world")
        finally:
            shutil.rmtree(tmp_dir)

    def test_load_instances_from_yaml_file_not_found(self):
        """
        Test that attempting to load instances from a non-existent file
        raises a FileNotFoundError.
        """
        with self.assertRaises(FileNotFoundError) as context:
            load_instances_from_yaml("nonexistent.yaml")
        self.assertIn("File nonexistent.yaml not found", str(context.exception))


if __name__ == "__main__":
    unittest.main()
