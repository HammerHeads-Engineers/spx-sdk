# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from typing import Any, Dict
from spx_sdk.components import SpxComponent, SpxComponentState
from spx_sdk.attributes.resolve_attribute import (
    substitute_attribute_references_hierarchical,
    resolve_attribute_reference_hierarchical,
    ATTRIBUTE_REFERENCE_PATTERN
)
from spx_sdk.attributes.resolve_attribute import (
    extract_attribute_wrappers_hierarchical,
    substitute_with_wrappers
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

        # 1.5) Prepare empty wrapper mapping: key -> list of (ref, wrapper)
        self._wrappers: Dict[str, list] = {}

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
        Defer parameter resolution: collect wrappers for each raw param now.
        """
        if self._enabled is False:
            return True
        self.state = SpxComponentState.PREPARING
        # For every key in self.params, extract wrappers without evaluating
        for key, raw_val in self.params.items():
            # If raw_val is a string containing reference syntax, extract wrappers
            if isinstance(raw_val, str) and ATTRIBUTE_REFERENCE_PATTERN.search(raw_val):
                wrappers = extract_attribute_wrappers_hierarchical(self.parent, raw_val)
            else:
                # static literal or string without references: assign immediately, cast if possible
                if isinstance(raw_val, str):
                    try:
                        evaluated = eval(raw_val)
                    except Exception:
                        evaluated = raw_val
                else:
                    evaluated = raw_val
                setattr(self, key, evaluated)
                wrappers = []
            self._wrappers[key] = wrappers
        self.state = SpxComponentState.PREPARED
        return True

    def apply_wrappers(self):
        """
        Resolve raw param expressions by substituting attribute values.
        Sets self.<key> to the resolved value (eval if possible).
        """
        for key, raw_val in self.params.items():
            wrappers = self._wrappers.get(key, [])
            # Only reapply for dynamic parameters (with wrappers)
            if not wrappers:
                continue
            # Substitute wrapper values into the raw text
            substituted = substitute_with_wrappers(raw_val, wrappers)
            # Try to evaluate numeric/boolean expressions, fallback to string
            try:
                resolved = eval(substituted)
            except Exception:
                resolved = substituted
            setattr(self, key, resolved)

    def write_outputs(self, result) -> None:
        """
        Write the result value to all output attributes.
        """
        for output in self.outputs.values():
            output.set(result)
        return result

    def run(self, result=None) -> Any:
        if self._enabled is False:
            return True
        self.state = SpxComponentState.RUNNING
        # First, resolve parameters now that wrappers are ready
        self.apply_wrappers()
        if result is None:
            return None  # No result to set, nothing to run

        self.write_outputs(result)
        self.state = SpxComponentState.STOPPED
        return result
