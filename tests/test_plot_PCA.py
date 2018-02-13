# coding=utf-8

"""
"""

import unittest
import logging
import os
from md_utils.md_common import silent_remove, capture_stderr, capture_stdout
from md_utils.plot_PCA import main

__author__ = 'adams'

logging.basicConfig(level=logging.DEBUG)
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
TRAJ_GLOB = os.path.join(PCA_DIR, '*dcd')


class TestMainFailWell(unittest.TestCase):
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoSuchFile(self):
        test_input = ['-p', 'ghost']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("not find specified file" in output)


class TestMain(unittest.TestCase):
    def testWithInwardData(self):
        silent_remove(PNG_FILE)
        test_input = ["--traj", TRAJ_FILE, "--top", TOP_FILE, "-i", IG_FILE, "-e", EG_FILE, "-n", NAME, "-o", PCA_DIR]
        try:
            main(test_input)
            os.path.isfile(PNG_FILE)
        finally:
            silent_remove(PNG_FILE, disable=DISABLE_REMOVE)

    def testGlob(self):
        silent_remove(PNG_FILE)
        test_input = ["-t", TRAJ_GLOB, "-p", TOP_FILE, "-i", IG_FILE, "-e", EG_FILE, "-n", NAME, "-o", PCA_DIR]
        try:
            main(test_input)
            os.path.isfile(PNG_FILE)
        finally:
            silent_remove(PNG_FILE, disable=DISABLE_REMOVE)
