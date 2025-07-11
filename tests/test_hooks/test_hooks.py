# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest

from spx_sdk.components import SpxComponent
from spx_sdk.hooks.hooks import Hooks
from spx_sdk.registry import register_class
from spx_sdk.attributes import SpxAttributes

_ = SpxAttributes  # Ensure SpxAttributes is registered


@register_class(name="dummy_hook")
class DummyHook(SpxComponent):
    def __init__(self, name, parent=None, definition=None):
        super().__init__(name=name, parent=parent, definition=definition)
        self.invoked = False

    def run(self, *args, **kwargs):
        self.invoked = True
        return True


@register_class(name="another_hook")
class AnotherHook(SpxComponent):
    def __init__(self, name, parent=None, definition=None):
        self.param = None
        super().__init__(name=name, parent=parent, definition=definition)
        self.count = 0

    def run(self, *args, **kwargs):
        self.count += 1
        return True


class TestHooksContainer(unittest.TestCase):
    def setUp(self):
        register_class(name="another_hook")(AnotherHook)
        register_class(name="dummy_hook")(DummyHook)
        # Silence logging
        import logging
        logging.getLogger().setLevel(logging.CRITICAL)
        self.root = SpxComponent(name="root")

    def test_single_string_entry_registers_and_triggers(self):
        hooks_def = {"on_run": "dummy_hook"}
        Hooks(name="hooks", definition=hooks_def, parent=self.root)

        hooks = self.root.get_hooks("on_run")
        self.assertEqual(len(hooks), 1)
        hook = hooks[0]
        self.assertIsInstance(hook, DummyHook)
        self.assertFalse(hook.invoked)

        self.root.trigger_hooks("on_run")
        self.assertTrue(hook.invoked)

    def test_list_of_strings_registers_multiple_and_counts(self):
        hooks_def = {"on_update": ["dummy_hook", "another_hook"]}
        Hooks(name="hooks", definition=hooks_def, parent=self.root)

        hooks = self.root.get_hooks("on_update")
        # Should have DummyHook then AnotherHook
        self.assertIsInstance(hooks[0], DummyHook)
        self.assertIsInstance(hooks[1], AnotherHook)

        # Trigger multiple times
        self.root.trigger_hooks("on_update")
        self.assertTrue(hooks[0].invoked)
        self.assertEqual(hooks[1].count, 1)

    def test_dict_entry_with_parameters_passes_to_definition(self):
        custom_def = {"param": 5}
        hooks_def = {"on_custom": {"another_hook": custom_def}}
        Hooks(name="hooks", definition=hooks_def, parent=self.root)

        hooks = self.root.get_hooks("on_custom")
        self.assertEqual(len(hooks), 1)
        hook = hooks[0]
        self.assertIsInstance(hook, AnotherHook)
        self.assertEqual(hook.definition, custom_def)

    def test_duplicate_entries_named_uniquely(self):
        hooks_def = {"on_dup": ["dummy_hook", "dummy_hook"]}
        Hooks(name="hooks", definition=hooks_def, parent=self.root)

        hooks = self.root.get_hooks("on_dup")
        names = [h.name for h in hooks]
        self.assertEqual(names, ["dummy_hook", "dummy_hook_1"])

    def test_invalid_definition_raises(self):
        bad_defs = [
            {"on_err": 123},
            {"on_err": {"a": 1, "b": 2, "c": 3}},  # dict with multiple keys
            {"on_err": [True, "dummy_hook"]},
        ]
        for bd in bad_defs:
            with self.assertRaises(ValueError):
                Hooks(name="hooks", definition=bd, parent=self.root)


if __name__ == '__main__':
    unittest.main()
