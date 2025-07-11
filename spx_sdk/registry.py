# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import importlib
import os
import sys
import subprocess
import logging
import fnmatch
import yaml
from copy import deepcopy

class_registry = {}
instance_registry = {}


def register_class(cls=None, *, name=None):
    """
    Register a class in the registry.
    If a name is provided, it will be used as the key in the registry.
    If no name is provided, the class's __name__ will be used.
    If cls is None, return a decorator that registers the class when called.
    :param cls: The class to register.
    :param name: Optional name for the class in the registry.
                 If not provided, the class's __name__ will be used.
    :return: The class itself.
    """
    if cls is None:
        return lambda cls: register_class(cls, name=name)

    class_name = name if name else cls.__name__
    base_class = cls.__bases__[0].__name__
    class_registry[class_name] = {"class": cls, "base_class": base_class}
    return cls


def create_instance(class_name, *args, **kwargs):
    """
    Create an instance of a registered class or YAML template by its name.

    If the registry entry includes a 'template' dict, merges that template
    with any provided 'definition' in kwargs (caller’s values override
    the template). Then calls the constructor of the registered class
    (often SpxContainer) with the merged definition.

    If the class_name is not in the registry, attempts a dynamic import of
    a Python class path. Raises ValueError if no class can be found.

    Args:
        class_name (str): Name of the class or template to instantiate.
        *args: Positional arguments forwarded to the class constructor.
        **kwargs: Keyword arguments forwarded to the class constructor,
                  including an optional 'definition' dict.

    Returns:
        object: New instance of the target class.

    Raises:
        ValueError: If the class_name is not registered and cannot be imported.
    """
    entry = class_registry.get(class_name)
    if entry:
        cls = entry["class"]
        # If this entry carries a YAML‐template, merge it with the caller’s definition
        if "template" in entry:
            # grab the template dict
            tmpl = entry["template"] or {}
            # grab the caller’s definition (e.g. parameters) or empty dict
            own_def = kwargs.get("definition", {}) or {}
            # shallow‐merge (caller’s keys override template’s)
            merged = {**tmpl, **own_def}
            kwargs["definition"] = deepcopy(merged)
    else:
        # fallback: try to import a real Python class
        cls = dynamic_import(class_name)
        if cls is None:
            raise ValueError(f"Class {class_name} not found and could not be imported")

    # Finally call the initializer
    return cls(*args, **kwargs)


def dynamic_import(class_path):
    """
    Dynamically import a class from a module.
    The class_path should be in the format 'module.submodule.ClassName'.
    This function will attempt to import the module and then get the class from it.
    If the class cannot be found, it will return None.
    :param class_path: The full path to the class (e.g., 'module.submodule.ClassName').
    :return: The class if found, None otherwise.
    """
    try:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls
    except (ImportError, AttributeError, ValueError) as e:
        print(f"Error importing {class_path}: {e}")
        return None


def load_module_from_path(file_path, module_name=None):
    """
    Load a module from a given file path.
    If module_name is provided, it will be used as the module name.
    If not, the module name will be derived from the file name.
    This function will remove the module from sys.modules if it already exists,
    allowing for reloading the module.
    :param file_path: Path to the .py file.
    :param module_name: Optional name for the module.
                        If not provided, the file name (without extension) will be used.
    :return: The loaded module.
    """
    if not module_name:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
    # If the module exists in sys.modules, remove it
    if module_name in sys.modules:
        del sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_modules_from_directory(directory, skip_pattern="*test*"):
    """
    Recursively traverse the given directory and load all .py modules (except __init__.py),
    skipping files whose names match the specified skip_pattern.
    :param directory: Base directory to start loading modules from.
    :param skip_pattern: Pattern used to filter out files.
                         Default is "*test*", which will skip any file whose name contains "test" (case-insensitive).
    """
    if directory is None:
        return
    directory_path = os.path.abspath(directory)
    if directory_path not in sys.path:
        sys.path.append(directory_path)

    for filename in os.listdir(directory_path):
        # If the file's name matches skip_pattern, skip it.
        if fnmatch.fnmatch(filename.lower(), skip_pattern.lower()):
            continue
        if filename.endswith(".py") and filename != "__init__.py":
            logging.debug("Loading module: %s", filename)
            module_name = os.path.splitext(filename)[0]
            load_module_from_path(os.path.join(directory_path, filename), module_name)


def load_modules_recursively(directory, skip_pattern="*test*"):
    """
    Recursively traverse the given directory and load all .py modules (except __init__.py),
    while skipping any directories or files whose name matches the skip_pattern
    (case-insensitive).
    :param directory: The base directory to traverse.
    :param skip_pattern: Pattern to use for skipping directories or files.
                         Default is "*test*", so any folder or file containing "test" (any case) is skipped.
    """
    if directory is None:
        return

    directory_path = os.path.abspath(directory)
    if directory_path not in sys.path:
        sys.path.append(directory_path)

    for root, dirs, files in os.walk(directory_path):
        # Exclude subdirectories whose name matches the skip pattern.
        dirs[:] = [d for d in dirs if not fnmatch.fnmatch(d.lower(), skip_pattern.lower())]
        if root not in sys.path:
            sys.path.append(root)
        for filename in files:
            # Skip files matching the skip pattern.
            if fnmatch.fnmatch(filename.lower(), skip_pattern.lower()):
                continue
            if filename.endswith(".py") and filename != "__init__.py":
                filepath = os.path.join(root, filename)
                # Create a module name based on the file's relative path from the base directory.
                rel_path = os.path.relpath(filepath, directory_path)
                module_name = os.path.splitext(rel_path)[0].replace(os.sep, ".")
                logging.debug("Loading module %s from path %s", module_name, filepath)
                load_module_from_path(filepath, module_name)


