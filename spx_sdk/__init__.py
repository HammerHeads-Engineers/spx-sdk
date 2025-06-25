# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

__version__ = "0.1.0-rc.3"

import pkgutil
import importlib

# Dynamically import all submodules so that @register_class decorators run
for _, mod_name, _ in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{mod_name}")

__all__ = [
    "__version__",
]
