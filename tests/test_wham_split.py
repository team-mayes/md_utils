# coding=utf-8
"""
Tests for wham_block.
"""
import filecmp
import os
import unittest
import tempfile
import shutil

from md_utils.wham_split import rmsd_split, main
from tests.test_wham import (META_PATH, TPL_LOC)

__author__ = 'mayes'

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'wham_test_data')
GOOD_OUT_DIR = os.path.join(SUB_DATA_DIR, 'good_split_out')


# Tests #

class BlockAverage(unittest.TestCase):
    def testBlockAverage(self):
        directory_name = None
        try:
            directory_name = tempfile.mkdtemp()
            rmsd_split(META_PATH, 12, tpl_dir=TPL_LOC, base_dir=directory_name)
            dir_cmp = (filecmp.dircmp(directory_name, GOOD_OUT_DIR))
            self.assertFalse(dir_cmp.diff_files)
        finally:
            shutil.rmtree(directory_name)


# class TestMain(unittest.TestCase):
#     # Examples of "good" input
#     def testGood(self):
#         directory_name = None
#         try:
#             directory_name = tempfile.mkdtemp()
#             print("hello", SUB_DATA_DIR)
#             print("hello", TPL_LOC)
#             print("hello", directory_name)
#             main(["-d", directory_name])
#         finally:
#             shutil.rmtree(directory_name)


class TestMainNoOutput(unittest.TestCase):
    # Test that program can fail well
    def testNoArgs(self):
        # Will not be able to find what is needed to run...
        main([])
