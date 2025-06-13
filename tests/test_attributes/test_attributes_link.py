# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import sys
import os
from copy import deepcopy
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from unittest import TestCase, main
from spx_sdk.attributes import SpxAttributes, SpxAttribute


attributes_data = {
    "Attributes": {
        "Voltage": {
            "unit": "V",
            "type": "float"
        },
        "Current": {
            "unit": "A",
            "type": "float",
            "default": 1.3
        },
        "Power": {
            "unit": "W",
            "type": "float"
        },
        "VoltageSetpoint": {
            "type": "float",
            "default": 1343.7
        },
        "PowerOn": {
            "unit": "boolean",
            "type": "bool",
            "default": False
        }
    },
}


class PowerSupply:
    def __init__(self):
        self._voltage = -2.7
        self._current = 2.0
        self._voltage_setpoint = 1333.0
        self._power_on = False

    def run(self):
        pass

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value

    @property
    def voltage(self):
        if self._power_on:
            self._voltage = self._voltage_setpoint
        return self._voltage

    @voltage.setter
    def voltage(self, value):
        self._voltage = value

    def set_voltage_setpoint(self, value):
        self._voltage_setpoint = value

    def get_voltage_setpoint(self):
        return self._voltage_setpoint

    @property
    def power(self):
        if not self._power_on:
            return 0.0
        return self._current * self._voltage

    @property
    def power_on(self):
        return self._power_on

    @power_on.setter
    def power_on(self, value):
        self._power_on = value


class Test_Attributes(TestCase):
    def test_attributes_init(self):
        attributes = SpxAttributes(name="attributes", definition=deepcopy(attributes_data["Attributes"]))
        self.assertIsInstance(attributes, SpxAttributes)

        self.assertEqual(len(attributes), 5)
        self.assertEqual(attributes.internal["Power"], 0.0)
        self.assertEqual(attributes.internal["PowerOn"], False)
        self.assertEqual(attributes.internal["Current"], 1.3)
        self.assertEqual(attributes.internal["VoltageSetpoint"], 1343.7)

        attributes.internal["PowerOn"] = True
        self.assertEqual(attributes.internal["PowerOn"], True)

        attributes.internal["Current"] = 5.77
        self.assertEqual(attributes.internal["Current"], 5.77)

        attributes.internal["VoltageSetpoint"] = 3137.432
        self.assertEqual(attributes.internal["VoltageSetpoint"], 3137.432)


class Test_Attribute(TestCase):
    def test_attribute_init(self):
        attributes = SpxAttributes(name="attributes", definition=deepcopy(attributes_data["Attributes"]))
        attribute: SpxAttribute = attributes.get("Power")
        attribute.external_value = 11.3
        self.assertEqual(attribute.external_value, 11.3)

        attribute.internal_value = 11.7
        self.assertEqual(attribute.internal_value, 11.7)

        power_supply = PowerSupply()
        power_supply.power_on = True
        attribute.link_to_internal_property(power_supply, "power")
        self.assertEqual(attribute.internal_value, -5.4)

        attribute_voltage: SpxAttribute = attributes.get("Voltage")
        attribute_current: SpxAttribute = attributes.get("Current")

        attribute_voltage.link_to_internal_property(power_supply, "voltage")
        attribute_current.link_to_internal_property(power_supply, "current")

        self.assertEqual(attribute.internal_value, 0.0)

        attribute_voltage.internal_value = 2
        self.assertEqual(attribute.internal_value, 2.6)

        attribute_voltage_setpoint: SpxAttribute = attributes.get("VoltageSetpoint")
        attribute_voltage_setpoint.link_to_internal_func(power_supply, "get_voltage_setpoint", "set_voltage_setpoint")

        self.assertEqual(attribute_voltage_setpoint.internal_value, 1343.7)
        self.assertEqual(attribute_voltage.internal_value, 1343.7)

        attribute_power_on: SpxAttribute = attributes.get("PowerOn")
        attribute_power_on.link_to_internal_property(power_supply, "power_on")

        self.assertEqual(attribute_power_on.internal_value, False)
        attribute_voltage.internal_value = 15.6
        self.assertEqual(attribute_voltage.internal_value, 15.6)

        attribute_power_on.internal_value = True
        self.assertEqual(attribute_voltage.internal_value, 1343.7)  # Proof that currently internal PowerSupply logic is working

    def test_attribute_internal_external(self):
        attributes = SpxAttributes(name="attributes", definition=deepcopy(attributes_data["Attributes"]))
        self.assertEqual(attributes.internal["Voltage"], 0.0)

        attributes.internal["Voltage"] = 325.8
        self.assertEqual(attributes.internal["Voltage"], 325.8)
        self.assertEqual(attributes.external["Voltage"], 325.8)

        attributes.external["Voltage"] = 100.7
        self.assertEqual(attributes.internal["Voltage"], 325.8)
        self.assertEqual(attributes.external["Voltage"], 100.7)

        attributes.internal["Voltage"] = 123.5
        self.assertEqual(attributes.internal["Voltage"], 123.5)
        self.assertEqual(attributes.external["Voltage"], 123.5)

        attributes.external["Voltage"] = 100.3
        self.assertEqual(attributes.internal["Voltage"], 123.5)
        self.assertEqual(attributes.external["Voltage"], 100.3)
        attributes.prepare()

        self.assertEqual(attributes.internal["Voltage"], 123.5)
        self.assertEqual(attributes.external["Voltage"], 123.5)


if __name__ == "__main__":
    main()
