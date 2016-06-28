# coding=utf-8

"""
Tests for the common lib.
"""
import logging
import shutil
import tempfile
import unittest
import os

from md_utils.md_common import (find_files_by_dir, read_csv,
                                write_csv, str_to_bool, read_csv_header, fmt_row_data, calc_k, diff_lines,
                                create_out_fname, dequote, quote, conv_raw_val)
from md_utils.fes_combo import DEF_FILE_PAT
from md_utils.wham import CORR_KEY, COORD_KEY, FREE_KEY, RAD_KEY_SEQ

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Constants #
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'lammps_proc')
FES_DIR = os.path.join(DATA_DIR, 'fes_out')
CALC_PKA_DIR = 'calc_pka'

CSV_FILE = os.path.join(DATA_DIR, CALC_PKA_DIR, 'rad_PMF_last2ns3_1.txt')
FRENG_TYPES = [float, str]

ORIG_WHAM_FNAME = "PMF_last2ns3_1.txt"
ORIG_WHAM_PATH = os.path.join(DATA_DIR, ORIG_WHAM_FNAME)
SHORT_WHAM_PATH = os.path.join(DATA_DIR, ORIG_WHAM_FNAME)
EMPTY_CSV = os.path.join(DATA_DIR, 'empty.csv')

OUT_PFX = 'rad_'

# Data #

CSV_HEADER = ['coord', 'free_energy', 'corr']
GHOST = 'ghost'

# Output files #

GOOD_OH_DIST_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_oh_dist_good.csv')
ALMOST_OH_DIST_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_oh_dist_good_small_diff.csv')
NOT_OH_DIST_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_oh_dist_diff_val.csv')
MISS_COL_OH_DIST_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_oh_dist_miss_val.csv')
MISS_LINE_OH_DIST_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_oh_dist_missing_line.csv')

IMPROP_SEC = os.path.join(SUB_DATA_DIR, 'glue_improp.data')
IMPROP_SEC_ALT = os.path.join(SUB_DATA_DIR, 'glue_improp_diff_ord.data')


def expected_dir_data():
    """
    :return: The data structure that's expected from `find_files_by_dir`
    """
    return {os.path.abspath(os.path.join(FES_DIR, "1.00")): ['fes.out'],
            os.path.abspath(os.path.join(FES_DIR, "2.75")): ['fes.out', 'fes_cont.out'],
            os.path.abspath(os.path.join(FES_DIR, "5.50")): ['fes.out', 'fes_cont.out'],
            os.path.abspath(os.path.join(FES_DIR, "multi")): ['fes.out', 'fes_cont.out',
                                                              'fes_cont2.out', 'fes_cont3.out'],
            os.path.abspath(os.path.join(FES_DIR, "no_overwrite")): ['fes.out'], }


def csv_data():
    """
    :return: Test data as a list of dicts.
    """
    rows = [{CORR_KEY: 123.42, COORD_KEY: "75", FREE_KEY: True},
            {CORR_KEY: 999.43, COORD_KEY: "yellow", FREE_KEY: False}]
    return rows


def is_one_of_type(val, types):
    """Returns whether the given value is one of the given types.

    :param val: The value to evaluate
    :param types: A sequence of types to check against.
    :return: Whether the given value is one of the given types.
    """
    result = False
    val_type = type(val)
    for tt in types:
        if val_type is tt:
            result = True
    return result


# Tests #

class TestRateCalc(unittest.TestCase):
    """
    Tests calculation of a rate coefficient by the Eyring equation.
    """
    def test_calc_k(self):
        temp = 900.0
        delta_g = 53.7306
        rate_coeff = calc_k(temp, delta_g)
        self.assertEqual(rate_coeff, 1.648326791137026)

    # def test_calc_k_real(self):
    #     temp = 300.0
    #     delta_g = 36
    #     rate_coeff = calc_k(temp, delta_g)
    #     rate_coeff2 = calc_k(temp, 12.3)
    #     print(rate_coeff2/rate_coeff)
    #     print("Rate coefficient in s^-1: {}".format(rate_coeff))
    #     print("Timescale in s: {}".format(1/rate_coeff))
    #     print("Timescale in min: {}".format(1/rate_coeff/60))
    #     print("Timescale in hours: {}".format(1/rate_coeff/60/60))
    #     print("Timescale in days: {}".format(1/rate_coeff/60/60/24))
    #     print("Timescale in months: {}".format(1/rate_coeff/60/60/24/30))
    #     print("Timescale in years: {}".format(1/rate_coeff/60/60/24/365.25))
    #
    #
    # def test_calc_k_real2(self):
    #     temp = 300.0
    #     delta_g = 12.3
    #     rate_coeff = calc_k(temp, delta_g)
    #     print("Rate coefficient in s^-1: {}".format(rate_coeff))
    #     print("Timescale in s: {}".format(1/rate_coeff))
    #     print("Timescale in ms: {}".format(1000/rate_coeff))
    #     print("Timescale in microseconds: {}".format(1000*1000/rate_coeff))


