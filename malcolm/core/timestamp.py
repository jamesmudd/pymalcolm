import time

import numpy as np
from annotypes import Anno

from .serializable import Serializable


with Anno("Seconds since Jan 1, 1970 00:00:00 UTC"):
    ASecondsPastEpoch = np.int64
with Anno("Nanoseconds relative to the secondsPastEpoch field"):
    ANanoseconds = np.int32
with Anno("An integer value whose interpretation is deliberately undefined"):
    AUserTag = np.int32


zero32 = np.int32(0)


@Serializable.register_subclass("time_t")
class TimeStamp(Serializable):

    __slots__ = ["secondsPastEpoch", "nanoseconds", "userTag"]

    # noinspection PyPep8Naming
    # secondsPastEpoch and userTag are camelCase to maintain compatibility with
    # EPICS normative types
    def __init__(self, secondsPastEpoch=None, nanoseconds=None, userTag=zero32):
        # type: (ASecondsPastEpoch, ANanoseconds, AUserTag) -> None
        # Set initial values
        if secondsPastEpoch is None or nanoseconds is None:
            now = time.time()
            self.secondsPastEpoch = np.int64(now)
            self.nanoseconds = np.int32(now % 1 / 1e-9)
        else:
            self.secondsPastEpoch = np.int64(secondsPastEpoch)
            self.nanoseconds = np.int32(nanoseconds)
        self.userTag = userTag

    def to_time(self):
        # type: () -> float
        return self.secondsPastEpoch + 1e-9 * self.nanoseconds

    def to_dict(self):
        # This needs to be fast as we do it a lot, so use a plain dict instead
        # of an OrderedDict
        return dict(
            typeid=self.typeid,
            secondsPastEpoch=self.secondsPastEpoch,
            nanoseconds=self.nanoseconds,
            userTag=self.userTag
        )
