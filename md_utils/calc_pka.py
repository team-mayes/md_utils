# !/usr/bin/env python
# coding=utf-8

"""
Calculates the proton dissociation constant (PKA) for the given free energy
data for a set of coordinates.

* Input is rad_PMF (use corr col (3))
** Plan for standard WHAM, too.
* Find local max (inc, then dec) (two back) (middle val is tgt);
  in the algorithm below, I will call the coordinate points
  r_i-1 r_i, and r_i+1   (middle point, r_i, is the tgt);
  and for energy, corr_i-1, corr_i, and coor_i+1
* Up to local max, do math and add to sum
** Will need to calculate the spacing between coordinate values
  (called delta_r); usually this will be a constant number, but
  it is not in the case of your sample data because I deleted
  points. You can certainly calculate this every step if you wish,
  so we don't have to count on equal spacing; the calculation
  can be delta_r = r_i+1 - r_i
** we will need pi
** a new constant we can call inv_C_0 (that's a zero) = 1660.0
   (it's units are Angstrom ^ 3 / molecule )
** will will need kBT (you calculated this before, in wham_rad;
   you can have the user enter the temp. The temp will be the
   same as used in wham_rad and in making the wham input line
** sum_for_pka += 4.0 * pi * r_i ** 2 * math.exp( -corr_i / kBT ) * delta_r
** pKa = - math.log10 ( inv_C_0 / sum_for_pka )
* Result is PKA: out to stdout
* Debug out local max value
"""
from __future__ import print_function
import logging
import math
import argparse
import os
import sys
import numpy as np
from md_utils.md_common import (find_files_by_dir,
                                read_csv, write_csv, calc_kbt, create_out_fname, warning, allow_write)
from md_utils.wham import FREE_KEY, CORR_KEY, COORD_KEY

__author__ = 'mayes'


# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('calc_pka')

# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2

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
            MAX_VAL: float}

NO_MAX_RET = np.nan
NO_MAX_ERR = "No local max found"


# Exceptions #

class NoMaxError(Exception):
    pass


# Logic #


def write_result(result, src_file, overwrite=False, basedir=None):
    """Writes the result to a file named for the given source file.

    :param result: The result to write.
    :param src_file: The original source file name.
    :param overwrite: Whether to overwrite an existing file name.
    :param basedir: The base directory to target (uses the source file's base directory
        if not specified)
    """
    f_name = create_out_fname(src_file, prefix=OUT_PFX, base_dir=basedir)
    if allow_write(f_name, overwrite=overwrite):
        write_csv(result, f_name, OUT_KEY_SEQ)


def calc_pka(file_data, kbt, coord_ts=None):
    """Calculates the proton dissociation constant (PKA) for the given free energy data.

    :param file_data: The list of dicts to process.
    :param kbt: The experimental temperature multiplied by Boltzmann's Constant.
    :param coord_ts: specified user parameter; integrate to this coordinate value
    :return: The PKA for the given data set or an error string if no local max is found.
    """
    sum_for_pka = 0.0
    data_len = len(file_data)
    last_idx = data_len - 1
    for i in range(data_len):
        if i == last_idx:
            raise NoMaxError(NO_MAX_ERR)
        cur_coord = file_data[i][COORD_KEY]
        cur_corr = file_data[i][CORR_KEY]
        if math.isinf(cur_corr):
            continue
        delta_r = file_data[i + 1][COORD_KEY] - cur_coord
        sum_for_pka += 4.0 * math.pi * cur_coord ** 2 * math.exp(-cur_corr / kbt) * delta_r

        if i == 0:
            continue

        if coord_ts is None:
            if cur_corr > file_data[i - 1][CORR_KEY] and cur_corr > file_data[i + 1][CORR_KEY]:
                logger.info("Found local max '%f' at coordinate '%f'", cur_corr, cur_coord)
                return -math.log10(inv_C_0 / sum_for_pka), cur_corr, cur_coord
        else:
            if cur_coord >= coord_ts:
                logger.info("Integrating to input TS coordinate '%f' with value '%f'", cur_coord, cur_corr)
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
    parser.add_argument('-c', "--coord_ts", help='Manually entered coordinate of TS. '
                                                 'Used in place of first local maximum.',
                        type=float)
    parser.add_argument("temp", help="The temperature in Kelvin for the simulation", type=float)

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        warning(e)
        parser.print_help()
        return [], INPUT_ERROR

    return args, GOOD_RET


def main(argv=None):
    """ Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    kbt = calc_kbt(args.temp)
    if args.coord_ts is not None:
        logger.info("Read TS coordinate value: '%f'", args.coord_ts)

    try:
        if args.src_file is not None:
            file_data = read_csv(args.src_file, data_conv=KEY_CONV)
            f_base_name = os.path.basename(args.src_file)
            try:
                pka, cur_corr, cur_coord = calc_pka(file_data, kbt, args.coord_ts)
                result = [{SRC_KEY: f_base_name, PKA_KEY: pka, MAX_VAL: cur_corr, MAX_LOC: cur_coord}]
            except NoMaxError:
                result = [{SRC_KEY: f_base_name, PKA_KEY: NO_MAX_RET, MAX_VAL: NO_MAX_RET, MAX_LOC: NO_MAX_RET}]
            write_result(result, args.src_file, args.overwrite)
        else:
            found_files = find_files_by_dir(args.base_dir, args.pattern)
            logger.debug("Found '%d' dirs with files to process", len(found_files))
            if len(found_files) == 0:
                raise IOError("No files found in specified directory '{}'".format(args.base_dir))
            for f_dir, files in found_files.items():
                results = []
                for pmf_path, fname in ([(os.path.join(f_dir, tgt), tgt) for tgt in sorted(files)]):
                    file_data = read_csv(pmf_path, data_conv=KEY_CONV)
                    try:
                        pka, cur_corr, cur_coord = calc_pka(file_data, kbt, args.coord_ts)
                        results.append({SRC_KEY: fname, PKA_KEY: pka, MAX_VAL: cur_corr, MAX_LOC: cur_coord})
                    except NoMaxError:
                        results.append({SRC_KEY: fname, PKA_KEY: NO_MAX_RET, MAX_VAL: NO_MAX_RET,
                                        MAX_LOC: NO_MAX_RET})

                write_result(results, os.path.basename(f_dir), args.overwrite,
                             basedir=os.path.dirname(f_dir))
    except IOError as e:
        warning(e)
        return IO_ERROR

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
