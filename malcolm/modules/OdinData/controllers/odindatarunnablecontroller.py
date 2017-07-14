import sys

from malcolm.core.rlock import RLock
from malcolm.modules.scanning.controllers import RunnableController
from malcolm.core import method_also_takes, REQUIRED
from malcolm.modules.builtin.vmetas import StringMeta, NumberMeta

from malcolm.modules.OdinData.parts import \
    OdinDataFileWriterPart, OdinDataEigerProcessPart, OdinDataEigerDecoderPart

sys.path.insert(
    0, "/dls_sw/work/tools/RHEL6-x86_64/odin/odin-data/tools/python")
from odindataclient import OdinDataClient


@method_also_takes(
    "rank", NumberMeta("int16", "Rank of this process"), REQUIRED,
    "processes", NumberMeta("int16", "Total number of processes"), REQUIRED,
    "ipAddress", StringMeta(
        "IP of server where this service is running"), REQUIRED,
    "serverRank", NumberMeta("int16", "Rank of this process on its server"), 0,
    "fanIP", StringMeta("IP of server where EigerFan is running"), REQUIRED)
class OdinDataRunnableController(RunnableController):

    use_cothread = False  # Make ZMQ happy

    DATASET = "/entry/detector/detector"

    def __init__(self, process, parts, params):
        super(OdinDataRunnableController, self).__init__(
            process, parts, params)

        self.client = OdinDataClient(params.rank, params.processes,
                                     params.ipAddress,
                                     RLock(use_cothread=False),
                                     server_rank=params.serverRank)

        self.add_part(self._make_plugin_part(OdinDataEigerDecoderPart))
        self.add_part(self._make_plugin_part(OdinDataEigerProcessPart))
        self.add_part(self._make_plugin_part(OdinDataFileWriterPart))

    def _make_plugin_part(self, plugin):
        plugin_part = plugin(self.client.processor, self.mri)
        return plugin_part

    def _request_status(self):
        return self.client.request_status()
