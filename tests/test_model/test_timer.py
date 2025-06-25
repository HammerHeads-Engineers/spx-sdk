

import time
import unittest

from spx_sdk.model.timer import SimpleTimer


class TestSimpleTimer(unittest.TestCase):
    def test_reset_initial_state(self):
        """After reset, timer should be zero and not running."""
        timer = SimpleTimer(name="t", definition={})
        # reset called in populate
        self.assertFalse(timer.is_running())
        self.assertEqual(timer.elapsed(), 0.0)
        self.assertEqual(timer.time, 0.0)

    def test_start_and_stop(self):
        """Start should set running=True, stop should capture elapsed time."""
        timer = SimpleTimer(name="t", definition={})
        # Start the timer
        started = timer.start()
        self.assertTrue(started)
        self.assertTrue(timer.is_running())
        # Sleep a bit
        time.sleep(0.02)
        # Stop the timer
        stopped = timer.stop()
        self.assertTrue(stopped)
        self.assertFalse(timer.is_running())
        elapsed_after = timer.elapsed()
        self.assertGreater(elapsed_after, 0.0)
        # Subsequent stop returns False and does not change timer
        prev = timer.elapsed()
        self.assertFalse(timer.stop())
        self.assertEqual(timer.elapsed(), prev)

    def test_start_idempotent(self):
        """Starting an already running timer returns False."""
        timer = SimpleTimer(name="t", definition={})
        self.assertTrue(timer.start())
        self.assertFalse(timer.start(), "Second start should return False")
        timer.stop()

    def test_elapsed_while_running(self):
        """elapsed() should increase while timer is running."""
        timer = SimpleTimer(name="t", definition={})
        timer.start()
        val1 = timer.elapsed()
        time.sleep(0.01)
        val2 = timer.elapsed()
        self.assertGreater(val2, val1)
        timer.stop()

    def test_time_property_with_resolution(self):
        """time property should round elapsed according to resolution."""
        # Use a resolution of 0.05 seconds
        timer = SimpleTimer(name="t", definition={"resolution": 0.05})
        # Manually set timer value via setter
        timer.time = 0.12  # setter should assign timer=0.12
        # time property should round: 0.12/0.05 = 2.4 → round(2.4)=2 → 2*0.05 = 0.1
        self.assertAlmostEqual(timer.time, 0.1)
        # Non-numeric setter raises
        with self.assertRaises(ValueError):
            timer.time = "invalid"

    def test_time_setter_stops_running(self):
        """Setting time while running should stop the timer."""
        timer = SimpleTimer(name="t", definition={})
        timer.start()
        self.assertTrue(timer.is_running())
        # setting time stops it
        timer.time = 1.23
        self.assertFalse(timer.is_running())
        self.assertAlmostEqual(timer.elapsed(), 1.23)
        self.assertAlmostEqual(timer.time, 1.23)


if __name__ == "__main__":
    unittest.main()
