

# spx-sdk

spx-sdk is a Python library designed as a foundation for building and extending physics-based simulation models of hardware devices within the SPX environment. It provides tools and abstractions to define and compose simulation components, configure simulation workflows, and integrate virtual prototypes seamlessly into your product development lifecycle and CI/CD pipelines.

## Features

- **Modular Components**: Easily define and combine device models and subcomponents.
- **Configurable Workflows**: Customize simulation parameters, scenarios, and execution order.
- **CI/CD Integration**: Automate simulation runs as part of your build and testing pipelines.
- **Extensible Architecture**: Extend core classes to support custom hardware models and simulation logic.

## Installation

Install via pip:

```bash
pip install spx-sdk
```

## Getting Started

```python
from spx_sdk.components import SpxComponent, SpxContainer
from spx_sdk.registry import register_class

# Register a custom component
@register_class(name="info")
class InfoComponent(SpxComponent):
    def _populate(self, parameters):
        self.info = None
        
    def run(self, *args, **kwargs):
        print(self.info)

yaml_data = '''
info:
    info: "Hello World!"
'''

# Parse JSON and build the container
data = json.loads(yaml_data)
instance = SpxContainer(
    name='Root',
    definition=data,
    parent=None
)
# Run the simulation
sim.run()
```

For full documentation, examples, and advanced configuration, visit the project docs.