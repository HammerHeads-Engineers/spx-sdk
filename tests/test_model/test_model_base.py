

import unittest
import uuid

from spx_sdk.model.model_base import BaseModel
from spx_sdk.model.timer import SimpleTimer
from spx_sdk.model.polling import SimplePolling


class TestBaseModel(unittest.TestCase):
    def test_uid_is_valid_uuid(self):
        """Each BaseModel instance gets a unique UUID string."""
        model1 = BaseModel(name="m1", definition={})
        model2 = BaseModel(name="m2", definition={})
        # Validate format
        uuid_obj1 = uuid.UUID(model1.uid)
        uuid_obj2 = uuid.UUID(model2.uid)
        self.assertEqual(str(uuid_obj1), model1.uid)
        self.assertEqual(str(uuid_obj2), model2.uid)
        # Ensure uniqueness
        self.assertNotEqual(model1.uid, model2.uid)

    def test_timer_and_polling_children_exist(self):
        """BaseModel must always have 'timer' and 'polling' children of correct types."""
        model = BaseModel(name="m", definition={})
        children = model.get_children()
        self.assertIn("timer", children)
        self.assertIn("polling", children)
        self.assertIsInstance(children["timer"], SimpleTimer)
        self.assertIsInstance(children["polling"], SimplePolling)

    def test_custom_timer_and_polling_config(self):
        """Timer and Polling should use provided definitions for interval/resolution."""
        defs = {"timer": {"resolution": 0.25}, "polling": {"interval": 0.2}}
        model = BaseModel(name="m", definition=defs)
        timer = model.get_children()["timer"]
        polling = model.get_children()["polling"]
        self.assertEqual(timer.resolution, 0.25)
        self.assertFalse(timer.running)
        self.assertEqual(polling.interval, 0.2)

    def test_other_definition_keys_ignored(self):
        """Any keys other than 'timer' or 'polling' in definition should not create children."""
        defs = {"foo": {}, "timer": {}, "polling": {}}
        model = BaseModel(name="m", definition=defs)
        children = model.get_children()
        self.assertIn("foo", children)
        self.assertIn("timer", children)
        self.assertIn("polling", children)


if __name__ == "__main__":
    unittest.main()
