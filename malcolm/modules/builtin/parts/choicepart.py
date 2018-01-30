from annotypes import Anno, Array, Sequence, Union

from malcolm.core import Part, PartRegistrar, ChoiceMeta, APartName, \
    AMetaDescription
from ..util import set_tags, AWriteable, AConfig, AGroup, AWidget


with Anno("Possible choices for this attribute"):
    AChoices = Array[str]
with Anno("Initial value of the created attribute"):
    AValue = str
UChoices = Union[AChoices, Sequence[str], str]


class ChoicePart(Part):
    """Create a single choice Attribute on the Block"""
    def __init__(self,
                 name,  # type: APartName
                 description,  # type: AMetaDescription
                 choices,  # type: UChoices
                 value,  # type: AValue
                 writeable=False,  # type: AWriteable
                 config=True,  # type: AConfig
                 group=None,  # type: AGroup
                 widget=None,  # type: AWidget
                 ):
        # type: (...) -> None
        super(ChoicePart, self).__init__(name)
        meta = ChoiceMeta(description, choices)
        set_tags(meta, writeable, config, group, widget)
        self.attr = meta.create_attribute_model(value)
        self.writeable_func = self.attr.set_value if writeable else None

    def setup(self, registrar):
        # type: (PartRegistrar) -> None
        registrar.add_attribute_model(self.name, self.attr, self.writeable_func)