class TestFindFiles(unittest.TestCase):
    """
    Tests for the file finder.
    """

    def test_find(self):
        found = find_files_by_dir(FES_DIR, DEF_FILE_PAT)
        exp_data = expected_dir_data()
        self.assertEqual(len(exp_data), len(found))
        for key, files in exp_data.items():
            found_files = found.get(key)
            try:
                # noinspection PyUnresolvedReferences
                self.assertCountEqual(files, found_files)
            except AttributeError:
                self.assertItemsEqual(files, found_files)


class TestReadFirstRow(unittest.TestCase):

    def testFirstRow(self):
        self.assertListEqual(CSV_HEADER, read_csv_header(CSV_FILE))

    def testEmptyFile(self):
        self.assertIsNone(read_csv_header(EMPTY_CSV))


class TestCreateOutFname(unittest.TestCase):
    def testOutFname(self):
        """
        Check for prefix addition.
        """
        self.assertTrue(create_out_fname(ORIG_WHAM_PATH, prefix=OUT_PFX).endswith(
            os.sep + OUT_PFX + ORIG_WHAM_FNAME))


class TestReadCsv(unittest.TestCase):
    def testReadCsv(self):
        """
        Verifies the contents of the CSV file.
        """
        result = read_csv(CSV_FILE)
        self.assertTrue(result)
        for row in result:
            self.assertEqual(3, len(row))
            self.assertIsNotNone(row.get(FREE_KEY, None))
            self.assertIsInstance(row[FREE_KEY], str)
            self.assertIsNotNone(row.get(CORR_KEY, None))
            self.assertIsInstance(row[CORR_KEY], str)
            self.assertIsNotNone(row.get(COORD_KEY, None))
            self.assertIsInstance(row[COORD_KEY], str)

    def testReadTypedCsv(self):
        """
        Verifies the contents of the CSV file.
        """
        result = read_csv(CSV_FILE, data_conv={FREE_KEY: float,
                                               CORR_KEY: float,
                                               COORD_KEY: float, })
        self.assertTrue(result)
        for row in result:
            self.assertEqual(3, len(row))
            self.assertIsNotNone(row.get(FREE_KEY, None))
            self.assertTrue(is_one_of_type(row[FREE_KEY], FRENG_TYPES))
            self.assertIsNotNone(row.get(CORR_KEY, None))
            self.assertTrue(is_one_of_type(row[CORR_KEY], FRENG_TYPES))
            self.assertIsNotNone(row.get(COORD_KEY, None))
            self.assertIsInstance(row[COORD_KEY], float)

    def testReadTypedCsvAllConv(self):
        """
        Verifies the contents of the CSV file using the all_conv function.
        """
        result = read_csv(CSV_FILE, all_conv=float)
        self.assertTrue(result)
        for row in result:
            self.assertEqual(3, len(row))
            self.assertIsNotNone(row.get(FREE_KEY, None))
            self.assertTrue(is_one_of_type(row[FREE_KEY], FRENG_TYPES))
            self.assertIsNotNone(row.get(CORR_KEY, None))
            self.assertTrue(is_one_of_type(row[CORR_KEY], FRENG_TYPES))
            self.assertIsNotNone(row.get(COORD_KEY, None))
            self.assertIsInstance(row[COORD_KEY], float)


class TestWriteCsv(unittest.TestCase):
    def testWriteCsv(self):
        tmp_dir = None
        data = csv_data()
        try:
            tmp_dir = tempfile.mkdtemp()
            tgt_fname = create_out_fname(SHORT_WHAM_PATH, prefix=OUT_PFX, base_dir=tmp_dir)

            write_csv(data, tgt_fname, RAD_KEY_SEQ)
            csv_result = read_csv(tgt_fname,
                                  data_conv={FREE_KEY: str_to_bool,
                                             CORR_KEY: float,
                                             COORD_KEY: str, })
            self.assertEqual(len(data), len(csv_result))
            for i, csv_row in enumerate(csv_result):
                self.assertDictEqual(data[i], csv_row)
        finally:
            shutil.rmtree(tmp_dir)


