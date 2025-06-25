# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import time
import threading
import logging
from typing import Any, Dict

from spx_sdk.registry import register_class
from spx_sdk.components import SpxComponent


@register_class(name="simple_polling")
class SimplePolling(SpxComponent):
    """
    SimplePolling component that periodically invokes its parent component's run() method
    at a fixed interval.
    Configuration key:
      - interval (float): sleep interval in seconds between polls (default 0.1)
    """
    def _populate(self, definition: Dict[str, Any]) -> None:
        """
        Initialize interval and state from definition.
        """
        # Store definition
        self.definition = definition or {}
        # Initialize polling parameters
        self.reset()

    def reset(self, *args, **kwargs) -> bool:
        """
        Initialize or reinitialize polling parameters.
        """
        self.interval = self.definition.get("interval", 0.1)
        self.running = False
        self.thread = None
        return True

    def start(self, *args, **kwargs) -> bool:
        if not self._enabled:
            self.logger.debug(f"Component {self.name} is disabled; skipping start")
            return False
        if self.running:
            logging.warning("Polling is already running.")
            return False
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return True

    def run(self, *args, **kwargs):
        """
        Hook into parent.run() loop; does nothing by default.
        """
        return True

    def stop(self, *args, **kwargs) -> bool:
        """
        Stop the polling loop and wait for thread to finish.
        """
        self.running = False
        if self.thread is not None:
            self.thread.join()
            self.thread = None
        return True

    def _run(self):
        """
        Internal polling loop: call parent.run() then sleep for interval.
        """
        try:
            while self.running:
                if self.parent:
                    self.parent.run()
                time.sleep(self.interval)
        except Exception as e:
            logging.error(f"SimplePolling encountered error: {e}")
        finally:
            self.running = False
