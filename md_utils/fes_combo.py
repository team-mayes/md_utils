# !/usr/bin/env python
# coding=utf-8

"""
Combines one or more FES files into a single file where each line has a
timestep value unique to the combined file.  Files with higher initial
timestep values take precedence.
"""

from __future__ import print_function
import logging

from md_utils.md_common import find_files_by_dir, GOOD_RET, INPUT_ERROR, warning

__author__ = 'cmayes'


import argparse
import os
import sys

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('fes_combo')
logger.setLevel(logging.INFO)
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
        f_key, f_map = map_fes(tgt_file)

        if f_key is not None:
            mapped_files[f_key] = f_map

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
    f_map = {}
    first_key = None
    with open(tgt_file) as tf:
        for t_line in tf:
            try:
                tstep = int(t_line.strip().split()[0].strip())
                f_map[tstep] = t_line
                if first_key is None:
                    first_key = tstep
            except Exception as e:
                logger.debug("Error '%s' for line '%s'", e, t_line)
    return first_key, f_map


def extract_header(tgt_file):
    """
    Collects lines that don't have a timestep and returns them.

    :param tgt_file: The file to process.
    :return: The headers for the given file.
    """
    with open(tgt_file) as tf:
        h_lines = []
        for t_line in tf:
            s_line = t_line.strip().split()
            if len(s_line) < 2:
                h_lines.append(t_line)
                continue
            try:
                # If we have a timestep, this is not a header line
                int(s_line[0])
                break
            except ValueError:
                h_lines.append(t_line)
        return h_lines


def write_combo(headers, combo, combo_file):
    """
    Writes the headers, then the combo, to the combo file location.
    :param headers: The headers to write.
    :param combo: A dict of combined file contents indexed by timestep.
    :param combo_file: The file location for the output.
    """
    with open(combo_file, 'w') as f:
        for h_line in headers:
            if not h_line:
                f.write(os.linesep)
            else:
                f.write(h_line)
        for key, line in sorted(combo.items()):
            f.write(line)
    print("Wrote file: {}".format(combo_file))

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

    args = None
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def main(argv=None):
    """
    Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret
    found_files = find_files_by_dir(args.base_dir, args.pattern)
    print("Found {} dirs with files to combine".format(len(found_files)))
    for f_dir, files in found_files.iteritems():
        if not files:
            logger.warn("No files with pattern '{}' found for dir '{}'".format(args.pattern, f_dir))
            continue
        combo_file = os.path.join(f_dir, args.target_file)
        if os.path.exists(combo_file) and not args.overwrite:
            warning("Target file already exists: '{}' \n"
                    "Skipping dir '{}'".format(combo_file, f_dir))
            continue
        combo = combine([os.path.join(f_dir, tgt) for tgt in files])
        write_combo(extract_header(os.path.join(f_dir, files[0])), combo, combo_file)

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
