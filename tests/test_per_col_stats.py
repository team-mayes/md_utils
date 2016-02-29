import unittest
import os

from md_utils import per_col_stats
from md_utils.md_common import capture_stdout


__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'small_tests')
INPUT1 = os.path.join(SUB_DATA_DIR, 'qm_box_sizes.txt')


class TestMaxDimen(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(per_col_stats.main,["-f", INPUT1]) as output:
            self.assertTrue("Min value per column:  11.103000  14.996000  17.988000" in output)
            self.assertTrue("Max value per column:  11.891000  15.605000  18.314000" in output)
            self.assertTrue("Avg value per column:  11.456333  15.323000  18.135667" in output)
            self.assertTrue("Std. dev. per column:   0.400247   0.306984   0.165149" in output)

