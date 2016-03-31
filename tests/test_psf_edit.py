import unittest
import os

from md_utils import psf_edit
import md_utils.md_common


__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'psf_edit')
ATOM_DICT_FILE = os.path.join(SUB_DATA_DIR, 'atom_reorder.csv')
DEF_INI = os.path.join(SUB_DATA_DIR, 'psf_edit.ini')
DEF_OUT = os.path.join(SUB_DATA_DIR, 'new.psf')
GOOD_OUT = os.path.join(SUB_DATA_DIR, 'glue_autopsf.psf')


class TestPDBEdit(unittest.TestCase):

    def testReproducePSF(self):
        try:
            psf_edit.main(["-c", DEF_INI])
            self.assertFalse(md_utils.md_common.diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            md_utils.md_common.silent_remove(DEF_OUT)

