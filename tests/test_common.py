# coding=utf-8

"""
Tests for the common lib.
"""
import logging
import shutil
import tempfile
import unittest

import os

from md_utils.common import (find_files_by_dir, create_out_fname, read_csv,
                             write_csv, str_to_bool)
from md_utils.fes_combo import DEF_FILE_PAT
from md_utils.wham import CORR_KEY, COORD_KEY, FREE_KEY, RAD_KEY_SEQ

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_common')


# Constants #
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
FES_OUT_DIR = 'fes_out'
CALC_PKA_DIR = 'calc_pka'
CSV_FILE = os.path.join(DATA_DIR, CALC_PKA_DIR, 'rad_PMFlast2ns3_1.txt')
FES_BASE = os.path.join(DATA_DIR, FES_OUT_DIR)
FRENG_TYPES = [float, str]

ORIG_WHAM_FNAME = "PMFlast2ns3_1.txt"
ORIG_WHAM_PATH = os.path.join(DATA_DIR, ORIG_WHAM_FNAME)
SHORT_WHAM_PATH = os.path.join(DATA_DIR, ORIG_WHAM_FNAME)

OUT_PFX = 'rad_'

# Util Functions #


def expected_dir_data():
    """
    :return: The data structure that's expected from `find_files_by_dir`
    """
    return {os.path.abspath(os.path.join(FES_BASE, "1.00")): ['fes.out'],
            os.path.abspath(os.path.join(FES_BASE, "2.75")): ['fes.out', 'fes_cont.out'],
            os.path.abspath(os.path.join(FES_BASE, "5.50")): ['fes.out', 'fes_cont.out'],
            os.path.abspath(os.path.join(FES_BASE, "multi")): ['fes.out', 'fes_cont.out',
                                                               'fes_cont2.out', 'fes_cont3.out'], }


def csv_data():
    """
    :return: Test data as a list of dicts.
    """
    rows = [{CORR_KEY: 123.42, COORD_KEY: "75", FREE_KEY: True},
            {CORR_KEY: 999.43, COORD_KEY: "yellow", FREE_KEY: False}]
    return rows


def is_one_of_type(val, types):
    """Returns whether the given value is one of the given types.

    :param val: The value to evaluate
    :param types: A sequence of types to check against.
    :return: Whether the given value is one of the given types.
    """
    val_type = type(val)
    for tt in types:
        if val_type is tt:
            return True
    return False


# Tests #


class TestFindFiles(unittest.TestCase):
    """
    Tests for the file finder.
    """

    def test_find(self):
        self.maxDiff = None
        found = find_files_by_dir(FES_BASE, DEF_FILE_PAT)
        exp_data = expected_dir_data()
        self.assertEqual(len(exp_data), len(found))
        for key, files in exp_data.items():
            found_files = found.get(key)
            try:
                self.assertCountEqual(files, found_files)
            except AttributeError:
                self.assertItemsEqual(files, found_files)



class TestCreateOutFname(unittest.TestCase):
    def testOutFname(self):
        """
        Check for prefix addition.
        """
        self.assertTrue(create_out_fname(ORIG_WHAM_PATH, OUT_PFX).endswith(
            os.sep + OUT_PFX + ORIG_WHAM_FNAME))


class TestReadCsv(unittest.TestCase):
    def testReadCsv(self):
        """
        Verifies the contents of the CSV file.
        """
        result = read_csv(CSV_FILE)
        self.assertTrue(result)
        for row in result:
            self.assertEqual(3, len(row))
            self.assertIsNotNone(row.get(FREE_KEY, None))
            self.assertIsInstance(row[FREE_KEY], str)
            self.assertIsNotNone(row.get(CORR_KEY, None))
            self.assertIsInstance(row[CORR_KEY], str)
            self.assertIsNotNone(row.get(COORD_KEY, None))
            self.assertIsInstance(row[COORD_KEY], str)

    def testReadTypedCsv(self):
        """
        Verifies the contents of the CSV file.
        """
        result = read_csv(CSV_FILE, {FREE_KEY: float,
                                     CORR_KEY: float,
                                     COORD_KEY: float, })
        self.assertTrue(result)
        for row in result:
            self.assertEqual(3, len(row))
            self.assertIsNotNone(row.get(FREE_KEY, None))
            self.assertTrue(is_one_of_type(row[FREE_KEY], FRENG_TYPES))
            self.assertIsNotNone(row.get(CORR_KEY, None))
            self.assertTrue(is_one_of_type(row[CORR_KEY], FRENG_TYPES))
            self.assertIsNotNone(row.get(COORD_KEY, None))
            self.assertIsInstance(row[COORD_KEY], float)


class TestWriteCsv(unittest.TestCase):
    def testWriteCsv(self):
        tmp_dir = None
        data = csv_data()
        try:
            tmp_dir = tempfile.mkdtemp()
            tgt_fname = create_out_fname(SHORT_WHAM_PATH, OUT_PFX, base_dir=tmp_dir)

            write_csv(data, tgt_fname, RAD_KEY_SEQ)
            csv_result = read_csv(tgt_fname, {FREE_KEY: str_to_bool,
                                              CORR_KEY: float,
                                              COORD_KEY: str, })
            self.assertEqual(len(data), len(csv_result))
            for i, csv_row in enumerate(csv_result):
                self.assertDictEqual(data[i], csv_row)
            logger.debug(csv_result)
        finally:
            shutil.rmtree(tmp_dir)
