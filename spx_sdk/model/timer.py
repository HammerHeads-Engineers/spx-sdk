# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import time
from typing import Dict, Any

from spx_sdk.registry import register_class
from spx_sdk.components import SpxComponent


@register_class(name="simple_timer")
class SimpleTimer(SpxComponent):
    """SimpleTimer component that measures elapsed time with configurable resolution."""

    def _populate(self, definition: Dict[str, Any]) -> None:
        self.resolution = definition.get("resolution", None)
        self.reset()

    def reset(self) -> bool:
        self.running = False
        self.start_time = 0.0
        self.timer = 0.0
        return True

    def start(self) -> bool:
        if not self.running:
            self.start_time = time.time()
            self.running = True
            return True
        return False

    def stop(self) -> bool:
        if self.running:
            self.timer = time.time() - self.start_time
            self.running = False
            return True
        return False

    def elapsed(self) -> float:
        if self.running:
            return time.time() - self.start_time
        return self.timer

    def is_running(self) -> bool:
        return self.running

    @property
    def time(self) -> float:
        elapsed = self.elapsed()
        if self.resolution:
            elapsed = round(elapsed / self.resolution) * self.resolution
        return elapsed

    @time.setter
    def time(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("time must be a numeric value")
        if self.running:
            self.stop()
        self.timer = float(value)
