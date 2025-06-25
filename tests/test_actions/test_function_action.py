import unittest
from spx_sdk.registry import register_class, clear_registry
from spx_sdk.components import SpxComponent, SpxContainer
from spx_sdk.attributes.attributes import SpxAttributes, SpxAttribute
from spx_sdk.actions.function_action import FunctionAction


class TestFunctionAction(unittest.TestCase):
    def setUp(self):
        clear_registry()  # Clear registry before each test to avoid conflicts
        # Silence logging
        register_class()(SpxContainer)  # Ensure SpxContainer is registered
        register_class(name="attributes")(SpxAttributes)
        register_class()(SpxAttribute)
        register_class(name="function")(FunctionAction)
        register_class(name="attributes")(SpxAttributes)
        register_class(name="spx_component")(SpxComponent)
        register_class(name="spx_container")(SpxContainer)
        # Create a root component and attributes container
        self.root = SpxComponent(name='root')
        attrs_def = {
            'out1': 0.0,
            'out2': 0.0,
            'voltage': 2.0,
            'current': 3.0,
            'apparent_power': 0.0
        }
        self.attrs = SpxAttributes(name='attributes',
                                   definition=attrs_def,
                                   parent=self.root)

    def test_configuration_parsing(self):
        # Ensure FunctionAction fields reflect the provided definition
        definition = {
            'function': 'function',
            'output': '#ext(apparent_power)',
            'call': '(lambda a, b: a * b)(#attr(voltage), #attr(current))'
        }
        action = FunctionAction(name='function',
                                parent=self.root,
                                definition=definition)
        action.prepare()
        action.run()
        self.assertEqual(action.function, 'function')
        self.assertEqual(action.output, '#ext(apparent_power)')
        self.assertEqual(action.call, 6.0)  # 2.0 * 3.0 = 6.0

    def test_run_without_call_returns_none_and_no_change(self):
        # Definition without 'call' => run returns None, outputs unchanged
        definition = {
            'function': 'no_call',
            'output': '#attr(out1)'
        }
        action = FunctionAction(name='no_call',
                                parent=self.root,
                                definition=definition)
        action.prepare()
        # Set initial external value
        out_attr = self.attrs.get('out1')
        out_attr.external.set(123)
        result = action.run()
        self.assertFalse(result)
        # external value remains unchanged
        self.assertEqual(out_attr.external.get(), 123)

    def test_simple_expression_evaluates_and_sets_output(self):
        # Simple literal expression
        definition = {
            'function': 'simple',
            'call': '1 + 2',
            'output': '#attr(out1)'
        }
        action = FunctionAction(name='simple',
                                parent=self.root,
                                definition=definition)
        action.prepare()
        result = action.run()
        self.assertEqual(result, 3)
        out_attr = self.attrs.get('out1')
        self.assertEqual(out_attr.external.get(), 3)

    def test_expression_with_input_reference(self):
        # Expression referencing existing attribute value
        # Initialize internal value of out1
        out1 = self.attrs.get('out1')
        out1.internal.set(5)
        definition = {
            'function': 'mul',
            'call': '#attr(out1) * 10',
            'output': '#attr(out2)'
        }
        action = FunctionAction(name='mul',
                                parent=self.root,
                                definition=definition)
        action.prepare()
        result = action.run()
        self.assertEqual(result, 50)
        out2 = self.attrs.get('out2')
        self.assertEqual(out2.internal.get(), 50)

    def test_multiple_outputs_receive_same_result(self):
        # Same result should be set to multiple outputs
        definition = {
            'function': 'multi',
            'call': '7',
            'output': ['#attr(out1)', '#attr(out2)']
        }
        action = FunctionAction(name='multi',
                                parent=self.root,
                                definition=definition)
        action.prepare()
        result = action.run()
        self.assertEqual(result, 7)
        self.assertEqual(self.attrs.get('out1').external.get(), 7)
        self.assertEqual(self.attrs.get('out2').external.get(), 7)


if __name__ == '__main__':
    unittest.main()
