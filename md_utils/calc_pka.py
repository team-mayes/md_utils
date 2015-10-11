# !/usr/bin/env python
# coding=utf-8

"""
Calculates the proton dissociation constant (PKA) for the given free energy
data for a set of coordinates.
"""
from __future__ import print_function
import logging
import math

from md_utils.common import (find_files_by_dir, create_out_fname,
                             read_csv, write_csv, calc_kbt)
from md_utils.wham import FREE_KEY, CORR_KEY, COORD_KEY

NO_MAX_ERR = "No local max found"

__author__ = 'cmayes'

import argparse
import os
import sys

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('calc_pka')

# Constants #
OUT_PFX = 'pKa.'
# Inverse of the standard concentration in Angstrom ^ 3 / molecule
inv_C_0 = 1660.0
# Defaults #

DEF_FILE_PAT = 'rad_PMF*'
SRC_KEY = 'source_file'
PKA_KEY = 'pKa'
MAX_LOC = 'max_loc'
MAX_VAL = 'max_val'

OUT_KEY_SEQ = [SRC_KEY, PKA_KEY, MAX_LOC, MAX_VAL]

KEY_CONV = {FREE_KEY: float,
            CORR_KEY: float,
            COORD_KEY: float,
            MAX_LOC: float,
            MAX_VAL: float }

# Logic #


def write_result(result, src_file, overwrite=False, basedir=None):
    """Writes the result to a file named for the given source file.

    :param result: The result to write.
    :param src_file: The original source file name.
    :param overwrite: Whether to overwrite an existing file name.
    :param basedir: The base directory to target (uses the source file's base directory
        if not specified)
    """
    out_fname = create_out_fname(src_file, OUT_PFX, base_dir=basedir)
    if os.path.exists(out_fname) and not overwrite:
        logger.warn("Not overwriting existing file '%s'", out_fname)
        return
    write_csv(result, out_fname, OUT_KEY_SEQ)


def calc_pka(file_data, kbt):
    """Calculates the proton dissociation constant (PKA) for the given free energy data.

    :param file_data: The list of dicts to process.
    :param kbt: The experimental temperature multiplied by Boltzmann's Constant.
    :return: The PKA for the given data set or an error string if no local max is found.
    """
    sum_for_pka = 0.0
    data_len = len(file_data)
    last_idx = data_len - 1
    for i in range(data_len):
        if i == last_idx:
            return NO_MAX_ERR
        cur_coord = file_data[i][COORD_KEY]
        cur_corr = file_data[i][CORR_KEY]
        if math.isinf(cur_corr):
            continue
        delta_r = file_data[i + 1][COORD_KEY] - cur_coord
        sum_for_pka += 4.0 * math.pi * cur_coord ** 2 * math.exp(-cur_corr / kbt) * delta_r

        if i == 0:
            continue
        if cur_corr > file_data[i - 1][CORR_KEY] and cur_corr > file_data[i + 1][CORR_KEY]:
            logger.info("Found local max '%f' at coordinates '%f'", cur_corr, cur_coord)
            return -math.log10(inv_C_0 / sum_for_pka), cur_corr, cur_coord


# CLI Processing #


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    :param argv: is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Calculates the proton dissociation constant '
                                                 '(PKA) for the given radially-corrected free '
                                                 'energy data for a set of coordinates.')
    parser.add_argument("-d", "--base_dir", help="The starting point for a file search "
                                                 "(defaults to current directory)",
                        default=os.getcwd())
    parser.add_argument("-f", "--src_file", help="The single file to read from (takes precedence "
                                                 "over base_dir)")
    parser.add_argument('-p', "--pattern", help="The file pattern to search for "
                                                "(defaults to '{}')".format(DEF_FILE_PAT),
                        default=DEF_FILE_PAT)
    parser.add_argument('-o', "--overwrite", help='Overwrite existing target file',
                        action='store_true')
    parser.add_argument("temp", help="The temperature in Kelvin for the simulation", type=float)

    args = parser.parse_args(argv)

    return args, 0


def main(argv=None):
    """ Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != 0:
        return ret

    kbt = calc_kbt(args.temp)

    if args.src_file is not None:
        file_data = read_csv(args.src_file, KEY_CONV)
        pka, cur_corr, cur_coord = calc_pka(file_data, kbt)
        result = [{SRC_KEY: args.src_file, PKA_KEY: pka, MAX_VAL: cur_corr, MAX_LOC: cur_coord}]
        write_result(result, args.src_file, args.overwrite)
    else:
        found_files = find_files_by_dir(args.base_dir, args.pattern)
        logger.debug("Found '%d' dirs with files to process", len(found_files))
        for fdir, files in found_files.items():
            results = []
            if not files:
                logger.warn("No files found for dir '%s'", fdir)
                continue
            for pmf_path, fname in ([(os.path.join(fdir, tgt), tgt) for tgt in sorted(files)]):
                file_data = read_csv(pmf_path, KEY_CONV)
                pka, cur_corr, cur_coord = calc_pka(file_data, kbt)
                results.append({SRC_KEY: fname, PKA_KEY: pka, MAX_VAL: cur_corr,
                            MAX_LOC: cur_coord})

            write_result(results, os.path.basename(fdir), args.overwrite,
                         basedir=os.path.dirname(fdir))

    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
