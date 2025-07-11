# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from spx_sdk.components import SpxComponent


class InheritedItem(SpxComponent):
    """
    Test item class inheriting from Item for PythonFile import tests.
    """
    def __init__(self, *args, **kwargs):
        # Initialize base Item with explicit name for predictable child keys
        super().__init__(name="InheritedItem", parent=None, definition=None)
        # Numeric and array attributes for testing
        self._count = 100
        self._ratio = 0.5
        self._ids = [10, 20, 30]
        self._ratios = [0.1, 0.2, 0.3]

    @property
    def summary(self):
        return f"InheritedItem with count={self._count} and ratio={self._ratio}"

    @property
    def count(self) -> int:
        """Return a test count value."""
        return self._count

    @count.setter
    def count(self, value: int) -> None:
        """Set a test count value."""
        self._count = value

    @property
    def ratio(self) -> float:
        """Return a test ratio value."""
        return self._ratio

    @ratio.setter
    def ratio(self, value: float) -> None:
        """Set a test ratio value."""
        self._ratio = value

    @property
    def ids(self) -> list[int]:
        """Return a test list of IDs."""
        return self._ids

    @ids.setter
    def ids(self, value: list[int]) -> None:
        """Set a test list of IDs."""
        self._ids = value

    @property
    def ratios(self) -> list[float]:
        """Return a test list of ratios."""
        return self._ratios

    @ratios.setter
    def ratios(self, value: list[float]) -> None:
        """Set a test list of ratios."""
        self._ratios = value
