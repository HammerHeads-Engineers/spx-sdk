# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from typing import Any, Dict
from spx_sdk.components import SpxComponent, SpxComponentState
from spx_sdk.attributes.resolve_attribute import (
    substitute_attribute_references_hierarchical,
    resolve_attribute_reference_hierarchical
)


class Action(SpxComponent):
    """
    Base class for a single action mapping inputs to a function call and writing an output.
    Definition keys:
      - function (str): name of the function to call
      - output (str): hash-ref string for output attribute
      - param_1 (str, Any): param_1 name -> hash-ref string or value for input
      - param_2 (str, Any): param_2 name -> hash-ref string or value for input
      - ...
    """
    def _populate(self, definition: Dict) -> None:
        self.function: str = None
        self.output: Any = None  # Can be a single string or a list of strings
        self.outputs: dict = {}  # Will be populated with attribute instances keyed by name
        # 1) Extract any extra keys (besides 'function' and 'output') into self.params
        #    so that subclasses can use them later.
        self.params = {}
        for key in list(definition.keys()):
            if key not in ("function", "output"):
                self.params[key] = definition.pop(key)

        # 2) Delegate to parent to populate "function" and "output" attributes, etc.
        super()._populate(definition)

        # Resolve outputs into a dict of attribute instances keyed by attribute name, if any
        if self.output:
            refs = self.output if isinstance(self.output, list) else [self.output]
            for ref in refs:
                if ref is None:
                    continue
                attr = resolve_attribute_reference_hierarchical(self.parent, ref)
                if attr is None:
                    raise ValueError(f"Output reference '{ref}' could not be resolved.")
                # Use the attribute's name as the dictionary key
                self.outputs[attr.name] = attr
        self.state = SpxComponentState.INITIALIZED

    def resolve_param(self, param):
        if not isinstance(param, str):
            return param
        # Substitute attribute references (e.g. "$attr(x)") with literal values
        expr = substitute_attribute_references_hierarchical(self.parent, param)
        # Normalize boolean literals
        expr = expr.replace("true", "True").replace("false", "False")
        # Evaluate the resulting expression to compute numeric or boolean results
        try:
            return eval(expr)
        except Exception:
            return expr

    def prepare(self, *args, **kwargs) -> bool:
        """
        Resolve all parameters into instance attributes before running.
        """
        if self._enabled is False:
            return True
        self.state = SpxComponentState.PREPARING
        # For every key in self.params, resolve its value and assign to self.key
        for key, raw_val in self.params.items():
            # Ensure this Action subclass actually defines this parameter
            if not hasattr(self, key):
                raise AttributeError(f"Cannot set unknown parameter '{key}' on {self.__class__.__name__}")
            resolved = self.resolve_param(raw_val)
            setattr(self, key, resolved)
        self.state = SpxComponentState.PREPARED
        return True

    def run(self, result=None) -> Any:
        if self._enabled is False:
            return True
        if result is None:
            return None  # No result to set, nothing to run
        self.state = SpxComponentState.RUNNING
        for output in self.outputs.values():
            output.set(result)
        self.state = SpxComponentState.STOPPED
        return result
