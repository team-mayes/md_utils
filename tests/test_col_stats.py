import unittest
import os

from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
from md_utils.col_stats import DEF_ARRAY_FILE, main
import logging


__author__ = 'hmayes'

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'small_tests')

# Input files #

DEF_INPUT = os.path.join(SUB_DATA_DIR, DEF_ARRAY_FILE)
HEADER_INPUT = os.path.join(SUB_DATA_DIR, "qm_box_sizes_header.txt")
CSV_INPUT = os.path.join(SUB_DATA_DIR, "qm_box_sizes.csv")
CSV_HEADER_INPUT = os.path.join(SUB_DATA_DIR, "qm_box_sizes_header.csv")
# CSV_HEADER_INPUT2 = os.path.join(SUB_DATA_DIR, "all_sum_dru_san_tight_small_fit.csv")
VEC_INPUT = os.path.join(SUB_DATA_DIR, "vector_input.txt")
BAD_INPUT = os.path.join(SUB_DATA_DIR, 'bad_per_col_stats_input.txt')
BAD_INPUT2 = os.path.join(SUB_DATA_DIR, 'bad_per_col_stats_input2.txt')
MIXED_INPUT = os.path.join(SUB_DATA_DIR, "msm_sum_output.csv")
ALL_NAN_INPUT = os.path.join(SUB_DATA_DIR, "msm_sum_output_no_floats.csv")
HIST_INPUT = os.path.join(SUB_DATA_DIR, "msm_sum_output_more.csv")
# NON_FLOAT_INPUT = os.path.join(SUB_DATA_DIR, "sum_2016-04-05_dru_san_ph4.5_ph4.5_300extInt_short.csv")

# Output files #

# noinspection PyUnresolvedReferences
CSV_OUT = os.path.join(SUB_DATA_DIR, "stats_qm_box_sizes.csv")
GOOD_CSV_OUT = os.path.join(SUB_DATA_DIR, "stats_qm_box_sizes_good.csv")
GOOD_CSV_BUFFER_OUT = os.path.join(SUB_DATA_DIR, "stats_qm_box_sizes_buffer_good.csv")
# noinspection PyUnresolvedReferences
CSV_HEADER_OUT = os.path.join(SUB_DATA_DIR, "stats_qm_box_sizes_header.csv")
GOOD_CSV_HEADER_OUT = os.path.join(SUB_DATA_DIR, "stats_qm_box_sizes_header_good.csv")
# noinspection PyUnresolvedReferences
BAD_INPUT_OUT = os.path.join(SUB_DATA_DIR, "stats_bad_per_col_stats_input.csv")
GOOD_BAD_INPUT_OUT = os.path.join(SUB_DATA_DIR, "stats_bad_per_col_stats_input_good.csv")
# noinspection PyUnresolvedReferences
MIXED_OUT = os.path.join(SUB_DATA_DIR, "stats_msm_sum_output.csv")
GOOD_MIXED_OUT = os.path.join(SUB_DATA_DIR, "stats_msm_sum_output_good.csv")
# noinspection PyUnresolvedReferences
ALL_NAN_OUT = os.path.join(SUB_DATA_DIR, "stats_msm_sum_output_no_floats.csv")
GOOD_ALL_NAN_OUT = os.path.join(SUB_DATA_DIR, "stats_msm_sum_output_no_floats_good.csv")
# noinspection PyUnresolvedReferences
HIST_OUT = os.path.join(SUB_DATA_DIR, "stats_msm_sum_output_more.csv")
GOOD_HIST_OUT = os.path.join(SUB_DATA_DIR, "stats_msm_sum_output_more_good.csv")
# noinspection PyUnresolvedReferences
HIST_COUNT = os.path.join(SUB_DATA_DIR, "counts_msm_sum_output_more.csv")
GOOD_HIST_COUNT = os.path.join(SUB_DATA_DIR, "counts_msm_sum_output_more_good.csv")
# noinspection PyUnresolvedReferences
HIST_PNG1 = os.path.join(SUB_DATA_DIR, "msm_sum_output_more(1,0)_max_rls.png")
# noinspection PyUnresolvedReferences
HIST_PNG2 = os.path.join(SUB_DATA_DIR, "msm_sum_output_more(1,0)_max_path.png")
# noinspection PyUnresolvedReferences
HIST_PNG3 = os.path.join(SUB_DATA_DIR, "msm_sum_output_more(0,-1)_max_rls.png")

MIN_MAX_INPUT = os.path.join(SUB_DATA_DIR, "msm_sum_output_test_min_max.csv")
MIN_MAX_FILE = os.path.join(SUB_DATA_DIR, "msm_ini_vals.csv")
MIN_MAX_OUT = os.path.join(SUB_DATA_DIR, "stats_msm_sum_output_test_min_max.csv")
GOOD_MIN_MAX_OUT = os.path.join(SUB_DATA_DIR, "stats_msm_sum_output_test_min_max_good.csv")

# Test data #

GOOD_OUT = "         Min values:        10.000000        14.995000        10.988000\n" \
           "         Max values:        11.891000        15.605000        18.314000\n" \
           "         Avg values:        11.092250        15.241000        16.348750\n" \
           "            Std dev:         0.798138         0.299536         3.576376"


