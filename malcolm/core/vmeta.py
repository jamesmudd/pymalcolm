from .meta import Meta
from .ntscalar import NTScalar


class VMeta(Meta):
    """Abstract base class for validating the values of Attributes"""
    attribute_class = NTScalar

    def validate(self, value):
        """Abstract function to validate a given value

        Args:
            value: Value to validate
        """
        raise NotImplementedError()

    def create_attribute(self, initial_value=None):
        """Make an Attribute instance of the correct type for this Meta

        Args:
            initial_value: The initial value the Attribute should take
        """
        attr = self.attribute_class(self, initial_value)
        return attr

    def doc_type_string(self):
        """Abstract function to return the python type string.

        For example, "str" or "numpy.int32"
        """
        raise NotImplementedError()
