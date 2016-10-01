# coding=utf-8

"""
Tests for wham_rad.
"""

import logging
import unittest
import os

import md_utils
from md_utils import md_common
from md_utils.lammps import find_atom_data
from md_utils.lammps_dist import atom_distances
from md_utils.md_common import InvalidDataError, diff_lines

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# File Locations #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
LAM_DATA_DIR = os.path.join(DATA_DIR, 'lammps_dist')
DUMP_PATH = os.path.join(LAM_DATA_DIR, '1.50_small.dump')
STD_DIST_PATH = os.path.join(LAM_DATA_DIR, 'std_pairs_1.50_small.csv')
DIST_PATH = os.path.join(LAM_DATA_DIR, 'pairs_1.50_small.csv')
PAIRS_PATH = os.path.join(LAM_DATA_DIR, 'atom_pairs.txt')
PAIRS_PATH2 = os.path.join(LAM_DATA_DIR, 'atom_pairs2.txt')
DUMP_LIST = os.path.join(LAM_DATA_DIR, 'dump_list.txt')
DUMP_OUT = os.path.join(LAM_DATA_DIR, 'pairs_dump_list.csv')
GOOD_DUMP_OUT = os.path.join(LAM_DATA_DIR, 'pairs_dump_list_good.csv')

# Data #

LAM_ATOMS = {7500000: {17467: [1116, 38, -0.82, -13.3474, -9.77472, 0.566407],
                       4167: [272, 9, -0.51, -2.90332, 4.1959, -0.319479]},
             7500010: {17467: [1116, 38, -0.82, -13.2865, -9.72761, 0.578118],
                       4167: [272, 9, -0.51, -2.92659, 4.13608, -0.270837]},
             7500020: {17467: [1116, 38, -0.82, -13.2259, -9.67559, 0.587055],
                       4167: [272, 9, -0.51, -2.95968, 4.10041, -0.239808]},
             7500030: {17467: [1116, 38, -0.82, -13.1778, -9.6271, 0.595548],
                       4167: [272, 9, -0.51, -3.00944, 4.05809, -0.207916]},
             7500040: {17467: [1116, 38, -0.82, -13.1348, -9.58866, 0.605338],
                       4167: [272, 9, -0.51, -3.05803, 4.06638, -0.176754]},
             7500050: {17467: [1116, 38, -0.82, -13.1059, -9.56761, 0.624937],
                       4167: [272, 9, -0.51, -3.08408, 4.11423, -0.1371]},
             7500060: {17467: [1116, 38, -0.82, -13.0893, -9.54197, 0.645511],
                       4167: [272, 9, -0.51, -3.15378, 4.16002, -0.134485]},
             7500070: {17467: [1116, 38, -0.82, -13.0658, -9.51954, 0.683413],
                       4167: [272, 9, -0.51, -3.19654, 4.23121, -0.120521]},
             7500080: {17467: [1116, 38, -0.82, -13.0411, -9.49329, 0.73031],
                       4167: [272, 9, -0.51, -3.20867, 4.30202, -0.0954135]},
             7500090: {17467: [1116, 38, -0.82, -13.0308, -9.46276, 0.771404],
                       4167: [272, 9, -0.51, -3.27254, 4.37238, -0.111996]},
             7500100: {17467: [1116, 38, -0.82, -13.028, -9.43718, 0.8038],
                       4167: [272, 9, -0.51, -3.39168, 4.40742, -0.184281]}}

ATOM_DIST = {7500000: {(4167, 17467): 17.465446579913035,
                       (4168, 4197): 5.572394809599909},
             7500010: {(4167, 17467): 17.32773384537704,
                       (4168, 4197): 5.592634621806166},
             7500020: {(4167, 17467): 17.200498583156506,
                       (4168, 4197): 5.659566262054097},
             7500030: {(4167, 17467): 17.06826074399486,
                       (4168, 4197): 5.534633534862449},
             7500040: {(4167, 17467): 16.98861615703186,
                       (4168, 4197): 5.3843480598621225},
             7500050: {(4167, 17467): 16.97675829737141,
                       (4168, 4197): 5.418799109249207},
             7500060: {(4167, 17467): 16.943065879306378,
                       (4168, 4197): 5.266585720056211},
             7500070: {(4167, 17467): 16.944961740483688,
                       (4168, 4197): 4.966874907434251},
             7500080: {(4167, 17467): 16.96081003370571,
                       (4168, 4197): 4.771782319654156},
             7500090: {(4167, 17467): 16.953322170217845,
                       (4168, 4197): 4.67085250454015},
             7500100: {(4167, 17467): 16.896979504188344,
                       (4168, 4197): 4.540623282628058}}


# Tests #

class TestFindAtomData(unittest.TestCase):
    def testGood(self):
        self.assertEqual(LAM_ATOMS, find_atom_data(DUMP_PATH, {4167, 17467}))

    def testMissingAtoms(self):
        with self.assertRaises(InvalidDataError):
            find_atom_data(DUMP_PATH, {-97})


class TestAtomDistances(unittest.TestCase):
    def testTwoPair(self):
        pairs = [(4167, 17467), (4168, 4197)]
        dists = atom_distances(DUMP_PATH, pairs)
        for tstep, tdist in ATOM_DIST.items():
            for pair in pairs:
                self.assertAlmostEqual(tdist[pair], dists[tstep][pair])


class TestMain(unittest.TestCase):
    def testDefault(self):
        try:
            md_utils.lammps_dist.main(["-f", DUMP_PATH, "-p", PAIRS_PATH])
            self.assertFalse(diff_lines(STD_DIST_PATH, DIST_PATH))
        finally:
            md_common.silent_remove(DIST_PATH)

    def testDumpList(self):
        try:
            md_utils.lammps_dist.main(["-l", DUMP_LIST, "-p", PAIRS_PATH2])
            self.assertFalse(diff_lines(DUMP_OUT, GOOD_DUMP_OUT))
        finally:
            md_common.silent_remove(DUMP_OUT)
