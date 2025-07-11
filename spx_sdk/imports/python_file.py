# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from spx_sdk.registry import register_class, load_module_from_path
from spx_sdk.components import SpxComponent
from spx_sdk.attributes import SpxAttribute


@register_class(name="python_file")
@register_class(name="import")
class PythonFile(SpxComponent):

    def _populate(self, definition: dict) -> None:
        self.class_instances = {}
        for module_path, params in definition.items():
            params["path"] = module_path
            class_instance = self.create_instance_from_module(params)
            class_name = params["class"]
            self.class_instances[class_name] = class_instance

    def create_instance_from_module(self, module_info: dict):
        file_path = module_info["path"]
        class_name = module_info["class"]
        module = load_module_from_path(file_path)
        cls = getattr(module, class_name)

        # Extract custom init parameters if provided
        init_info = module_info.get("init", {})
        init_args = init_info.get("args", [])
        init_kwargs = init_info.get("kwargs", {})

        if SpxComponent in cls.__bases__:
            # Prepend root and definition for Item subclasses
            args = [self.get_root(), self.definition] + init_args
            class_instance = cls(*args, **init_kwargs)
        else:
            # Instantiate plain classes with provided args/kwargs
            class_instance = cls(*init_args, **init_kwargs)
        return class_instance

    def prepare(self):
        if isinstance(self.definition, dict):
            for module_path, params in self.definition.items():
                for attr, methods in params["attributes"].items():
                    class_name = params["class"]
                    attribute: SpxAttribute = self.get_root().get("attributes").get(attr)
                    if "property" in methods:
                        attribute.link_to_internal_property(self.class_instances[class_name], methods["property"])
                    elif "getter" in methods:
                        getter_name = methods["getter"]
                        setter_name = methods.get("setter", None)
                        attribute.link_to_internal_func(self.class_instances[class_name], getter_name, setter_name)

    def reset(self):
        for module_path, params in self.definition.items():
            for attr, methods in params["attributes"].items():
                attribute: SpxAttribute = self.get_root().get("attributes").get(attr)
                attribute.unlink_internal_property()
