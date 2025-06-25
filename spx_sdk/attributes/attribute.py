# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from spx_sdk.components import SpxContainer
from spx_sdk.registry import register_class

"""
type_mapping: dict
    A mapping from data type names (string) to a dict specifying the Python
    'type' and a 'default' value for that type. Supported keys are:
    "float", "bool", "int", and "str".
"""
type_mapping = {
    "float": {"type": float, "default": 0.0},
    "bool": {"type": bool, "default": False},
    "int": {"type": int, "default": 0},
    "str": {"type": str, "default": ""}
}


class LinkedProperty:
    """
    A helper that binds a named getter and optional setter on a target instance
    so that getting or setting through this object delegates to the underlying
    attribute or method of that instance.
    """
    def __init__(self, instance, getter_name, setter_name=None):
        self._instance = instance
        self._getter_name = getter_name
        if not setter_name:
            setter_name = getter_name
        self._setter_name = setter_name

    def get_value(self):
        if self._instance is None:
            raise AttributeError("Linked property is not set.")
        getter = getattr(self._instance, self._getter_name)

        if callable(getter):
            return getter()
        else:
            return getter

    def set_value(self, value):
        if self._instance is None:
            raise AttributeError("Linked property is not set.")
        setter = getattr(type(self._instance), self._setter_name)
        if callable(setter):
            setter(self._instance, value)
        elif isinstance(setter, property):
            if setter.fset:
                setattr(self._instance, self._setter_name, value)
        else:
            raise AttributeError(f"{self._setter_name} is neither a function nor a property")


@register_class(name="Attribute")
@register_class(name="attribute")
@register_class()
class SpxAttribute(SpxContainer):
    """
    Represents a typed model attribute with separate internal and external values,
    trigger callbacks on value changes, and the ability to link its values to
    properties or methods of its owning component.
    """

    def _populate(self, definition):
        """
        Populate the attribute from a definition dict or a single value.
        If a dict is provided, it can contain:
        - 'type': the data type of the attribute (default is 'float')
        - 'default': the initial value for the attribute (optional)
        If a single value is provided, it is treated as the initial value.
        """

        if not isinstance(definition, dict):
            self.type = type(definition).__name__
            if self.type not in type_mapping:
                raise ValueError(f"Unsupported type: {self.type}. Supported types are: {', '.join(type_mapping.keys())}")
            self.initial_value = definition
        else:
            # Infer type: explicit 'type' key or derive from default value
            if "type" in definition:
                t = definition["type"]
            elif "default" in definition:
                default_val = definition["default"]
                t = type(default_val).__name__
            else:
                t = "float"

            # Validate against supported types
            if t not in type_mapping:
                raise ValueError(
                    f"Unsupported type: {t}. Supported types are: {', '.join(type_mapping.keys())}"
                )
            self.type = t
            # Set initial value to provided default or mapping default
            self.initial_value = definition.get(
                "default", type_mapping[self.type]["default"]
            )
            definition.pop("type", None)  # Remove type from definition to avoid conflicts
            definition.pop("default", None)  # Remove default from definition to avoid conflicts

        self._external_value = None
        self._internal_value = self.initial_value
        self._linked_internal_property = None
        self._linked_external_property = None
        self.unit = None

        super()._populate(definition)

    @property
    def external_value(self):
        if self._external_value is not None:
            return self._external_value
        return self._internal_value

    @external_value.setter
    def external_value(self, value):
        expected_type = type_mapping.get(self.type, type_mapping["str"])["type"]
        try:
            if self._linked_external_property:
                self._linked_external_property.set_value(expected_type(value))
            self._external_value = expected_type(value)  # Change of external value will set external value
            # Trigger hooks for value change
            self.trigger_hooks("on_set")
            self.trigger_hooks("on_external_set")
        except (ValueError, TypeError) as e:
            raise TypeError(f"Expected type {self.type}, but given {type(value).__name__}") from e

    @property
    def internal_value(self):
        if self._linked_internal_property:
            self._internal_value = self._linked_internal_property.get_value()
        return self._internal_value

    @internal_value.setter
    def internal_value(self, value):
        expected_type = type_mapping.get(self.type, type_mapping["str"])["type"]
        try:
            if self._linked_internal_property:
                self._linked_internal_property.set_value(expected_type(value))
            self._internal_value = expected_type(value)
            self._external_value = None  # Change of internal value will reset external value
            # Trigger hooks for value change
            self.trigger_hooks("on_set")
            self.trigger_hooks("on_internal_set")
        except (ValueError, TypeError) as e:
            raise TypeError(f"Expected type {self.type}, but given {type(value).__name__}") from e

    def link_to_internal_property(self, instance, property_name):
        internal_value = self.internal_value
        self._linked_internal_property = LinkedProperty(instance, property_name)
        self._linked_internal_property.set_value(internal_value)

    def link_to_external_property(self, instance, property_name):
        external_value = self.external_value
        self._linked_external_property = LinkedProperty(instance, property_name)
        self._linked_external_property.set_value(external_value)

    def link_to_internal_func(self, instance, getter, setter=None):
        internal_value = self.internal_value
        self._linked_internal_property = LinkedProperty(instance, getter, setter)
        if setter:
            self._linked_internal_property.set_value(internal_value)

    def link_to_external_func(self, instance, getter, setter=None):
        external_value = self.external_value
        self._linked_external_property = LinkedProperty(instance, getter, setter)
        if setter:
            self._linked_external_property.set_value(external_value)

    def unlink_internal_property(self):
        self._linked_internal_property = None

    def unlink_external_property(self):
        self._linked_external_property = None

    def prepare(self):
        self._external_value = None

    def run(self):
        self._external_value = None

    @property
    def internal(self):
        """
        Returns a wrapper to get/set this attribute's internal value.
        """
        return InternalAttributeWrapper(self)

    @property
    def external(self):
        """
        Returns a wrapper to get/set this attribute's external value.
        """
        return ExternalAttributeWrapper(self)

    def get_wrapper(self, wrapper_type: str) -> 'InternalAttributeWrapper | ExternalAttributeWrapper':
        """
        Return the corresponding attribute wrapper by name.

        Args:
            wrapper_type (str): 'internal' or 'external'.

        Returns:
            InternalAttribute or ExternalAttribute wrapper instance.
        """
        t = wrapper_type.lower()
        if t == "internal":
            return InternalAttributeWrapper(self)
        if t == "external":
            return ExternalAttributeWrapper(self)
        raise ValueError(f"Unknown wrapper type '{wrapper_type}'")

    def get(self):
        """Return the internal value."""
        return self.internal_value

    def set(self, value):
        """Set the internal value."""
        self.internal_value = value

    def __getitem__(self, key: str):
        # Leaf: try to return attribute
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"Attribute '{self.name}' has no child or attribute named '{key}'.")

    def __setitem__(self, key: str, value) -> None:
        # Leaf: attempt to set property or attribute
        cls_attr = getattr(self.__class__, key, None)
        # If it's a property on the class
        if isinstance(cls_attr, property):
            if cls_attr.fset is None:
                raise AttributeError(f"Property '{key}' on attribute '{self.name}' is read-only")
            # Use setattr to invoke the property's setter
            setattr(self, key, value)
        else:
            # Not a property: set or create a normal attribute
            setattr(self, key, value)


