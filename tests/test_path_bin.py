# coding=utf-8

"""
Tests path_bin.
"""

import logging
import unittest
import os
from md_utils.md_common import find_backup_filenames, silent_remove, diff_lines
from md_utils.path_bin import process_infile, bin_data, main

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
PB_DATA_DIR = os.path.join(DATA_DIR, 'path_bin')
PB_GOOD = os.path.join(PB_DATA_DIR, '100th_CEC_z2_4.txt')
PB_GOOD_XYZ = os.path.join(PB_DATA_DIR, '100th_CEC_z2_4.xyz')
PB_REF_XYZ = os.path.join(PB_DATA_DIR, 'ref-100th_CEC_z2_4.xyz')
PB_GOOD_LOG = os.path.join(PB_DATA_DIR, '100th_CEC_z2_4.log')
PB_REF_LOG = os.path.join(PB_DATA_DIR, 'ref-100th_CEC_z2_4.log')
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


class TestMain(unittest.TestCase):
    def testGood(self):
        try:
            main([PB_GOOD])
            self.assertEqual(2, len(diff_lines(PB_GOOD_XYZ, PB_REF_XYZ, delimiter=" ", csv_format=False)))
            self.assertEqual(0, len(diff_lines(PB_GOOD_LOG, PB_REF_LOG)))
        finally:
            silent_remove(PB_GOOD_LOG)
            silent_remove(PB_GOOD_XYZ)
            # pass

    def testMoveExisting(self):
        try:
            self.assertFalse(find_backup_filenames(PB_GOOD_LOG))
            self.assertFalse(find_backup_filenames(PB_GOOD_XYZ))
            main([PB_GOOD])
            # repeated on purpose to make back-up files
            main([PB_GOOD])
            log_backs = find_backup_filenames(PB_GOOD_LOG)
            self.assertEqual(1, len(log_backs))
            xyz_backs = find_backup_filenames(PB_GOOD_XYZ)
            self.assertEqual(1, len(xyz_backs))
        finally:
            silent_remove(PB_GOOD_LOG)
            silent_remove(PB_GOOD_XYZ)
            for log_back in find_backup_filenames(PB_GOOD_LOG):
                silent_remove(log_back)
            for xyz_back in find_backup_filenames(PB_GOOD_XYZ):
                silent_remove(xyz_back)


def check_idx_lines(self, xyz_list):
    """
    Verifies the length and data types of the values in each line of the given list.
    :param self
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
