# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import re
from typing import Tuple, Any, Optional, Union
from spx_sdk.components import SpxComponent
from spx_sdk.attributes import SpxAttribute
from spx_sdk.attributes.attribute import InternalAttributeWrapper, ExternalAttributeWrapper


# Define a regex pattern to match attribute references
ATTRIBUTE_REFERENCE_PATTERN = re.compile(r'[#\$@](attr|internal|external|in|out|ext)\(([^)]+)\)')


def is_attribute_reference(reference: str) -> Tuple[bool, str, Optional[str]]:
    """
    Check if the reference is an attribute reference and parse it.

    Args:
        reference (str): The reference string to check.

    Returns:
        Tuple[bool, str, Optional[str]]:
            - bool: whether `reference` is an attribute reference.
            - str: the parsed attribute string.
            - Optional[str]: the reference type ('attr', 'internal', or 'external'), or None.
    """
    is_attr = False
    attr_type = None
    attr_string = reference

    if isinstance(reference, str):
        match = ATTRIBUTE_REFERENCE_PATTERN.match(reference)
        if match:
            is_attr = True
            raw_type = match.group(1)
            attr_string = match.group(2)
            # Map to 'external' only if raw_type indicates external
            if raw_type in ("external", "out", "ext"):
                attr_type = "external"
            else:
                attr_type = "internal"
        elif '.' in reference:
            is_attr = True
            attr_type = "internal"
            attr_string = reference

    return is_attr, attr_string, attr_type


def find_attribute(instance: SpxComponent, attribute_string: str) -> Optional[SpxAttribute]:
    """
    Find and return the attribute object based on a simple name or a dot-separated path.

    Delegates:
      - dot-containing strings → nested lookup across children/instances
      - simple names → lookup in the 'attributes' container of the instance
    """
    if '.' in attribute_string:
        return _find_nested_attribute(instance, attribute_string)
    else:
        return _find_simple_attribute(instance, attribute_string)


def _find_simple_attribute(instance: SpxComponent, attr_name: str) -> Optional[SpxAttribute]:
    """
    Lookup an attribute by name in the 'attributes' container of the given instance.
    """
    attrs_cont = instance.get("attributes", None)
    if attrs_cont is None:
        raise ValueError(f"Component '{instance.name}' has no 'attributes' container.")
    return attrs_cont.get(attr_name, None)


def _find_nested_attribute(instance: SpxComponent, attribute_string: str) -> Optional[SpxAttribute]:
    """
    Lookup an attribute via a dot-separated path through component children, falling back
    to an 'instances' container if necessary, and finally in the 'attributes' container.
    """
    parts = attribute_string.split('.')
    current = instance

    # Traverse through component children for all but the final segment
    for segment in parts[:-1]:
        next_comp = current.get(segment, None)
        if next_comp is None:
            instances_cont = current.get("instances", None)
            if instances_cont and segment in instances_cont:
                next_comp = instances_cont.get(segment)
            else:
                return None
        current = next_comp

    # Final segment should be an attribute name
    attr_name = parts[-1]
    attrs_cont = current.get("attributes", None)
    if attrs_cont is None:
        raise ValueError(f"Component '{current.name}' has no 'attributes' container.")
    return attrs_cont.get(attr_name, None)


def resolve_attribute_reference(
    instance: SpxComponent,
    attribute_name: str
) -> Optional[Union[InternalAttributeWrapper, ExternalAttributeWrapper]]:
    """
    Resolve the attribute reference and return the attribute object and its type.

    Args:
        instance: The instance containing the attribute.
        attribute_name (str): The attribute reference string.

    Returns:
        Optional[Union[InternalAttributeWrapper, ExternalAttributeWrapper]]:
            A wrapper for the resolved attribute, or None if not an attribute reference.
    """
    is_attr, attr_string, attr_type = is_attribute_reference(attribute_name)
    if not is_attr:
        return None
    attribute = find_attribute(instance, attr_string)
    if attribute is None:
        raise ValueError(f"Attribute '{attr_string}' not found in instance '{instance.name}'.")
    return attribute.get_wrapper(attr_type)


def get_attribute_value(attribute: SpxAttribute, attr_type: str) -> Any:
    """
    Get the value of the attribute based on its type.

    Args:
        attribute (Attribute): The attribute object.
        attr_type (str): The attribute type ('internal' or 'external').

    Returns:
        Any: The attribute value.

    Raises:
        ValueError: If the attribute is None.
    """
    if attribute is None:
        raise ValueError("Attribute cannot be None when getting its value.")
    if attr_type == "internal":
        return attribute.internal_value
    else:
        return attribute.external_value


def set_attribute_value(attribute: SpxAttribute, attr_type: str, value: Any) -> None:
    """
    Set the value of the attribute based on its type.

    Args:
        attribute (Attribute): The attribute object.
        attr_type (str): The attribute type ('internal' or 'external').
        value (Any): The value to set.

    Raises:
        ValueError: If the attribute is None.
    """
    if attribute is None:
        raise ValueError("Attribute cannot be None when setting its value.")
    if attr_type == "internal":
        attribute.internal_value = value
    else:
        attribute.external_value = value


def resolve_reference(instance: SpxComponent, reference: str) -> Any:
    """
    Resolve the reference to its actual value.

    Args:
        instance: The instance containing the reference.
        reference (str): The reference string.

    Returns:
        Any: The resolved value if it was an attribute reference, otherwise the original `reference` string.
    """
    is_attr, attr_string, attr_type = is_attribute_reference(reference)
    if is_attr:
        attribute = find_attribute(instance, attr_string)
        if attribute is None:
            return reference
        return get_attribute_value(attribute, attr_type)
    return reference


def resolve_attribute_reference_hierarchical(
    instance: SpxComponent,
    reference: str
) -> Optional[Union[InternalAttributeWrapper, ExternalAttributeWrapper]]:
    """
    Resolve an attribute reference by searching up the component hierarchy.
    Starting from `instance`, traverse parent links until an attributes container
    with the named attribute is found. Returns the corresponding wrapper or None.
    """
    # Parse reference syntax
    is_attr, attr_string, attr_type = is_attribute_reference(reference)
    if not is_attr:
        return None

    # Walk up from the given instance to root
    current = instance
    while current is not None:
        # Attempt to find attribute on this component
        try:
            attribute = find_attribute(current, attr_string)
        except ValueError:
            attribute = None

        if attribute is not None:
            return attribute.get_wrapper(attr_type)
        current = current.parent  # move to next parent

    return None


def substitute_attribute_references_hierarchical(
    instance: SpxComponent,
    text: str
) -> str:
    """
    Replace all attribute reference patterns in `text` with their resolved values.
    Uses hierarchical resolution on `$attr(...)`, `$ext(...)`, etc., starting from `instance`.
    Args:
        instance (SpxComponent): Component context to resolve attribute references.
        text (str): The input string containing reference patterns.

    Returns:
        str: A new string with each reference replaced by repr(value).
    """
    def _repl(match: re.Match) -> str:
        ref = match.group(0)
        wrapper = resolve_attribute_reference_hierarchical(instance, ref)
        if wrapper is None:
            # Leave unknown refs unchanged
            return ref
        try:
            value = wrapper.get()
        except Exception:
            # Fallback: return original ref on error
            return ref
        # Use repr to preserve data types in embedded expressions
        return repr(value)

    return ATTRIBUTE_REFERENCE_PATTERN.sub(_repl, text)
