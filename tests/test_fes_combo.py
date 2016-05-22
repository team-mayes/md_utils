# coding=utf-8

import logging
import os
import unittest

from md_utils.md_common import find_files_by_dir, capture_stdout, silent_remove, diff_lines, capture_stderr
from md_utils.fes_combo import combine, DEF_FILE_PAT, DEF_TGT, map_fes, extract_header, write_combo, main

__author__ = 'cmayes'

# Logging #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
FES_OUT_DIR = 'fes_out'
FES_ALL_DIR = 'fes_all'
FES_MULTI_DIR = 'multi'
FES_SINGLE_DIR = '1.00'
FES_TWO_DIR = '5.50'
FES_NO_FILE_DIR = '77.00'
FES_ALREADY_THERE_DIR = 'no_overwrite'
HEADER_FILE = 'fes_headers.txt'
HEADER_DIR = os.path.join(DATA_DIR, HEADER_FILE)
# Source Dirs #
FES_OUT_BASE = os.path.join(DATA_DIR, FES_OUT_DIR)
FES_OUT_SINGLE = os.path.join(FES_OUT_BASE, FES_SINGLE_DIR)
FES_OUT_TWO = os.path.join(FES_OUT_BASE, FES_TWO_DIR)
FES_OUT_NONE = os.path.join(FES_OUT_BASE, FES_NO_FILE_DIR)
FES_OUT_MULTI = os.path.join(FES_OUT_BASE, FES_MULTI_DIR)
FES_OUT_NO_OVERWRITE = os.path.join(FES_OUT_BASE, FES_ALREADY_THERE_DIR)
# Target Files #
FES_ALL_BASE = os.path.join(DATA_DIR, FES_ALL_DIR)
FES_ALL_SINGLE = os.path.join(FES_ALL_BASE, FES_SINGLE_DIR, DEF_TGT)
FES_ALL_TWO = os.path.join(FES_ALL_BASE, FES_TWO_DIR, DEF_TGT)
FES_ALL_MULTI = os.path.join(FES_ALL_BASE, FES_MULTI_DIR, DEF_TGT)
# Target writers #
FES_ALL_MULTI_FILE = os.path.join(FES_OUT_BASE, FES_MULTI_DIR, DEF_TGT)
GOOD_FES_ALL_MULTI_FILE = os.path.join(FES_OUT_BASE, FES_MULTI_DIR, "all_fes_good.csv")


def header_lines(tgt_file):
    """
    Extracts and returns a list of the header lines from the given file location.
    :tgt_file: The file location to read from.
    """
    with open(tgt_file) as tf:
        h_lines = []
        for t_line in tf:
            s_line = t_line.strip().split()
            if len(s_line) < 2:
                h_lines.append(t_line)
                continue
            try:
                # If we have a timestep, this is not a header line
                int(s_line[0])
            except (ValueError, TypeError):
                h_lines.append(t_line)
        return h_lines


# Tests #
class TestFesCombo(unittest.TestCase):
    """
    Tests for the functions in fes_combo.
    """

    def test_single(self):
        test_dict = find_files_by_dir(FES_OUT_SINGLE, DEF_FILE_PAT)
        self.assertEqual(1, len(test_dict))
        f_dir, files = test_dict.popitem()
        combo = combine([os.path.join(f_dir, tgt) for tgt in files])
        self.assertDictEqual(map_fes(FES_ALL_SINGLE)[1], combo)

    def test_two(self):
        test_dict = find_files_by_dir(FES_OUT_TWO, DEF_FILE_PAT)
        self.assertEqual(1, len(test_dict))
        f_dir, files = test_dict.popitem()
        combo = combine([os.path.join(f_dir, tgt) for tgt in files])
        self.assertDictEqual(map_fes(FES_ALL_TWO)[1], combo)

    def test_multi(self):
        test_dict = find_files_by_dir(FES_OUT_MULTI, DEF_FILE_PAT)
        self.assertEqual(1, len(test_dict))
        f_dir, files = test_dict.popitem()
        combo = combine([os.path.join(f_dir, tgt) for tgt in files])
        self.assertDictEqual(map_fes(FES_ALL_MULTI)[1], combo)

    def test_headers(self):
        test_dict = find_files_by_dir(FES_OUT_SINGLE, DEF_FILE_PAT)
        self.assertEqual(1, len(test_dict))
        f_dir, files = test_dict.popitem()
        headers = extract_header(os.path.join(f_dir, files[0]))
        ref_headers = header_lines(HEADER_DIR)
        self.assertEqual(len(headers), len(ref_headers))
        self.assertListEqual(ref_headers, headers)

    def test_writer(self):
        test_dict = find_files_by_dir(FES_OUT_MULTI, DEF_FILE_PAT)
        self.assertEqual(1, len(test_dict))
        f_dir, files = test_dict.popitem()
        combo = combine([os.path.join(f_dir, tgt) for tgt in files])
        try:
            write_combo(extract_header(os.path.join(f_dir, files[0])), combo, FES_ALL_MULTI_FILE)
            self.assertEqual(map_fes(FES_ALL_MULTI), map_fes(FES_ALL_MULTI_FILE))
        finally:
            os.remove(FES_ALL_MULTI_FILE)


class TestFesComboMain(unittest.TestCase):
    def testNoArgs(self):
        try:
            main(["-d", FES_OUT_MULTI])
            self.assertFalse(diff_lines(FES_ALL_MULTI_FILE, GOOD_FES_ALL_MULTI_FILE))
        finally:
            silent_remove(FES_ALL_MULTI_FILE)

    def testBadArg(self):
        with capture_stderr(main, ["-@"]) as output:
            self.assertTrue("unrecognized arguments" in output)

    def testNoComboFiles(self):
        with capture_stdout(main, ["-d", FES_OUT_NONE]) as output:
            self.assertTrue("Found 0 dirs with files to combine" in output)

    def testNoOverwrite(self):
        # main(["-d", FES_OUT_NO_OVERWRITE])
        with capture_stderr(main, ["-d", FES_OUT_NO_OVERWRITE]) as output:
            self.assertTrue("already exists" in output)

    def testHelpOption(self):
        with capture_stdout(main, ["-h"]) as output:
            self.assertTrue("optional arguments" in output)