class InternalAttributeWrapper:
    """
    Wrapper for accessing and setting the internal_value of an SpxAttribute.
    """
    def __init__(self, attribute: SpxAttribute):
        self._attribute = attribute
        self.name = attribute.name
        self.type = attribute.type

    def get(self):
        """Return the internal value."""
        return self._attribute.internal_value

    def set(self, value):
        """Set the internal value."""
        self._attribute.internal_value = value

    def __repr__(self):
        return f"<Internal {self._attribute.name}={self.get()!r}>"


class ExternalAttributeWrapper:
    """
    Wrapper for accessing and setting the external_value of an SpxAttribute.
    """
    def __init__(self, attribute: SpxAttribute):
        self._attribute = attribute
        self.name = attribute.name
        self.type = attribute.type

    def get(self):
        """Return the external value."""
        return self._attribute.external_value

    def set(self, value):
        """Set the external value."""
        self._attribute.external_value = value

    def __repr__(self):
        return f"<External {self._attribute.name}={self.get()!r}>"


# New wrapper for plain Python attributes
class StaticAttributeWrapper:
    """
    Wrapper for accessing and setting a plain Python attribute on any object.
    """
    def __init__(self, instance, attr_name):
        self._instance = instance
        self.name = attr_name

    def get(self):
        """Return the attribute's current value."""
        return getattr(self._instance, self.name)

    def set(self, value):
        """Set the attribute's value."""
        setattr(self._instance, self.name, value)

    def __repr__(self):
        val = self.get()
        return f"<Static {self.name}={val!r}>"
