# coding=utf-8

"""
Tests for the common lib.
"""
import logging
import shutil
import tempfile
import unittest
import os
import numpy as np
from md_utils.md_common import (find_files_by_dir, read_csv, get_fname_root,
                                write_csv, str_to_bool, read_csv_header, fmt_row_data, calc_k, diff_lines,
                                create_out_fname, dequote, quote, conv_raw_val, pbc_calc_vector, pbc_vector_avg,
                                read_csv_dict, InvalidDataError, unit_vector, vec_angle, vec_dihedral)
from md_utils.fes_combo import DEF_FILE_PAT
from md_utils.wham import CORR_KEY, COORD_KEY, FREE_KEY, RAD_KEY_SEQ

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Constants #
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'small_tests')
LAMMPS_PROC_DIR = os.path.join(DATA_DIR, 'lammps_proc')
FES_DIR = os.path.join(DATA_DIR, 'fes_out')
CALC_PKA_DIR = 'calc_pka'
PDB_DIR = os.path.join(DATA_DIR, 'pdb_edit')

ELEM_DICT_FILE = os.path.join(PDB_DIR, 'element_dict.csv')
ATOM_DICT_FILE = os.path.join(PDB_DIR, 'atom_reorder.csv')
GOOD_ATOM_DICT = {1: 20, 2: 21, 3: 22, 4: 23, 5: 24, 6: 25, 7: 26, 8: 27, 9: 2, 10: 1, 11: 3, 12: 4, 13: 5, 14: 6,
                  15: 7, 16: 8, 17: 9, 18: 10, 19: 11, 20: 12, 21: 13, 22: 14, 23: 15, 24: 16, 25: 17, 26: 18, 27: 19}


CSV_FILE = os.path.join(DATA_DIR, CALC_PKA_DIR, 'rad_PMF_last2ns3_1.txt')
FRENG_TYPES = [float, str]

ORIG_WHAM_ROOT = "PMF_last2ns3_1"
ORIG_WHAM_FNAME = ORIG_WHAM_ROOT + ".txt"
ORIG_WHAM_PATH = os.path.join(DATA_DIR, ORIG_WHAM_FNAME)
SHORT_WHAM_PATH = os.path.join(DATA_DIR, ORIG_WHAM_FNAME)
EMPTY_CSV = os.path.join(DATA_DIR, 'empty.csv')

OUT_PFX = 'rad_'

# Data #

CSV_HEADER = ['coord', 'free_energy', 'corr']
GHOST = 'ghost'

# Output files #

DIFF_LINES_BASE_FILE = os.path.join(SUB_DATA_DIR, 'diff_lines_base_file.csv')
DIFF_LINES_PREC_DIFF = os.path.join(SUB_DATA_DIR, 'diff_lines_prec_diff.csv')
DIFF_LINES_ONE_VAL_DIFF = os.path.join(SUB_DATA_DIR, 'diff_lines_one_val_diff.csv')
DIFF_LINES_MISS_VAL = os.path.join(SUB_DATA_DIR, 'diff_lines_miss_val.csv')
MISS_LINES_MISS_LINE = os.path.join(SUB_DATA_DIR, 'diff_lines_miss_line.csv')
DIFF_LINES_ONE_NAN = os.path.join(SUB_DATA_DIR, 'diff_lines_one_nan.csv')
DIFF_LINES_ONE_NAN_PREC_DIFF = os.path.join(SUB_DATA_DIR, 'diff_lines_one_nan.csv')

DIFF_LINES_SCI_FILE = os.path.join(SUB_DATA_DIR, 'cv_analysis_quat.log')
DIFF_LINES_ALT_SCI_FILE = os.path.join(SUB_DATA_DIR, 'cv_analysis_quat_good.log')

IMPROP_SEC = os.path.join(LAMMPS_PROC_DIR, 'glue_improp.data')
IMPROP_SEC_ALT = os.path.join(LAMMPS_PROC_DIR, 'glue_improp_diff_ord.data')

