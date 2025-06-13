# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
import logging
from dataclasses import dataclass
from spx_sdk.components import SpxComponent, SpxComponentState


# A minimal subclass to observe state transitions and propagation
class TestComponent(SpxComponent):
    foo = None
    bar = None


@dataclass(init=False)
class DataComponent(SpxComponent):
    # dataclass fields to test _populate behavior
    x: int = 0
    y: str = ""


class TestSpxComponent(unittest.TestCase):
    def setUp(self):
        # configure logger to avoid noisy output
        logging.basicConfig(level=logging.CRITICAL)

    def test_initialization_and_populate_non_dataclass(self):
        # Non-dataclass should have arbitrary attributes set from definition
        comp = TestComponent(name="comp1", definition={"foo": 42, "bar": "baz"})
        self.assertEqual(comp.name, "comp1")
        self.assertEqual(comp.state, SpxComponentState.INITIALIZED)
        self.assertTrue(hasattr(comp, "foo"))
        self.assertEqual(comp.foo, 42)
        self.assertEqual(comp.bar, "baz")

    def test_initialization_and_populate_dataclass(self):
        # Dataclass subclass should only populate declared fields
        data = DataComponent(name="data", definition={"x": 5, "y": "hello"})
        self.assertEqual(data.x, 5)
        self.assertEqual(data.y, "hello")
        self.assertEqual(data.state, SpxComponentState.INITIALIZED)

    def test_add_and_remove_child(self):
        parent = TestComponent(name="parent")
        child = TestComponent(name="child")
        parent.add_child(child)
        self.assertIn(child, parent.get_children_list())
        self.assertEqual(child.get_parent(), parent)
        # removing
        parent.remove_child(child)
        self.assertNotIn(child, parent.get_children_list())
        self.assertIsNone(child.get_parent())

    def test_add_child_self_and_invalid(self):
        comp = TestComponent(name="c")
        with self.assertRaises(ValueError):
            comp.add_child(comp)
        with self.assertRaises(ValueError):
            comp.add_child(object())

    def test_get_hierarchy_and_root(self):
        root = TestComponent(name="root")
        c1 = TestComponent(name="c1", parent=root)
        c2 = TestComponent(name="c2", parent=c1)
        hier = root.get_hierarchy()
        self.assertEqual(hier, {
            "name": "root",
            "children": [{
                "name": "c1",
                "children": [{"name": "c2", "children": []}]
            }]
        })
        self.assertIs(c2.get_root(), root)
        self.assertIs(root.get_root(), root)

    def test_prepare_propagation_and_states(self):
        root = TestComponent(name="r1")
        child = TestComponent(name="c1", parent=root)
        result = root.prepare()
        self.assertTrue(result)
        self.assertEqual(root.state, SpxComponentState.PREPARED)
        self.assertEqual(child.state, SpxComponentState.PREPARED)

    def test_run_propagation_and_states(self):
        root = TestComponent(name="r2")
        child = TestComponent(name="c2", parent=root)
        result = root.run()
        self.assertTrue(result)
        self.assertEqual(root.state, SpxComponentState.STOPPED)
        self.assertEqual(child.state, SpxComponentState.STOPPED)

    def test_start_delegates_to_run(self):
        root = TestComponent(name="r3")
        child = TestComponent(name="c3", parent=root)
        result = root.start()
        self.assertTrue(result)
        self.assertEqual(root.state, SpxComponentState.STARTED)
        self.assertEqual(child.state, SpxComponentState.STARTED)

    def test_pause_stop_reset_destroy(self):
        root = TestComponent(name="r4")
        child = TestComponent(name="c4", parent=root)
        # pause
        self.assertTrue(root.pause())
        self.assertEqual(root.state, SpxComponentState.PAUSED)
        self.assertEqual(child.state, SpxComponentState.PAUSED)
        # stop
        self.assertTrue(root.stop())
        self.assertEqual(root.state, SpxComponentState.STOPPED)
        self.assertEqual(child.state, SpxComponentState.STOPPED)
        # reset
        self.assertTrue(root.reset())
        self.assertEqual(root.state, SpxComponentState.RESET)
        self.assertEqual(child.state, SpxComponentState.RESET)
        # destroy
        self.assertTrue(root.destroy())
        self.assertEqual(root.state, SpxComponentState.DESTROYED)
        self.assertEqual(child.state, SpxComponentState.DESTROYED)
        self.assertEqual(root.get_children(), {})
        self.assertEqual(root.get_children_list(), [])
        self.assertIsNone(child.parent)

    def test_repr(self):
        root = TestComponent(name="repr1")
        TestComponent(name="repr2", parent=root)
        rep = repr(root)
        self.assertIn("TestComponent(name='repr1'", rep)
        self.assertIn("children=1", rep)

    def test_getitem_child_access(self):
        root = TestComponent(name="root")
        c1 = TestComponent(name="c1", parent=root)
        c2 = TestComponent(name="c2", parent=root)
        # Access by key
        self.assertIs(root["c1"], c1)
        self.assertIs(root["c2"], c2)

    def test_setitem_replace_child(self):
        root = TestComponent(name="root")
        c1 = TestComponent(name="c1", parent=root)
        c2 = TestComponent(name="c2")
        # Replace c1 with c2 under key 'c1'
        root["c1"] = c2
        self.assertIn("c1", root.get_children())
        self.assertIs(root["c1"], c2)
        self.assertEqual(c2.get_parent(), root)
        self.assertIsNone(c1.get_parent())

        # Setting a non-component should raise ValueError
        with self.assertRaises(ValueError):
            root["c3"] = object()

    def test_get_children_methods(self):
        root = TestComponent(name="root")
        c1 = TestComponent(name="c1", parent=root)
        c2 = TestComponent(name="c2", parent=root)
        # get_children returns dict
        children_dict = root.get_children()
        self.assertIsInstance(children_dict, dict)
        self.assertIn("c1", children_dict)
        self.assertIn("c2", children_dict)
        # get_children_list returns list
        children_list = root.get_children_list()
        self.assertIsInstance(children_list, list)
        self.assertCountEqual(children_list, [c1, c2])

    def test_register_and_get_hooks(self):
        """register_hook should add and dedupe hooks; get_hooks should retrieve them."""
        root = SpxComponent(name="root")
        # Create two dummy hook components
        hook1 = TestComponent(name="h1")
        hook2 = TestComponent(name="h2")
        # Register hook1 twice and hook2 once
        root.register_hook("on_event", hook1)
        root.register_hook("on_event", hook1)
        root.register_hook("on_event", hook2)
        hooks = root.get_hooks("on_event")
        # Should contain each only once and preserve order
        self.assertEqual(hooks, [hook1, hook2])

    def test_trigger_hooks_invokes_run(self):
        """trigger_hooks should call run() on each registered hook."""
        root = SpxComponent(name="root")

        # Define a hook component that records calls
        class RecordingHook(TestComponent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.called = False

            def run(self, *args, **kwargs):
                self.called = True
                return True
        hook = RecordingHook(name="rec", parent=None)
        root.register_hook("on_run", hook)
        # Trigger; should set called=True
        root.trigger_hooks("on_run")
        self.assertTrue(hook.called)

    def test_prepare_triggers_on_prepare(self):
        """prepare() should trigger any registered on_prepare hooks."""
        root = SpxComponent(name="root")
        # Dummy hook to record invocation
        hook = TestComponent(name="hp")
        hook.called = False

        def record_prepare(*args, **kwargs):
            hook.called = True
        hook.run = record_prepare
        root.register_hook("on_prepare", hook)
        # Call prepare
        root.prepare()
        self.assertTrue(hook.called)

    def test_run_triggers_on_run(self):
        """run() should trigger any registered on_run hooks."""
        root = SpxComponent(name="root")
        hook = TestComponent(name="hr")
        hook.called = False

        def record_run(*args, **kwargs):
            hook.called = True
        hook.run = record_run
        root.register_hook("on_run", hook)
        root.run()
        self.assertTrue(hook.called)

    def test_start_triggers_on_start(self):
        """start() should trigger any registered on_start hooks."""
        root = TestComponent(name="roott")
        hook = TestComponent(name="hs")
        hook.called = False

        def record_start(*args, **kwargs):
            hook.called = True
        hook.run = record_start
        root.register_hook("on_start", hook)
        root.start()
        self.assertTrue(hook.called)


if __name__ == '__main__':
    unittest.main()
