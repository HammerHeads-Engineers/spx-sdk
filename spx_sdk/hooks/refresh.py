# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from spx_sdk.registry import register_class
from spx_sdk.components import SpxComponent


@register_class(name="refresh_model")
class RefreshHook(SpxComponent):
    def run(self, *args, **kwargs):
        self.get_root().prepare(*args, **kwargs)
        return self.get_root().run(*args, **kwargs)
