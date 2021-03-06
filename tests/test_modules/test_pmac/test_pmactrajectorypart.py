from mock import Mock, call, patch

from scanpointgenerator import LineGenerator, CompoundGenerator
import pytest

from malcolm.core import Context, Process
from malcolm.modules.pmac.parts import PmacTrajectoryPart
from malcolm.modules.pmac.infos import MotorInfo, ControllerInfo, CSInfo
from malcolm.modules.pmac.blocks import pmac_trajectory_block, cs_block
from malcolm.testutil import ChildTestCase


class TestPMACTrajectoryPart(ChildTestCase):
    def setUp(self):
        self.process = Process("Process")
        self.context = Context(self.process)
        self.cs = self.create_child_block(
            cs_block, self.process, mri="PMAC:CS1", prefix="PV:CSPRE")
        self.child = self.create_child_block(
            pmac_trajectory_block, self.process, mri="PMAC:TRAJ",
            prefix="PV:PRE")
        self.o = PmacTrajectoryPart(name="pmac", mri="PMAC:TRAJ")
        self.process.start()

    def tearDown(self):
        del self.context
        self.process.stop(timeout=1)

    def test_init(self):
        registrar = Mock()
        self.o.setup(registrar)
        registrar.add_attribute_model.assert_called_once_with(
            "minTurnaround", self.o.min_turnaround,
            self.o.min_turnaround.set_value
        )

    def test_bad_units(self):
        with self.assertRaises(AssertionError) as cm:
            self.do_configure(["x", "y"], units="m")
        assert str(cm.exception) == "x: Expected scan units of 'm', got 'mm'"

    def resolutions_and_use_call(self, useB=True):
        return [
            call.put('useA', True),
            call.put('useB', useB),
            call.put('useC', False),
            call.put('useU', False),
            call.put('useV', False),
            call.put('useW', False),
            call.put('useX', False),
            call.put('useY', False),
            call.put('useZ', False)]

    def make_part_info(self, x_pos=0.5, y_pos=0.0, units="mm"):
        part_info = dict(
            xpart=[MotorInfo(
                cs_axis="A",
                cs_port="CS1",
                acceleration=2.5,
                resolution=0.001,
                offset=0.0,
                max_velocity=1.0,
                current_position=x_pos,
                scannable="x",
                velocity_settle=0.0,
                units=units
            )],
            ypart=[MotorInfo(
                cs_axis="B",
                cs_port="CS1",
                acceleration=2.5,
                resolution=0.001,
                offset=0.0,
                max_velocity=1.0,
                current_position=y_pos,
                scannable="y",
                velocity_settle=0.0,
                units=units
            )],
            brick=[ControllerInfo(i10=1705244)],
            cs1=[CSInfo(mri="PMAC:CS1", port="CS1")]
        )
        return part_info

    def do_configure(self, axes_to_scan, completed_steps=0, x_pos=0.5,
                     y_pos=0.0, duration=1.0, units="mm"):
        part_info = self.make_part_info(x_pos, y_pos, units)
        steps_to_do = 3 * len(axes_to_scan)
        xs = LineGenerator("x", "mm", 0.0, 0.5, 3, alternate=True)
        ys = LineGenerator("y", "mm", 0.0, 0.1, 2)
        generator = CompoundGenerator([ys, xs], [], [], duration)
        generator.prepare()
        self.o.configure(
            self.context, completed_steps, steps_to_do, part_info,
            generator, axes_to_scan)

    def test_validate(self):
        generator = CompoundGenerator([], [], [], 0.0102)
        axesToMove = ["x"]
        part_info = self.make_part_info()
        ret = self.o.validate(part_info, generator, axesToMove)
        expected = 0.010166
        assert ret.value.duration == expected

    @patch("malcolm.modules.pmac.parts.pmactrajectorypart.INTERPOLATE_INTERVAL",
           0.2)
    def test_configure(self):
        # Pretend to respond on demand values before they are actually set
        self.set_attributes(self.cs, demandA=-0.1375, demandB=0.0)
        self.do_configure(axes_to_scan=["x", "y"])
        assert self.cs.handled_requests.mock_calls == [
            call.put('deferMoves', True),
            call.put('csMoveTime', 0),
            call.put('demandA', -0.1375),
            call.put('demandB', 0.0),
            call.put('deferMoves', False)
        ]
        assert self.child.handled_requests.mock_calls == [
            call.put('numPoints', 4000000),
            call.put('cs', 'CS1'),
            call.put('useA', False),
            call.put('useB', False),
            call.put('useC', False),
            call.put('useU', False),
            call.put('useV', False),
            call.put('useW', False),
            call.put('useX', False),
            call.put('useY', False),
            call.put('useZ', False),
            call.put('pointsToBuild', 1),
            call.put('timeArray', pytest.approx([2000])),
            call.put('userPrograms', pytest.approx([8])),
            call.put('velocityMode', pytest.approx([3])),
            call.post('buildProfile'),
            call.post('executeProfile'),
        ] + self.resolutions_and_use_call() + [
            call.put('pointsToBuild', 16),
            # pytest.approx to allow sensible compare with numpy arrays
            call.put('positionsA', pytest.approx([
                -0.125, 0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.6375,
                0.625, 0.5, 0.375, 0.25, 0.125, 0.0, -0.125, -0.1375])),
            call.put('positionsB', pytest.approx([
                 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.05,
                 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])),
            call.put('timeArray', pytest.approx([
                 100000, 500000, 500000, 500000, 500000, 500000, 500000,
                 200000, 200000, 500000, 500000, 500000, 500000, 500000,
                 500000, 100000])),
            call.put('userPrograms', pytest.approx([
                 1, 4, 1, 4, 1, 4, 2, 8, 1, 4, 1, 4, 1, 4, 2, 8])),
            call.put('velocityMode', pytest.approx([
                 2, 0, 0, 0, 0, 0, 1, 0, 2, 0, 0, 0, 0, 0, 1, 3])),
            call.post('buildProfile')
        ]
        assert self.o.completed_steps_lookup == [
            0, 0, 1, 1, 2, 2, 3, 3,
            3, 3, 4, 4, 5, 5, 6, 6]

    @patch("malcolm.modules.pmac.parts.pmactrajectorypart.PROFILE_POINTS", 4)
    @patch("malcolm.modules.pmac.parts.pmactrajectorypart.INTERPOLATE_INTERVAL",
           0.2)
    def test_update_step(self):
        # Pretend to respond on demand values before they are actually set
        self.set_attributes(self.cs, demandA=-0.1375, demandB=0.0)
        self.do_configure(axes_to_scan=["x", "y"], x_pos=0.0, y_pos=0.2)
        positionsA = self.child.handled_requests.put.call_args_list[-5][0][1]
        assert len(positionsA) == 4
        assert positionsA[-1] == 0.25
        assert self.o.end_index == 2
        assert len(self.o.completed_steps_lookup) == 5
        assert len(self.o.profile["time_array"]) == 1
        self.o.registrar = Mock()
        self.child.handled_requests.reset_mock()
        self.o.update_step(
            3, self.context.block_view("PMAC:TRAJ"))
        self.o.registrar.report.assert_called_once()
        assert self.o.registrar.report.call_args[0][0].steps == 1
        assert not self.o.loading
        assert self.child.handled_requests.mock_calls == [
            call.put('pointsToBuild', 4),
            call.put('positionsA', pytest.approx([
                0.375, 0.5, 0.625, 0.6375])),
            call.put('positionsB', pytest.approx([
                0.0, 0.0, 0.0, 0.05])),
            call.put('timeArray', pytest.approx([
                500000, 500000, 500000, 200000])),
            call.put('userPrograms', pytest.approx([
                1, 4, 2, 8])),
            call.put('velocityMode', pytest.approx([
                0, 0, 1, 0])),
            call.post('appendProfile')]
        assert self.o.end_index == 3
        assert len(self.o.completed_steps_lookup) == 9
        assert len(self.o.profile["time_array"]) == 1

    def test_run(self):
        self.o.run(self.context)
        assert self.child.handled_requests.mock_calls == [
            call.post('executeProfile')]

    def test_reset(self):
        self.o.reset(self.context)
        assert self.child.handled_requests.mock_calls == [
            call.post('abortProfile')]

    def test_multi_run(self):
        # Pretend to respond on demand values before they are actually set
        self.set_attributes(self.cs, demandA=-0.1375)
        self.do_configure(axes_to_scan=["x"])
        assert self.o.completed_steps_lookup == (
            [0, 0, 1, 1, 2, 2, 3, 3])
        self.child.handled_requests.reset_mock()
        # Pretend to respond on demand values before they are actually set
        self.set_attributes(self.cs, demandA=0.6375)
        self.do_configure(
            axes_to_scan=["x"], completed_steps=3, x_pos=0.6375)
        assert self.child.handled_requests.mock_calls == [
            call.put('numPoints', 4000000),
            call.put('cs', 'CS1'),
            call.put('useA', False),
            call.put('useB', False),
            call.put('useC', False),
            call.put('useU', False),
            call.put('useV', False),
            call.put('useW', False),
            call.put('useX', False),
            call.put('useY', False),
            call.put('useZ', False),
            call.put('pointsToBuild', 1),
            call.put('timeArray', pytest.approx([2000])),
            call.put('userPrograms', pytest.approx([8])),
            call.put('velocityMode', pytest.approx([3])),
            call.post('buildProfile'),
            call.post('executeProfile'),
        ] + self.resolutions_and_use_call(useB=False) + [
           call.put('pointsToBuild', 8),
           call.put('positionsA', pytest.approx([
               0.625, 0.5, 0.375, 0.25, 0.125, 0.0, -0.125, -0.1375])),
           call.put('timeArray', pytest.approx([
               100000, 500000, 500000, 500000, 500000, 500000, 500000,
               100000])),
           call.put('userPrograms', pytest.approx([1, 4, 1, 4, 1, 4, 2, 8])),
           call.put('velocityMode', pytest.approx([2, 0, 0, 0, 0, 0, 1, 3])),
           call.post('buildProfile')
        ]

    @patch("malcolm.modules.pmac.parts.pmactrajectorypart.INTERPOLATE_INTERVAL",
           0.2)
    def test_long_steps_lookup(self):
        # Pretend to respond on demand values before they are actually set
        self.set_attributes(self.cs, demandA=0.6250637755102041)
        self.do_configure(
            axes_to_scan=["x"], completed_steps=3, x_pos=0.62506, duration=14.0)
        assert self.child.handled_requests.mock_calls[-6:] == [
            call.put('pointsToBuild', 14),
            call.put('positionsA', pytest.approx([
                0.625, 0.5625, 0.5, 0.4375, 0.375, 0.3125, 0.25, 0.1875,
                0.125, 0.0625, 0.0, -0.0625, -0.125, -0.12506377551020409])),
            call.put('timeArray', pytest.approx([
                7143, 3500000, 3500000, 3500000, 3500000, 3500000, 3500000,
                3500000, 3500000, 3500000, 3500000, 3500000, 3500000, 7143])),
            call.put('userPrograms', pytest.approx([
                1, 0, 4, 0, 1, 0, 4, 0, 1, 0, 4, 0, 2, 8])),
            call.put('velocityMode', pytest.approx([
                2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3])),
            call.post('buildProfile')
        ]
        assert self.o.completed_steps_lookup == (
            [3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6])

    @patch("malcolm.modules.pmac.parts.pmactrajectorypart.PROFILE_POINTS", 9)
    def test_split_in_a_long_step_lookup(self):
        # Pretend to respond on demand values before they are actually set
        self.set_attributes(self.cs, demandA=0.6250637755102041)
        self.do_configure(
            axes_to_scan=["x"], completed_steps=3, x_pos=0.62506,
            duration=14.0)
        # The last 6 calls show what trajectory we are building, ignore the
        # first 11 which are just the useX calls and cs selection
        assert self.child.handled_requests.mock_calls[-6:] == [
            call.put('pointsToBuild', 9),
            call.put('positionsA', pytest.approx([
                0.625, 0.5625, 0.5, 0.4375, 0.375, 0.3125, 0.25, 0.1875,
                0.125])),
            call.put('timeArray', pytest.approx([
                7143, 3500000, 3500000, 3500000, 3500000, 3500000, 3500000,
                3500000, 3500000])),
            call.put('userPrograms', pytest.approx([
                1, 0, 4, 0, 1, 0, 4, 0, 1])),
            call.put('velocityMode', pytest.approx([
                2, 0, 0, 0, 0, 0, 0, 0, 0])),
            call.post('buildProfile')
        ]
        # The completed steps works on complete (not split) steps, so we expect
        # the last value to be the end of step 6, even though it doesn't
        # actually appear in the velocity arrays
        assert self.o.completed_steps_lookup == (
            [3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6])
        # Mock out the registrar that would have been registered when we
        # attached to a controller
        self.o.registrar = Mock()
        # Now call update step and get it to generate the next lot of points
        # scanned can be any index into completed_steps_lookup so that there
        # are less than PROFILE_POINTS left to go in it
        self.o.update_step(
            scanned=2, child=self.process.block_view("PMAC:TRAJ"))
        # Expect the rest of the points
        assert self.child.handled_requests.mock_calls[-6:] == [
            call.put('pointsToBuild', 5),
            call.put('positionsA', pytest.approx([
                0.0625, 0.0, -0.0625, -0.125, -0.12506377551020409])),
            call.put('timeArray',pytest.approx([
                3500000, 3500000, 3500000, 3500000, 7143])),
            call.put('userPrograms', pytest.approx([
                0, 4, 0, 2, 8])),
            call.put('velocityMode', pytest.approx([
                0, 0, 0, 1, 3])),
            call.post('appendProfile')
        ]
        assert self.o.registrar.report.call_count == 1
        assert self.o.registrar.report.call_args[0][0].steps == 3
        # And for the rest of the lookup table to be added
        assert self.o.completed_steps_lookup == (
            [3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6])

