from loggable import Loggable
from malcolm.core.attributemeta import AttributeMeta


class MapMeta(Loggable):
    """A meta object to store a set of attribute metas"""

    def __init__(self, name):
        super(MapMeta, self).__init__(logger_name=name)

        self.name = name
        self.attributes = []

    def add_element(self, attribute_meta, required=False):
        """
        Add an attribute to the list, stating whether it is required.

        Args:
            attribute_meta(AttributeMeta): Attribute instance to store
            required(bool): Whether attribute is required or optional
        """

        self.attributes.append((attribute_meta, required))
