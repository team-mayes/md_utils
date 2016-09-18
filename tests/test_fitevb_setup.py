# coding=utf-8

"""
Tests for fitevb_setup.py.
"""
import os
import unittest
import logging

import shutil

from md_utils.fitevb_setup import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.dirname(TEST_DIR)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'fitevb')

FITEVB_OUT = os.path.join(SUB_DATA_DIR, 'fit.best')
FITEVB_OUT_RESID = os.path.join(SUB_DATA_DIR, 'fit_with_resid.best')
FITEVB_OUT_TOO_FEW = os.path.join(SUB_DATA_DIR, 'fit_too_few.best')
FITEVB_OUT_TOO_MANY = os.path.join(SUB_DATA_DIR, 'fit_too_many.best')

ALL_BEST = os.path.join(SUB_DATA_DIR, 'all_best.dat')
ORIG_ALL_BEST = os.path.join(SUB_DATA_DIR, 'orig_all_best.dat')
GOOD_ALL_BEST = os.path.join(SUB_DATA_DIR, 'all_best_good.dat')
ALL_BEST_CSV = os.path.join(MAIN_DIR, 'all_best.csv')
GOOD_ALL_BEST_CSV = os.path.join(SUB_DATA_DIR, 'all_best_good.csv')
ALL_BEST_DIFF = os.path.join(MAIN_DIR, 'all_best_perc_diff.csv')
GOOD_ALL_BEST_DIFF = os.path.join(SUB_DATA_DIR, 'all_best_perc_diff_good.csv')

ORIG_ALL_BEST1 = os.path.join(SUB_DATA_DIR, 'orig_all_best1.dat')
FITEVB_OUT1 = os.path.join(SUB_DATA_DIR, 'fit1.best')
GOOD_ALL_BEST1 = os.path.join(SUB_DATA_DIR, 'all_best1_good.dat')
GOOD_ALL_BEST_CSV1 = os.path.join(SUB_DATA_DIR, 'all_best1_good.csv')
GOOD_ALL_BEST_DIFF1 = os.path.join(SUB_DATA_DIR, 'all_best_perc_diff1_good.csv')
GOOD_INP_OUT1 = os.path.join(SUB_DATA_DIR, 'fit1_good.inp')

ORIG_ALL_BEST_RESID = os.path.join(SUB_DATA_DIR, 'orig_all_best_w_resid.dat')
GOOD_ALL_BEST_RESID = os.path.join(SUB_DATA_DIR, 'all_best_resid_good.dat')
GOOD_ALL_BEST_RESID_CSV = os.path.join(SUB_DATA_DIR, 'all_best_w_resid_good.csv')
GOOD_ALL_BEST_RESID_DIFF = os.path.join(SUB_DATA_DIR, 'all_best_w_resid_perc_diff_good.csv')

ALL_BEST_STR = 'all_best.dat'
GOOD_ALL_BEST_NEW = os.path.join(SUB_DATA_DIR, 'all_best_new_good.dat')

DA_GAUSS_INI = os.path.join(SUB_DATA_DIR, 'fitevb_setup.ini')
MISS_SEC_INI = os.path.join(SUB_DATA_DIR, 'fitevb_setup_missing_section.ini')
MISS_PARAM_INI = os.path.join(SUB_DATA_DIR, 'fitevb_setup_missing_param.ini')

GOOD_NO_INITIAL_OUT = os.path.join(SUB_DATA_DIR, 'fit_no_initial.inp')
GOOD_VII_FIT_OUT = os.path.join(SUB_DATA_DIR, 'fit_vii_good.inp')
GOOD_NO_VII_FIT_OUT = os.path.join(SUB_DATA_DIR, 'fit_not_vii_good.inp')

# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(MAIN_DIR, 'fit.inp')
SUB_DIR_DEF_OUT = os.path.join(SUB_DATA_DIR, 'fit.inp')

MISS_KEY_INFO_INI = os.path.join(SUB_DATA_DIR, 'fitevb_setup_missing_keyinfo.ini')
WRONG_SECTION_INI = os.path.join(SUB_DATA_DIR, 'fitevb_setup_wrong_section.ini')
BAD_DIR_INI = os.path.join(SUB_DATA_DIR, 'fitevb_setup_bad_dir.ini')
MISS_GROUP_NAME = os.path.join(SUB_DATA_DIR, 'fitevb_setup_miss_req_param.ini')

