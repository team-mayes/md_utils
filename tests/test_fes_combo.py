import logging
import os
import unittest

from raptor_utils.common import find_files_by_dir
from raptor_utils.fes_combo import combine, DEF_FILE_PAT, DEF_TGT, map_fes

__author__ = 'cmayes'

# Logging #
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_fes_combo')
logger.setLevel(logging.DEBUG)

DATA_DIR = 'test_data'
FES_OUT_DIR = 'fes_out'
FES_ALL_DIR = 'fes_all'
FES_MULTI_DIR = 'multi'
FES_SINGLE_DIR = '1.00'
FES_TWO_DIR = '5.50'
# Source Dirs #
FES_OUT_BASE = os.path.join(DATA_DIR, FES_OUT_DIR)
FES_OUT_SINGLE = os.path.join(FES_OUT_BASE, FES_SINGLE_DIR)
FES_OUT_TWO = os.path.join(FES_OUT_BASE, FES_TWO_DIR)
FES_OUT_MULTI = os.path.join(FES_OUT_BASE, FES_MULTI_DIR)
# Target Files #
FES_ALL_BASE = os.path.join(DATA_DIR, FES_ALL_DIR)
FES_ALL_SINGLE = os.path.join(FES_ALL_BASE, FES_SINGLE_DIR, DEF_TGT)
FES_ALL_TWO = os.path.join(FES_ALL_BASE, FES_TWO_DIR, DEF_TGT)
FES_ALL_MULTI = os.path.join(FES_ALL_BASE, FES_MULTI_DIR, DEF_TGT)

# Tests #
class TestFesCombo(unittest.TestCase):
    """
    Tests for the functions in fes_combo.
    """
    def test_single(self):
        test_dict = find_files_by_dir(FES_OUT_SINGLE, DEF_FILE_PAT)
        self.assertEqual(1, len(test_dict))
        fdir, files = test_dict.popitem()
        combo = combine([os.path.join(fdir, tgt) for tgt in files])
        self.assertDictEqual(map_fes(FES_ALL_SINGLE)[1], combo)

    def test_two(self):
        test_dict = find_files_by_dir(FES_OUT_TWO, DEF_FILE_PAT)
        self.assertEqual(1, len(test_dict))
        fdir, files = test_dict.popitem()
        combo = combine([os.path.join(fdir, tgt) for tgt in files])
        self.assertDictEqual(map_fes(FES_ALL_TWO)[1], combo)

    def test_multi(self):
        test_dict = find_files_by_dir(FES_OUT_MULTI, DEF_FILE_PAT)
        self.assertEqual(1, len(test_dict))
        fdir, files = test_dict.popitem()
        combo = combine([os.path.join(fdir, tgt) for tgt in files])
        self.assertDictEqual(map_fes(FES_ALL_MULTI)[1], combo)

