# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest

import yaml
from copy import deepcopy
from spx_sdk.components import SpxContainer, SpxComponent
from spx_sdk.attributes import SpxAttributes, SpxAttribute
from spx_sdk.actions.actions import Actions, Action
from spx_sdk.logic import Conditions

from spx_sdk.registry import register_class, clear_registry


class CameleonAction(Action):
    def _populate(self, definition):
        pass


class RegularContainer(Conditions):
    pass


class RegularComponent(SpxComponent):
    def _populate(self, definition):
        pass


class TestActionsLoading(unittest.TestCase):

    def setUp(self):
        clear_registry()

        register_class()(SpxComponent)
        register_class()(SpxContainer)
        register_class(name="attributes")(SpxAttributes)
        register_class()(SpxAttribute)
        register_class(name='add')(CameleonAction)
        register_class(name='mul')(CameleonAction)
        register_class(name='sub')(CameleonAction)
        register_class(name='dup')(CameleonAction)
        register_class(name='compute_power')(CameleonAction)
        register_class(name='compute_real_power')(CameleonAction)
        register_class(name='status_check')(CameleonAction)
        register_class(name='set')(CameleonAction)
        register_class(name='function')(CameleonAction)
        register_class(name='custom')(CameleonAction)

        register_class(name='conditions')(RegularContainer)

        register_class(name='if')(RegularComponent)
        register_class(name='when')(RegularComponent)
        register_class(name='case')(RegularComponent)
        register_class(name='ifelse')(RegularComponent)
        register_class(name='if_else')(RegularComponent)
        register_class(name='condition')(RegularComponent)
        register_class(name='else')(RegularComponent)

    def test_basic_yaml_loading_creates_actions(self):
        yaml_str = """
actions:
  - mul: "#ext(prod)"
    x: "#attr(x)"
    y: "#attr(y)"
"""
        data = yaml.safe_load(yaml_str)
        acts = Actions(name='acts', definition=data['actions'])

        # Should create exactly one action named 'mul'
        self.assertEqual(len(acts), 1)
        self.assertIn('mul', acts)

        action = acts['mul']
        self.assertIsInstance(action, Action)
        self.assertEqual(action.definition["function"], 'mul')
        self.assertEqual(action.definition["output"], '#ext(prod)')
        self.assertEqual(action.definition['x'], '#attr(x)')
        self.assertEqual(action.definition['y'], '#attr(y)')
        # self.assertEqual(action.definition["params"], {'x': '#attr(x)', 'y': '#attr(y)'})


class TestRegisteredActionSubclass(unittest.TestCase):
    def test_custom_action_subclass_used(self):
        # Dynamically register a custom Action subclass
        @register_class(name='custom')
        class CustomAction(Action):
            def _populate(self, definition):
                pass

        yaml_str = """
actions:
  - custom: "#ext(out)"
    inp: "#attr(inp)"
"""
        data = yaml.safe_load(yaml_str)
        acts = Actions(name='acts2', definition=data['actions'])

        action = acts['custom']
        self.assertIsInstance(action, CustomAction)


class TestActionsDefinitionInvalid(unittest.TestCase):
    def test_invalid_definition_raises(self):
        with self.assertRaises(ValueError):
            Actions(name='acts3', definition={'not': 'a list'})