NO_OFF_DIAG_INI = os.path.join(SUB_DATA_DIR, 'fitevb_setup_no_offdiag.ini')
NO_OFF_DIAG_FITEVB_OUT = os.path.join(SUB_DATA_DIR, 'fit_no_off.best')
GOOD_NO_OFF_DIAG_OUT = os.path.join(SUB_DATA_DIR, 'fit_no_offdiag_good.inp')

ARQ_INI = os.path.join(SUB_DATA_DIR, 'fitevb_setup_arq.ini')
GOOD_ARQ_OUT = os.path.join(SUB_DATA_DIR, 'fit_arq_good.inp')
ARQ2_INI = os.path.join(SUB_DATA_DIR, 'fitevb_setup_arq2.ini')
GOOD_ARQ2_OUT = os.path.join(SUB_DATA_DIR, 'fit_arq2_good.inp')

GHOST_STR = 'ghost'


class TestFitEVBSetupFailWell(unittest.TestCase):
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoIni(self):
        test_input = []
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments:" in output)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)

    def testExtraParams(self):
        test_input = ["-c", MISS_SEC_INI, "-f", FITEVB_OUT]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("expected only the following parameters" in output)

    def testMissReqParams(self):
        test_input = ["-c", MISS_GROUP_NAME, "-f", FITEVB_OUT]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("In configuration file section 'REP1', missing parameter 'group_names'" in output)

    def testMissingParam(self):
        test_input = ["-c", MISS_PARAM_INI, "-f", FITEVB_OUT, ]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("missing parameter" in output)

    def testInputFile(self):
        test_input = ["-c", MISS_KEY_INFO_INI, "-f", FITEVB_OUT]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("expected comma-separated numerical lower range" in output)

    def testWrongSectionIni(self):
        test_input = ["-c", WRONG_SECTION_INI, "-f", FITEVB_OUT]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("program expects only the following sections" in output)

    def testGhostFile(self):
        test_input = ["-c", DA_GAUSS_INI, "-f", GHOST_STR]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problems reading specified" in output)

    def testTooFewInFitEVBOut(self):
        test_input = ["-c", DA_GAUSS_INI, "-f", FITEVB_OUT_TOO_FEW]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("(15) does not equal the total number of values (13)" in output)

    def testTooManyInFitEVBOut(self):
        test_input = ["-c", DA_GAUSS_INI, "-f", FITEVB_OUT_TOO_MANY]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("(15) does not equal the total number of values (17)" in output)

    def testMissingBest(self):
        test_input = ["-c", DA_GAUSS_INI, "-f", FITEVB_OUT, "-r"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("(16) does not equal the total number of values (15)" in output)

    def testSumWOBest(self):
        test_input = ["-c", DA_GAUSS_INI, "-s", ORIG_ALL_BEST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("specified, which is required with a specified" in output)


class TestFitEVBSetupFailWellQuitUnexpectedly(unittest.TestCase):
    def testGhostDir(self):
        test_input = ["-c", BAD_DIR_INI, "-f", FITEVB_OUT]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Invalid directory" in output)


class TestFitEVBSetupQuitUnexpectedly(unittest.TestCase):
    def testNoOffDiagFit(self):
        test_input = ["-c", NO_OFF_DIAG_INI, "-f", NO_OFF_DIAG_FITEVB_OUT]
        try:
            main(test_input)
            self.assertFalse(diff_lines(SUB_DIR_DEF_OUT, GOOD_NO_OFF_DIAG_OUT))
        finally:
            silent_remove(SUB_DIR_DEF_OUT, disable=DISABLE_REMOVE)


class TestFitEVBSetup(unittest.TestCase):
    def testNoFitEVBOut(self):
        try:
            main(["-c", DA_GAUSS_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_NO_INITIAL_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testWithBest(self):
        test_input = ["-c", DA_GAUSS_INI, "-f", FITEVB_OUT_RESID, "-r"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(DEF_OUT, GOOD_NO_VII_FIT_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testViiFit(self):
        try:
            main(["-c", DA_GAUSS_INI, "-f", FITEVB_OUT, "-v"])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_VII_FIT_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testARQFit(self):
        # In the EVB param file, this is option "PT" with "2-asymmetric" (confusing, huh?)
        test_input = ["-c", ARQ_INI]
        try:
            main(test_input)
            self.assertFalse(diff_lines(SUB_DIR_DEF_OUT, GOOD_ARQ_OUT))
        finally:
            silent_remove(SUB_DIR_DEF_OUT, disable=DISABLE_REMOVE)

    def testARQ2Fit(self):
        # In the EVB param file, this is option "PT" with "1-asymmetric" (confusing, huh?)
        test_input = ["-c", ARQ2_INI]
        try:
            main(test_input)
            self.assertFalse(diff_lines(SUB_DIR_DEF_OUT, GOOD_ARQ2_OUT))
        finally:
            silent_remove(SUB_DIR_DEF_OUT, disable=DISABLE_REMOVE)

    def testCollectBest(self):
        try:
            shutil.copyfile(ORIG_ALL_BEST, ALL_BEST)
            main(["-c", DA_GAUSS_INI, "-f", FITEVB_OUT, "-s", ALL_BEST])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_NO_VII_FIT_OUT))
            self.assertFalse(diff_lines(ALL_BEST, GOOD_ALL_BEST))
            self.assertFalse(diff_lines(ALL_BEST_CSV, GOOD_ALL_BEST_CSV))
            self.assertFalse(diff_lines(ALL_BEST_DIFF, GOOD_ALL_BEST_DIFF))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)
            silent_remove(ALL_BEST, disable=DISABLE_REMOVE)
            silent_remove(ALL_BEST_CSV, disable=DISABLE_REMOVE)
            silent_remove(ALL_BEST_DIFF, disable=DISABLE_REMOVE)

    def testCollectBestWResid(self):
        try:
            shutil.copyfile(ORIG_ALL_BEST_RESID, ALL_BEST)
            main(["-c", DA_GAUSS_INI, "-f", FITEVB_OUT_RESID, "-s", ALL_BEST, "-r"])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_NO_VII_FIT_OUT))
            self.assertFalse(diff_lines(ALL_BEST, GOOD_ALL_BEST_RESID))
            self.assertFalse(diff_lines(ALL_BEST_CSV, GOOD_ALL_BEST_RESID_CSV))
            self.assertFalse(diff_lines(ALL_BEST_DIFF, GOOD_ALL_BEST_RESID_DIFF))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)
            silent_remove(ALL_BEST, disable=DISABLE_REMOVE)
            silent_remove(ALL_BEST_CSV, disable=DISABLE_REMOVE)
            silent_remove(ALL_BEST_DIFF, disable=DISABLE_REMOVE)

    def testCollectBestWResid1(self):
        try:
            shutil.copyfile(ORIG_ALL_BEST1, ALL_BEST)
            main(["-c", DA_GAUSS_INI, "-f", FITEVB_OUT1, "-s", ALL_BEST, "-r"])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_INP_OUT1))
            self.assertFalse(diff_lines(ALL_BEST, GOOD_ALL_BEST1))
            self.assertFalse(diff_lines(ALL_BEST_CSV, GOOD_ALL_BEST_CSV1))
            self.assertFalse(diff_lines(ALL_BEST_DIFF, GOOD_ALL_BEST_DIFF1))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)
            silent_remove(ALL_BEST, disable=DISABLE_REMOVE)
            silent_remove(ALL_BEST_CSV, disable=DISABLE_REMOVE)
            silent_remove(ALL_BEST_DIFF, disable=DISABLE_REMOVE)

    def testCollectBestWResidNoInitialBest(self):
        try:
            # Ensure that this is not already a summary file
            silent_remove(ALL_BEST_STR, disable=DISABLE_REMOVE)
            main(["-c", DA_GAUSS_INI, "-f", FITEVB_OUT1, "-s", ALL_BEST_STR, "-r"])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_INP_OUT1))
            self.assertFalse(diff_lines(ALL_BEST_STR, GOOD_ALL_BEST_NEW))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)
            silent_remove(ALL_BEST_STR, disable=DISABLE_REMOVE)
