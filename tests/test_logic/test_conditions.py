# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest

# adjust import path if your project layout differs
from spx_sdk.logic import IfChain


class DummyChild:
    """
    A fake “condition” node that records whether run/prepare
    was called and returns a preset boolean.
    """
    def __init__(self, return_value):
        self.return_value = return_value
        self.run_called = False
        self.prepare_called = False
        self.last_context = None

    def run(self, *args, context=None, **kwargs):
        self.run_called = True
        self.last_context = context
        return self.return_value

    def prepare(self, *args, context=None, **kwargs):
        self.prepare_called = True
        self.last_context = context
        return self.return_value


class TestConditions(unittest.TestCase):
    def setUp(self):
        # start with an “empty” Conditions container
        # in your code Conditions may take definition/parent args; adjust as needed
        self.conditions = IfChain(name="condition", definition=[], parent=None)

    def test_run_stops_on_first_true(self):
        c1 = DummyChild(False)
        c2 = DummyChild(True)
        c3 = DummyChild(True)
        self.conditions.children = {"c1": c1, "c2": c2, "c3": c3}

        ctx = {'foo': 123}
        result = self.conditions.run(context=ctx)

        self.assertTrue(result)
        # c1 always called
        self.assertTrue(c1.run_called)
        # c2 returns True so called
        self.assertTrue(c2.run_called)
        # c3 should never be called
        self.assertFalse(c3.run_called)
        # context passed through
        self.assertEqual(c1.last_context, ctx)
        self.assertEqual(c2.last_context, ctx)

    def test_run_calls_all_when_none_true(self):
        c1 = DummyChild(False)
        c2 = DummyChild(False)
        self.conditions.children = {"c1": c1, "c2": c2}

        ctx = {'bar': 'xyz'}
        result = self.conditions.run(context=ctx)

        self.assertTrue(result)
        # both should have been called
        self.assertTrue(c1.run_called)
        self.assertTrue(c2.run_called)

    def test_prepare_stops_on_first_true(self):
        c1 = DummyChild(False)
        c2 = DummyChild(True)
        c3 = DummyChild(True)
        self.conditions.children = {"c1": c1, "c2": c2, "c3": c3}

        ctx = {'baz': 0}
        result = self.conditions.prepare(context=ctx)

        self.assertTrue(result)
        self.assertTrue(c1.prepare_called)
        self.assertTrue(c2.prepare_called)
        self.assertFalse(c3.prepare_called)
        self.assertEqual(c1.last_context, ctx)
        self.assertEqual(c2.last_context, ctx)

    def test_prepare_calls_all_when_none_true(self):
        c1 = DummyChild(False)
        c2 = DummyChild(False)
        self.conditions.children = {"c1": c1, "c2": c2}

        ctx = {'qux': 42}
        result = self.conditions.prepare(context=ctx)

        self.assertTrue(result)
        self.assertTrue(c1.prepare_called)
        self.assertTrue(c2.prepare_called)

    def test_no_children_run_and_prepare(self):
        # with no children, both run() and prepare() still return True
        self.conditions.children = {}

        self.assertTrue(self.conditions.run(context={}))
        self.assertTrue(self.conditions.prepare(context={}))


if __name__ == "__main__":
    unittest.main()
