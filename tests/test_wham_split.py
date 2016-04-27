# coding=utf-8
"""
Tests for wham_block.
"""
import filecmp

import logging
import os
import unittest
import tempfile
import shutil

from md_utils.wham_split import rmsd_split
from tests.test_wham import (META_PATH, TPL_LOC)

__author__ = 'cmayes'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
