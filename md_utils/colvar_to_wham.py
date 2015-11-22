# !/usr/bin/env python
# coding=utf-8

"""
Reads a COLVAR file from an umbrella sampling run with a spherical potential and
processes to provide the radial distance [R] (the CV) to give a list of CV
values to WHAM. Echos the timestep from the COLVAR file.
"""
from __future__ import print_function
import logging
import math

from md_utils.md_common import (find_files_by_dir, create_out_fname, write_csv, list_to_file)

__author__ = 'hmayes'

import argparse
import os
import sys

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('colvar_to_wham')

# Keys #

TIMESTEP_KEY = "timestep"
DX_KEY = "dx"
DY_KEY = "dy"
DZ_KEY = "dz"
R_KEY = "r"
COLVAR_WHAM_KEY_SEQ = [R_KEY]

# Constants #

OUT_PFX = 'to_wham_'

# Defaults #

DEF_FILE_PAT = 'COLVAR*'


# Logic #


def calc_R(dx,dy,dz):
    """Calculates the radial distance (R) for the given dx, dy, dz (X1-X2, Y1-Y2, Z1-Z2)

    :param dx, dy, dz: the  (X1-X2, Y1-Y2, Z1-Z2) for timestep under consideration.
    :return: radial distance.
    """
    return math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

def calc_for_wham(src_file):
    """
    Calculates the radial distance for each line, returning a list of dicts.

    :param src_file: The file with the data to correct.
    :return: The radial distance of the file as a list of dicts.
    """
    reslines = []
    logger.debug("Found '%s' file to process", src_file)
    with open(src_file) as colvar:
        for wline in colvar:
            wres = {}
            try:
                swline = wline.strip().split()
                if len(swline) < 4 or "#" in swline[0]:
                    continue
                wres[TIMESTEP_KEY] = float(swline[0])
                wres[DX_KEY] = float(swline[1])
                wres[DY_KEY] = float(swline[2])
                wres[DZ_KEY] = float(swline[3])
                wres[R_KEY] = calc_R(wres[DX_KEY],wres[DY_KEY],wres[DZ_KEY])
            except Exception as e:
                logger.debug("Error '%s' for line '%s'", e, wline)
            reslines.append(wres)
    return reslines


# CLI Processing #


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    :param argv: is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Calculates R for each line of the target file(s).')
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

    if args.src_file is not None:
        proc_data = calc_for_wham(args.src_file)
        write_csv(proc_data, create_out_fname(args.src_file, OUT_PFX), COLVAR_WHAM_KEY_SEQ)
    else:
        found_files = find_files_by_dir(args.base_dir, args.pattern)
        logger.debug("Found '%d' dirs with files to process", len(found_files))
        for fdir, files in found_files.iteritems():
            if not files:
                logger.warn("No files found for dir '%s'", fdir)
                continue
            for colvar_path in ([os.path.join(fdir, tgt) for tgt in files]):
                proc_data = calc_for_wham(colvar_path)
                out_fname = create_out_fname(colvar_path, OUT_PFX)
                if os.path.exists(out_fname) and not args.overwrite:
                    logger.warn("Not overwriting existing file '%s'", out_fname)
                    continue
                list_to_file([str(d['r']) for d in proc_data if 'r' in d], out_fname)
                #write_csv(proc_data, out_fname, COLVAR_WHAM_KEY_SEQ, extrasaction="ignore")

    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
