import os
import unittest
from raptor_utils.common import find_files_by_dir
from raptor_utils.fes_combo import DEF_FILE_PAT

__author__ = 'cmayes'

DATA_DIR = 'test_data'
FES_OUT_DIR = 'fes_out'
FES_BASE = os.path.join(DATA_DIR, FES_OUT_DIR)


def expected_dir_data():
    return {os.path.abspath(os.path.join(FES_BASE, "1.00")): ['fes.out'],
            os.path.abspath(os.path.join(FES_BASE, "5.50")): ['fes.out', 'fes_cont.out'],
            os.path.abspath(os.path.join(FES_BASE, "multi")): ['fes.out', 'fes_cont.out',
                                                               'fes_cont2.out', 'fes_cont3.out'], }


# Tests #
class TestFindFiles(unittest.TestCase):
    "Calc tests"

    def test_find(self):
        self.maxDiff = None
        found = find_files_by_dir(FES_BASE, DEF_FILE_PAT)
        for key, files in expected_dir_data().iteritems():
            found_files = found.get(key)
            self.assertItemsEqual(files, found_files)
