from malcolm.core import Part, config_tag, NumberMeta, PartRegistrar, \
    APartName, Widget


class CounterPart(Part):
    """Defines a counter `Attribute` with zero and increment `Method` objects"""

    def __init__(self, name):
        # type: (APartName) -> None
        super(CounterPart, self).__init__(name)
        # TODO: why doesn't this show up in the docs for CounterPart?
        self.counter = NumberMeta(
            "float64", "The current value of the counter",
            tags=[config_tag(), Widget.TEXTINPUT.tag()]
        ).create_attribute_model()
        """Attribute holding the current counter value"""

    def setup(self, registrar):
        # type: (PartRegistrar) -> None
        # Add some Attribute and Methods to the Block
        registrar.add_attribute_model(
            "counter", self.counter, self.counter.set_value)
        registrar.add_method_model(self.zero)
        registrar.add_method_model(self.increment)

    def zero(self):
        """Zero the counter attribute"""
        self.counter.set_value(0)

    def increment(self):
        """Add one to the counter attribute"""
        self.counter.set_value(self.counter.value + 1)
