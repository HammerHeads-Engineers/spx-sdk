# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
from copy import deepcopy
from spx_sdk.registry import clear_registry, register_class, create_instance
from spx_sdk.logic import Conditions, Condition, IfChain
from spx_sdk.components import SpxComponent, SpxContainer


# Dummy action classes that record when run/prepare are called
@register_class(name="ActionA")
class ActionA(SpxComponent):
    def _populate(self, definition):
        self.run_called = False
        self.prepare_called = False
        self.foo = None
        self.baz = None
        self.x = None
        self.else_foo = None
        super()._populate(definition)

    def run(self, *args, **kwargs):
        self.run_called = True
        return super().run(*args, **kwargs)

    def prepare(self, *args, **kwargs):
        self.prepare_called = True
        return super().prepare(*args, **kwargs)


@register_class(name="ActionB")
class ActionB(ActionA):
    bar = None
    y = None
    qux = None


class TestConditions(unittest.TestCase):
    def setUp(self):
        # Reset the registry and re-register our classes
        clear_registry()
        # Conditions needs to be registered under both its __name__ and "conditions"
        register_class()(Conditions)
        register_class(name="conditions")(Conditions)
        # Condition registered under multiple aliases:
        for alias in ("if", "when", "case", "ifelse", "if_else", "condition"):
            register_class(name=alias)(Condition)

        register_class()(Condition)
        # Actions are already registered above
        register_class()(ActionA)
        register_class()(ActionB)
        register_class(name="else")(SpxContainer)  # else is an alias for ActionA
        register_class(name="actions")(SpxContainer)
        # Sample definition mixing valid/invalid nodes
        self.definition = [
            {
                "if": "True",
                "actions": [
                    {"ActionA": {"foo": 1}},
                    {"ActionB": {"bar": 2}},
                ],
            },
            {
                "else": None,
                "actions": [
                    {"ActionA": {"baz": 3}},
                ],
            },
            {},            # should be skipped
            "not a dict",  # should be skipped
        ]

        # Instantiate the top‐level Conditions container
        self.conditions = IfChain(name="", parent=None, definition=deepcopy(self.definition))

    def test_populate_children(self):
        # Only two valid dict nodes → two children
        self.assertEqual(len(self.conditions.children), 2)

        # First child is a Condition with definition "True"
        first = self.conditions.get_children_list()[0]
        self.assertIsInstance(first, Condition)
        self.assertEqual(first.definition, "True")

        # Its children should be two actions
        self.assertEqual(len(first.children), 1)
        first_actions = first.get_children_list()[0]
        types = {type(ch) for ch in first_actions.get_children_list()}
        self.assertEqual(types, {ActionA, ActionB})

        # Check definitions on those actions
        defs = [ch.definition for ch in first_actions.get_children_list()]
        self.assertIn({"foo": 1}, defs)
        self.assertIn({"bar": 2}, defs)

        # Second child is the "else" condition
        second = self.conditions.get_children_list()[1]
        self.assertIsInstance(second, SpxContainer)
        self.assertEqual(second.definition, None)
        self.assertEqual(len(second.children), 1)
        self.assertIsInstance(second.get_children_list()[0], SpxContainer)
        second_actions = second.get_children_list()[0]
        self.assertEqual(second_actions.get_children_list()[0].definition, {"baz": 3})

    def test_run_and_prepare_propagation(self):
        # Prepare should call prepare on the first Condition and its actions
        result = self.conditions.prepare()
        self.assertTrue(result)
        first, second = self.conditions.get_children_list()

        # Only the first branch has evaluate=True, so its actions get prepared
        for action in first.get_children_list():
            self.assertEqual(str(action.state), "PREPARED")
        for action in second.get_children_list():
            self.assertNotEqual(str(action.state), "PREPARED")

        # Now run
        result = self.conditions.run()
        self.assertTrue(result)

        for action in first.get_children_list():
            self.assertEqual(str(action.state), "STOPPED")
        for action in second.get_children_list():
            self.assertNotEqual(action.state, "RUNNING")

    def test_condition_evaluate(self):
        # Directly create a Condition instance via registry
        cond = create_instance("if", name="if", parent=None, definition="1 < 2")
        self.assertTrue(cond.evaluate("1 < 2"))
        self.assertFalse(cond.evaluate("1 > 2"))
        # Syntax error or NameError should be caught and return False
        self.assertFalse(cond.evaluate("a < b"))

    def test_empty_or_non_dict_nodes_are_skipped(self):
        # Definitions with only invalid nodes
        empty = Conditions(name="if", parent=None, definition=[{}, [], 123, None])
        self.assertEqual(empty.children, {})

    def test_single_scalar_definition_fallback(self):
        # If definition is not a list, fallback to generic _populate
        # Here we give a dict with a registered class
        cfg = {"ActionA": {"x": 42}, "ActionB": {"y": 99}}
        cont = Conditions(name="if", parent=None, definition=cfg)
        # Should instantiate both ActionA and ActionB under this one Conditions container
        # but since Conditions._populate only handles lists, it will fallback to SpxContainer._populate
        # which for dict will create children named "ActionA" and "ActionB"
        self.assertEqual({type(c) for c in cont.get_children_list()}, {ActionA, ActionB})

    def test_nested_complex_definition(self):
        complex_def = [
            {
                "if": "True",
                "ActionA": {"foo": 1},
                "conditions": [
                    {
                        "when": "False",
                        "ActionB": {"bar": 2},
                        "ActionA": {"baz": 3},
                    }
                ],
                "ActionB": {"qux": 4},
            },
            {
                "else": None,
                "actions": [
                    {"ActionA": {"else_foo": 5}},
                ],
            },
        ]
        conds = IfChain(name="", parent=None, definition=complex_def)

        # Top-level should have two children
        self.assertEqual(len(conds.children), 2)

        top_if = conds.get_children_list()[0]
        self.assertIsInstance(top_if, Condition)
        self.assertEqual(top_if.definition, "True")

        # The top_if should have three children: ActionA, nested Condition, ActionB
        self.assertEqual(len(top_if.children), 3)
        self.assertIsInstance(top_if.get_children_list()[0], ActionA)
        self.assertEqual(top_if.get_children_list()[0].definition, {"foo": 1})

        nested_cond = top_if.get_children_list()[1]
        self.assertIsInstance(nested_cond, Conditions)
        # self.assertEqual(nested_cond.definition, [
        #     {
        #         "when": "False",
        #         "ActionB": {"bar": 2},
        #         "ActionA": {"baz": 3},
        #     }
        # ])

        self.assertIsInstance(top_if.get_children_list()[2], ActionB)
        self.assertEqual(top_if.get_children_list()[2].definition, {"qux": 4})

        # Nested condition has a single Condition child whose own children are the actions
        inner = nested_cond.get_children_list()[0]
        self.assertIsInstance(inner, Condition)
        self.assertEqual(len(inner.children), 2)
        self.assertIsInstance(inner.get_children_list()[0], ActionB)
        self.assertEqual(inner.get_children_list()[0].definition, {"bar": 2})
        self.assertIsInstance(inner.get_children_list()[1], ActionA)
        self.assertEqual(inner.get_children_list()[1].definition, {"baz": 3})

        # The else branch is a Condition with definition None and one ActionA child
        else_branch = conds.get_children_list()[1]
        self.assertIsInstance(else_branch, SpxComponent)
        self.assertEqual(else_branch.definition, None)
        self.assertEqual(len(else_branch.children), 1)
        child = else_branch.get_children_list()[0]
        self.assertIsInstance(child, SpxContainer)
        self.assertEqual(len(child.children), 1)
        self.assertIsInstance(child.get_children_list()[0], ActionA)
        self.assertEqual(child.get_children_list()[0].definition, {"else_foo": 5})

        # Prepare and run
        result_prepare = conds.prepare()
        self.assertTrue(result_prepare)

        self.assertEqual(str(top_if.state), "PREPARED")
        self.assertEqual(str(top_if.get_children_list()[0].state), "PREPARED")
        self.assertEqual(str(top_if.get_children_list()[1].state), "PREPARED")
        self.assertEqual(str(else_branch.state), "INITIALIZED")

        result_run = conds.run()
        self.assertTrue(result_run)

        # After prepare/run, only actions under "True" conditions should be prepared/run
        # top_if is True, nested_cond is False, so only top_if children except nested_cond's children get prepared/run
        # ActionA(foo=1) and ActionB(qux=4) should be prepared/run
        self.assertEqual(str(top_if.state), "STOPPED")
        self.assertEqual(str(top_if.get_children_list()[0].state), "STOPPED")
        self.assertEqual(str(top_if.get_children_list()[1].state), "STOPPED")

        # For the nested condition, its children are actions; all should have prepare_called and run_called as False
        for action in inner.get_children_list():
            self.assertFalse(action.prepare_called)
            self.assertFalse(action.run_called)

        self.assertTrue(top_if.get_children_list()[2].prepare_called)
        self.assertTrue(top_if.get_children_list()[2].run_called)

        # else branch actions should not be prepared/run
        actions_else = else_branch.get_children_list()[0]
        self.assertEqual(str(actions_else.state), "INITIALIZED")
        self.assertEqual(len(actions_else.children), 1)
        self.assertIsInstance(actions_else.get_children_list()[0], ActionA)
        self.assertEqual(actions_else.get_children_list()[0].definition, {"else_foo": 5})
        self.assertFalse(actions_else.get_children_list()[0].prepare_called)
        self.assertFalse(actions_else.get_children_list()[0].run_called)


if __name__ == "__main__":
    unittest.main()
