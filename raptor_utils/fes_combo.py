from __future__ import print_function
import logging

from raptor_utils.common import find_files_by_dir

__author__ = 'cmayes'

# !/usr/bin/env python

"""
Module docstring.
"""

import argparse
import os
import sys

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)

logger = logging.getLogger('fes_combo')
logger.setLevel(logging.DEBUG)

# Defaults #

DEF_FILE_PAT = 'fes*.out'
DEF_TGT = 'all_fes.csv'

# Logic #

def combine(tgt_files):
    """
    Reads in and combines target files, sorting for precedence by the largest
    timestep value in the first data row.  Note that this function reads the
    entire contents of each file into memory and will therefore scale poorly
    for very large files.

    :param tgt_files: A list of the absolute locations of the files to combine.
    :return: A list of the combined lines of the target files.
    """
    mapped_files = {}
    for tgt_file in tgt_files:
        fkey, fmap = map_fes(tgt_file)

        if fkey:
            mapped_files[fkey] = fmap

    combo_dict = {}
    for key, cur_dict in sorted(mapped_files.items()):
        logger.debug("Processing timestep '{}'".format(key))
        combo_dict.update(cur_dict)
    return combo_dict


def map_fes(tgt_file):
    fmap = {}
    fkey = None
    with open(tgt_file) as tf:
        for tline in tf:
            try:
                tstep = int(tline.strip().split()[0].strip())
                fmap[tstep] = tline
                if not fkey:
                    fkey = tstep
            except Exception, e:
                logger.debug("Error '{}' for line '{}'".format(e, tline))
    return fkey, fmap


# CLI Processing #

def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Combines one or more FES files into a single file '
                                                 'where each line has a timestep value unique to the '
                                                 'combined file.  Files with higher initial timestep '
                                                 'values take precedence.')
    parser.add_argument("-d", "--base_dir", help="The starting point for a file search "
                                                 "(defaults to current directory)",
                        default=os.getcwd())
    parser.add_argument('-p', "--pattern", help="The file pattern to search for "
                                                "(defaults to '{}')".format(DEF_FILE_PAT),
                        default=DEF_FILE_PAT)
    parser.add_argument('-t', "--target_file", help="The name of the target combined file "
                                                    "(defaults to '{}')".format(DEF_TGT),
                        default=DEF_TGT)
    parser.add_argument('-o', "--overwrite", help='Overwrite existing target file',
                        action='store_true')

    args = parser.parse_args(argv)

    return args, 0




def main(argv=None):
    args, ret = parse_cmdline(argv)
    if ret != 0:
        return ret
    found_files = find_files_by_dir(args.base_dir, args.pattern)
    logger.debug("Found '{}' dirs with files to combine".format(len(found_files)))
    for fdir, files in found_files.iteritems():
        combo_file = os.path.join(fdir, args.target_file)
        if os.path.exists(combo_file) and not args.overwrite:
            logger.warning("Target file '{}' already exists.  Skipping dir '{}'".
                           format(combo_file, fdir))
            continue
        combo = combine([os.path.join(fdir, tgt) for tgt in files])
        #write_combo(combo, combo_file)

    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
