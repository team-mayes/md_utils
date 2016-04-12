import unittest
import os

from md_utils import per_col_stats
from md_utils.md_common import capture_stdout, capture_stderr
from md_utils.per_col_stats import DEF_ARRAY_FILE


__author__ = 'hmayes'

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'small_tests')

# Input files #

DEF_INPUT = os.path.join(SUB_DATA_DIR, DEF_ARRAY_FILE)
VEC_INPUT = os.path.join(SUB_DATA_DIR, "vector_input.txt")
BAD_INPUT = os.path.join(SUB_DATA_DIR, 'bad_per_col_stats_input.txt')
BAD_INPUT2 = os.path.join(SUB_DATA_DIR, 'bad_per_col_stats_input2.txt')


class TestPerCol(unittest.TestCase):
    def testNoArgs(self):
        with capture_stderr(per_col_stats.main, []) as output:
            self.assertTrue("Problems reading file" in output)

    def testDefInp(self):
        # per_col_stats.main(["-f", DEF_INPUT])
        with capture_stdout(per_col_stats.main, ["-f", DEF_INPUT]) as output:
            self.assertTrue("Min value per column:    10.000000    14.995000    10.988000" in output)
            self.assertTrue("Max value per column:    11.891000    15.605000    18.314000" in output)
            self.assertTrue("Avg value per column:    11.092250    15.241000    16.348750" in output)
            self.assertTrue("Std. dev. per column:     0.798138     0.299536     3.576376" in output)

    def testArrayInp(self):
        # per_col_stats.main(["-f", VEC_INPUT])
        with capture_stderr(per_col_stats.main, ["-f", VEC_INPUT]) as output:
            self.assertTrue("File contains a vector" in output)

    def testBadInput(self):
        # Test what happens when cannot convert a value to float
        # per_col_stats.main(["-f", BAD_INPUT])
        with capture_stderr(per_col_stats.main, ["-f", BAD_INPUT]) as output:
            self.assertTrue("Could not convert the following line to floats" in output)

    def testIncDimen(self):
        # Test what happens when the lines do not all have the same number of dimensions
        with capture_stderr(per_col_stats.main, ["-f", BAD_INPUT2]) as output:
            self.assertTrue("Problems reading data" in output)
            self.assertTrue("found 3 values " in output)
            self.assertTrue("and 2 values" in output)

    def testDefInpWithBuffer(self):
        with capture_stdout(per_col_stats.main, ["-f", DEF_INPUT, "-b", "6"]) as output:
            self.assertTrue('Max value plus 6.0 buffer:    17.891000    21.605000    24.314000' in output)

    def testDefInpWithBadBuffer(self):
        bad_buffer = 'xyz'
        with capture_stderr(per_col_stats.main, ["-f", DEF_INPUT, "-b", bad_buffer]) as output:
            self.assertTrue('WARNING:  Problems reading data: Input for buffer ({}) could not be converted to '
                            'a float.'.format(bad_buffer) in output)
