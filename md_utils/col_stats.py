#!/usr/bin/env python
"""
Given a file with columns of data (space separated, no other data):
by default: returns the min, max, avg, and std dev per column
alternately: returns maximum x, y, and z coordinates, plus the values after a buffer length is added
"""

from __future__ import print_function

import copy
import csv
from operator import itemgetter
import matplotlib
import seaborn as sns
import pandas as pd
import numpy as np
import sys
import os
import warnings
import argparse

matplotlib.use('Agg', warn=False)
import matplotlib.pyplot as plt
from md_utils.md_common import (InvalidDataError, warning,
                                np_float_array_from_file, create_out_fname, list_to_csv, read_csv, GOOD_RET,
                                INPUT_ERROR, IO_ERROR, INVALID_DATA)

__author__ = 'hmayes'

# Constants #

# Defaults
DEF_ARRAY_FILE = 'qm_box_sizes.txt'
DEF_DELIMITER = ' '
TOL = 0.0001


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in space-separated columns and returns the min, max, avg, and '
                                                 'std dev for each column.')
    parser.add_argument("-f", "--file", help="The location of the file with the dimensions with one line per vector, "
                                             "space-separated, containing at least two lines. The default file is {}, "
                                             "located in the current directory".format(DEF_ARRAY_FILE),
                        default=DEF_ARRAY_FILE)

    parser.add_argument("-b", "--buffer", help="If specified, the program will output only the max dimension"
                                               "in each column plus an additional buffer amount (float).",
                        default=None)

    parser.add_argument("-d", "--delimiter", help="Delimiter. Default is '{}'".format(DEF_DELIMITER),
                        default=DEF_DELIMITER)

    parser.add_argument("-m", "--min_max_file", help="CSV file with column names (first line), "
                                                     "initial values (second line), min values "
                                                     "(third line), and max values (fourth line), used to further "
                                                     "analyze the data file.",
                        default=None)

    parser.add_argument("-n", "--names", help="File contains column names (header) (default is false). "
                                              "Note: lines beginning with '#' are ignored.",
                        action='store_true')

    parser.add_argument("-o", "--out_dir", help="Output folder. Default is the directory of the file to be processed.",
                        default=None)

    parser.add_argument("-s", "--histogram", help="Create histograms of the non-numerical data (default is false).",
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


def process_file(data_file, out_dir, len_buffer, delimiter, min_max_dict, header=False, make_hist=False):
    try:
        dim_vectors, header_row, hist_data = np_float_array_from_file(data_file, delimiter=delimiter,
                                                                      header=header, gather_hist=make_hist)

    except InvalidDataError as e:
        raise InvalidDataError("{}\n"
                               "Run program with '-h' to see options, such as specifying header row (-n) "
                               "and/or delimiter (-d)".format(e))

    if header:
        to_print = [[''] + header_row]
    else:
        to_print = []

    max_vector = dim_vectors.max(axis=0)
    min_vector = dim_vectors.min(axis=0)
    avg_vector = dim_vectors.mean(axis=0)
    med_vector = np.percentile(dim_vectors, 50, axis=0)

    # noinspection PyTypeChecker
    to_print += [['Min values:'] + min_vector.tolist(),
                 ['Max values:'] + max_vector.tolist(),
                 ['Avg values:'] + avg_vector.tolist(),
                 ['Std dev:'] + dim_vectors.std(axis=0, ddof=1).tolist(),
                 ['5% percentile:'] + np.percentile(dim_vectors, 4.55, axis=0).tolist(),
                 ['32% percentile:'] + np.percentile(dim_vectors, 31.73, axis=0).tolist(),
                 ['50% percentile:'] + med_vector.tolist(),
                 ['68% percentile:'] + np.percentile(dim_vectors, 68.27, axis=0).tolist(),
                 ['95% percentile:'] + np.percentile(dim_vectors, 95.45, axis=0).tolist(),
                 ]
    if len_buffer is not None:
        to_print.append(['Max plus {} buffer:'.format(len_buffer)] + (max_vector + len_buffer).tolist())

    if min_max_dict is not None:
        nan_list = [np.nan] * len(header_row)
        avg_ini_diff = ['Avg % Diff:'] + nan_list
        med_ini_diff = ['Med % Diff:'] + nan_list
        med_is_min = ['Median is Min:'] + nan_list
        med_is_max = ['Median is Max:'] + nan_list
        for col_num, header in enumerate(to_print[0]):
            if header in min_max_dict[0]:
                ini_val = min_max_dict[0][header]
                low_val = min_max_dict[1][header]
                upp_val = min_max_dict[2][header]
                avg_val = avg_vector[col_num - 1]
                med_val = med_vector[col_num - 1]
                min_val = min_vector[col_num - 1]
                max_val = max_vector[col_num - 1]
                min_tol = max(TOL * max(abs(min_val), abs(low_val)), TOL)
                med_tol = max(TOL * abs(med_val), TOL)
                max_tol = max(TOL * max(abs(max_val), abs(upp_val)), TOL)
                if (low_val - min_val) > min_tol:
                    warning("Minimum value found for header '{}' ({}) is less than lower bound ({})"
                            "".format(header, min_val, low_val))
                if (max_val - upp_val) > max_tol:
                    warning("Maximum value found for header '{}' ({}) is greater than upper bound ({})"
                            "".format(header, max_val, upp_val))
                avg_ini_diff[col_num] = (avg_val - ini_val) / ini_val * 100
                med_ini_diff[col_num] = (med_val - ini_val) / ini_val * 100
                if abs(med_val - low_val) > med_tol:
                    med_is_min[col_num] = 0
                else:
                    med_is_min[col_num] = 1
                if abs(med_val - upp_val) > med_tol:
                    med_is_max[col_num] = 0
                else:
                    med_is_max[col_num] = 1
                    # else:
                    #     for min_max_list in [avg_ini_diff, med_ini_diff, med_is_min, med_is_max]:
                    #         min_max_list.append(np.nan)
        for min_max_list in [avg_ini_diff, med_ini_diff, med_is_min, med_is_max]:
            to_print.append(min_max_list)

    # Printing to standard out: do not print quotes around strings because using csv writer
    # print("Number of dimensions ({}) based on first line of file: {}".format(len(dim_vectors[0]), data_file))
    if len(dim_vectors[0]) < 12:
        for index, row in enumerate(to_print):
            # formatting for header
            if index == 0 and header:
                print("{:>20s} {}".format(row[0],
                                          ' '.join(['{:>16s}'.format(x.strip()) for x in row[1:]])))
            # formatting for vals
            else:
                print("{:>20s} {}".format(row[0], ' '.join(['{:16.6f}'.format(x) for x in row[1:]])))

    f_name = create_out_fname(data_file, prefix='stats_', ext='.csv', base_dir=out_dir)
    list_to_csv(to_print, f_name)
    # list_to_file(to_print, f_name, delimiter=',')

    if make_hist:
        create_hists(data_file, header_row, hist_data, out_dir)


def create_hist_plot(hist_dict, header, out_dir, data_file):
    """
    See https://stanford.edu/~mwaskom/software/seaborn/examples/horizontal_barplot.html
    @param hist_dict: dict of label, count
    @param header: name of dictionary
    @param out_dir: str, name of directory where files are to be saved
    @param data_file: name of data file
    @return: a list of lists (label, count)
    """
    # remove spaces in name
    header = "".join(header.split())

    # convert dict to list for creating bar chat
    bar_data = [[key, val] for key, val in hist_dict.items()]
    bar_data.sort(key=itemgetter(1), reverse=True)

    # bar chart background style
    sns.set(style="whitegrid", font='Arial')
    # color options include pastel
    sns.set_color_codes("deep")
    # Initialize the matplotlib figure
    f, ax = plt.subplots(figsize=(6, 6))
    # Create pandas dataframe
    new_df = pd.DataFrame(bar_data, columns=["key", "count"])
    # Plot
    sns.barplot(x="count", y="key", data=new_df,
                label="Total", color="b")
    # other options: xlim=(0, 24)
    ax.set(xlabel="Count", ylabel="")
    ax.set_title(header)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.tight_layout()

    f_name = create_out_fname(data_file, suffix=header, base_dir=out_dir, ext=".png")
    plt.savefig(f_name, dpi=300)
    print("Wrote file: {}".format(f_name))

    # quote strings for printing so csv properly read, and add header
    count_to_print = [[header + "_key", header + "_count"]]
    for row in bar_data:
        count_to_print.append([row[0], row[1]])

    return count_to_print


def create_hists(data_file, header_row, hist_data, out_dir):
    counts_to_print = []
    if len(hist_data) > 0:
        for col in hist_data:
            count_to_print = create_hist_plot(hist_data[col], header_row[col], out_dir, data_file)

            if len(counts_to_print) == 0:
                counts_to_print = count_to_print
            else:
                len1 = len(counts_to_print)
                len2 = len(count_to_print)
                width1 = len(counts_to_print[0])
                width2 = len(count_to_print[0])
                combined_list = []
                for row in range(min(len1, len2)):
                    combined_list.append(counts_to_print[row] + count_to_print[row])
                for row in range(len2, len1):
                    combined_list.append(counts_to_print[row] + [""] * width2)
                for row in range(len1, len2):
                    # noinspection PyTypeChecker
                    combined_list.append([""] * width1 + count_to_print[row])
                counts_to_print = copy.deepcopy(combined_list)
    f_name = create_out_fname(data_file, prefix='counts_', ext='.csv', base_dir=out_dir)
    list_to_csv(counts_to_print, f_name, delimiter=',')


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    len_buffer = None

    try:
        if args.buffer is not None:
            try:
                len_buffer = float(args.buffer)
            except ValueError:
                raise InvalidDataError("Input for buffer ({}) could not be converted to a float.".format(args.buffer))
        if args.out_dir is None:
            args.out_dir = os.path.dirname(args.file)
        if args.min_max_file is None:
            min_max_dict = None
        else:
            min_max_dict = read_csv(args.min_max_file, quote_style=csv.QUOTE_NONNUMERIC)
        process_file(args.file, args.out_dir, len_buffer, args.delimiter, min_max_dict,
                     header=args.names, make_hist=args.histogram)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
