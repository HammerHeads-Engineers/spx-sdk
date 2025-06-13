# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from typing import Any, Dict, List
from spx_sdk.registry import register_class, get_classes_by_base
from spx_sdk.components import SpxContainer
from spx_sdk.actions.action import Action


@register_class(name="actions")
@register_class(name="Actions")
class Actions(SpxContainer):
    """
    SPX container for a list of actions. Definition must be a list of dicts:
      - <function_name>: "<output_ref>"
        <param1>: "<input_ref1>"
        ...
    Each dict is turned into an Action child component.
    """
    def _populate(self, definition: List[Dict[str, Any]]) -> None:
        # Validate definition format
        if not isinstance(definition, list):
            raise ValueError("Actions definition must be a list of mappings")

        # Track occurrences of each action name for unique naming
        name_counts: Dict[str, int] = {}
        # Pre-fetch all subclasses of Action once
        subclasses = get_classes_by_base(Action.__name__)

        for entry in definition:
            if not isinstance(entry, dict) or not entry:
                continue
            # Get the first (function -> output) pair
            fn_name, output_ref = next(iter(entry.items()))
            # Determine a unique child name
            count = name_counts.get(fn_name, 0)
            child_name = fn_name if count == 0 else f"{fn_name}_{count}"
            name_counts[fn_name] = count + 1
            # Collect remaining key/value pairs as params
            params = {k: v for k, v in entry.items() if k != fn_name}
            action_def = {"function": fn_name, "output": output_ref, **params}
            # Instantiate either the specific subclass or default Action
            action_cls = subclasses.get(fn_name)
            if action_cls:
                action_cls(name=child_name, parent=self, definition=action_def)
            else:
                super()._populate(entry)
