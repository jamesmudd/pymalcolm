from malcolm.core import StringArray, Serializable, VArrayMeta


@Serializable.register_subclass("malcolm:core/StringArrayMeta:1.0")
class StringArrayMeta(VArrayMeta):
    """Meta object containing information for a string array"""

    def validate(self, value):
        """
        Verify value can be iterated and cast elements to strings

        Args:
            value (iterable): value to be validated

        Returns:
            List of Strings or None if value is None
        """
        if value is None:
            return StringArray()
        else:
            return StringArray(value)

    def doc_type_string(self):
        return "[str]"
