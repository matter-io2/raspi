import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import io
import time

import makerbot_driver


class s3gHelperFunctionTests(unittest.TestCase):
    def setUp(self):
        self.g = makerbot_driver.Gcode.GcodeStates()

    def tearDown(self):
        self.g = None

    def test_get_position_unspecified_axis_location(self):
        setattr(self.g.position, 'X', None)
        self.assertRaises(makerbot_driver.Gcode.UnspecifiedAxisLocationError,
                          self.g.get_position)

    def test_get_position_no_offsets(self):
        position = {
            'X': 0,
            'Y': 1,
            'Z': 2,
            'A': 3,
            'B': 4,
        }
        for key in position:
            setattr(self.g.position, key, position[key])
        self.g.ofset_register = None
        expectedPosition = [0, 1, 2, 3, 4]
        self.assertEqual(expectedPosition, self.g.get_position())

    def test_lose_position(self):
        position = {
            'X': 1,
            'Y': 2,
            'Z': 3,
            'A': 4,
            'B': 5,
        }
        for key in position:
            setattr(self.g.position, key, position[key])
        axes = ['X', 'Y', 'Z', 'A', 'B']
        self.g.lose_position(axes)
        for axis in axes:
            self.assertEqual(getattr(self.g.position, axis), None)

    def test_lose_position_no_axes(self):
        position = {
            'X': 0,
            'Y': 0,
            'Z': 0,
            'A': 0,
            'B': 0,
        }
        for key in position:
            setattr(self.g.position, key, position[key])
        axes = []
        self.g.lose_position(axes)
        for axis in ['X', 'Y', 'Z', 'A', 'B']:
            self.assertEqual(getattr(self.g.position, axis), 0)

    def test_lose_position_minimal_codes(self):
        position = {
            'X': 0,
            'Y': 0,
            'Z': 0,
            'A': 0,
            'B': 0,
        }
        for key in position:
            setattr(self.g.position, key, position[key])
        axes = ['X']
        self.g.lose_position(axes)
        self.assertEqual(None, getattr(self.g.position, 'X'))
        for axis in ['Y', 'Z', 'A', 'B']:
            self.assertEqual(0, getattr(self.g.position, axis))

    def test_set_build_name(self):
        build_name = 'test'
        self.g.set_build_name(build_name)
        self.assertEqual(self.g.values['build_name'], build_name)

    def test_set_build_name_non_string(self):
        build_name = 9
        self.assertRaises(TypeError, self.g.set_build_name, build_name)

    def test_update_point_with_codes_only_a_and_b_has_tool_index(self):
        point = makerbot_driver.Gcode.Point()
        codes = {
            'X': 1,
            'Y': 2,
            'Z': 3,
            'A': 4,
            'B': 5,
        }
        tool_index = 0
        self.g.update_point_with_codes(point, codes, tool_index)
        expected_point = [1, 2, 3, 4, 5]
        got_point = point.ToList()
        self.assertEqual(expected_point, got_point)

    def test_update_point_with_codes_only_a_and_b_no_tool_index(self):
        point = makerbot_driver.Gcode.Point()
        codes = {
            'X': 1,
            'Y': 2,
            'Z': 3,
            'A': 4,
            'B': 5,
        }
        tool_index = None
        self.g.update_point_with_codes(point, codes, tool_index)
        expected_point = [1, 2, 3, 4, 5]
        got_point = point.ToList()
        self.assertEqual(expected_point, got_point)

    def test_update_point_with_codes_e_code_tool_index_0(self):
        point = makerbot_driver.Gcode.Point()
        codes = {
            'X': 1,
            'Y': 2,
            'Z': 3,
            'E': 4,
        }
        tool_index = 0
        self.g.update_point_with_codes(point, codes, tool_index)
        expected_point = [1, 2, 3, 4, None]
        got_point = point.ToList()
        self.assertEqual(expected_point, got_point)

    def test_update_point_with_codes_e_code_tool_index_1(self):
        point = makerbot_driver.Gcode.Point()
        codes = {
            'X': 1,
            'Y': 2,
            'Z': 3,
            'E': 4,
        }
        tool_index = 1
        self.g.update_point_with_codes(point, codes, tool_index)
        expected_point = [1, 2, 3, None ,4]
        got_point = point.ToList()
        self.assertEqual(expected_point, got_point)

    def test_update_point_with_codes_e_code_with_a_and_b_codes(self):
        point = makerbot_driver.Gcode.Point()
        codes = {
            'X': 0,
            'Y': 1,
            'Z': 2,
            'A': 3,
            'B': 4,
            'E': 5,
        }
        tool_index = 0
        with self.assertRaises(makerbot_driver.Gcode.ConflictingCodesError):
            self.g.update_point_with_codes(point, codes, tool_index)

    def test_update_point_with_codes_e_code_no_tool_index(self):
        point = makerbot_driver.Gcode.Point()
        codes = {
            'E': 0,
        }
        tool_index = None
        with self.assertRaises(makerbot_driver.Gcode.NoToolIndexError):
            self.g.update_point_with_codes(point, codes, tool_index)

    def test_update_point_with_codes_no_codes(self):
        point = makerbot_driver.Gcode.Point()
        codes = {}
        tool_index = None
        expected_point = [None, None, None, None, None]
        self.g.update_point_with_codes(point, codes, tool_index)
        got_point = point.ToList()
        self.assertEqual(expected_point, got_point)


