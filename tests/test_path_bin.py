# coding=utf-8

"""
Tests path_bin.
"""

import logging
import unittest
import os
from md_utils.path_bin import process_infile, bin_data

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
        xyz_idx, min_z, max_z = process_infile(PB_GOOD, "z")
        self.assertEqual(24438, len(xyz_idx))
        self.assertEqual(24470, len(dump_idx(xyz_idx)))
        self.assertAlmostEqual(7.827428, max_z)
        self.assertAlmostEqual(-9.040946, min_z)
        check_idx_lines(self, xyz_idx)

    def testBadLen(self):
        xyz_list, min_z, max_z = process_infile(PB_BAD_LEN, "x")
        self.assertEqual(2, len(xyz_list))
        check_idx_lines(self, xyz_list)

    def testBadData(self):
        xyz_list, min_z, max_z = process_infile(PB_BAD_DATA, "y")
        self.assertEqual(5, len(xyz_list))
        check_idx_lines(self, xyz_list)


class TestBinData(unittest.TestCase):
    def testGood(self):
        xyz_idx, min_z, max_z = process_infile(PB_GOOD, "z")
        bins, bin_map = bin_data(xyz_idx, min_z, max_z, 0.1)
        self.assertEqual(24470, len(dump_idx(xyz_idx)))
        self.assertEqual(162, len(bins))
        self.assertEqual(162, len(bin_map))

def check_idx_lines(self, xyz_list):
    """
    Verifies the length and data types of the values in each line of the given list.
    :param xyz_list: The list to check.
    """
    for key, vals in xyz_list.items():
        self.assertIsInstance(key, float)
        self.assertGreaterEqual(len(vals), 1)
        for item in vals:
            self.assertEqual(3, len(item))
            for coord in item:
                self.assertIsInstance(coord, float)

def dump_idx(xyz_idx):
    dump = []
    for val in xyz_idx.values():
        dump.extend(val)
    return dump
