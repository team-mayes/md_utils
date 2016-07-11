# !/usr/bin/env python
# coding=utf-8

"""
Block averages input data for WHAM, used to test data convergence.
(first half, first quarter, first eighth...)
"""

from __future__ import print_function, division
import logging

import six

from md_utils.md_common import find_files_by_dir, chunk, allow_write, str_to_file, GOOD_RET, warning, INVALID_DATA
from md_utils.wham import (read_meta, read_meta_rmsd, write_rmsd,
                           DIR_KEY, LINES_KEY, STEP_SUBMIT_FNAME,
                           fill_submit_wham, DEF_BASE_SUBMIT_TPL,
                           DEF_LINE_SUBMIT_TPL, TemplateNotReadableError)
from md_utils.wham_split import read_tpl

__author__ = 'cmayes'


import argparse
import os
import sys

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('wham_block')
logger.setLevel(logging.INFO)

# Constants #

STEP_META_FNAME = "meta.{:02d}"

# Defaults #

DEF_TPL_DIR = os.path.join(os.getcwd(), 'tpl')
DEF_FILE_PAT = 'meta.00'
DEF_STEPS_NUM = 12

# I/O #


def write_submit(tgt_dir, sub_tpl_base, sub_tpl_line, step, overwrite=False):
    """
    Uses the given templates and step number to write a submit script to the given target file location.

    :param sub_tpl_base: The base template.
    :param sub_tpl_line: The line template.
    :param step: The step number.
    :param tgt_dir: The target directory.
    :param overwrite: Whether to allow overwrites.
    """
    sub_file = os.path.join(tgt_dir, STEP_SUBMIT_FNAME.format(step))
    if allow_write(sub_file, overwrite):
        wham_fill = fill_submit_wham(sub_tpl_base, sub_tpl_line, step, use_part=False)
        str_to_file(wham_fill, sub_file)


# TODO: Write tests for write_avg_rmsd
def write_avg_rmsd(tgt_dir, rmsd, overwrite=False):
    """
    Writes out all of the described RMSD files into the given target directory.

    :param tgt_dir: The data where the files will go.
    :param rmsd: A dict of an array of floats keyed by file name.
    :param overwrite: Whether to overwrite existing files.
    """
    for rmsd_fname, data in rmsd.items():
        f_name = os.path.join(tgt_dir, rmsd_fname)
        if allow_write(f_name, overwrite=overwrite):
            write_rmsd(data, f_name)


def write_meta(tgt_dir, meta, step, overwrite=False):
    """
    Writes out the meta file using the original meta data structure as a beginning.

    :param tgt_dir: The target directory for the meta file.
    :param meta: The parsed data from the original meta file.
    :param step: The step number being processed.
    :param overwrite: Whether to overwrite an existing meta file.
    """
    step_meta = STEP_META_FNAME.format(step)
    f_name = os.path.join(tgt_dir, step_meta)
    if allow_write(f_name, overwrite=overwrite):
        with open(f_name, 'w') as m_file:
            for m_line in meta[LINES_KEY]:
                rmsd_loc = os.path.join("{:02d}".format(step),
                                        os.path.basename(m_line[0]))
                m_file.write(rmsd_loc)
                m_file.write('\t')
                m_file.write('\t'.join(m_line[1:]))
                m_file.write('\n')
        print("Wrote file: {}".format(f_name))


# Logic #


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


def block_average(meta_file, steps, tpl_dir=DEF_TPL_DIR, overwrite=False, base_dir=None):
    """
    Reads the given meta file, fetches the RMSD files in the inventory, computes
    the average over the given number of cycles, and writes each computed RMSD
    and meta file for each cycle.

    :param meta_file: The initial meta file.
    :param steps: The number of averaging steps to perform.
    :param overwrite: Whether to overwrite existing files.
    :param base_dir: The base directory to write to (defaults to the meta file's dir)
    """
    meta = read_meta(meta_file)
    rmsd = read_meta_rmsd(meta)
    sub_tpl_base = read_tpl(os.path.join(tpl_dir, DEF_BASE_SUBMIT_TPL))
    sub_tpl_line = read_tpl(os.path.join(tpl_dir, DEF_LINE_SUBMIT_TPL))

    if not base_dir:
        base_dir = meta[DIR_KEY]
    for step in range(1, steps + 1):
        rmsd_base_dir = os.path.join(base_dir, "{:02d}".format(step))
        rmsd = rmsd_avg(rmsd, pair_avg)
        first_vals = six.next(six.itervalues(rmsd))
        if not first_vals:
            logger.info("No more values at step %d; stopping", step)
            break
        os.makedirs(rmsd_base_dir)
        write_avg_rmsd(rmsd_base_dir, rmsd, overwrite)
        write_meta(base_dir, meta, step, overwrite)
        write_submit(base_dir, sub_tpl_base, sub_tpl_line, step, overwrite)


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

    return args, GOOD_RET


def main(argv=None):
    """
    Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    try:
        for meta_dir, meta_files in find_files_by_dir(args.base_dir, args.pattern).items():
            for meta_file in meta_files:
                block_average(os.path.join(meta_dir, meta_file), args.steps, overwrite=args.overwrite)
    except TemplateNotReadableError as e:
        warning(e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
