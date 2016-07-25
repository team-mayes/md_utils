import unittest
import os

from md_utils.psf_edit import main
from md_utils.md_common import diff_lines, silent_remove, capture_stdout

__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'psf_edit')
ATOM_DICT_FILE = os.path.join(SUB_DATA_DIR, 'atom_reorder.csv')
DEF_INI = os.path.join(SUB_DATA_DIR, 'psf_edit.ini')
DEF_OUT = os.path.join(SUB_DATA_DIR, 'glue_revised_new.psf')
GOOD_OUT = os.path.join(SUB_DATA_DIR, 'glue_revised.psf')

QMMM_OUT_INI = os.path.join(SUB_DATA_DIR, 'psf_make_qmmm_input.ini')
QMMM_OUT = os.path.join(SUB_DATA_DIR, 'amino_id.dat')
GOOD_QMMM_OUT = os.path.join(SUB_DATA_DIR, 'amino_id_good.dat')


class TestPDBEdit(unittest.TestCase):
    def testReproducePSF(self):
        try:
            main(["-c", DEF_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT)

    def testPrintQMMM(self):
        try:
            # main(["-c", QMMM_OUT_INI])
            with capture_stdout(main, ["-c", QMMM_OUT_INI]) as output:
                self.assertTrue("Total charge from QMMM atoms: -1.0" in output)
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
            self.assertFalse(diff_lines(QMMM_OUT, GOOD_QMMM_OUT))
        finally:
            silent_remove(DEF_OUT)
            silent_remove(QMMM_OUT)
            # pass