class TestFormatData(unittest.TestCase):
    def testFormatRows(self):
        raw = [{"a": 1.3333322333, "b": 999.222321}, {"a": 333.44422222, "b": 17.121}]
        fmt_std = [{'a': '1.3333', 'b': '999.2223'}, {'a': '333.4442', 'b': '17.1210'}]
        self.assertListEqual(fmt_std, fmt_row_data(raw, "{0:.4f}"))


class TestDiffLines(unittest.TestCase):
    def testSameFile(self):
        self.assertFalse(diff_lines(GOOD_OH_DIST_OUT_PATH, GOOD_OH_DIST_OUT_PATH))

    def testMachinePrecDiff(self):
        self.assertFalse(diff_lines(GOOD_OH_DIST_OUT_PATH, ALMOST_OH_DIST_OUT_PATH))

    def testMachinePrecDiff2(self):
        self.assertFalse(diff_lines(ALMOST_OH_DIST_OUT_PATH, GOOD_OH_DIST_OUT_PATH))

    def testDiff(self):
        print("hello ", diff_lines(NOT_OH_DIST_OUT_PATH, GOOD_OH_DIST_OUT_PATH))
        # self.assertTrue(diff_lines(NOT_OH_DIST_OUT_PATH, GOOD_OH_DIST_OUT_PATH))
        # self.assertTrue(diff_lines(GOOD_OH_DIST_OUT_PATH, NOT_OH_DIST_OUT_PATH))

    def testDiffColNum(self):
        hello = diff_lines(MISS_COL_OH_DIST_OUT_PATH, GOOD_OH_DIST_OUT_PATH)
        for line in hello:
            print(line)
        self.assertTrue(diff_lines(MISS_COL_OH_DIST_OUT_PATH, GOOD_OH_DIST_OUT_PATH))
        self.assertTrue(diff_lines(GOOD_OH_DIST_OUT_PATH, MISS_COL_OH_DIST_OUT_PATH))

    def testMissLine(self):
        diff_line_list = diff_lines(GOOD_OH_DIST_OUT_PATH, MISS_LINE_OH_DIST_OUT_PATH)
        self.assertTrue(len(diff_line_list) == 1)
        self.assertTrue("- 540010,1.04337066817119" in diff_line_list[0])

    def testDiffOrd(self):
        # diff_line_list = diff_lines(IMPROP_SEC, IMPROP_SEC_ALT)
        # print(diff_line_list)
        self.assertTrue(diff_lines(IMPROP_SEC, IMPROP_SEC_ALT))


class TestQuoteDeQuote(unittest.TestCase):
    def testQuoting(self):
        self.assertTrue(quote((0, 1)) == '"(0, 1)"')

    def testNoQuotingNeeded(self):
        self.assertTrue(quote('"(0, 1)"') == '"(0, 1)"')

    def testDequote(self):
        self.assertTrue(dequote('"(0, 1)"') == '(0, 1)')

    def testNoDequoteNeeded(self):
        self.assertTrue(dequote("(0, 1)") == '(0, 1)')

    def testDequoteUnmatched(self):
        self.assertTrue(dequote('"' + '(0, 1)') == '"(0, 1)')


class TestConversions(unittest.TestCase):
    def testNotBool(self):
        try:
            str_to_bool("hello")
        except ValueError as e:
            self.assertTrue("Cannot covert" in e.message)

    def testIntList(self):
        int_str = '2,3,4'
        int_list = [2, 3, 4]
        self.assertEquals(int_list, conv_raw_val(int_str, []))

    def testNotIntMissFlag(self):
        non_int_str = 'a,b,c'
        try:
            conv_raw_val(non_int_str, [])
        except ValueError as e:
            self.assertTrue("invalid literal for int()" in e.message)

    def testNotIntList(self):
        non_int_str = 'a,b,c'
        non_int_list = ['a', 'b', 'c']
        self.assertEquals(non_int_list, conv_raw_val(non_int_str, [], int_list=False))
