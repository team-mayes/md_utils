# !/usr/bin/env python
# coding=utf-8

"""
Creates a radial correction value for each line of the target file(s).
"""
from __future__ import print_function

import logging
import math
import argparse
import os
import sys
from md_utils.md_common import (find_files_by_dir, write_csv,
                                calc_kbt, create_out_fname, allow_write, GOOD_RET, INPUT_ERROR)
from md_utils.wham import CORR_KEY, COORD_KEY, FREE_KEY, RAD_KEY_SEQ

__author__ = 'mayes'

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wham_rad')

# Constants #

OUT_PFX = 'rad_'

# Defaults #

DEF_FILE_PAT = 'PMF*'


# Logic #


def calc_corr(coord, freng, kbt):
    """Calculates the radial correction for the given free energy.

    :param coord: The coordinates under consideration.
    :param freng: The free energy to correct.
    :param kbt: The experimental temperature in Kelvin multiplied by Boltzmann's Constant.
    :return: The radially corrected free energy. If there is an error, return freng
             because the most likely error is that freng is inf; in that case, just return freng,
             which is handled later.
    """
    try:
        return freng + kbt * math.log(4 * math.pi * coord ** 2)
    except TypeError:
        return freng


def calc_rad(src_file, kbt):
    """
    Applies radial correction to the free energy values in the given source file, returning a list of dicts
    containing the corrected contents of the given file.

    :param src_file: The file with the data to correct.
    :param kbt: The experimental temperature in Kelvin multiplied by Boltzmann's Constant.
    :return: The corrected contents of the file as a list of dicts.
    """
    res_lines = []
    with open(src_file) as wham:
        for w_line in wham:
            w_res = {}
            try:
                sw_line = w_line.strip().split()
                if len(sw_line) < 2 or "#" in sw_line[0]:
                    continue
                w_res[COORD_KEY] = float(sw_line[0])
                try:
                    w_res[FREE_KEY] = float(sw_line[1])
                except ValueError:
                    w_res[FREE_KEY] = sw_line[1]
            except Exception as e:
                logger.debug("Error {} for line {}".format(e, w_line))
            w_res[CORR_KEY] = calc_corr(w_res[COORD_KEY], w_res[FREE_KEY], kbt)
            res_lines.append(w_res)
    return res_lines


def to_zero_point(corr_res):
    """
    # Sets the highest free energy value as zero for the given data set.
    Sets the free energy value at the furthest coordinate as zero for the given data set.

    :param corr_res: The data set to orient.
    :return: The data set reoriented relative to the highest free energy value.
    """
    # max_cor_freng = None
    # for z_row in corr_res:
    #     try:
    #         row_corr_val = z_row[CORR_KEY]
    #         if max_cor_freng < row_corr_val and not math.isinf(row_corr_val):
    #             max_cor_freng = row_corr_val
    #     except Exception, e:
    #         logger.debug("Error finding zero point: '%s'", e)
    #         continue
    # for z_row in corr_res:
    #     z_row[CORR_KEY] -= max_cor_freng
    # return corr_res

    max_coord = 0.0
    set_cor_freng = 0.0
    for z_row in corr_res:
        try:
            row_coord_val = z_row[COORD_KEY]
            row_corr_val = z_row[CORR_KEY]
            if max_coord < row_coord_val and not math.isinf(row_corr_val):
                max_coord = row_coord_val
                set_cor_freng = row_corr_val
        except Exception as e:
            logger.debug("Error finding zero point: '%s'", e)
            continue
    for z_row in corr_res:
        z_row[CORR_KEY] -= set_cor_freng
    return corr_res


# CLI Processing #


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    :param argv: is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates a radial correction value for each line '
                                                 'of the target file(s). \n'
                                                 'The output is a three-column file: original coord, original free'
                                                 ' energy, radially-corrected free-energy (with zero set to equal'
                                                 ' the furthest (highest) coordinate corrected free energy).')
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

    try:
        args = parser.parse_args(argv)
    except SystemExit:
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

    if args.src_file is not None:
        proc_data = to_zero_point(calc_rad(args.src_file, kbt))
        write_csv(proc_data, create_out_fname(args.src_file, prefix=OUT_PFX), RAD_KEY_SEQ)
    else:
        found_files = find_files_by_dir(args.base_dir, args.pattern)
        logger.debug("Found '%d' dirs with files to process", len(found_files))
        # noinspection PyCompatibility
        for f_dir, files in found_files.iteritems():
            if not files:
                logger.warn("No files found for dir '%s'", f_dir)
                continue
            for pmf_path in ([os.path.join(f_dir, tgt) for tgt in files]):
                proc_data = to_zero_point(calc_rad(pmf_path, kbt))
                f_name = create_out_fname(pmf_path, prefix=OUT_PFX)
                if allow_write(f_name, overwrite=args.overwrite):
                    write_csv(proc_data, f_name, RAD_KEY_SEQ)
    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