# To test PBC math
PBC_BOX = np.full(3, 24.25)
A_VEC = [3.732, -1.803, -1.523]
B_VEC = [4.117, 0.135, -2.518]
GOOD_A_MINUS_B = np.array([-0.385, -1.938, 0.995])
GOOD_A_B_AVG = np.array([3.9245, -0.834, -2.0205])
C_VEC = [24.117, -20.135, -52.518]
GOOD_A_MINUS_C = np.array([3.865, -5.918, 2.495])
GOOD_A_C_AVG = np.array([1.7995, 1.156, -2.7705])

VEC_1 = np.array([3.712, -1.585, -3.116])
VEC_2 = np.array([4.8760, -1.129, -3.265])
VEC_3 = np.array([5.498, -0.566, -2.286])
VEC_4 = np.array([5.464, -1.007, -0.948])

VEC_21 = np.array([-1.164, -0.456, 0.149])
VEC_23 = np.array([0.622, 0.563, 0.979])
VEC_34 = np.array([-0.034, -0.441, 1.338])

# vec21 = {ndarray} [-1.164 -0.456  0.149]
# vec23 = {ndarray} [ 0.622  0.563  0.979]
# vec34 = {ndarray} [-0.034 -0.441  1.338]


UNIT_VEC_3 = np.array([0.91922121129527656, -0.094630630337054641, -0.38220074372881085])
ANGLE_123 = 120.952786591
DIH_1234 = 39.4905248514


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


class TestFnameManipulation(unittest.TestCase):
    def testOutFname(self):
        """
        Check for prefix addition.
        """
        self.assertTrue(create_out_fname(ORIG_WHAM_PATH, prefix=OUT_PFX).endswith(
            os.sep + OUT_PFX + ORIG_WHAM_FNAME))

    def testGetRootName(self):
        """
        Check for prefix addition.
        """
        root_name = get_fname_root(ORIG_WHAM_PATH)
        self.assertEqual(root_name, ORIG_WHAM_ROOT)
        self.assertNotEqual(root_name, ORIG_WHAM_FNAME)
        self.assertNotEqual(root_name, ORIG_WHAM_PATH)


