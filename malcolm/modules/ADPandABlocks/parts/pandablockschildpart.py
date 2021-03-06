import re

from annotypes import add_call_types

from malcolm.core import PartRegistrar
from malcolm.modules import scanning, ADCore, builtin
from malcolm.modules.ADCore.util import AttributeDatasetType


def capture_field(child, attr_name):
    if attr_name.endswith("Capture"):
        attr = child[attr_name]
        if attr.value.lower() != "no":
            return attr.value


def dataset_info(name, child, attr_name, capture):
    dataset_name_attr = attr_name + "DatasetName"
    dataset_type_attr = attr_name + "DatasetType"
    if dataset_name_attr in child and dataset_type_attr in child:
        dataset_name = child[dataset_name_attr].value
        if dataset_name == "":
            return
        assert "." not in dataset_name, \
            "Dataset name should not contain '.'"
        dataset_type = AttributeDatasetType(child[dataset_type_attr].value)
        uppercase_attr = re.sub("([A-Z])", r"_\1", attr_name).upper()
        # If we have Min Max Mean, just take Mean
        capture = capture.split(" ")[-1]
        return ADCore.infos.NDAttributeDatasetInfo(
            name=dataset_name,
            type=dataset_type,
            rank=2,
            attr="%s.%s.%s" % (name, uppercase_attr, capture))


class PandABlocksChildPart(builtin.parts.ChildPart):
    def setup(self, registrar):
        # type: (PartRegistrar) -> None
        super(PandABlocksChildPart, self).setup(registrar)
        self.register_hooked(scanning.hooks.ReportStatusHook,
                             self.report_status)

    @add_call_types
    def report_status(self, context):
        # type: (scanning.hooks.AContext) -> scanning.hooks.UInfos
        ret = []
        child = context.block_view(self.mri)
        for attr_name in child:
            capture = capture_field(child, attr_name)
            if capture:
                info = dataset_info(
                    self.name, child, attr_name[:-len("Capture")], capture)
                if info:
                    ret.append(info)
        return ret
