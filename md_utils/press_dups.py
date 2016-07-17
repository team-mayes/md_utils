#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Compresses a CSV to combine rows that have duplicate values for the specified column.  All of the other
column values will be averaged as floats.
"""
import argparse
import logging
import sys
from collections import defaultdict
from functools import reduce
import numpy as np
from md_utils.md_common import warning, GOOD_RET, read_csv, create_out_fname, write_csv, read_csv_header, INPUT_ERROR

logger = logging.getLogger(__name__)

# Defaults #

DEF_COL_NAME = 'RMSD'

# Constants #

PREFIX = "pressed_"


# Logic #

def avg_rows(rows):
    """Takes the average of each value for a given key in the given list of dicts,
    returning a single dict containing the average for each key.

    :param rows: The rows to average.
    :return: A dict with the average for each key.
    """
    if len(rows) == 1:
        return rows[0]

    agg_vals = {k: [rows[j][k] for j in range(len(rows))] for k in rows[0].keys()}
    return {k: (reduce(np.add, v) / len(v)) for k, v in agg_vals.items()}


def compress_dups(data, column):
    """Compresses rows that have the same value for the given column key,
    averaging the values for the other entries.

    :param data: The data to compress.
    :param column: The column to search for duplicates.
    :return: The data compressed for duplicates and sorted by the target
        column's values.
    """
    idx = defaultdict(list)
    for row in data:
        idx[row[column]].append(row)

    dedup = []

    for idx_row in sorted(idx.items()):
        dedup.append(avg_rows(idx_row[1]))
    return dedup


# CLI Processing #


def parse_cmdline(argv=None):
    """
    Returns the parsed argument list and return code.
    :param argv: A list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Compresses duplicate rows in a '
                                                 'given file based on values from '
                                                 'a given column')

    parser.add_argument('-c', '--column', default=DEF_COL_NAME,
                        help="Specify dupe column. (defaults to {})".format(DEF_COL_NAME),
                        metavar="DUPE_COL")
    parser.add_argument("file", help="The CSV file to process")

    args = []
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        warning(e)
        return args, INPUT_ERROR

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

    deduped = compress_dups(read_csv(args.file, all_conv=float), args.column)
    write_csv(deduped, create_out_fname(args.file, prefix=PREFIX),
              read_csv_header(args.file))

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
