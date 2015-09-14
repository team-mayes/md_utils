# !/usr/bin/env python
# coding=utf-8

"""
Splits WHAM files and directories into 2-`n` partitions based on the number of
steps specified.
"""

from __future__ import print_function, division
import logging
import math

from md_utils.common import (find_files_by_dir, chunk, file_to_str,
                             allow_write, str_to_file, swerr)
from md_utils.wham import (read_meta, read_meta_rmsd, DIR_KEY, write_rmsd,
                           LINES_KEY, DEF_BASE_SUBMIT_TPL,
                           DEF_TPL_DIR, fill_submit_wham, STEP_SUBMIT_FNAME, DEF_PART_LINE_SUBMIT_TPL,
                           TemplateNotReadableError)

__author__ = 'cmayes'

import argparse
import os
import sys

# Exceptions #

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wham_split')

# Defaults #

DEF_FILE_PAT = 'meta.00'
DEF_STEPS_NUM = 12

# Constants #
TPL_IO_ERR_MSG = "Couldn't read template at '{}'.  Have you run md_init in this directory?"
STEP_DBG_MSG = "Step %d: Dividing %d lines from file %s into %d chunks of %d lines each."
SPLIT_DIR_FMT = "{:02d}_{:02d}"
STEP_META_FNAME = "meta." + SPLIT_DIR_FMT


# I/O #

def write_meta(tgt_dir, meta, step, overwrite=False):
    """
    Writes out the meta file using the original meta data structure as a beginning.

    :param tgt_dir: The target directory for the meta file.
    :param meta: The parsed data from the original meta file.
    :param step: The step number being processed.
    :param overwrite: Whether to overwrite an existing meta file.
    """
    for step_part in range(1, step + 2):
        step_meta = STEP_META_FNAME.format(step, step_part)
        meta_tgt = os.path.join(tgt_dir, step_meta)
        if os.path.exists(meta_tgt) and not overwrite:
            logger.warn("Not overwriting existing meta file '%s'", meta_tgt)
            return
        with open(meta_tgt, 'w') as mfile:
            for mline in meta[LINES_KEY]:
                    rmsd_loc = os.path.join(SPLIT_DIR_FMT.format(step, step_part),
                                            os.path.basename(mline[0]))
                    mfile.write(rmsd_loc)
                    mfile.write('\t')
                    mfile.write('\t'.join(mline[1:]))
                    mfile.write('\n')


def read_tpl(tpl_loc):
    """Attempts to read the given template location and throws A
    TemplateNotReadableError if it can't read the given location.

    :param tpl_loc: The template location to read.
    :raise TemplateNotReadableError: If there is an IOError reading the location.
    """
    try:
        return file_to_str(tpl_loc)
    except IOError as e:
        raise TemplateNotReadableError(TPL_IO_ERR_MSG.format(tpl_loc), e)

# Logic #


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
        wham_fill = fill_submit_wham(sub_tpl_base, sub_tpl_line, step, use_part=True)
        str_to_file(wham_fill, sub_file)


def rmsd_split(meta_file, steps, tpl_dir=DEF_TPL_DIR, overwrite=False, base_dir=None):
    """
    Reads the given meta file, fetches the RMSD files in the inventory, and creates a succession
    of directories that split the original RMSD files into a larger number of chunks for each step
    such that step 1 will create a split of 2 in 01_01 and 01_02, etc.

    :param meta_file: The initial meta file.
    :param steps: The number of averaging steps to perform.
    :param tpl_dir: The directory that contains the submit templates.
    :param overwrite: Whether to overwrite existing files.
    :param base_dir: The base directory to write to (defaults to the meta file's dir)
    """
    meta = read_meta(meta_file)
    rmsd = read_meta_rmsd(meta)
    sub_tpl_base = read_tpl(os.path.join(tpl_dir, DEF_BASE_SUBMIT_TPL))
    sub_tpl_line = read_tpl(os.path.join(tpl_dir, DEF_PART_LINE_SUBMIT_TPL))

    if not base_dir:
        base_dir = meta[DIR_KEY]
    for step in range(1, steps + 1):
        for rmsd_fname, data in rmsd.items():
            data_len = len(data)
            chunk_num = step + 1
            chunk_size = math.floor(data_len / chunk_num)
            logger.debug(STEP_DBG_MSG, step, data_len, rmsd_fname, chunk_num,
                         chunk_size)

            rmsd_chunks = [ch for ch in chunk(data, chunk_size, list)]
            for step_part in range(1, chunk_num + 1):
                rmsd_tgt_dir = os.path.join(base_dir, SPLIT_DIR_FMT.
                                            format(step, step_part))
                if not os.path.exists(rmsd_tgt_dir):
                    os.makedirs(rmsd_tgt_dir)
                tgt_file = os.path.join(rmsd_tgt_dir, rmsd_fname)
                if os.path.exists(tgt_file) and not overwrite:
                    logger.warn("Not overwriting existing RMSD file '%s'", tgt_file)
                    continue
                write_rmsd(rmsd_chunks[step_part - 1], tgt_file)

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

    try:
        for meta_dir, meta_files in find_files_by_dir(args.base_dir, args.pattern).items():
            for meta_file in meta_files:
                rmsd_split(os.path.join(meta_dir, meta_file), args.steps, overwrite=args.overwrite)
    except TemplateNotReadableError as e:
        swerr(e)
        return 3

    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
