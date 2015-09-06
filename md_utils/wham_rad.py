from __future__ import print_function
import csv
import logging
import math

from md_utils.common import find_files_by_dir

__author__ = 'cmayes'

# !/usr/bin/env python

"""
Creates a radial correction value for each line of the target file(s).
"""

import argparse
import os
import sys

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wham_rad')

# Constants #

OUT_PFX = 'rad_'
# Boltzmann's Constant in kcal/mol Kelvin
BOLTZ_CONST = 0.0019872041

# Defaults #

DEF_FILE_PAT = 'PMF*'


# Keys #
CORR_KEY = 'corr'
COORD_KEY = 'coord'
FREE_KEY = 'free_energy'

# Logic #

def create_out_fname(src_file):
    return os.path.abspath(os.path.join(os.path.dirname(src_file),
                                        OUT_PFX + os.path.basename(src_file)))

def calc_corr(coord, freng, kbt):
    try:
        return freng + kbt * math.log(4 * math.pi * coord ** 2)
    except TypeError:
        return freng

def calc_rad(src_file, kbt):
    reslines = []
    with open(src_file) as wham:
        for wline in wham:
            wres = {}
            try:
                swline = wline.strip().split()
                if len(swline) < 2 or "#" in swline[0]:
                    continue
                wres[COORD_KEY] = float(swline[0])
                try:
                    wres[FREE_KEY] = float(swline[1])
                except ValueError:
                    wres[FREE_KEY] = swline[1]
            except Exception, e:
                logger.debug("Error '{}' for line '{}'".format(e, wline))
            wres[CORR_KEY] = calc_corr(wres[COORD_KEY], wres[FREE_KEY], kbt)
            reslines.append(wres)
    return reslines

def to_zero_point(corr_res):
    max_cor_freng = None
    for zrow in corr_res:
        try:
            row_corr_val = zrow[CORR_KEY]
            if max_cor_freng < row_corr_val and not math.isinf(row_corr_val):
                max_cor_freng = row_corr_val
        except Exception, e:
            logger.debug("Error finding zero point: '%s'", e)
            continue
    for zrow in corr_res:
        zrow[CORR_KEY] -= max_cor_freng
    return corr_res

def write_result(proc_data, out_fname):
    with open(out_fname, 'w') as csvfile:
        fieldnames = [COORD_KEY, FREE_KEY, CORR_KEY]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(proc_data)

# CLI Processing #

def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates a radial correction value for each line '
                                                 'of the target file(s).')
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
    args, ret = parse_cmdline(argv)
    if ret != 0:
        return ret

    kbt = args.temp * BOLTZ_CONST

    if args.src_file is not None:
        proc_data = to_zero_point(calc_rad(args.src_file, kbt))
        write_result(proc_data, create_out_fname(args.src_file))
    else:
        found_files = find_files_by_dir(args.base_dir, args.pattern)
        logger.debug("Found '{}' dirs with files to process".format(len(found_files)))
        for fdir, files in found_files.iteritems():
            if not files:
                logger.warn("No files found for dir '{}'")
                continue
            for pmf_path in ([os.path.join(fdir, tgt) for tgt in files]):
                proc_data = to_zero_point(calc_rad(pmf_path, kbt))
                out_fname = create_out_fname(pmf_path)
                if os.path.exists(out_fname) and not args.overwrite:
                    logger.warn("Not overwriting existing file '%s'", out_fname)
                    continue
                write_result(proc_data, out_fname)

    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
