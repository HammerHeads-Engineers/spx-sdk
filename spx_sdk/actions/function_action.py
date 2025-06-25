from typing import Any
from spx_sdk.registry import register_class
from spx_sdk.actions.action import Action


@register_class(name="function")
class FunctionAction(Action):
    """
    FunctionAction class for executing a function.
    Inherits from Action to manage action components.
    """

    def _populate(self, definition: dict) -> None:
        self.call = None
        super()._populate(definition)

    def run(self, *args, **kwargs) -> Any:
        """
        Evaluate the call expression, resolving attribute references,
        and write the result to all output attributes.
        """
        super().run()
        if self.call is None:
            return False  # No call defined, nothing to run
        return self.write_outputs(self.call)
