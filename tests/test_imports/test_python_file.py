# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import os
import unittest

from spx_sdk.imports.python_file import PythonFile
from spx_sdk.components import SpxComponent
from spx_sdk.registry import register_class


class TestPythonFile(unittest.TestCase):
    def setUp(self):
        # Locate our test‐import modules (mod1.py, mod2.py)
        tests_dir = os.path.dirname(__file__)
        imports_dir = os.path.abspath(
            os.path.join(tests_dir, '..', 'test_imports')
        )
        self.mod1 = os.path.join(imports_dir, 'mod1.py')
        self.mod2 = os.path.join(imports_dir, 'mod2.py')

        # Definition dict matching your implementation: path, class, attributes
        self.definition = {
            self.mod1: {
                'class': 'FakeItemClass',
                'attributes': {
                    'status':    {'property': 'status'},
                    'int_value': {'property': 'int_value'},
                    'float_list': {'getter':   'float_list', 'setter': 'float_list'},
                }
            },
            self.mod2: {
                'class': 'InheritedItem',
                'attributes': {
                    'count': {'property': 'count'},
                    'ids':   {'getter':   'ids',   'setter': 'ids'},
                }
            }
        }

    def test_populate_creates_children_and_class_instances(self):
        pf = PythonFile(name='pf', definition=self.definition)
        # keys in children & class_instances
        expected = {'FakeItemClass', 'InheritedItem'}
        self.assertSetEqual(set(pf.class_instances.keys()), expected)

        # Instances should be Item subclasses
        fake = pf.class_instances['FakeItemClass']
        inh = pf.class_instances['InheritedItem']
        self.assertIsNotNone(fake)
        self.assertIsInstance(inh, SpxComponent)

    def test_create_instance_from_module_plain_branch(self):
        pf = PythonFile(name='pf', definition={})
        # Branch: subclass of Item in mod1
        info1 = {'path': self.mod1, 'class': 'FakeItemClass'}
        inst1 = pf.create_instance_from_module(info1)
        self.assertIsNotNone(inst1)

        self.assertEqual(inst1.description, "Fake item for unit tests")
        self.assertEqual(inst1.enabled, True)
        self.assertEqual(inst1._status, "initialized")
        # # Numeric and array attributes for testing
        self.assertEqual(inst1._int_value, 42)
        self.assertEqual(inst1._float_value, 3.14)

    def test_create_instance_from_module_item_branch(self):
        pf = PythonFile(name='pf', definition={})
        # Branch: subclass of Item in mod1
        info1 = {'path': self.mod2, 'class': 'InheritedItem'}
        inst1 = pf.create_instance_from_module(info1)

        self.assertIsInstance(inst1, SpxComponent)

        # Verify numeric and array properties on InheritedItem
        self.assertEqual(inst1.count, 100)
        self.assertEqual(inst1.ratio, 0.5)
        self.assertListEqual(inst1.ids, [10, 20, 30])
        self.assertListEqual(inst1.ratios, [0.1, 0.2, 0.3])
        self.assertEqual(inst1.summary, "InheritedItem with count=100 and ratio=0.5")

        # Test setter behavior for these properties
        inst1.count = 200
        self.assertEqual(inst1.count, 200)
        inst1.ratio = 0.75
        self.assertEqual(inst1.ratio, 0.75)
        new_ids = [5, 6, 7]
        inst1.ids = new_ids
        self.assertListEqual(inst1.ids, new_ids)
        new_ratios = [0.5, 0.6]
        inst1.ratios = new_ratios
        self.assertListEqual(inst1.ratios, new_ratios)

    def test_create_instance_from_module_plain_class(self):
        pf = PythonFile(name='pf', definition={})
        # Create a temporary plain module file
        temp_path = os.path.join(os.path.dirname(__file__), 'temp_plain.py')
        with open(temp_path, 'w') as f:
            f.write("""class Simple:
    def __init__(self):
        self.value = 123
""")
        try:
            info = {'path': temp_path, 'class': 'Simple'}
            inst = pf.create_instance_from_module(info)
            self.assertFalse(isinstance(inst, SpxComponent))
            self.assertEqual(inst.value, 123)
        finally:
            os.remove(temp_path)

    def test_create_instance_from_module_plain_with_init_params(self):
        pf = PythonFile(name='pf', definition={})
        # Create a temp module with __init__ requiring positional and keyword args
        temp_path = os.path.join(os.path.dirname(__file__), 'temp_param.py')
        with open(temp_path, 'w') as f:
            f.write("""class ParamClass:
    def __init__(self, x, y, scale=1):
        self.x = x
        self.y = y
        self.scale = scale
""")
        try:
            info = {
                'path': temp_path,
                'class': 'ParamClass',
                'init': {
                    'args': [5, 10],
                    'kwargs': {'scale': 2}
                }
            }
            inst = pf.create_instance_from_module(info)
            self.assertTrue(hasattr(inst, 'x') and inst.x == 5)
            self.assertTrue(hasattr(inst, 'y') and inst.y == 10)
            self.assertTrue(hasattr(inst, 'scale') and inst.scale == 2)
        finally:
            os.remove(temp_path)

    def test_prepare_and_reset_no_exceptions(self):
        pf = PythonFile(name='pf', definition=self.definition)
        # Attach a real SpxAttributes under root so prepare() can find them
        from spx_sdk.attributes.attributes import SpxAttributes, SpxAttribute
        register_class()(SpxAttribute)
        # Build an attributes definition covering all names
        attr_names = []
        for cfg in self.definition.values():
            attr_names.extend(cfg['attributes'].keys())
        attrs_def = {name: {} for name in attr_names}
        # Create the container under the same root
        SpxAttributes(name='attributes', definition=attrs_def, parent=pf.get_root())

        # Should run without error
        try:
            pf.prepare()
            pf.reset()
        except Exception as e:
            self.fail(f"prepare/reset raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