# Additional complex structure tests
class TestActionsComplexStructures(unittest.TestCase):
    def setUp(self):
        clear_registry()

        register_class()(SpxComponent)
        register_class()(SpxContainer)
        register_class(name="attributes")(SpxAttributes)
        register_class()(SpxAttribute)
        register_class(name="actions")(Actions)
        register_class(name='add')(CameleonAction)
        register_class(name='mul')(CameleonAction)
        register_class(name='sub')(CameleonAction)
        register_class(name='dup')(CameleonAction)
        register_class(name='compute_power')(CameleonAction)
        register_class(name='compute_real_power')(CameleonAction)
        register_class(name='status_check')(CameleonAction)
        register_class(name='set')(CameleonAction)
        register_class(name='function')(CameleonAction)
        register_class(name='custom')(CameleonAction)

        register_class(name='conditions')(RegularContainer)

        register_class(name='if')(RegularComponent)
        register_class(name='when')(RegularComponent)
        register_class(name='case')(RegularComponent)
        register_class(name='ifelse')(RegularComponent)
        register_class(name='if_else')(RegularComponent)
        register_class(name='condition')(RegularComponent)
        register_class(name='else')(RegularComponent)

    def test_registered_and_default_action_mix(self):
        # Register a custom Action subclass for 'add'
        @register_class(name='add')
        class AddAction(Action):
            def _populate(self, definition):
                pass

        yaml_str = """
actions:
  - add: "#ext(sum)"
    a: "#attr(a)"
    b: "#attr(b)"
  - mul: "#ext(prod)"
    x: "#attr(x)"
    y: "#attr(y)"
"""
        data = yaml.safe_load(yaml_str)
        acts = Actions(name='acts_complex', definition=data['actions'])

        # 'add' should use AddAction, 'mul' falls back to base Action
        add_act = acts['add']
        mul_act = acts['mul']
        self.assertIsInstance(add_act, AddAction)
        self.assertIsInstance(mul_act, Action)
        # Params should be correctly parsed
        self.assertEqual(add_act.definition['a'], '#attr(a)')
        self.assertEqual(add_act.definition['b'], '#attr(b)')
        self.assertEqual(mul_act.definition['x'], '#attr(x)')
        self.assertEqual(mul_act.definition['y'], '#attr(y)')

    def test_empty_entries_are_skipped(self):
        yaml_str = """
actions:
  - {}
  - sub: "#ext(diff)"
    x: "#attr(x)"
    y: "#attr(y)"
"""
        data = yaml.safe_load(yaml_str)
        acts = Actions(name='acts_skip', definition=data['actions'])

        # The empty dict should be skipped, only 'sub' remains
        self.assertEqual(len(acts), 1)
        self.assertIn('sub', acts)

    def test_multi_output_parsing(self):
        yaml_str = """
actions:
  - dup:
      - "#ext(a)"
      - "#ext(b)"
    x: "#attr(x)"
"""
        data = yaml.safe_load(yaml_str)
        acts = Actions(name='acts_multi', definition=data['actions'])

        # Should create an action named 'dup'
        self.assertEqual(len(acts), 1)
        self.assertIn('dup', acts)

        action = acts['dup']
        self.assertIsInstance(action, Action)
        # Output_ref should be parsed as list of strings
        self.assertEqual(action.definition["output"], ["#ext(a)", "#ext(b)"])
        self.assertEqual(action.definition["function"], 'dup')
        # Params should be correctly parsed
        self.assertEqual(action.definition['x'], '#attr(x)')

    def test_duplicate_action_names_get_unique_keys(self):
        # Two actions with the same name should get unique keys in the container
        yaml_str = """
actions:
  - set: "#ext(status)"
    value: "FAULT"
  - set: "#ext(error)"
    value: true
"""
        data = yaml.safe_load(yaml_str)
        acts = Actions(name='acts_dup', definition=data['actions'])

        # There should be two entries with distinct keys
        self.assertEqual(len(acts), 2)
        keys = list(acts.children.keys())
        self.assertNotEqual(keys[0], keys[1],
                            "Actions with identical names must be disambiguated in keys")

        # First key should be the original name, second should be suffixed
        self.assertEqual(keys[0], 'set')
        self.assertEqual(keys[1], 'set_1')

        # Verify first and second action outputs and parameter values
        act1 = acts[keys[0]]
        act2 = acts[keys[1]]
        self.assertEqual(act1.definition["output"], "#ext(status)")
        self.assertEqual(act2.definition["output"], "#ext(error)")

        # Parameter 'value' extracted correctly (note: parsed by Action.params)
        self.assertEqual(act1.definition['value'], 'FAULT')
        self.assertEqual(act2.definition['value'], True)


