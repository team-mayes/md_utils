# !/usr/bin/env python
# coding=utf-8

"""
Calculates the average and standard deviation for the given radially-corrected
free energy data for a set of coordinates.
"""
from __future__ import print_function
import csv
import logging

import re

from md_utils.common import (find_files_by_dir, read_csv, mean, pstdev, allow_write)
from md_utils.wham import FREE_KEY, CORR_KEY, COORD_KEY

OUT_FNAME_FMT = "avg_rad_PMF.{}.csv"

__author__ = 'cmayes'

import argparse
import os
import sys
from collections import defaultdict

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('calc_split_avg')

# Constants #
OUT_PFX = 'stdev.'
# Inverse of the standard concentration in Angstrom ^ 3 / molecule
inv_C_0 = 1660.0
# Defaults #

DEF_FILE_PAT = 'rad_PMF*'
MEAN_KEY = 'mean'
STDEV_KEY = 'stdev'

OUT_KEY_SEQ = [COORD_KEY, MEAN_KEY, STDEV_KEY]

KEY_CONV = {FREE_KEY: float,
            CORR_KEY: float,
            COORD_KEY: float, }

AVG_KEY_CONV = {MEAN_KEY: float,
            STDEV_KEY: float,
            COORD_KEY: float, }


# Logic #


def bin_by_pattern(vals, pat='rad_PMF.(\d+)_\d+'):
    """
    Categorizes the given list of strings into bins where the strings have the
    same captured value from the given pattern.

    :param vals: The values to bin.
    :param pat: The pattern to use for matching.  Should contain a capturing group.
    :return: A dict of the values keyed by the matching captured substring.
    """
    rpat = re.compile(pat)
    prefix_bin = defaultdict(list)
    for pfile in vals:
        pmat = rpat.match(pfile)
        if pmat and len(pmat.groups()) >= 1:
            prefix_bin[pmat.group(1)].append(pfile)
    return prefix_bin

def calc_avg_stdev(coord_bin):
    collect_coord = defaultdict(list)
    for csv_data in (read_csv(cfile, KEY_CONV) for cfile in coord_bin):
        for drow in csv_data:
            collect_coord[drow[COORD_KEY]].append(drow[CORR_KEY])
    results = []
    for coord, freng_vals in collect_coord.items():
        results.append((coord, mean(freng_vals), pstdev(freng_vals)))
    return results


def write_avg_stdev(result, out_fname, overwrite=False, basedir=None):
    """Writes the result to a file named for the given source file.

    :param result: The result to write.
    :param out_fname: The target out file.
    :param overwrite: Whether to overwrite an existing file name.
    :param basedir: The base directory to target (uses the source file's base directory
        if not specified)
    """
    if basedir:
        tgt_file = os.path.join(basedir, out_fname)
    else:
        tgt_file = out_fname

    if allow_write(tgt_file, overwrite=overwrite):
        with open(tgt_file , 'w') as csvfile:
            res_writer = csv.writer(csvfile)
            res_writer.writerow(OUT_KEY_SEQ)
            for res_row in sorted(result):
                res_writer.writerow(res_row)

# CLI Processing #


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    :param argv: is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Calculates the average and standard deviation '
                                                 'for the given radially-corrected free '
                                                 'energy data for a set of coordinates.')
    parser.add_argument("-d", "--base_dir", help="The starting point for a file search "
                                                 "(defaults to current directory)",
                        default=os.getcwd())
    parser.add_argument('-p', "--pattern", help="The file pattern to search for "
                                                "(defaults to '{}')".format(DEF_FILE_PAT),
                        default=DEF_FILE_PAT)
    parser.add_argument('-o', "--overwrite", help='Overwrite existing target file',
                        action='store_true')

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


    found_files = find_files_by_dir(args.base_dir, args.pattern)
    logger.debug("Found '%d' dirs with files to process", len(found_files))
    for fdir, files in found_files.items():
        bin_pfx = bin_by_pattern(files)
        for pfx, binf in bin_pfx.items():
            bin_results = calc_avg_stdev([os.path.join(fdir, tgt) for tgt in binf])
            avg_fname = OUT_FNAME_FMT.format(pfx)
            write_avg_stdev(bin_results, os.path.join(fdir, avg_fname), overwrite=args.overwrite)
    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
