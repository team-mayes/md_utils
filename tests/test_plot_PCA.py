# coding=utf-8

"""
"""

import unittest
import logging
import os
from md_utils.md_common import silent_remove, diff_lines
from md_utils.plot_PCA import main

__author__ = 'adams'

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
PCA_DIR = os.path.join(DATA_DIR, 'plot_PCA')
TRAJ_FILE = os.path.join(PCA_DIR, 'short.dcd')
TOP_FILE = os.path.join(PCA_DIR, 'step5_assembly.xplor_ext.psf')
IG_FILE = os.path.join(PCA_DIR, 'IG_indices.txt')
EG_FILE = os.path.join(PCA_DIR, 'EG_indices.txt')
NAME = 'test.png'
PNG_FILE = os.path.join(PCA_DIR, 'test.png')


class TestMainNoOutput(unittest.TestCase):
    def testNoArg(self):
        main(['-h'])

class TestMain(unittest.TestCase):
    def testWithInwardData(self):
        silent_remove(PNG_FILE)
        test_input = [ "--traj", TRAJ_FILE, "--top", TOP_FILE, "-i", IG_FILE, "-e", EG_FILE, "-n", NAME, "-o", PCA_DIR]
        try:
            main(test_input)
            os.path.isfile(PNG_FILE)
        finally:
            silent_remove(PNG_FILE, disable=DISABLE_REMOVE)
