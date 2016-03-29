import unittest
import os

from md_utils import pdb_edit
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'pdb_edit')
ATOM_DICT_FILE = os.path.join(SUB_DATA_DIR, 'atom_reorder.csv')
DEF_INI = os.path.join(SUB_DATA_DIR, 'pdb_edit.ini')
ATOM_DICT_BAD_INI = os.path.join(SUB_DATA_DIR, 'pdb_edit_bad_reorder.ini')
DEF_OUT = os.path.join(SUB_DATA_DIR, 'new.pdb')
GOOD_OUT = os.path.join(SUB_DATA_DIR, 'glue_autopsf_short_good.pdb')

GOOD_ATOM_DICT = {1: 20, 2: 21, 3: 22, 4: 23, 5: 24, 6: 25, 7: 26, 8: 27, 9: 2, 10: 1, 11: 3, 12: 4, 13: 5, 14: 6,
                  15: 7, 16: 8, 17: 9, 18: 10, 19: 11, 20: 12, 21: 13, 22: 14, 23: 15, 24: 16, 25: 17, 26: 18, 27: 19}



class TestPDBEdit(unittest.TestCase):
    def testReadAtomNumDict(self):
        dict = pdb_edit.read_atom_dict(ATOM_DICT_FILE)
        assert cmp(dict, GOOD_ATOM_DICT) == 0

    def testReadBadAtomNumDict(self):
        with capture_stderr(pdb_edit.main,["-c", ATOM_DICT_BAD_INI]) as output:
            self.assertTrue("xx" in output)
            self.assertTrue("26" in output)
            self.assertTrue("Problems with input information" in output)

    def testReorderAtoms(self):
        try:
            pdb_edit.main(["-c", DEF_INI])
            # for debugging:
            with open(DEF_OUT) as f:
                with open(GOOD_OUT) as g:
                    for d_line, g_line in zip(f,g):
                        if d_line !=g_line:
                            print(d_line,g_line)
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT)

