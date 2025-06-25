import time
import unittest

from spx_sdk.model.polling import SimplePolling
from spx_sdk.components import SpxComponent


class DummyParent(SpxComponent):
    """A simple dummy parent that counts run() calls."""
    def __init__(self):
        super().__init__(name="dummy", parent=None, definition={})
        self.called = 0

    def run(self, *args, **kwargs):
        self.called += 1
        return True


class TestSimplePolling(unittest.TestCase):
    def test_default_interval_and_reset(self):
        """Default interval is 0.1 and reset sets running=False and thread=None."""
        parent = DummyParent()
        poll = SimplePolling(name="poll", parent=parent, definition={})
        # After populate and reset
        self.assertEqual(poll.interval, 0.1)
        self.assertFalse(poll.running)
        self.assertIsNone(poll.thread)

        # Change definition and reset again
        poll.definition["interval"] = 0.5
        poll.reset()
        self.assertEqual(poll.interval, 0.5)

    def test_start_stop_disabled(self):
        """If polling is disabled, start() returns False."""
        parent = DummyParent()
        poll = SimplePolling(name="poll", parent=parent, definition={"interval": 0.01})
        poll.enabled = False
        self.assertFalse(poll.start())
        self.assertFalse(poll.running)
        # stop should be safe and idempotent
        self.assertTrue(poll.stop())
        self.assertFalse(poll.running)
        self.assertIsNone(poll.thread)

    def test_stop_without_start(self):
        """Calling stop before start returns True and leaves thread None."""
        parent = DummyParent()
        poll = SimplePolling(name="poll", parent=parent, definition={"interval": 0.01})
        # Ensure not running
        self.assertFalse(poll.running)
        # stop should return True and not error
        self.assertTrue(poll.stop())
        self.assertIsNone(poll.thread)
        self.assertFalse(poll.running)

    def test_start_polling_invokes_parent_run(self):
        """Start will spin a thread that periodically calls parent.run()."""
        parent = DummyParent()
        # Use a fast interval
        poll = SimplePolling(name="poll", parent=parent, definition={"interval": 0.01})
        # Start polling
        self.assertTrue(poll.start())
        # Allow a few intervals to pass
        time.sleep(0.05)
        # Stop polling
        self.assertTrue(poll.stop())
        # Parent.run should have been called at least once
        self.assertGreaterEqual(parent.called, 1)

    def test_multiple_start_calls(self):
        """Second start() while running returns False."""
        parent = DummyParent()
        poll = SimplePolling(name="poll", parent=parent, definition={"interval": 0.01})
        self.assertTrue(poll.start())
        self.assertFalse(poll.start(), "Starting again should fail when already running")
        # Clean up
        poll.stop()


if __name__ == "__main__":
    unittest.main()
