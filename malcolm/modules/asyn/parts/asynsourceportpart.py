from annotypes import Anno, Any

from malcolm.core import Part, PartRegistrar, StringMeta, Port
from malcolm.modules import ca


with Anno("Source Port type"):
    APortType = Port


class AsynSourcePortPart(Part):
    """Defines a string `Attribute` representing a asyn port that should be
    depicted as an Source Port on a Block"""

    def __init__(self,
                 name,  # type: ca.util.APartName
                 description,  # type: ca.util.AMetaDescription
                 rbv,  # type: ca.util.ARbv
                 port_type,  # type: APortType
                 group=None  # type: ca.util.AGroup
                 ):
        # type: (...) -> None
        super(AsynSourcePortPart, self).__init__(name)
        self.port_type = port_type
        self.meta = StringMeta(description)
        self.caa = ca.util.CAAttribute(
            self.meta, ca.util.catools.DBR_STRING, rbv=rbv, group=group,
            on_connect=self.update_tags)

    def setup(self, registrar):
        # type: (PartRegistrar) -> None
        self.caa.setup(registrar, self.name, self.register_hooked)

    def update_tags(self, value):
        # type: (Any) -> None
        # Add the Source Port tags
        old_tags = self.meta.tags
        new_tags = self.port_type.with_source_port_tag(
            old_tags, connected_value=value)
        if old_tags != new_tags:
            self.meta.set_tags(new_tags)
