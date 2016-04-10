# coding=utf-8

"""
Tests for evbdump2data
"""
import os
import unittest

from md_utils import evbdump2data
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'


TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'evbd2d')

# Test input files

SERCA_INI = os.path.join(SUB_DATA_DIR, 'evbd2d_serca.ini')
INCOMP_INI = os.path.join(SUB_DATA_DIR, 'evbd2d_missing_data.ini')
TPL_DUMP_MISMATCH_INI = os.path.join(SUB_DATA_DIR, 'evbd2d_glu_tpl_serca_dump.ini')
TPL_MISS_ATOM_INI = os.path.join(SUB_DATA_DIR, 'evbd2d_glu_tpl_missing_atom.ini')
TPL_WRONG_ATOM_ORDER_INI = os.path.join(SUB_DATA_DIR, 'evbd2d_glu_tpl_wrong_atom_order.ini')

# evbd2d_glu_tpl_missing_atom.ini

GLU_INI = os.path.join(SUB_DATA_DIR, 'evbd2d_glu.ini')
GLU_NEW_INI = os.path.join(SUB_DATA_DIR, 'evbd2d_glu_new_types.ini')
GLU_BAD_ATOM_TYPE_INI = os.path.join(SUB_DATA_DIR, 'evbd2d_glu_type_mismatch.ini')
GLU_BAD_DATA_INI = os.path.join(SUB_DATA_DIR, 'evbd2d_glu_bad_dump.ini')


# Test output files #

GOOD_PROT_OUT = os.path.join(SUB_DATA_DIR, 'serca_prot_good.data')
GOOD_DEPROT_OUT = os.path.join(SUB_DATA_DIR, 'serca_deprot_good.data')

# noinspection PyUnresolvedReferences
GLU_DEF_OUT = os.path.join(SUB_DATA_DIR, '0.625_20c_100ps_reorder_retype_548990.data')
GLU_GOOD_OUT = os.path.join(SUB_DATA_DIR, '0.625_20c_100ps_reorder_retype_548990_good.data')
GLU_DATA_TPL = os.path.join(SUB_DATA_DIR, 'glue_tpl.data')

# noinspection PyUnresolvedReferences
REPROD_TPL = os.path.join(TEST_DIR, 'reproduced_tpl.data')
# noinspection PyUnresolvedReferences
DEF_PROT_OUT = os.path.join(SUB_DATA_DIR, 'serca_prot_deprot_10.data')
# noinspection PyUnresolvedReferences
DEF_DEPROT_OUT = os.path.join(SUB_DATA_DIR, 'serca_prot_deprot_20.data')


class TestEVBDump2Data(unittest.TestCase):
    def testNoIni(self):
        with capture_stdout(evbdump2data.main, []) as output:
            self.assertTrue("usage:" in output)
        with capture_stderr(evbdump2data.main, []) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)

    def testMissingConfig(self):
        with capture_stderr(evbdump2data.main, ["-c", INCOMP_INI]) as output:
            self.assertTrue("Input data missing" in output)
        with capture_stdout(evbdump2data.main, ["-c", INCOMP_INI]) as output:
            self.assertTrue("optional arguments" in output)

    def testSercaProtDeprot(self):
        """
        Tests a SERCA file that has a protonated and deprotonated state
        Also checks that can handle and empty line
        and a dump file that was cut off
        """
        with capture_stderr(evbdump2data.main, ["-c", SERCA_INI]) as output:
            # Make sure it handles the extra empty line
            self.assertFalse("WARNING:  Problems reading file" in output)
            self.assertTrue("did not have the full list of atom numbers" in output)
        try:
            self.assertFalse(diff_lines(DEF_PROT_OUT, GOOD_PROT_OUT))
            self.assertFalse(diff_lines(DEF_DEPROT_OUT, GOOD_DEPROT_OUT))
        finally:
            silent_remove(DEF_PROT_OUT)
            silent_remove(DEF_DEPROT_OUT)

    def testNoWaterDump(self):
        with capture_stderr(evbdump2data.main, ["-c", GLU_NEW_INI]) as output:
            self.assertTrue("Found no water molecules" in output)
        silent_remove(REPROD_TPL)

    def testNoHydData(self):
        """
        Because the types do not match the data file, did not find the molecules desired.
        """
        evbdump2data.main(["-c", GLU_BAD_ATOM_TYPE_INI])
        with capture_stderr(evbdump2data.main, ["-c", GLU_BAD_ATOM_TYPE_INI]) as output:
            self.assertTrue("Check the data file" in output)
        silent_remove(REPROD_TPL)

    def testGlu(self):
        try:
            with capture_stdout(evbdump2data.main, ["-c", GLU_INI]) as output:
                # Checking intermediate charge calculation
                self.assertTrue("After atom 27 (last_p1), the total charge is: -1.000" in output)
                self.assertTrue("system is neutral" in output)
                self.assertTrue("After atom 31 (last_hyd), the total charge is" in output)
                self.assertTrue(GLU_DEF_OUT in output)
                self.assertFalse(diff_lines(GLU_DEF_OUT, GLU_GOOD_OUT))
                self.assertTrue(REPROD_TPL in output)
                self.assertFalse(diff_lines(REPROD_TPL, GLU_DATA_TPL))
        finally:
            silent_remove(GLU_DEF_OUT)
            silent_remove(REPROD_TPL)

    def testGluBadDump(self):
        try:
            with capture_stderr(evbdump2data.main, ["-c", GLU_BAD_DATA_INI]) as output:
                self.assertTrue("Problems reading data: Unexpected line in file test_data/evbd2d/glu_bad.dump: "
                                "ITEM: XYZ MS id mol type q x y z" in output)
        finally:
            silent_remove(REPROD_TPL)

    def testTplDumpMismatch(self):
        try:
            with capture_stderr(evbdump2data.main, ["-c", TPL_DUMP_MISMATCH_INI]) as output:
                self.assertTrue("listed number of atoms (214084) does not equal the number of atoms in the "
                                "template data file (1429)" in output)
        finally:
            silent_remove(REPROD_TPL)

    def testTplMissAtom(self):
        with capture_stderr(evbdump2data.main, ["-c", TPL_MISS_ATOM_INI]) as output:
                self.assertTrue("The data file system is not neutral. Total charge -0.510000" in output)
                self.assertTrue("The data file system is not neutral. Total charge -0.510000" in output)

    def testMissingArg(self):
        evbdump2data.main(["-c", ])

    def testTplAtomWrongOrder(self):
        evbdump2data.main(["-c", TPL_WRONG_ATOM_ORDER_INI])
