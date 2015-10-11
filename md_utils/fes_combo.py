# !/usr/bin/env python
# coding=utf-8

"""
Combines one or more FES files into a single file where each line has a
timestep value unique to the combined file.  Files with higher initial
timestep values take precedence.
"""

from __future__ import print_function
import logging

from md_utils.common import find_files_by_dir

__author__ = 'cmayes'


import argparse
import os
import sys

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('fes_combo')

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

        if fkey is not None:
            mapped_files[fkey] = fmap

    combo_dict = {}
    for key, cur_dict in sorted(mapped_files.items()):
        logger.debug("Processing timestep '%s'", key)
        combo_dict.update(cur_dict)
    return combo_dict


def map_fes(tgt_file):
    """
    Maps each line of the given FES output file to its timestep value.  Lines that do not have a timestep
    for its first element are discarded.

    :param tgt_file: The file location to process.
    :return: A dict with each FES data line mapped to its int timestep value.
    """
    fmap = {}
    first_key = None
    with open(tgt_file) as tf:
        for tline in tf:
            try:
                tstep = int(tline.strip().split()[0].strip())
                fmap[tstep] = tline
                if first_key is None:
                    first_key = tstep
            except Exception as e:
                logger.debug("Error '%s' for line '%s'", e, tline)
    return first_key, fmap


def extract_header(tgt_file):
    """
    Collects lines that don't have a timestep and returns them.

    :param tgt_file: The file to process.
    :return: The headers for the given file.
    """
    with open(tgt_file) as tf:
        hlines = []
        for tline in tf:
            sline = tline.strip().split()
            if len(sline) < 2:
                hlines.append(tline)
                continue
            try:
                # If we have a timestep, this is not a header line
                int(sline[0])
                break
            except ValueError:
                hlines.append(tline)
        return hlines


def write_combo(headers, combo, combo_file):
    """
    Writes the headers, then the combo, to the combo file location.
    :param headers: The headers to write.
    :param combo: A dict of combined file contents indexed by timestep.
    :param combo_file: The file location for the output.
    """
    with open(combo_file, 'w') as f:
        for hline in headers:
            if not hline:
                f.write(os.linesep)
            else:
                f.write(hline)
        for key, line in sorted(combo.items()):
            f.write(line)

# CLI Processing #


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    :param argv: A list of arguments, or `None` for ``sys.argv[1:]``.
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
    """
    Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != 0:
        return ret
    found_files = find_files_by_dir(args.base_dir, args.pattern)
    logger.debug("Found '%d' dirs with files to combine", len(found_files))
    for fdir, files in found_files.iteritems():
        if not files:
            logger.warn("No files found for dir '%s'", fdir)
            continue
        combo_file = os.path.join(fdir, args.target_file)
        if os.path.exists(combo_file) and not args.overwrite:
            logger.warning("Target file '%s' already exists.  Skipping dir '%s'",
                           combo_file, fdir)
            continue
        combo = combine([os.path.join(fdir, tgt) for tgt in files])
        write_combo(extract_header(os.path.join(fdir, files[0])), combo, combo_file)

    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
