import unittest
import os

from md_utils import data_reorder
from md_utils.md_common import diff_lines, silent_remove, capture_stderr, capture_stdout

__author__ = 'hmayes'

# Directories #

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'data_reorder')

# Input files #

DEF_INI = os.path.join(SUB_DATA_DIR, 'data_reorder.ini')
SERCA_INI = os.path.join(SUB_DATA_DIR, 'data_reorder_serca.ini')
BAD_DICT_INI = os.path.join(SUB_DATA_DIR, 'data_reorder_bad_dict.ini')
GLUP_INI = os.path.join(SUB_DATA_DIR, 'data_reorder_glup_glue.ini')

# Output files

# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(SUB_DATA_DIR, '4.25_ord.data')
GOOD_OUT = os.path.join(SUB_DATA_DIR, '4.25_ord_good.data')
# noinspection PyUnresolvedReferences
SERCA_0_OUT = os.path.join(SUB_DATA_DIR, 'reus_0_edited_ord.data')
SERCA_0_GOOD_OUT = os.path.join(SUB_DATA_DIR, 'reus_0_edited_ord_good.data')
# noinspection PyUnresolvedReferences
SERCA_1_OUT = os.path.join(SUB_DATA_DIR, 'reus_1_edited_ord.data')
SERCA_1_GOOD_OUT = os.path.join(SUB_DATA_DIR, 'reus_1_edited_ord_good.data')
# noinspection PyUnresolvedReferences
GLUP_OUT = os.path.join(SUB_DATA_DIR, 'glup_autopsf_ord.data')
GLUP_GOOD_OUT = os.path.join(SUB_DATA_DIR, 'glup_autopsf_ord_good.data')


class TestDataReorder(unittest.TestCase):

    def testNoArgs(self):
        with capture_stderr(data_reorder.main, []) as output:
            self.assertTrue("Could not read file" in output)
        with capture_stdout(data_reorder.main, []) as output:
            self.assertTrue("optional arguments" in output)

    def testDefIni(self):
        try:
            data_reorder.main(["-c", DEF_INI])
            # for debugging:
            # with open(PDB_TPL) as f:
            #     with open(PDB_TPL_OUT) as g:
            #         for d_line, g_line in zip(f, g):
            #             if d_line.strip() != g_line.strip():
            #                 print(d_line.strip())
            #                 print(g_line.strip())
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT)

    def testSerca(self):
        """
        Tests on another set of data, and a bad file location
        """
        with capture_stderr(data_reorder.main, ["-c", SERCA_INI]) as output:
            self.assertTrue("No such file or directory" in output)
            self.assertFalse(diff_lines(SERCA_0_OUT, SERCA_0_GOOD_OUT))
            self.assertFalse(diff_lines(SERCA_1_OUT, SERCA_1_GOOD_OUT))
            silent_remove(SERCA_0_OUT)
            silent_remove(SERCA_1_OUT)

    def testBadDict(self):
        with capture_stderr(data_reorder.main, ["-c", BAD_DICT_INI]) as output:
            print(output)
            self.assertTrue("Expected exactly two comma-separated values" in output)

    def testGlupIni(self):
        try:
            data_reorder.main(["-c", GLUP_INI])
            self.assertFalse(diff_lines(GLUP_OUT, GLUP_GOOD_OUT))
        finally:
            silent_remove(GLUP_OUT)
