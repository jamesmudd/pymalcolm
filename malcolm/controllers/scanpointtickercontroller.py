import numpy
import time

from malcolm.core.attribute import Attribute
from malcolm.core.controller import Controller
from malcolm.core.method import takes, Method, REQUIRED
from malcolm.metas import PointGeneratorMeta, StringMeta, NumberMeta
from malcolm.statemachines import RunnableDeviceStateMachine


@RunnableDeviceStateMachine.insert
@takes()
class ScanPointTickerController(Controller):

    def create_attributes(self):
        self.value = Attribute("value", NumberMeta(
            "meta", "Value", numpy.float64))
        yield self.value
        self.generator = Attribute(
            "generator", PointGeneratorMeta("meta", "Scan Point Generator"))
        yield self.generator
        self.axis_name = Attribute(
            "axis_name", StringMeta("meta", "Name of the axis"))
        yield self.axis_name
        self.exposure = Attribute(
            "exposure", NumberMeta("meta", "Exposure time", numpy.float64))
        yield self.exposure

    @takes(PointGeneratorMeta("generator", "Generator instance"), REQUIRED,
           StringMeta("axis_name", "Specifier for axis"), REQUIRED,
           NumberMeta("exposure",
                      "Detector exposure time", numpy.float64), REQUIRED)
    def configure(self, params):
        """
        Configure the controller

        Args:
            generator(PointGenerator): Generator to create points
            axis_name(String): Specifier for axis
            exposure(Double): Exposure time for detector
        """

        self.generator.set_value(params.generator)
        self.axis_name.set_value(params.axis_name)
        self.exposure.set_value(params.exposure)
        self.block.notify_subscribers()

    @Method.wrap_method
    def run(self):
        """
        Start the ticker process

        Yields:
            Point: Scan points from PointGenerator
        """
        axis_name = self.axis_name.value
        for point in self.generator.value.iterator():
            self.value.set_value(point.positions[axis_name])
            self.block.notify_subscribers()
            time.sleep(self.exposure.value)