def install_requirements_from_dir(directory, requirements_pattern="requirements*.txt"):
    """
    Recursively traverse the given directory. For each file that matches the given
    requirements_pattern (default: "requirements*.txt"), install its packages using pip.
    Uses the PIP_INDEX_URL environment variable if set (pointing to a local mirror).
    :param directory: The base directory to traverse.
    :param requirements_pattern: Pattern to match requirement files.
                                 Default is "requirements*.txt".
    :return: None
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Sprawdzamy, czy nazwa pliku pasuje do wzorca, zignorowaliśmy wielkość liter
            if fnmatch.fnmatch(file.lower(), requirements_pattern.lower()):
                req_file = os.path.join(root, file)
                print(f"Installing requirements from {req_file}...")
                cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-r", req_file]
                local_index = os.environ.get("PIP_INDEX_URL")
                if local_index:
                    cmd.extend(["--index-url", local_index])
                subprocess.check_call(cmd)


def get_classes_by_base(base_class_name: str):
    """
    Return all registered classes that inherit (directly or indirectly) from the given base class name.
    :param base_class_name: The name of the base class to filter by.
    :return: A dict mapping class names to class objects for all subclasses of base_class_name.
    """
    result = {}
    for name, info in class_registry.items():
        cls = info["class"]
        # Check all ancestor classes in MRO (excluding the class itself)
        ancestor_names = [c.__name__ for c in cls.__mro__[1:]]
        if base_class_name in ancestor_names:
            result[name] = cls
    return result


def get_class_names_by_base(base_class_name: str):
    """
    Return all registered class names whose recorded base_class matches base_class_name.
    :param base_class_name: The name of the base class to filter by.
    :return: A list of class names that inherit from base_class_name.
    """
    return [
        name
        for name, info in class_registry.items()
        if info["base_class"] == base_class_name
    ]


def filter_instances_by_base_class(base_class):
    """
    Filter instances by base class.
    This function returns a dictionary of instance names and their corresponding instances
    that are instances of the specified base class.
    The base class must be registered in the class_registry.
    :param base_class: The base class to filter by.
    :return: A dictionary of instance names and their corresponding instances.
    """
    filtered_instances = {}
    for instance_name, instance in instance_registry.items():
        if isinstance(instance, base_class):
            filtered_instances[instance_name] = instance
    return filtered_instances


def filter_instances_by_base_class_name(base_class_name):
    """
    Filter instances by base class name.
    This function returns a dictionary of instance names and their corresponding instances
    that are instances of the specified base class name.
    The base class name must be registered in the class_registry.
    :param base_class_name: The base class name to filter by.
    :return: A dictionary of instance names and their corresponding instances.
    """
    filtered_instances = {}
    for instance_name, instance in instance_registry.items():
        for instance_base_class in type(instance).__bases__:
            if instance_base_class.__name__ == base_class_name:
                filtered_instances[instance_name] = instance
    return filtered_instances


def get_instance(instance_name):
    """
    Get an instance by name.
    The instance must be registered in the instance_registry.
    :param instance_name: The name of the instance to retrieve.
    :return: The instance if found, None otherwise.
    """
    if instance_name in instance_registry:
        return instance_registry[instance_name]
    else:
        raise ValueError(f"Instance {instance_name} not found in registry.")


def get_all_instances():
    """
    Get all instances in the instance registry.
    :return: A dictionary of instance names and their corresponding instances.
    """
    if instance_registry is None:
        raise ValueError("Instance registry is empty.")
    return instance_registry


def get_all_classes():
    """
    Get all classes in the class registry.
    :return: A dictionary of class names and their corresponding classes.
    """
    if class_registry is None:
        raise ValueError("Class registry is empty.")
    return class_registry


def clear_registry():
    """
    Clear the class and instance registries.
    This function resets the class_registry and instance_registry to empty dictionaries.
    :return: None
    """
    class_registry.clear()
    instance_registry.clear()
    logging.debug("Cleared class and instance registries.")


def get_class(class_name: str):
    """
    Get class by name.
    The class must be registered in the class_registry.
    :param class_name: The name of the class to retrieve.
    :return: The class if found, None otherwise.
    """
    if class_name not in class_registry:
        raise ValueError(f"Class {class_name} not found in registry.")
    return class_registry[class_name]["class"]


def get_class_base(class_name: str):
    """
    Get base class name by class name.
    The class must be registered in the class_registry.
    :param class_name: The name of the class to retrieve.
    :return: The base class name if found, None otherwise.
    """
    if class_name not in class_registry:
        raise ValueError(f"Class {class_name} not found in registry.")
    return class_registry[class_name]["base_class"]


def load_instances_from_yaml(filename: str):
    """
    Load instances from a YAML file.
    The YAML file should contain a mapping of instance names to their class names and parameters.
    The class must be registered in the class_registry.
    :param filename: Path to the YAML file.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found.")
    with open(filename, "r") as file:
        load_instances_from_yaml_data(file)


def load_instances_from_yaml_data(yaml_data: str):
    """
    Load instances from a YAML string.
    The YAML string should contain a mapping of instance names to their class names and parameters.
    The class must be registered in the class_registry.
    :param yaml_data: YAML string containing instance definitions.
    """
    data = yaml.safe_load(yaml_data)

    for instance_name, instance_info in data.items():
        class_name = instance_info["class"]
        parameters = instance_info.get("parameters", {})
        instance = create_instance(class_name, **parameters)
        instance_registry[instance_name] = instance
        logging.debug(f"Loaded instance {instance_name} of class {class_name} with parameters {parameters}")
