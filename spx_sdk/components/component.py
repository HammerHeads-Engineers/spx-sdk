# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import logging
import dataclasses
from spx_sdk.registry import register_class
from typing import Optional, Any, List, Dict
from enum import Enum, auto


class SpxComponentState(Enum):
    INITIALIZED = auto()
    PREPARING = auto()
    PREPARED = auto()
    STARTING = auto()
    STARTED = auto()
    RUNNING = auto()
    PAUSING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    DESTROYING = auto()
    DESTROYED = auto()
    RESETTING = auto()
    RESET = auto()
    FAULT = auto()
    UNKNOWN = auto()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


@register_class()
class SpxComponent:
    """
    SpxComponent represents a node in a hierarchical component tree.

    Attributes:
        name (str): Unique name of this component instance.
        parent (Optional[SpxComponent]): Parent component in the hierarchy.
        children (Dict[str, SpxComponent]): Mapping of child component names to instances.
        definition (Any): Configuration data used to populate this component.
        state (SpxComponentState): Current lifecycle state of the component.

    This class provides methods to manage child components, control the component’s lifecycle
    (prepare, run, start, pause, stop, reset, destroy), and navigate the component tree.
    It supports dict-like access (`component['child']`), containment checks
    (`'child' in component`), and length queries (`len(component)`).
    """
    def __init__(
            self,
            name: Optional[str] = None,
            parent: Optional["SpxComponent"] = None,
            definition: Optional[Any] = None
            ):
        self.name = name if name is not None else self.__class__.__name__
        self.parent = parent
        self.definition: Any = definition
        self.children: Dict[str, SpxComponent] = {}
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}.{self.name}"
        )
        if parent is not None:
            parent.add_child(self)

        self.state = SpxComponentState.INITIALIZED
        # Component enabled flag: when False, lifecycle methods do nothing
        self._enabled: bool = True
        # Hook registry: event name → list of hook components
        self.hooks: Dict[str, List[SpxComponent]] = {}
        self._populate(self.definition)
        self.logger.debug(f"Created {self.__class__.__name__}(name={self.name}, definition={self.definition!r})")

    def add_child(self, child: "SpxComponent"):
        """Prevent adding itself as a child"""
        if child is self:
            raise ValueError(f"Cannot add {self.name} as its own child.")
        if not isinstance(child, SpxComponent):
            raise ValueError("Only SpxComponent instances can be added as children.")
        # add or replace child by its name
        self.children[child.name] = child
        child.parent = self

    def remove_child(self, child: "SpxComponent"):
        if child.name in self.children:
            self.children.pop(child.name)
            child.parent = None

    def get_children(self) -> Dict[str, "SpxComponent"]:
        """Return the internal dict of children keyed by name."""
        return self.children

    def get_children_list(self) -> List["SpxComponent"]:
        """Return a list of child components."""
        return list(self.children.values())

    def get_parent(self):
        return self.parent

    def get_hierarchy(self):
        return {
            "name": self.name,
            "children": [child.get_hierarchy() for child in self.children.values()],
        }

    def get_root(self):
        if self.parent is None:
            return self
        return self.parent.get_root()

    def prepare(self, *args, **kwargs) -> bool:
        """Prepare the component and propagate to children."""
        if not self._enabled:
            # Trigger on_prepare hooks
            self.trigger_hooks("on_event", *args, **kwargs)
            self.trigger_hooks("on_prepare", *args, **kwargs)
            self.logger.debug(f"Component {self.name} is disabled; skipping prepare")
            return False
        # Trigger on_prepare hooks
        self.trigger_hooks("on_event", *args, **kwargs)
        self.trigger_hooks("on_prepare", *args, **kwargs)
        self.logger.debug(f"Preparing {self.name}")
        self.state = SpxComponentState.PREPARING
        for child in self.children.values():
            child.prepare(*args, **kwargs)
        self.state = SpxComponentState.PREPARED
        return True

    def run(self, *args, **kwargs) -> bool:
        """Run the component and propagate to children."""
        if not self._enabled:
            # Trigger on_run hooks
            self.trigger_hooks("on_event", *args, **kwargs)
            self.trigger_hooks("on_run", *args, **kwargs)
            self.logger.debug(f"Component {self.name} is disabled; skipping run")
            return False
        # Trigger on_run hooks
        self.trigger_hooks("on_event", *args, **kwargs)
        self.trigger_hooks("on_run", *args, **kwargs)
        self.logger.debug(f"Running {self.name}")
        self.state = SpxComponentState.RUNNING
        for child in self.children.values():
            child.run(*args, **kwargs)
        self.state = SpxComponentState.STOPPED
        return True

    def start(self, *args, **kwargs) -> bool:
        """Start the component and propagate to children."""
        if not self._enabled:
            self.logger.debug(f"Component {self.name} is disabled; skipping start")
            return False
        # Trigger on_start hooks
        self.trigger_hooks("on_event", *args, **kwargs)
        self.trigger_hooks("on_start", *args, **kwargs)
        self.logger.debug(f"Starting {self.name}")
        self.state = SpxComponentState.STARTING
        for child in self.children.values():
            child.start(*args, **kwargs)
        self.state = SpxComponentState.STARTED
        return True

    def pause(self, *args, **kwargs) -> bool:
        """Pause the component and propagate to children."""
        self.logger.debug(f"Pausing {self.name}")
        self.state = SpxComponentState.PAUSING
        for child in self.children.values():
            child.pause(*args, **kwargs)
        self.state = SpxComponentState.PAUSED
        return True

    def stop(self, *args, **kwargs) -> bool:
        """Stop the component and propagate to children."""
        if not self._enabled:
            self.logger.debug(f"Component {self.name} is disabled; skipping stop")
            return False
        self.logger.debug(f"Stopping {self.name}")
        self.state = SpxComponentState.STOPPING
        for child in self.children.values():
            child.stop(*args, **kwargs)
        self.state = SpxComponentState.STOPPED
        return True

    def reset(self, *args, **kwargs) -> bool:
        """Reset the component and propagate to children."""
        self.logger.debug(f"Reset {self.name}")
        self.state = SpxComponentState.RESETTING
        for child in self.children.values():
            child.reset(*args, **kwargs)
        self.state = SpxComponentState.RESET
        return True

    def destroy(self, *args, **kwargs) -> bool:
        """Destroy the component and propagate to children."""
        self.logger.debug(f"Destroying {self.name}")
        self.state = SpxComponentState.DESTROYING
        for child in self.children.values():
            child.destroy(*args, **kwargs)
        self.parent = None
        self.children = {}
        self.state = SpxComponentState.DESTROYED
        return True

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', state={self.state.name}, parent={self.parent.__class__.__name__ if self.parent else None}, children={len(self.children)})"

    def _populate(self, definition: dict):
        """
        Generic hook to populate instance attributes from definition dict.
        By default, this will set each key in definition as an attribute.
        Subclasses can override to customize behavior.
        """
        if isinstance(definition, dict):
            if dataclasses.is_dataclass(self):
                field_names = {field.name for field in dataclasses.fields(self)}
                for key, value in definition.items():
                    if key in field_names:
                        setattr(self, key, value)
                    else:
                        path = self._get_full_path()
                        raise AttributeError(
                            f"Cannot set undefined dataclass field '{key}' on '{path}'"
                        )
            else:
                for key, value in definition.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                    else:
                        path = self._get_full_path()
                        raise AttributeError(
                            f"Cannot set undefined attribute '{key}' on '{path}'"
                        )

    def _get_full_path(self) -> str:
        """
        Construct the full component path by joining all parent names with dots.
        Returns a string like 'root.child.grandchild'.
        """
        path = self.name
        node = self.parent
        while node:
            path = f"{node.name}.{path}"
            node = node.parent
        return path

    def __getitem__(self, key: str):
        """
        If this component has children, retrieve a child by name.
        If no children exist, treat the key as an attribute name on this instance.
        Raises KeyError if neither a child nor an attribute with that name exists.
        """
        if len(self.children) > 0:
            # Normal child lookup
            try:
                return self.children[key]
            except KeyError:
                raise KeyError(f"No child named '{key}' in component '{self.name}'.")
        else:
            # Leaf: try to return attribute
            if hasattr(self, key):
                return getattr(self, key)
            raise KeyError(f"Component '{self.name}' has no child or attribute named '{key}'.")

    def __setitem__(self, key: str, value) -> None:
        """
        If this component has children, set or replace a child by name.
        If no children exist, set an attribute on this instance.
        Raises ValueError if assigning a child when the value is not an SpxComponent.
        """
        if len(self.children) > 0:
            # Expect value to be a child component
            if not isinstance(value, SpxComponent):
                raise ValueError("Only SpxComponent instances can be assigned as children.")
            old_child = self.children.get(key)
            if old_child is not None:
                old_child.parent = None
            self.children[key] = value
            value.parent = self
        else:
            # Leaf: attempt to set property or attribute
            cls_attr = getattr(self.__class__, key, None)
            # If it's a property on the class
            if isinstance(cls_attr, property):
                if cls_attr.fset is None:
                    raise AttributeError(f"Property '{key}' on component '{self.name}' is read-only")
                # Use setattr to invoke the property's setter
                setattr(self, key, value)
            else:
                # Not a property: set or create a normal attribute
                setattr(self, key, value)

    def get(self, key: str, default=None) -> Optional["SpxComponent"]:
        """
        Get a child component by name, returning a default if not found.

        Args:
            key (str): Name of the child component.
            default (Any): Value to return if the child is not found.

        Returns:
            Optional[SpxComponent]: The child component or the default.
        """
        return self.children.get(key, default)

    def __contains__(self, key: str) -> bool:
        """
        Check if a child component exists by name.

        Args:
            key (str): Name to check.

        Returns:
            bool: True if a child with the given name exists, False otherwise.
        """
        return key in self.children

    def __len__(self) -> int:
        """
        Return the number of child components.

        This allows using len(component) to retrieve the count of children.

        Returns:
            int: Number of child components.
        """
        return len(self.children)

    def __bool__(self) -> bool:
        """
        Always return True to ensure component truthiness is independent of child count.
        """
        return True

    def enable(self) -> None:
        """
        Enable the component. Lifecycle methods (prepare, run, start, stop)
        will execute when this component is enabled.
        """
        self._enabled = True
        # Trigger enable hooks
        self.trigger_hooks("on_event")
        self.trigger_hooks("on_enable")

    def disable(self) -> None:
        """
        Disable the component. Lifecycle methods (prepare, run, start, stop)
        become no-ops when the component is disabled.
        """
        self._enabled = False
        # Trigger disable hooks
        self.trigger_hooks("on_event")
        self.trigger_hooks("on_disable")

    @property
    def enabled(self) -> bool:
        """
        Whether the component is enabled. If False, prepare/run/start/stop
        will not execute.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """
        Setter for enabled flag. Allows toggling via assignment:
            component.enabled = False  # equivalent to component.disable()
        """
        if value:
            self.enable()
        else:
            self.disable()

    def register_hook(self, event: str, hook_component: "SpxComponent") -> None:
        """
        Register a hook component to be triggered on the given event.
        Prevents duplicate registrations of the same hook for the same event.
        """
        hooks_list = self.hooks.setdefault(event, [])
        if hook_component not in hooks_list:
            hooks_list.append(hook_component)

    def get_hooks(self, event: str) -> List["SpxComponent"]:
        """
        Get all registered hook components for the given event name.
        """
        return list(self.hooks.get(event, []))

    def trigger_hooks(self, event: str, *args, **kwargs) -> None:
        """
        Invoke all hooks registered under the given event.
        """
        for hook in self.hooks.get(event, []):
            try:
                hook.run(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Hook '{hook.name}' on event '{event}' failed: {e}")
