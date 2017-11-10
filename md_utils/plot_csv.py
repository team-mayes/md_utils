#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Compresses a CSV to combine rows that have duplicate values for the specified column.  All of the other
column values will be averaged as floats.
"""
import argparse
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from md_utils.md_common import warning, GOOD_RET, create_out_fname, INPUT_ERROR


# Logic #


# CLI Processing #


def parse_cmdline(argv=None):
    """
    Returns the parsed argument list and return code.
    :param argv: A list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Plots values from a CSV')

    # parser.add_argument('-c', '--column', default=DEF_COL_NAME,
    #                     help="Specify dupe column. (defaults to {})".format(DEF_COL_NAME),
    #                     metavar="DUPE_COL")
    parser.add_argument("csv_file", help="The CSV file to process")

    args = []
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        warning(e)
        return args, INPUT_ERROR

    return args, GOOD_RET


def plot_corr(f_name):
    """
    Given a csv, plot it as a heat map
    @param f_name: file name to save the correlation
    @return:
    """
    corr_data = pd.read_csv(f_name, index_col=0)
    i_name = create_out_fname(f_name, ext='.png')

    # Generate a mask for the upper triangle
    plot_mask = np.zeros_like(corr_data, dtype=np.bool)
    plot_mask[np.triu_indices_from(plot_mask)] = True

    # Set up the matplotlib figure
    sns.set(style="white")
    # f, ax = plt.subplots(figsize=(11, 9))
    plt.subplots(figsize=(11, 9))
    # Draw the heatmap with the plot_mask and correct aspect ratio

    sns.heatmap(corr_data, mask=plot_mask,
                vmin=0.0,
                vmax=100.0,
                square=True,
                # xticklabels=2,
                # yticklabels=2,
                linewidths=.5,
                cbar_kws={"shrink": .5, },
                )

    plt.xticks(rotation='vertical')
    plt.yticks(rotation='horizontal')

    # print output

    plt.savefig(i_name)
    print("Wrote file: {}".format(i_name))


def main(argv=None):
    """
    Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    plot_corr(args.csv_file)

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
