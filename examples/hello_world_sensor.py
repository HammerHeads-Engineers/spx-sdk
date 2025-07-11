# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import yaml
import numpy as np
from spx_sdk.model import Model

yaml_str = """
  attributes:
    temperature: 25.0
  actions:
    - function: $ext(temperature)
      call: $in(temperature) + (100 - $in(temperature)) * (1 - 0.945 ** $(.timer.time))
"""
data = yaml.safe_load(yaml_str)

sensor = Model(name='Model', definition=data)
sensor.prepare()

for t in np.arange(0, 60.1, 0.1):  # 0.1s ticks up to 60s
    sensor["timer"]["time"] = t
    sensor.run()
    print(f"{t:5.1f}s -> {sensor['attributes']['temperature']['external_value']:.2f}°C")


from spx_sdk.registry import register_class
from spx_sdk.actions.action import Action


@register_class(name="heat_loss")
class HeatLoss(Action):
    """
    Newton cooling: ΔT_loss = -k * (T - T_ambient)

    Params in YAML:
      T        – current temperature (input)
      k        – cooling coefficient (1/s)
      ambient  – ambient temperature (°C)
    """
    def _populate(self, definition):
        # pull in defaults first
        self.T = 25.0
        self.k = 0.005
        self.ambient = 20.0
        return super()._populate(definition)

    def run(self, **kwargs):
        super().run()
        # resolve inputs now
        # compute cooling
        delta = -self.k * (self.T - self.ambient)
        return self.write_outputs(self.T + delta)


yaml_str_hl = """
  attributes:
    temperature: 25.0
  actions:
    - function: $ext(temperature)
      call: $in(temperature) + (100 - $in(temperature)) * (1 - 0.945 ** $(.timer.time))
    - heat_loss: $ext(temperature)
      T:       $ext(temperature)
      k:       0.1
      ambient: 15.0
"""

model_def = yaml.safe_load(yaml_str_hl)
kettle = Model(name="Kettle", definition=model_def)
kettle.prepare()
for t in np.arange(0, 60.1, 0.1):
    kettle["timer"]["time"] = t
    kettle.run()
    print(f"{t:5.1f}s → {kettle['attributes']['temperature']['external_value']:.2f}°C")
