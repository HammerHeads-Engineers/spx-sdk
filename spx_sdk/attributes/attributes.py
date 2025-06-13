# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from typing import Any, Dict, Optional
from collections.abc import MutableMapping
from spx_sdk.components import SpxContainer, SpxComponent
from spx_sdk.attributes import SpxAttribute
from spx_sdk.registry import register_class


class InternalValue(MutableMapping):
    """
    Mutable mapping view over attribute values.

    Keys are attribute names, values are the respective internal/external values.
    """
    def __init__(self, attributes: Dict[str, SpxAttribute]) -> None:
        self._attributes = attributes

    def __setitem__(self, name: str, value: Any) -> None:
        # If the attribute exists, update its internal_value
        if name in self._attributes:
            self._attributes[name].internal_value = value
        else:
            raise KeyError(f"Attribute {name} did not exists.")

    def __getitem__(self, name: str):
        # Retrieve the internal_value for the named attribute
        if name in self._attributes:
            return self._attributes[name].internal_value
        else:
            raise KeyError(f"Attribute {name} did not exists.")

    def __delitem__(self, key: str) -> None:
        """Deletion is not supported."""
        raise NotImplementedError("Cannot delete items from InternalValue.")

    def __iter__(self):
        """Iterate over attribute names."""
        return iter(self._attributes)

    def __len__(self) -> int:
        """Return number of attributes."""
        return len(self._attributes)


class ExternalValue(MutableMapping):
    """
    Mutable mapping view over attribute values.

    Keys are attribute names, values are the respective internal/external values.
    """
    def __init__(self, attributes: Dict[str, SpxAttribute]) -> None:
        self._attributes = attributes

    def __setitem__(self, name: str, value: Any) -> None:
        # If the attribute exists, update its external_value
        if name in self._attributes:
            self._attributes[name].external_value = value
        else:
            raise KeyError(f"Attribute {name} did not exists.")

    def __getitem__(self, name: str):
        # Retrieve the external_value for the named attribute
        if name in self._attributes:
            return self._attributes[name].external_value
        else:
            raise KeyError(f"Attribute {name} did not exists.")

    def __delitem__(self, key: str) -> None:
        """Deletion is not supported."""
        raise NotImplementedError("Cannot delete items from ExternalValue.")

    def __iter__(self):
        """Iterate over attribute names."""
        return iter(self._attributes)

    def __len__(self) -> int:
        """Return number of attributes."""
        return len(self._attributes)


@register_class(name="Attributes")
@register_class(name="attributes")
class SpxAttributes(SpxContainer):
    """
    Container for SpxAttribute instances, providing direct value access.

    Attributes:
        children (Dict[str, SpxAttribute]): Mapping of attribute names to SpxAttribute instances.
        internal (_ValueView): View for getting/setting internal values.
        external (_ValueView): View for getting/setting external values.
    """

    def __init__(
        self,
        name: str,
        definition: Any,
        *,
        parent: Optional[SpxComponent] = None,
    ):
        # Tell SpxContainer: "load these entries, filtered to type=Attribute"
        super().__init__(name=name, definition=definition, parent=parent, type=SpxAttribute)

    def _populate(self, definition):
        super()._populate(definition)
        # Now SpxContainer has created one child per dict‐entry, each an Attribute.
        # And wire up our two “views”:
        self.internal = InternalValue(self.children)
        self.external = ExternalValue(self.children)