class TestPerColFailWell(unittest.TestCase):
    def testNoArgs(self):
        with capture_stderr(main, []) as output:
            self.assertTrue("Problems reading file" in output)

    def testArrayInp(self):
        with capture_stderr(main, ["-f", VEC_INPUT]) as output:
            self.assertTrue("File contains a vector" in output)

    def testIncDimen(self):
        # Test what happens when the lines do not all have the same number of dimensions
        with capture_stderr(main, ["-f", BAD_INPUT2]) as output:
            self.assertTrue("Problems reading data" in output)
            self.assertTrue("3 values " in output)
            self.assertTrue("2 values" in output)

    def testDefInpWithBadBuffer(self):
        bad_buffer = 'xyz'
        with capture_stderr(main, ["-f", DEF_INPUT, "-b", bad_buffer]) as output:
            self.assertTrue('WARNING:  Problems reading data: Input for buffer ({}) could not be converted to '
                            'a float.'.format(bad_buffer) in output)

    def testNoSuchOption(self):
        with capture_stderr(main, ["-@", DEF_INPUT]) as output:
            self.assertTrue("unrecognized argument" in output)
            self.assertTrue(DEF_INPUT in output)


class TestPerCol(unittest.TestCase):
    def testDefInp(self):
        try:
            with capture_stdout(main, ["-f", DEF_INPUT]) as output:
                self.assertTrue(GOOD_OUT in output)
                self.assertFalse(diff_lines(CSV_OUT, GOOD_CSV_OUT))
        finally:
            silent_remove(CSV_OUT, disable=DISABLE_REMOVE)

    def testBadInput(self):
        # Test what happens when cannot convert a value to float
        try:
            with capture_stderr(main, ["-f", BAD_INPUT]) as output:
                self.assertTrue("could not be converted to a float" in output)
                self.assertFalse(diff_lines(BAD_INPUT_OUT, GOOD_BAD_INPUT_OUT))
        finally:
            silent_remove(BAD_INPUT_OUT, disable=DISABLE_REMOVE)

    def testDefInpWithBuffer(self):
        try:
            with capture_stdout(main, ["-f", DEF_INPUT, "-b", "6"]) as output:
                self.assertTrue('Max plus 6.0 buffer:'
                                '        17.891000        21.605000        24.314000' in output)
                self.assertFalse(diff_lines(CSV_OUT, GOOD_CSV_BUFFER_OUT))
        finally:
            silent_remove(CSV_OUT, disable=DISABLE_REMOVE)

    def testHeader(self):
        """
        This input file has a header that starts with a '#' so is ignored by np
        """
        if logger.isEnabledFor(logging.DEBUG):
            main(["-f", HEADER_INPUT])
        try:
            with capture_stdout(main, ["-f", HEADER_INPUT]) as output:
                self.assertTrue(GOOD_OUT in output)
                self.assertFalse(diff_lines(CSV_HEADER_OUT, GOOD_CSV_OUT))
        finally:
            silent_remove(CSV_HEADER_OUT, disable=DISABLE_REMOVE)

    def testCsv(self):
        """
        This input file has a header that starts with a '#' so is ignored by np.loadtxt
        """
        if logger.isEnabledFor(logging.DEBUG):
            main(["-f", CSV_INPUT, "-d", ","])
        try:
            with capture_stdout(main, ["-f", CSV_INPUT, "-d", ","]) as output:
                self.assertTrue(GOOD_OUT in output)
                self.assertFalse(diff_lines(CSV_OUT, GOOD_CSV_OUT))
        finally:
            silent_remove(CSV_OUT, disable=DISABLE_REMOVE)

    def testCsvHeader(self):
        """
        This input file has a header that starts with a '#' so is ignored by np.loadtxt
        """
        try:
            with capture_stdout(main, ["-f", CSV_HEADER_INPUT, "-n", "-d", ","]) as output:
                self.assertTrue(GOOD_OUT in output)
                self.assertFalse(diff_lines(CSV_HEADER_OUT, GOOD_CSV_HEADER_OUT))
        finally:
            silent_remove(CSV_HEADER_OUT, disable=DISABLE_REMOVE)

    def testMixedInput(self):
        """
        This input file has tuples and lists that cannot be handled by np.loadtxt
        """
        try:
            with capture_stderr(main, ["-f", MIXED_INPUT, "-n", "-d", ","]) as output:
                self.assertTrue("could not be converted to a float" in output)
                self.assertFalse(diff_lines(MIXED_OUT, GOOD_MIXED_OUT))
        finally:
            silent_remove(MIXED_OUT, disable=DISABLE_REMOVE)

    def testAllNanInput(self):
        """
        This input file has only tuples and lists
        """
        try:
            with capture_stderr(main, ["-f", ALL_NAN_INPUT, "-n", "-d", ","]) as output:
                self.assertTrue("could not be converted to a float" in output)
                self.assertFalse(diff_lines(ALL_NAN_OUT, GOOD_ALL_NAN_OUT))
        finally:
            silent_remove(ALL_NAN_OUT, logger.isEnabledFor(logging.DEBUG))

    def testHist(self):
        try:
            main(["-f", HIST_INPUT, "-n", "-d", ",", "-s"])
            for p_file in [HIST_PNG1, HIST_PNG2, HIST_PNG3]:
                self.assertGreater(os.path.getsize(p_file), 10000)
            self.assertFalse(diff_lines(HIST_OUT, GOOD_HIST_OUT))
            self.assertFalse(diff_lines(HIST_COUNT, GOOD_HIST_COUNT))
        finally:
            [silent_remove(o_file,
                           disable=DISABLE_REMOVE) for o_file in [HIST_PNG1, HIST_PNG2, HIST_PNG3,
                                                                  HIST_OUT, HIST_COUNT, ]]

    def testMinMax(self):
        try:
            main(["-f", MIN_MAX_INPUT, "-n", "-d", ",", "-m", MIN_MAX_FILE])
            self.assertFalse(diff_lines(MIN_MAX_OUT, GOOD_MIN_MAX_OUT))
        finally:
            silent_remove(MIN_MAX_OUT,  disable=DISABLE_REMOVE)

    # def testTemp(self):
    #     main(["-f", '/Users/Heather/no_backup/comb.csv', "-n", "-d", ","])
