# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

class FakeItemClass:
    def __init__(self):
        # Custom attributes for testing
        self.description = "Fake item for unit tests"
        self.enabled = True
        self._status = "initialized"
        # Numeric and array attributes for testing
        self._int_value = 42
        self._float_value = 3.14
        self._int_list = [1, 2, 3]
        self._float_list = [1.1, 2.2, 3.3]

    @property
    def status(self) -> str:
        """Get the current status of the item."""
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        """Set the current status of the item."""
        self._status = value

    @property
    def info(self) -> str:
        """Return a summary information string."""
        return f"{self.name} - {self.description}"

    @property
    def int_value(self) -> int:
        """Return a test integer value."""
        return self._int_value

    @int_value.setter
    def int_value(self, value: int) -> None:
        """Set a test integer value."""
        self._int_value = value

    @property
    def float_value(self) -> float:
        """Return a test float value."""
        return self._float_value

    @float_value.setter
    def float_value(self, value: float) -> None:
        """Set a test float value."""
        self._float_value = value

    @property
    def int_list(self) -> list[int]:
        """Return a test list of integers."""
        return self._int_list

    @int_list.setter
    def int_list(self, value: list[int]) -> None:
        """Set a test list of integers."""
        self._int_list = value

    @property
    def float_list(self) -> list[float]:
        """Return a test list of floats."""
        return self._float_list

    @float_list.setter
    def float_list(self, value: list[float]) -> None:
        """Set a test list of floats."""
        self._float_list = value
