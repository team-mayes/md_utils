# coding=utf-8

"""
Tests path_bin.
"""

import logging
import unittest
import os
from md_utils.path_bin import process_infile

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_calc_pka')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
PB_DATA_DIR = os.path.join(DATA_DIR, 'path_bin')
PB_GOOD = os.path.join(PB_DATA_DIR, '100th_CEC_z2_4.txt')
PB_BAD_LEN = os.path.join(PB_DATA_DIR, 'bad_lengths.txt')
PB_BAD_DATA = os.path.join(PB_DATA_DIR, 'bad_data.txt')


class TestProcessInfile(unittest.TestCase):
    def testGood(self):
        xyz_list, max_z, min_z = process_infile(PB_GOOD, "z")
        self.assertEqual(24470, len(xyz_list))
        self.assertAlmostEqual(7.827428, max_z)
        self.assertAlmostEqual(-9.040946, min_z)
        check_lines(self, xyz_list)

    def testBadLen(self):
        xyz_list, max_z, min_z = process_infile(PB_BAD_LEN, "x")
        self.assertEqual(2, len(xyz_list))
        check_lines(self, xyz_list)

    def testBadData(self):
        xyz_list, max_z, min_z = process_infile(PB_BAD_DATA, "y")
        self.assertEqual(5, len(xyz_list))
        check_lines(self, xyz_list)


def check_lines(self, xyz_list):
    """
    Verifies the length and data types of the values in each line of the given list.
    :param xyz_list: The list to check.
    """
    for item in xyz_list:
        self.assertEqual(3, len(item))
        for coord in item:
            self.assertIsInstance(coord, float)
