# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest

from spx_sdk.components import SpxComponent
from spx_sdk.components.component import SpxComponentState


class TestSpxComponentEnable(unittest.TestCase):
    def test_default_enabled_state(self):
        comp = SpxComponent(name='comp')
        # By default, component should be enabled
        self.assertTrue(comp.enabled)
        self.assertTrue(comp._enabled)

    def test_enable_disable_methods(self):
        comp = SpxComponent(name='comp')
        comp.disable()
        self.assertFalse(comp.enabled)
        comp.enable()
        self.assertTrue(comp.enabled)

    def test_enabled_property_setter(self):
        comp = SpxComponent(name='comp')
        comp.enabled = False
        self.assertFalse(comp.enabled)
        comp.enabled = True
        self.assertTrue(comp.enabled)

    def test_lifecycle_methods_noop_when_disabled(self):
        comp = SpxComponent(name='comp')
        # Ensure initial state
        self.assertEqual(comp.state, SpxComponentState.INITIALIZED)

        comp.disable()
        # All lifecycle methods should return False and not change state
        self.assertFalse(comp.prepare())
        self.assertEqual(comp.state, SpxComponentState.INITIALIZED)

        self.assertFalse(comp.run())
        self.assertEqual(comp.state, SpxComponentState.INITIALIZED)

        self.assertFalse(comp.start())
        self.assertEqual(comp.state, SpxComponentState.INITIALIZED)

        self.assertFalse(comp.stop())
        self.assertEqual(comp.state, SpxComponentState.INITIALIZED)

    def test_lifecycle_methods_work_when_enabled(self):
        comp = SpxComponent(name='comp')
        comp.enable()

        # prepare should succeed and update state
        self.assertTrue(comp.prepare())
        self.assertEqual(comp.state, SpxComponentState.PREPARED)

        # run should succeed and update state
        self.assertTrue(comp.run())
        self.assertEqual(comp.state, SpxComponentState.STOPPED)

        # start (alias for run) should also work
        comp.state = SpxComponentState.PREPARED
        self.assertTrue(comp.start())
        self.assertEqual(comp.state, SpxComponentState.STARTED)

        # pause should succeed and update state
        comp.state = SpxComponentState.RUNNING
        self.assertTrue(comp.pause())
        self.assertEqual(comp.state, SpxComponentState.PAUSED)

        # stop should succeed and update state
        comp.state = SpxComponentState.RUNNING
        self.assertTrue(comp.stop())
        self.assertEqual(comp.state, SpxComponentState.STOPPED)


if __name__ == '__main__':
    unittest.main()
