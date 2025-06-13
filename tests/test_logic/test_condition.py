# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
from spx_sdk.registry import (
    register_class,
    clear_registry,
    create_instance,
)
from spx_sdk.components import SpxComponent
from spx_sdk.logic.conditions import Condition


class DummyChild(SpxComponent):
    """A child that records whether its prepare() or run() was invoked."""
    def __init__(self, name: str, *, parent=None):
        super().__init__(name=name, parent=parent, definition=None)
        self.did_prepare = False
        self.did_run = False

    def prepare(self, *args, **kwargs):
        self.did_prepare = True
        return True

    def run(self, *args, **kwargs):
        self.did_run = True
        return True


class TestCondition(unittest.TestCase):
    def setUp(self):
        # Wipe out any previous registrations
        clear_registry()

        # Re‐register our Condition under all its aliases:
        register_class(name="if")(Condition)
        register_class(name="when")(Condition)
        register_class(name="case")(Condition)
        register_class(name="ifelse")(Condition)
        register_class(name="if_else")(Condition)
        register_class(name="condition")(Condition)
        register_class()(Condition)

    def test_evaluate_valid(self):
        cond = Condition(name="condition", definition="2+3==5")
        self.assertTrue(cond.evaluate("2+3==5"))

    def test_evaluate_false(self):
        cond = Condition(name="condition", definition="2+3==6")
        self.assertFalse(cond.evaluate("2+3==6"))

    def test_evaluate_exception_returns_false(self):
        # nonsense Python should be caught
        cond = Condition(name="condition", definition="foo bar")
        self.assertFalse(cond.evaluate("foo bar"))

    def test_run_skipped_when_false(self):
        cond = Condition(name="condition", definition="1>2")
        child = DummyChild(name="child", parent=cond)
        result = cond.run()
        self.assertFalse(result, "run() should return False if condition fails")
        self.assertFalse(child.did_run, "Child.run() should not be called when condition fails")

    def test_run_propagates_when_true(self):
        cond = Condition(name="condition", definition="3>2")
        child = DummyChild(name="child", parent=cond)
        result = cond.run()
        self.assertTrue(result, "run() should return True if condition passes")
        self.assertTrue(child.did_run, "Child.run() should be called when condition passes")

    def test_prepare_skipped_when_false(self):
        cond = Condition(name="condition", definition="0>1")
        child = DummyChild(name="child", parent=cond)
        result = cond.prepare()
        self.assertFalse(result, "prepare() should return False if condition fails")
        self.assertFalse(child.did_prepare, "Child.prepare() should not be called when condition fails")

    def test_prepare_propagates_when_true(self):
        cond = Condition(name="condition", definition="5>1")
        child = DummyChild(name="child", parent=cond)
        result = cond.prepare()
        self.assertTrue(result, "prepare() should return True if condition passes")
        self.assertTrue(child.did_prepare, "Child.prepare() should be called when condition passes")

    def test_aliases_all_create_condition(self):
        """Ensure create_instance works for each registered alias."""
        for alias in ("if", "when", "case", "ifelse", "if_else", "condition", "Condition"):
            inst = create_instance(alias, name="condition", definition={"condition": "True"})
            self.assertIsInstance(inst, Condition, f"Alias {alias!r} should produce a Condition")

    # def test_missing_definition_dict_raises_on_load(self):
    #     # If no 'condition' key in definition, SpxContainer.load will try to
    #     # instantiate every key; here there's none, so children stay empty.
    #     cond = Condition(name="condition", definition={})
    #     self.assertFalse(hasattr(cond, "condition"), "No .condition attribute should be set")
    #     # run/prepare rely on self.condition; accessing it would be AttributeError
    #     with self.assertRaises(AttributeError):
    #         _ = cond.condition
    #     # run/prepare should see no .condition and thus raise
    #     with self.assertRaises(AttributeError):
    #         cond.run()
    #     with self.assertRaises(AttributeError):
    #         cond.prepare()


if __name__ == "__main__":
    unittest.main()