class TestProfileInformationParsing(unittest.TestCase):

    def setUp(self):
        self.g = makerbot_driver.Gcode.GcodeStates()
        profile = makerbot_driver.Profile('ReplicatorDual')
        self.g.profile = profile

    def tearDown(self):
        self.g = None

    def test_get_axes_values_key_error(self):
        key = 'this_is_going_to_fail_;('
        self.assertRaises(KeyError, self.g.get_axes_values, key)

    def test_get_axes_values(self):
        key = 'steps_per_mm'
        expected_values = [
            94.139704,
            94.139704,
            400,
            -96.275,
            -96.275,
        ]
        self.assertEqual(expected_values, self.g.get_axes_values(key))


class MachineProfileWith4Axes(unittest.TestCase):
    def setUp(self):
        self.g = makerbot_driver.Gcode.GcodeStates()
        profile = makerbot_driver.Profile('ReplicatorSingle')
        self.g.profile = profile

    def tearDown(self):
        self.g = None

    def test_get_axes_values_with_one_0(self):
        key = 'steps_per_mm'
        expected_values = [
            94.139704,
            94.139704,
            400,
            -96.275,
            0,
        ]
        self.assertEqual(expected_values, self.g.get_axes_values(key))


class GetAxesFeedrateSPM(unittest.TestCase):

    def setUp(self):
        self.g = makerbot_driver.Gcode.GcodeStates()
        profile = makerbot_driver.Profile('ReplicatorDual')
        self.g.profile = profile

    def tearDown(self):
        self.g = None

    def test_get_axes_feedrate_and_spm_non_listed_axes(self):
        axes = 'XYZ'
        self.assertRaises(ValueError, self.g.get_axes_feedrate_and_SPM, axes)

    def test_get_axes_feedrate_and_spm_no_axes(self):
        axes = []
        feedrate, spm = self.g.get_axes_feedrate_and_SPM(axes)
        for l in (feedrate, spm):
            self.assertEqual(l, [])

    def test_get_axes_feedrate_and_spm_bad_axes(self):
        axes = ['q']
        self.assertRaises(KeyError, self.g.get_axes_feedrate_and_SPM, axes)

    def test_get_axes_feedrate_and_spm_one_axis(self):
        axes = ['X']
        feedrate, spm = self.g.get_axes_feedrate_and_SPM(axes)
        expected_feedrate = [12450]
        expected_spm = [94.139704]
        self.assertEqual(expected_feedrate, feedrate)
        self.assertEqual(expected_spm, spm)

    def test_get_axes_feedrate_and_spm_many_axes(self):
        axes = ['X', 'Y', 'Z']
        feedrate, spm = self.g.get_axes_feedrate_and_SPM(axes)
        expected_feedrate = [12450, 12450, 1170]
        expected_spm = [94.139704, 94.139704, 400]
        self.assertEqual(expected_feedrate, feedrate)
        self.assertEqual(expected_spm, spm)


if __name__ == "__main__":
    unittest.main()
