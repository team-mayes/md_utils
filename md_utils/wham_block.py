# !/usr/bin/env python
# coding=utf-8

"""
Block averages input data for WHAM.
"""

from __future__ import print_function, division
import logging

from md_utils.common import find_files_by_dir, chunk

__author__ = 'cmayes'


import argparse
import os
import sys

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wham_block')

# Constants #
LINES_KEY = "lines"
DIR_KEY = "dir"
LOC_KEY = "loc"

# Defaults #

DEF_FILE_PAT = 'meta.00'
DEF_STEPS_NUM = 12

# Logic #


def read_meta(meta_file):
    """
    Reads the given meta file, returning the parsed value as a dict containing:

    * loc: A string with the original (possibly relative) location
    * dir: A string with absolute path for the directory containing the meta file.
    * lines: a list of four-element lists that represent each line in the meta file.

    :param meta_file: The meta file to parse.
    :return: The parsed contents of the meta file.
    """
    meta = {LOC_KEY: meta_file, DIR_KEY: os.path.dirname(os.path.abspath(meta_file))}
    lines = []
    with open(meta_file) as mfile:
        for mline in mfile:
            lines.append(mline.strip().split())
    meta[LINES_KEY] = lines
    return meta


def read_rmsd(fname):
    """
    Reads the RMSD file at the given file name.

    :param fname: The file's location.
    :return: The values in the RMSD file.
    """
    rmsd_values = []
    with open(fname) as rfile:
        row_val = None
        for rline in rfile:
            try:
                row_val = rline.split()[1]
                rmsd_values.append(float(row_val))
            except IndexError:
                logger.warn("RMSD Line '%s' did not have two fields", rline)
            except TypeError:
                logger.warn("RMSD Value '%s' is not a float", row_val)
    return rmsd_values


def read_meta_rmsd(meta):
    """
    Finds and parses the RMSD files described in the given parsed meta file's contents.

    :param meta: The result of calling read_meta with a meta file location.
    :return: A dict of lists containing floats for each line in each found RMSD file
        keyed by the RMSD file name (no directory info is included in the key)
    """
    rmsd_data = {}
    for line in meta[LINES_KEY]:
        rmsd_fname = os.path.basename(line[0])
        floc = os.path.join(meta[DIR_KEY], line[0])
        rmsd_data[rmsd_fname] = read_rmsd(floc)
    return rmsd_data


def pair_avg(vals):
    """
    Returns a list of the average between pairs of numbers in the input list.  If there is an odd
    final input value, it is dropped.

    :param vals:  A list of floats to pair and average.
    :return: The average of adjacent pairs in the given input list.
    """
    results = []
    for pair in chunk(vals, 2, list):
        if len(pair) == 2:
            results.append(sum(pair) / 2)
        else:
            logger.debug("'%s' is not a pair", pair)

    return results


def rmsd_avg(rmsd, avg_func):
    """
    Computes the average for the given RMSD value list using the given averaging function.

    :param rmsd: The data to process keyed by file name.
    :param avg_func: The function to apply to the data.
    :return: The averaged data keyed by file name.
    """
    avg = {}
    for fname, data in rmsd.items():
        avg[fname] = avg_func(data)
    return avg


def write_rmsd(tgt_dir, rmsd, overwrite=False):
    """
    Writes out all of the described RMSD files into the given target directory.

    :param tgt_dir: The data where the files will go.
    :param rmsd: A dict of an array of floats keyed by file name.
    :param overwrite: Whether to overwrite existing files.
    """
    for rmsd_fname, data in rmsd.items():
        tgt_file = os.path.join(tgt_dir, rmsd_fname)
        if os.path.exists(tgt_file) and not overwrite:
            logger.warn("Not overwriting existing RMSD file '%s'", tgt_file)
            continue
        with open(tgt_file, 'w') as wfile:
            for i, rmsd_val in enumerate(data, 1):
                wfile.write("\t".join((str(i), str(rmsd_val))))
                wfile.write("\n")


def write_meta(tgt_dir, meta, step, overwrite=False):
    """
    Writes out the meta file using the original meta data structure as a beginning.

    :param tgt_dir: The target directory for the meta file.
    :param meta: The parsed data from the original meta file.
    :param step: The step number being processed.
    :param overwrite: Whether to overwrite an existing meta file.
    """
    step_meta = "meta.{:02d}".format(step)
    meta_tgt = os.path.join(tgt_dir, step_meta)
    if os.path.exists(meta_tgt) and not overwrite:
        logger.warn("Not overwriting existing meta file '%s'", meta_tgt)
        return
    with open(meta_tgt, 'w') as mfile:
        for mline in meta[LINES_KEY]:
            rmsd_loc = os.path.join("{:02d}".format(step),
                                    os.path.basename(mline[0]))
            mfile.write(rmsd_loc)
            mfile.write('\t')
            mfile.write('\t'.join(mline[1:]))
            mfile.write('\n')


def block_average(meta_file, steps, overwrite):
    """
    Reads the given meta file, fetches the RMSD files in the inventory, computes
    the average over the given number of cycles, and writes each computed RMSD
    and meta file for each cycle.

    :param meta_file: The initial meta file.
    :param steps: The number of averaging steps to perform.
    :param overwrite: Whether to overwrite existing files.
    """
    meta = read_meta(meta_file)
    rmsd = read_meta_rmsd(meta)

    for step in range(1, steps + 1):
        base_dir = meta[DIR_KEY]
        rmsd_base_dir = os.path.join(base_dir, "{:02d}".format(step))
        rmsd = rmsd_avg(rmsd, pair_avg)
        logger.debug(len(rmsd.items()[1]))
        os.makedirs(rmsd_base_dir)
        write_rmsd(rmsd_base_dir, rmsd, overwrite)
        write_meta(meta[DIR_KEY], meta, step, overwrite)


# CLI Processing #


def parse_cmdline(argv=None):
    """
    Returns the parsed argument list and return code.
    :param argv: A list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Block averages input data for WHAM')
    parser.add_argument("-d", "--base_dir", help="The starting point for a meta file search "
                                                 "(defaults to current directory)",
                        default=os.getcwd())
    parser.add_argument('-p', "--pattern", help="The meta file pattern to search for "
                                                "(defaults to '{}')".format(DEF_FILE_PAT),
                        default=DEF_FILE_PAT)
    parser.add_argument('-s', "--steps", help="The number of averaging steps to take "
                                              "(defaults to '{}')".format(DEF_STEPS_NUM),
                        type=int, default=DEF_STEPS_NUM)
    parser.add_argument('-o', "--overwrite", help='Overwrite existing locations',
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

    for meta_dir, meta_files in find_files_by_dir(args.base_dir, args.pattern).items():
        for meta_file in meta_files:
            block_average(os.path.join(meta_dir, meta_file), args.steps, args.overwrite)

    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
