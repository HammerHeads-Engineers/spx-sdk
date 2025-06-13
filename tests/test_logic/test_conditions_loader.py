# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
from spx_sdk.registry import register_class, clear_registry
from spx_sdk.components import SpxComponent, SpxContainer
from spx_sdk.logic.conditions import Conditions


class TestConditionsLoader(unittest.TestCase):
    def setUp(self):
        # reset registry before each test
        clear_registry()

        # register our Conditions class under both 'conditions' and 'Conditions'
        register_class(name="conditions")(Conditions)
        register_class()(Conditions)

        # Define stub condition classes
        @register_class(name="if")
        class IfCondition(SpxComponent):
            pass

        @register_class(name="ifelse")
        class IfElseCondition(SpxComponent):
            pass

        @register_class(name="else")
        class ElseCondition(SpxComponent):
            pass

        # Define stub action classes
        @register_class(name="ActionA")
        class ActionA(SpxComponent):
            foo = None

        @register_class(name="ActionB")
        class ActionB(SpxComponent):
            bar = None
            baz = None

        @register_class(name="actions")
        class Actions(SpxContainer):
            pass

    def test_populate_builds_conditions_and_actions(self):
        """
        Given a list of dicts, each with a single condition key and an 'actions' list,
        Conditions._populate should create condition instances with nested action children.
        """
        definition = [
            {
                "if": "x < y",
                "ActionA": {"foo": 1},
                "ActionB": {"bar": 2}
            },
            {
                "else": None,
                "actions": [
                    {"ActionB": {"baz": 3}}
                ]
            },
            # a node that's not a non-empty dict should be skipped
            {},
            "not a dict",
        ]

        # instantiate via create_instance to get correct name lookup
        cond_container = Conditions(name="conditions", parent=None, definition=definition)

        # we expect 2 real children (the {} and the string are skipped)
        self.assertEqual(len(cond_container.children), 2)

        # first child: IfCondition
        first = cond_container.get_children_list()[0]
        self.assertEqual(first.__class__.__name__, "IfCondition")
        self.assertEqual(first.definition, "x < y")
        # its children should be two action instances
        self.assertEqual(len(first.children), 2)
        self.assertEqual(first.get_children_list()[0].__class__.__name__, "ActionA")
        self.assertEqual(first.get_children_list()[0].definition, {"foo": 1})
        self.assertEqual(first.get_children_list()[1].__class__.__name__, "ActionB")
        self.assertEqual(first.get_children_list()[1].definition, {"bar": 2})

        # second child: ElseCondition
        second = cond_container.get_children_list()[1]
        self.assertEqual(second.__class__.__name__, "ElseCondition")
        self.assertEqual(second.definition, None)
        # its children should be one ActionB
        self.assertEqual(len(second.children), 1)
        self.assertEqual(second.get_children_list()[0].__class__.__name__, "Actions")
        act_b = second.get_children_list()[0].get_children_list()[0]
        self.assertEqual(act_b.definition, {"baz": 3})


if __name__ == "__main__":
    unittest.main()
