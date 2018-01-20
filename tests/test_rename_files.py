# coding=utf-8

"""
"""
import os
import itertools
import unittest

import shutil

from md_utils.rename_files import main
from md_utils.md_common import (capture_stdout, capture_stderr, silent_remove)
import logging

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'rename_files')

# Files #

SMALL_FILE = os.path.join(SUB_DATA_DIR, 'small_file.txt')

# test data #
TEST_FILE_NAMES = ['has space.txt', 'has two spaces.txt', 'now!exclaim.txt']
# noinspection SpellCheckingInspection
REPLACED_FILE_NAMES1 = ['hasspace.txt', 'hastwospaces.txt', 'now!exclaim.txt']
REPLACED_FILE_NAMES2 = ['has space.txt', 'has two spaces.txt', 'now_exclaim.txt']
# noinspection SpellCheckingInspection
REPLACED_FILE_NAMES_B = ['pre_hasspace.txt', 'pre_hastwospaces.txt', 'now!exclaim.txt']
REPLACED_FILE_NAMES_S = ['has space.txt', 'has two spaces.txt', 'now_exclaim_yes.txt']
REPLACED_FILE_NAMES_E = ['has space.txt', 'has two spaces.txt', 'now_exclaim.dat']
ALL_NEW_OLD_FILES = set(itertools.chain(TEST_FILE_NAMES, REPLACED_FILE_NAMES1, REPLACED_FILE_NAMES2,
                                        REPLACED_FILE_NAMES_B, REPLACED_FILE_NAMES_S, REPLACED_FILE_NAMES_E))


def make_files(fname_list):
    """
    Create files fresh, because will be moved when program runs
    @param fname_list: list of file names without directory name
    """
    for fname in fname_list:
        new_file = os.path.join(SUB_DATA_DIR, fname)
        shutil.copyfile(SMALL_FILE, new_file)


def add_sub_dir(fname_list, abs_dir):
    """
    Create files fresh, because will be moved when program runs
    @param fname_list: list of file names without directory name
    @param abs_dir: absolute directory name
    @return full_name_list: a list of file names with the specified absolute directory
    """
    full_name_list = []
    for fname in fname_list:
        full_name_list.append(os.path.join(abs_dir, fname))
    return full_name_list


def count_files(fname_list):
    """
    Counts how many files in list exist
    @param fname_list: list of file names
    @return num_existing_files: a list of file names with the specified absolute directory
    """
    num_existing_files = 0
    for fname in fname_list:
        if os.path.isfile(fname):
            num_existing_files += 1
    return num_existing_files


def clean_dir():
    for fname in ALL_NEW_OLD_FILES:
        file_loc = os.path.join(SUB_DATA_DIR, fname)
        silent_remove(file_loc)


class TestRenameNoOutput(unittest.TestCase):
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testInvalidArg(self):
        test_input = ['-@']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("unrecognized arguments" in output)


def run_main_then_reset(test_input):
    """
    Reset test state after running debug version of test
    :param test_input: test input params
    :return:
    """
    main(test_input)
    # need to make again for capturing std out
    clean_dir()
    make_files(TEST_FILE_NAMES)


def run_test_option(test_input, new_names_this_test, text_object):
    # common instructions for multiple text options
    clean_dir()
    make_files(TEST_FILE_NAMES)
    num_changed_files = len(set(TEST_FILE_NAMES) - set(new_names_this_test))
    num_unchanged_files = len(TEST_FILE_NAMES) - num_changed_files
    initial_f_names = add_sub_dir(TEST_FILE_NAMES, SUB_DATA_DIR)
    expected_f_names = add_sub_dir(new_names_this_test, SUB_DATA_DIR)
    try:
        if logger.isEnabledFor(logging.DEBUG):
            if logger.isEnabledFor(logging.DEBUG):
                run_main_then_reset(test_input)
        with capture_stdout(main, test_input) as output:
            text_object.assertTrue("Found and renamed {} files".format(num_changed_files) in output)
        text_object.assertEqual(count_files(initial_f_names), num_unchanged_files)
        text_object.assertEqual(count_files(expected_f_names), len(expected_f_names))
    finally:
        clean_dir()


class TestRename(unittest.TestCase):
    def testNoFilesRenamed(self):
        clean_dir()
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("Found and renamed 0 files" in output)

    def testDefaultPatterns(self):
        test_input = ["-d", SUB_DATA_DIR]
        new_names_this_test = REPLACED_FILE_NAMES1
        run_test_option(test_input, new_names_this_test, self)

    def testAltPattern(self):
        test_input = ["-d", SUB_DATA_DIR, "-p", "!", "-n", "_"]
        new_names_this_test = REPLACED_FILE_NAMES2
        run_test_option(test_input, new_names_this_test, self)

    def testAddBegin(self):
        # test that prefix added to all 3 files
        test_input = ["-d", SUB_DATA_DIR, "-b", "pre_"]
        new_names_this_test = REPLACED_FILE_NAMES_B

        run_test_option(test_input, new_names_this_test, self)

    def testAddSuffix(self):
        # test that prefix added to all 3 files
        test_input = ["-d", SUB_DATA_DIR, "-s", "_yes", "-p", "!", "-n", "_"]
        new_names_this_test = REPLACED_FILE_NAMES_S

        run_test_option(test_input, new_names_this_test, self)

    def testAddExt(self):
        # test that prefix added to all 3 files
        # replace next next 2 lines for this test. The rest is the same!
        test_input = ["-d", SUB_DATA_DIR, "-e", ".dat", "-p", "!", "-n", "_"]
        new_names_this_test = REPLACED_FILE_NAMES_E

        run_test_option(test_input, new_names_this_test, self)
