from typing import Any, Dict
from spx_sdk.registry import register_class
from spx_sdk.actions.action import Action


@register_class(name="set")
@register_class(name="Set")
class SetAction(Action):
    """
    SetAction class for assigning a literal value to one or more attributes.
    Inherits from Action to manage outputs and inputs.
    """

    def _populate(self, definition: Dict[str, Any]) -> None:
        """
        Populate the SetAction with the given definition.
        Extracts 'value' from definition.params and
        then delegates to base class.
        """
        # Extract literal value: can be top‑level or inside "params"
        if "value" in definition:
            self.value = definition.pop("value")
            params = definition.get("params", {})
        else:
            params = definition.get("params", {})
            self.value = params.pop("value", None)
        # Now let base Action handle function, outputs, and remaining params
        super()._populate(definition)

    def run(self, *args, **kwargs) -> Any:
        """
        Execute the set operation: assign the literal value to all outputs.
        Returns the value that was set.
        """
        # Assign the stored literal value to each output wrapper
        for wrapper in self.outputs.values():
            wrapper.set(self.value)
        return True