class TestDeviceWithActions(unittest.TestCase):

    def setUp(self):
        clear_registry()

        register_class()(SpxComponent)
        register_class()(SpxContainer)
        register_class(name="attributes")(SpxAttributes)
        register_class()(SpxAttribute)
        register_class(name="actions")(Actions)
        register_class(name='add')(CameleonAction)
        register_class(name='mul')(CameleonAction)
        register_class(name='sub')(CameleonAction)
        register_class(name='dup')(CameleonAction)
        register_class(name='compute_power')(CameleonAction)
        register_class(name='compute_real_power')(CameleonAction)
        register_class(name='status_check')(CameleonAction)
        register_class(name='set')(CameleonAction)
        register_class(name='function')(CameleonAction)
        register_class(name='custom')(CameleonAction)

        register_class(name='conditions')(RegularContainer)

        register_class(name='if')(RegularComponent)
        register_class(name='when')(RegularComponent)
        register_class(name='case')(RegularComponent)
        register_class(name='ifelse')(RegularComponent)
        register_class(name='if_else')(RegularComponent)
        register_class(name='condition')(RegularComponent)
        register_class(name='else')(RegularComponent)

    def test_motor_device_actions(self):
        yaml_str = """
device:
  name: Motor
  attributes:
    voltage: 12
    current: 3
    power: 30
    apparent_power: 36
    status: "OK"
  actions:
    - compute_real_power: "#ext(power)"
      voltage: "#attr(voltage)"
      current: "#attr(current)"
    - status_check: "#ext(status)"
      threshold: "#attr(voltage)"
    - function: "#ext(apparent_power)"
      call: "numpy.multiply(#attr(voltage), #attr(current))"
    - conditions:
        - if: "#attr(apparent_power) > 100"
          set: "#ext(status) = 'Overload'"
        - else:
          actions:
            - set: "#ext(status)"
              value: "Normal"
"""
        data = yaml.safe_load(yaml_str)

        # Build root component and children
        root = SpxContainer(name='root', definition=deepcopy(data['device']), type=SpxComponent)
        # Create attributes under the root
        acts: Actions = root["actions"]

        # Validate action children
        self.assertIn('compute_real_power', acts)
        self.assertIn('status_check', acts)
        self.assertIn('function', acts)
        self.assertIn('conditions', acts)
        self.assertEqual(len(acts), 4)

        self.assertIsInstance(acts['conditions'], RegularContainer)

        compute_act: CameleonAction = acts['compute_real_power']
        status_act: CameleonAction = acts['status_check']
        function_act: CameleonAction = acts['function']
        conditions_act: RegularComponent = acts['conditions']

        # Assertions for compute_power action
        self.assertIsInstance(compute_act, CameleonAction)
        self.assertEqual(compute_act.definition["function"], 'compute_real_power')
        self.assertEqual(compute_act.definition["output"], '#ext(power)')
        self.assertEqual(compute_act.definition['voltage'], '#attr(voltage)')
        self.assertEqual(compute_act.definition['current'], '#attr(current)')

        # Assertions for status_check action
        self.assertIsInstance(status_act, CameleonAction)
        self.assertEqual(status_act.definition["function"], 'status_check')
        self.assertEqual(status_act.definition["output"], '#ext(status)')
        self.assertEqual(status_act.definition['threshold'], '#attr(voltage)')

        # Assertions for function action
        self.assertIsInstance(function_act, CameleonAction)
        self.assertEqual(function_act.definition["function"], 'function')
        self.assertEqual(function_act.definition["output"], '#ext(apparent_power)')
        self.assertEqual(function_act.definition['call'], 'numpy.multiply(#attr(voltage), #attr(current))')

        # Assertions for conditions action
        self.assertIsInstance(conditions_act, RegularContainer)
        self.assertEqual(len(conditions_act.children), 2)
        self.assertIsInstance(conditions_act.get_children_list()[0], RegularComponent)
        self.assertIsInstance(conditions_act.get_children_list()[1], RegularComponent)


if __name__ == '__main__':
    unittest.main()
