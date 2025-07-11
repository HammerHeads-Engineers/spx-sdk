# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from typing import Any, Optional, Type

from spx_sdk.registry import class_registry, create_instance, get_classes_by_base, register_class
from spx_sdk.components import SpxComponent


@register_class()
class SpxContainer(SpxComponent):
    """
    SpxContainer extends SpxComponent by automatically instantiating and organizing
    child components based on a provided definition.

    Two modes of operation:

    1. Filtered mode (when `type` is provided):
       - The definition may be a dict, list, or scalar.
       - For dict/list entries, if the key matches a subclass of `type`, that subclass
         is used; otherwise the base `type` class is used.
       - Scalar definitions are instantiated directly as the base `type`.

    2. Generic mode (when no `type` is provided):
       - Treat each dict key or single-key list node as a class name looked up in the registry.
       - Instantiate each matching class.
       - Other values (e.g. scalars) are ignored in generic mode.

    Child components are created during initialization by passing `definition` to `_populate`.
    """

    def __init__(
        self,
        definition: Any,
        *,
        name: Optional[str] = None,
        parent: Optional[SpxComponent] = None,
        type: Optional[Type[SpxComponent]] = None
    ):
        self._type = type
        # now actually load children
        super().__init__(name=name, parent=parent, definition=definition)

    def _populate(self, definition: Any) -> None:
        if self._type:
            self._load_filtered(definition)
        else:
            self._load_generic(definition)
        super()._populate(definition)

    def _handle_dict_filtered(self, definition: dict, base_cls, subclasses):
        """Instantiate children for dict-based filtered definitions."""
        # Iterate over a static list of keys to avoid modifying while iterating
        for cls_name in list(definition.keys()):
            cfg = definition.pop(cls_name)
            cls = subclasses.get(cls_name, base_cls)
            cls(name=cls_name, parent=self, definition=cfg)

    def _handle_list_filtered(self, definition: list, base_cls, subclasses):
        """Instantiate children for list-based filtered definitions, ensuring unique names."""
        # Track how many times each class name has been seen
        name_counts: dict[str, int] = {}
        original_len = len(definition)
        for _ in range(original_len):
            node = definition.pop(0)
            if isinstance(node, dict) and len(node) == 1:
                cls_name, cfg = next(iter(node.items()))
                cls = subclasses.get(cls_name, base_cls)
                # Determine unique child name
                count = name_counts.get(cls_name, 0) + 1
                name_counts[cls_name] = count
                child_name = cls_name if count == 1 else f"{cls_name}_{count - 1}"
                cls(name=child_name, parent=self, definition=cfg)
            elif isinstance(node, dict) and len(node) > 1:
                it = iter(node.items())
                cls_name, cfg = next(it)
                cls = subclasses.get(cls_name, base_cls)
                # Determine unique root name
                count = name_counts.get(cls_name, 0) + 1
                name_counts[cls_name] = count
                root_name = cls_name if count == 1 else f"{cls_name}_{count - 1}"
                root = cls(name=root_name, parent=self, definition=cfg)
                for sub_name, sub_cfg in it:
                    sub_cls = subclasses.get(sub_name, base_cls)
                    # For sub-children, no need to index as keys are unique under this root
                    sub_cls(name=sub_name, parent=root, definition=sub_cfg)
            else:
                # Scalar or unsupported dict form
                name = base_cls.__name__ if not isinstance(node, str) else node
                cfg = None if isinstance(node, str) else node
                # Determine unique child name
                count = name_counts.get(name, 0) + 1
                name_counts[name] = count
                child_name = name if count == 1 else f"{name}_{count - 1}"
                base_cls(name=child_name, parent=self, definition=cfg)

    def _handle_scalar_filtered(self, definition: Any, base_name: str, base_cls):
        """Instantiate a single child for scalar filtered definitions."""
        child = base_cls(name=base_name, parent=self, definition=definition)
        self.add_child(child)

    # Filtered mode: instantiate children using the specified type filter

    def _load_filtered(self, definition: Any) -> None:
        base_name = self._type.__name__
        subclasses = get_classes_by_base(base_name)
        base_entry = class_registry.get(base_name)
        if not base_entry:
            raise ValueError(f"Base class {base_name} not found in registry")
        base_cls = base_entry["class"]

        if isinstance(definition, dict):
            self._handle_dict_filtered(definition, base_cls, subclasses)
        elif isinstance(definition, list):
            self._handle_list_filtered(definition, base_cls, subclasses)
        else:
            self._handle_scalar_filtered(definition, base_name, base_cls)

    # Generic mode: instantiate children by registry lookup without type filter

    def _handle_dict_generic(self, definition: dict) -> None:
        """Instantiate children for generic dict definitions."""
        # Iterate over a static list of keys to avoid modifying while iterating
        for cls_name in list(definition.keys()):
            if cls_name not in class_registry:
                continue
            cfg = definition.pop(cls_name)
            create_instance(
                cls_name,
                name=cls_name,
                parent=self,
                definition=cfg
            )

    def _handle_list_generic(self, definition: list) -> None:
        """Instantiate children for generic list definitions."""
        # Process each element by popping from the front until empty,
        # ensure unique child names for duplicate class entries
        name_counts: dict[str, int] = {}
        original_len = len(definition)
        for _ in range(original_len):
            node = definition.pop(0)
            if isinstance(node, dict) and len(node) == 1:
                cls_name, cfg = next(iter(node.items()))
                if cls_name not in class_registry:
                    raise ValueError(f"Class '{cls_name}' not found in registry")
                # determine unique child name
                count = name_counts.get(cls_name, 0) + 1
                name_counts[cls_name] = count
                child_name = cls_name if count == 1 else f"{cls_name}_{count - 1}"
                create_instance(
                    cls_name,
                    name=child_name,
                    parent=self,
                    definition=cfg
                )
            elif isinstance(node, dict) and len(node) > 1:
                it = iter(node.items())
                cls_name, cfg = next(it)
                if cls_name not in class_registry:
                    raise ValueError(f"Class '{cls_name}' not found in registry")
                # determine unique root name
                count = name_counts.get(cls_name, 0) + 1
                name_counts[cls_name] = count
                root_name = cls_name if count == 1 else f"{cls_name}_{count - 1}"
                root = create_instance(
                    cls_name,
                    name=root_name,
                    parent=self,
                    definition=cfg
                )
                for sub_name, sub_cfg in it:
                    if sub_name not in class_registry:
                        raise ValueError(f"Class '{sub_name}' not found in registry")
                    # direct child under root; use sub_name (assuming no duplicates at this level)
                    create_instance(
                        sub_name,
                        name=sub_name,
                        parent=root,
                        definition=sub_cfg
                    )
            # ignore non-dict nodes

    def _load_generic(self, definition: Any) -> None:
        """
        Generic loading mode: treat each entry in a dict definition as
        class_name → configuration, or each node in a list as a single-key dict.
        Raises ValueError if a referenced class is not registered.
        """
        if isinstance(definition, dict):
            self._handle_dict_generic(definition)
        elif isinstance(definition, list):
            self._handle_list_generic(definition)
        else:
            # Scalar definitions are not loaded in generic mode
            return
