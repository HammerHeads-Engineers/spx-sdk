# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest

from spx_sdk.components import SpxComponent
from spx_sdk.attributes.attributes import SpxAttributes
from spx_sdk.actions.actions import Action


class TestActionOutputs(unittest.TestCase):
    def setUp(self):
        # Create a root component and attributes container
        self.root = SpxComponent(name='root')
        # Define two attributes for testing output resolution
        attrs_def = {
            'out1': {},
            'out2': {}
        }
        self.attrs = SpxAttributes(name='attributes',
                                   definition=attrs_def,
                                   parent=self.root)

    def test_single_output_resolution(self):
        # Single output reference: definition must include 'function'
        # and 'output'
        definition = {"function": "act_single", "output": "$attr(out1)"}
        action = Action(name='act_single',
                        parent=self.root,
                        definition=definition)
        # Ensure outputs dict exists and has correct length
        self.assertTrue(hasattr(action, 'outputs'))
        self.assertEqual(len(action.outputs), 1)
        # The resolved attribute instance should be under the key 'out1'
        self.assertIn('out1', action.outputs)
        self.assertEqual(action.outputs['out1'].get(),
                         self.attrs.internal.get('out1'))

    def test_list_output_resolution(self):
        # List of outputs should resolve to multiple attributes
        # (give function name too)
        definition = {
            "function": "act_list",
            "output": ["$external(out1)", "$ext(out2)"]
        }
        action = Action(name='act_list',
                        parent=self.root,
                        definition=definition)
        # Ensure outputs dict exists and has correct length
        self.assertTrue(hasattr(action, 'outputs'))
        self.assertEqual(len(action.outputs), 2)
        # Both attributes should be present as keys and
        # map to the correct instances
        self.assertIn('out1', action.outputs)
        self.assertIn('out2', action.outputs)
        self.assertEqual(action.outputs['out1'].get(),
                         self.attrs.external.get('out1'))
        self.assertEqual(action.outputs['out2'].get(),
                         self.attrs.external.get('out2'))

    def test_combined_input_output_resolution(self):
        # Combined inputs/outputs no longer applies: only outputs are resolved
        definition = {
            "function": "act_both",
            "output": ["$attr(out1)", "$attr(out2)"]
        }
        action = Action(name='act_both',
                        parent=self.root,
                        definition=definition)
        # Verify only outputs dict
        self.assertEqual(len(action.outputs), 2)
        self.assertIn('out1', action.outputs)
        self.assertIn('out2', action.outputs)
        self.assertEqual(action.outputs['out1'].get(),
                         self.attrs.internal.get('out1'))
        self.assertEqual(action.outputs['out2'].get(),
                         self.attrs.internal.get('out2'))


if __name__ == '__main__':
    unittest.main()
