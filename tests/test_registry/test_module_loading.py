# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import os
import sys
import tempfile
import shutil
import unittest
import logging

# Import the functions to test from your registry.py.
from spx_sdk.registry import (
    load_module_from_path,
    load_modules_from_directory,
    load_modules_recursively
)

# Optionally configure logging for the tests.
logging.basicConfig(level=logging.DEBUG)


class TestLoadModuleFromPath(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the module file.
        self.test_dir = tempfile.mkdtemp()
        self.module_filename = os.path.join(self.test_dir, "temp_module.py")
        with open(self.module_filename, "w", encoding="utf-8") as f:
            f.write("def foo():\n    return 'bar'\n")

    def tearDown(self):
        # Clean up the temporary directory.
        shutil.rmtree(self.test_dir)
        sys.modules.pop("temp_module", None)

    def test_initial_load(self):
        # Load the module and check its attributes.
        module = load_module_from_path(self.module_filename)
        self.assertTrue(hasattr(module, "foo"))
        self.assertEqual(module.foo(), "bar")
        self.assertIn("temp_module", sys.modules)

    def test_reload_after_modification(self):
        # Load the module initially.
        module = load_module_from_path(self.module_filename)
        self.assertEqual(module.foo(), "bar")
        # Change the file content.
        with open(self.module_filename, "w", encoding="utf-8") as f:
            f.write("def foo():\n    return 'changed'\n")
        # Re-load the module.
        module_new = load_module_from_path(self.module_filename)
        self.assertEqual(module_new.foo(), "changed")


class TestLoadModulesFromDirectory(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Create a Python file that should be loaded.
        self.module1 = os.path.join(self.test_dir, "mod1.py")
        with open(self.module1, "w", encoding="utf-8") as f:
            f.write("x = 100\n")
        # Create a Python file that should be skipped because its name contains "test".
        self.test_module = os.path.join(self.test_dir, "test_mod.py")
        with open(self.test_module, "w", encoding="utf-8") as f:
            f.write("x = 999\n")
        # Create an __init__.py file (which will be ignored).
        with open(os.path.join(self.test_dir, "__init__.py"), "w", encoding="utf-8") as f:
            f.write("# init")

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        sys.modules.pop("mod1", None)
        sys.modules.pop("test_mod", None)

    def test_load_modules_from_directory(self):
        # Call the function with a skip pattern for files containing "test".
        load_modules_from_directory(self.test_dir, skip_pattern="*test*")
        # "mod1" should be loaded.
        self.assertIn("mod1", sys.modules)
        # "test_mod" should be skipped.
        self.assertNotIn("test_mod", sys.modules)


class TestLoadModulesRecursively(unittest.TestCase):
    def setUp(self):
        self.base_dir = tempfile.mkdtemp()
        # Create a subdirectory that should be processed.
        self.subdir = os.path.join(self.base_dir, "subdir")
        os.makedirs(self.subdir)
        self.mod2_path = os.path.join(self.subdir, "mod2.py")
        with open(self.mod2_path, "w", encoding="utf-8") as f:
            f.write("def foo():\n    return 'hello'\n")
        # Create a subdirectory that should be skipped because its name contains "test".
        self.test_folder = os.path.join(self.base_dir, "test_folder")
        os.makedirs(self.test_folder)
        self.mod3_path = os.path.join(self.test_folder, "mod3.py")
        with open(self.mod3_path, "w", encoding="utf-8") as f:
            f.write("def bar():\n    return 'world'\n")

    def tearDown(self):
        shutil.rmtree(self.base_dir)
        sys.modules.pop("subdir.mod2", None)
        sys.modules.pop("test_folder.mod3", None)

    def test_load_modules_recursively(self):
        load_modules_recursively(self.base_dir, skip_pattern="*test*")
        # Expect that "subdir.mod2" is loaded.
        self.assertIn("subdir.mod2", sys.modules)
        # The module from the skipped directory should not be loaded.
        self.assertNotIn("test_folder.mod3", sys.modules)
        # Verify that the loaded module's function works.
        mod2 = sys.modules["subdir.mod2"]
        self.assertEqual(mod2.foo(), "hello")


if __name__ == "__main__":
    unittest.main()
