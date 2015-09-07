# coding=utf-8
"""
Tests for wham_block.
"""

import logging
import unittest
import tempfile
import shutil

from md_utils.wham_split import rmsd_split
from tests.test_wham import (META_PATH, TPL_LOC)

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_wham_split')


# Tests #


# TODO: Finish rmsd_split test
class BlockAverage(unittest.TestCase):

    def testBlockAverage(self):
        directory_name = None
        try:
            directory_name = tempfile.mkdtemp()
            rmsd_split(META_PATH, 12, tpl_dir=TPL_LOC, base_dir=directory_name)
        finally:
            shutil.rmtree(directory_name)
