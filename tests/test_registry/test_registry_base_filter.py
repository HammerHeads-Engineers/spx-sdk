# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import unittest
from spx_sdk.registry import (
    class_registry,
    clear_registry,
    register_class,
    get_classes_by_base,
    get_class_names_by_base,
)


class TestRegistryBaseFilter(unittest.TestCase):
    def setUp(self):
        # start each test with a clean registry
        clear_registry()

        # define a small inheritance hierarchy for testing
        class BaseA:
            pass

        class SubB(BaseA):
            pass

        class SubC(BaseA):
            pass

        class SubD(SubB):
            pass

        # register them in the global registry
        register_class()(BaseA)
        register_class()(SubB)
        register_class()(SubC)
        register_class()(SubD)

        # store for reference
        self.BaseA = BaseA
        self.SubB = SubB
        self.SubC = SubC
        self.SubD = SubD

    def test_get_classes_by_base_hits(self):
        # SubB and SubC inherit directly from BaseA
        result = get_classes_by_base("BaseA")
        # should contain exactly SubB and SubC
        self.assertCountEqual(result.keys(), ["SubB", "SubC", "SubD"])
        self.assertIs(result["SubB"], self.SubB)
        self.assertIs(result["SubC"], self.SubC)
        self.assertIs(result["SubD"], self.SubD)

    def test_get_class_names_by_base_hits(self):
        names = get_class_names_by_base("BaseA")
        self.assertCountEqual(names, ["SubB", "SubC"])

    def test_deeper_inheritance_not_included(self):
        # SubD inherits from SubB, not directly from BaseA
        names = get_class_names_by_base("BaseA")
        # SubD should not appear, only direct children
        self.assertNotIn("SubD", names)

    def test_base_object_includes_direct_object_subclasses(self):
        # BaseA was registered with base_class 'object'
        # so get_classes_by_base("object") should include BaseA
        result = get_classes_by_base("object")
        self.assertIn("BaseA", result)
        self.assertIs(result["BaseA"], self.BaseA)

    def test_no_such_base_returns_empty(self):
        # asking for a base_class_name never registered should give empty
        self.assertEqual(get_classes_by_base("NonExistent"), {})
        self.assertEqual(get_class_names_by_base("NonExistent"), [])

    def test_case_sensitive(self):
        # base_class_name matching is case-sensitive
        self.assertEqual(get_classes_by_base("basea"), {})
        self.assertEqual(get_class_names_by_base("basea"), [])

    def test_registry_state_untouched(self):
        # ensure class_registry itself still has our four entries
        self.assertCountEqual(list(class_registry.keys()),
                              ["BaseA", "SubB", "SubC", "SubD"])


if __name__ == "__main__":
    unittest.main()