class TestReadCsvDict(unittest.TestCase):
    def testReadAtomNumDict(self):
        # Will renumber atoms and then sort them
        test_dict = read_csv_dict(ATOM_DICT_FILE)
        self.assertEqual(test_dict, GOOD_ATOM_DICT)

    def testReadPDBDict(self):
        test_type = '  HY1 '
        test_elem = ' H'
        test_dict = read_csv_dict(ELEM_DICT_FILE, pdb_dict=True)
        self.assertTrue(test_type in test_dict)
        self.assertEqual(test_elem, test_dict[test_type])
        self.assertEqual(31, len(test_dict))

    def testStringDictAsInt(self):
        # Check that fails elegantly by passing returning value error
        try:
            test_dict = read_csv_dict(ELEM_DICT_FILE, one_to_one=False)
            self.assertFalse(test_dict)
        except ValueError as e:
            self.assertTrue("invalid literal for int()" in e.args[0])

    def testStringDictCheckDups(self):
        # Check that fails elegantly
        try:
            test_dict = read_csv_dict(ELEM_DICT_FILE, ints=False, )
            self.assertFalse(test_dict)
        except InvalidDataError as e:
            self.assertTrue("Did not find a 1:1 mapping" in e.args[0])


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
        self.assertFalse(diff_lines(DIFF_LINES_BASE_FILE, DIFF_LINES_BASE_FILE))

    def testMachinePrecDiff(self):
        self.assertFalse(diff_lines(DIFF_LINES_BASE_FILE, DIFF_LINES_PREC_DIFF))

    def testMachinePrecDiff2(self):
        self.assertFalse(diff_lines(DIFF_LINES_PREC_DIFF, DIFF_LINES_BASE_FILE))

    def testDiff(self):
        diffs = diff_lines(DIFF_LINES_ONE_VAL_DIFF, DIFF_LINES_BASE_FILE)
        self.assertEqual(len(diffs), 2)

    def testDiffColNum(self):
        diff_list_line = diff_lines(DIFF_LINES_MISS_VAL, DIFF_LINES_BASE_FILE)
        self.assertEqual(len(diff_list_line), 2)

    def testMissLine(self):
        diff_line_list = diff_lines(DIFF_LINES_BASE_FILE, MISS_LINES_MISS_LINE)
        self.assertEqual(len(diff_line_list), 1)
        self.assertTrue("- 540010,1.04337066817119" in diff_line_list[0])

    def testDiffOrd(self):
        diff_line_list = diff_lines(IMPROP_SEC, IMPROP_SEC_ALT, delimiter=" ")
        self.assertEqual(13, len(diff_line_list))

    def testDiffOneNan(self):
        diff_line_list = diff_lines(DIFF_LINES_BASE_FILE, DIFF_LINES_ONE_NAN)
        self.assertEqual(2, len(diff_line_list))

    def testDiffBothNanPrecDiff(self):
        # make there also be a precision difference so the entry-by-entry comparison will be made
        diff_line_list = diff_lines(DIFF_LINES_ONE_NAN_PREC_DIFF, DIFF_LINES_ONE_NAN)
        self.assertFalse(diff_line_list)

    def testSciVectorsPrecDiff(self):
        self.assertFalse(diff_lines(DIFF_LINES_SCI_FILE, DIFF_LINES_ALT_SCI_FILE))


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
            str_to_bool("hello there neighbor")
        except ValueError as e:
            self.assertTrue("Cannot covert" in e.args[0])

    def testIntList(self):
        int_str = '2,3,4'
        int_list = [2, 3, 4]
        self.assertEqual(int_list, conv_raw_val(int_str, []))

    def testNotIntMissFlag(self):
        non_int_str = 'a,b,c'
        try:
            conv_raw_val(non_int_str, [])
        except ValueError as e:
            self.assertTrue("invalid literal for int()" in e.args[0])

    def testNotIntList(self):
        non_int_str = 'a,b,c'
        non_int_list = ['a', 'b', 'c']
        self.assertEqual(non_int_list, conv_raw_val(non_int_str, [], int_list=False))


class TestVectorPBCMath(unittest.TestCase):
    def testSubtractInSameImage(self):
        self.assertTrue(np.allclose(pbc_calc_vector(VEC_1, VEC_2, PBC_BOX), VEC_21))
        self.assertTrue(np.allclose(pbc_calc_vector(VEC_3, VEC_2, PBC_BOX), VEC_23))
        self.assertFalse(np.allclose(pbc_calc_vector(VEC_3, VEC_2, PBC_BOX), VEC_21))
        self.assertTrue(np.allclose(pbc_calc_vector(A_VEC, B_VEC, PBC_BOX), GOOD_A_MINUS_B))

    def testSubtractInDiffImages(self):
        self.assertTrue(np.allclose(pbc_calc_vector(A_VEC, C_VEC, PBC_BOX), GOOD_A_MINUS_C))

    def testAvgInSameImage(self):
        self.assertTrue(np.allclose(pbc_vector_avg(A_VEC, B_VEC, PBC_BOX), GOOD_A_B_AVG))

    def testAvgInDiffImages(self):
        self.assertTrue(np.allclose(pbc_vector_avg(A_VEC, C_VEC, PBC_BOX), GOOD_A_C_AVG))

    def testUnitVector(self):
        test_unit_vec = unit_vector(VEC_3)
        self.assertTrue(np.allclose(test_unit_vec, UNIT_VEC_3))
        self.assertFalse(np.allclose(test_unit_vec, VEC_1))

    def testAngle(self):
        self.assertAlmostEqual(vec_angle(VEC_21, VEC_23), ANGLE_123)

    def testDihedral(self):
        self.assertAlmostEqual(vec_dihedral(VEC_21, VEC_23, VEC_34), DIH_1234)
