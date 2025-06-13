# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from .attribute import type_mapping, SpxAttribute, InternalAttributeWrapper, ExternalAttributeWrapper
from .attributes import SpxAttributes
from spx_sdk.attributes.resolve_attribute import (
    is_attribute_reference,
    find_attribute,
    resolve_attribute_reference,
    get_attribute_value,
    set_attribute_value,
    resolve_reference,
    resolve_attribute_reference_hierarchical,
    substitute_attribute_references_hierarchical,
)

__all__ = ["SpxAttribute",
           "InternalAttributeWrapper",
           "ExternalAttributeWrapper",
           "SpxAttributes",
           "type_mapping",
           "is_attribute_reference",
           "find_attribute",
           "resolve_attribute_reference",
           "get_attribute_value",
           "set_attribute_value",
           "resolve_reference",
           "resolve_attribute_reference_hierarchical",
           "substitute_attribute_references_hierarchical"
           ]
