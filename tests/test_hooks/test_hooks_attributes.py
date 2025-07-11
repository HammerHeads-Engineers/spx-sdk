# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
import yaml
import logging

from spx_sdk.components import SpxComponent
from spx_sdk.attributes import SpxAttributes, SpxAttribute
from spx_sdk.registry import register_class, class_registry
from spx_sdk.hooks.hooks import Hooks

_ = SpxAttribute
_ = Hooks

input_data_yaml = """
models:
  TemperatureSensor:
    attributes:
      temperature:
        default: 0.0
        # whenever we set temperature, trigger our “refresh_model” hook
        hooks:
          on_set:
            - refresh_model_X
"""


# 1) Define a “refresh_model” hook that simply records invocations
class RefreshHook(SpxComponent):
    def __init__(self, name, parent=None, definition=None):
        super().__init__(name=name, parent=parent, definition=definition)
        self.fired = False

    def run(self, *args, **kwargs):
        self.fired = True
        return True


class TestAttributeOnSetHook(unittest.TestCase):
    def setUp(self):
        class_registry.clear()  # clear any previous registrations
        # silence all logging noise
        logging.getLogger().setLevel(logging.CRITICAL)
        # root of our component tree:
        self.root = SpxComponent(name="root")
        register_class(name="hooks")(Hooks)
        register_class(name="SpxAttributes")(SpxAttributes)
        register_class()(SpxAttribute)
        register_class(name="refresh_model_X")(RefreshHook)

        # 2) load YAML + create Models → we only care about the attributes section here
        model_def = yaml.safe_load(input_data_yaml)["models"]["TemperatureSensor"]

        # 3) instantiate the attributes container as a child of root
        self.attrs = SpxAttributes(
            name="attributes",
            definition=model_def["attributes"],
            parent=self.root
        )
        # grab both pieces
        self.temp_attr = self.attrs.get("temperature")
        # find our hook instance via the component’s registry:
        hooks = self.temp_attr.get_hooks("on_set")
        # there should be exactly one, the RefreshHook
        self.assertEqual(len(hooks), 1)
        self.hook = hooks[0]
        self.assertIsInstance(self.hook, RefreshHook)

    def test_setting_temperature_triggers_hook(self):
        # initially not fired
        self.assertFalse(self.hook.fired)

        # 4) write to the internal value → this should fire the on_set hook
        self.attrs.internal["temperature"] = 42.0

        self.assertTrue(
            self.hook.fired,
            "Writing to temperature should have triggered the RefreshHook"
        )


if __name__ == "__main__":
    unittest.main()
