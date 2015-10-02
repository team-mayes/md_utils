# coding=utf-8

import logging
import os
import unittest

from md_utils.common import find_files_by_dir
from md_utils.fes_combo import combine, DEF_FILE_PAT, DEF_TGT, map_fes, extract_header, write_combo

__author__ = 'cmayes'

# Logging #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_fes_combo')
logger.setLevel(logging.INFO)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
FES_OUT_DIR = 'fes_out'
FES_ALL_DIR = 'fes_all'
FES_MULTI_DIR = 'multi'
FES_SINGLE_DIR = '1.00'
FES_TWO_DIR = '5.50'
HEADER_FILE = 'fes_headers.txt'
HEADER_DIR = os.path.join(DATA_DIR, HEADER_FILE)
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
# Target writers #
FES_ALL_MULTI_FILE = os.path.join(FES_OUT_BASE, FES_MULTI_DIR, DEF_TGT)


def header_lines(tgt_file):
    """
    Extracts and returns a list of the header lines from the given file location.
    :tgt_file: The file location to read from.
    """
    with open(tgt_file) as tf:
        hlines = []
        for tline in tf:
            sline = tline.strip().split()
            if len(sline) < 2:
                hlines.append(tline)
                continue
            try:
                # If we have a timestep, this is not a header line
                int(sline[0])
                break
            except:
                hlines.append(tline)
        return hlines


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

    def test_headers(self):
        test_dict = find_files_by_dir(FES_OUT_SINGLE, DEF_FILE_PAT)
        self.assertEqual(1, len(test_dict))
        fdir, files = test_dict.popitem()
        headers = extract_header(os.path.join(fdir, files[0]))
        ref_headers = header_lines(HEADER_DIR)
        self.assertEqual(len(headers), len(ref_headers))
        self.assertListEqual(ref_headers, headers)

    def test_writer(self):
        test_dict = find_files_by_dir(FES_OUT_MULTI, DEF_FILE_PAT)
        self.assertEqual(1, len(test_dict))
        fdir, files = test_dict.popitem()
        combo = combine([os.path.join(fdir, tgt) for tgt in files])
        try:
            write_combo(extract_header(os.path.join(fdir, files[0])), combo, FES_ALL_MULTI_FILE)
            self.assertEqual(map_fes(FES_ALL_MULTI), map_fes(FES_ALL_MULTI_FILE))
        finally:
            os.remove(FES_ALL_MULTI_FILE)
