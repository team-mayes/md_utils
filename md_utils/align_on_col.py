#!/usr/bin/env python
"""
For combining data from multiple files based on a common timestep. All other data will be ignored or, if in logging
mode, printed to a log file.
"""

from __future__ import print_function

from collections import defaultdict
import argparse
import os
import six
import sys
from md_utils.md_common import (InvalidDataError, warning, read_csv_to_dict, write_csv, create_out_fname,
                                longest_common_substring)

__author__ = 'hmayes'


# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3


# Constants #

# Defaults
DEF_CMP_FILE = 'compare_list.txt'
DEF_DELIM = ','
DEF_ALIGN_COL_NAME = 'timestep'
DEF_OUT_FILE = 'comb.csv'
RUN_NAME = 'run'


def read_cmp_file(c_file):
    """
    Given the name of a file, returns a list of its rows, after filtering out empty rows
    @param c_file: file location
    @return: list of non-empty rows
    """
    with open(c_file) as f:
        row_list = [row.strip() for row in f.readlines()]
        return filter(None, row_list)


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Make combine output from multiple files, with a common column '
                                                 'name, printing only data from common column values. ')
    parser.add_argument("-d", "--delimiter", help="The delimiter separating the file names in each row of the"
                                                  "compare_file_list. The default delimiter is '{}'.".format(DEF_DELIM),
                        default=DEF_DELIM)
    parser.add_argument("-f", "--compare_file_list", help="The location of the file that lists the files to be "
                                                          "combined. Each row should contain a list of files to be "
                                                          "combined by aligning on the col_name. "
                                                          "The default file name is {}, located in the "
                                                          "directory where the program as run.".format(DEF_CMP_FILE),
                        default=DEF_CMP_FILE, type=read_cmp_file)
    parser.add_argument("-l", "--output_location", help="The location (directory) for output files. The default is the "
                                                        "directory from which the program was called.",
                        default=None)
    parser.add_argument("-n", "--col_name", help="The common column name in the files used as the key to combine "
                                                 "files. The default file name is {}.".format(DEF_ALIGN_COL_NAME),
                        default=DEF_ALIGN_COL_NAME)
    parser.add_argument("-o", "--out_name", help="The output file name. The default is {}.".format(DEF_OUT_FILE),
                        default=DEF_OUT_FILE)
    parser.add_argument("-s", "--sep_out", help="A flag to specify a separate output files should be created for "
                                                "the aligned files from each row of the compare_file_list. If this "
                                                "is specified, the out_name will be used as a suffix. The base name "
                                                "will be based on the common part of the names of the files to be "
                                                "combined. If there is no common string, the output files will be "
                                                "numbered based on their row number in the compare_file_list. Separate "
                                                "output files will also be created if the column names from files on "
                                                "different lines to not match.",
                        action='store_true')
    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except (KeyError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def process_files(comp_f_list, col_name, base_out_name, delimiter, sep_out_flag, out_location):
    """
    Want to grab the timestep, first and 2nd mole found, first and 2nd ci^2
    print the timestep, residue ci^2
    @param comp_f_list: a list of lists of file names to process (file read during input processing)
    @param col_name: name of column to use for alignment
    @param base_out_name: name of file to be created, or suffix if multiple files to be created
    @param delimiter: string, delimiter separating file names on lines of the comp_f_list
    @param sep_out_flag: a boolean to note if separate output files should be made based on each row of input
    @param out_location: user-specified location for the output files, if specified
    @return: @raise InvalidDataError:
    """
    all_dicts = defaultdict(dict)

    # if need multiple output files, designate them by adding a prefix
    prefix = ''
    # if there will be multiple output files, make sure do not reuse a prefix, so keep copy of used names
    prefix_used = []
    # if one output file from multiple sets of file to combine, will change write_mode to append later
    write_mode = 'w'

    # we don't have to specify run names in the output if there one row set of files to combine,
    #  or if there will be separate output files
    if len(comp_f_list) < 2 or sep_out_flag:
        add_run_name = False
        headers = []
    else:
        add_run_name = True
        headers = [RUN_NAME]

    for line_num, line in enumerate(comp_f_list):
        dict_keys = None
        if sep_out_flag:
            headers = []
            all_dicts = defaultdict(dict)
        # separate on delimiter, strip any white space, and also get rid of empty entries
        comp_files = filter(None, [c_file.strip() for c_file in line.split(delimiter)])

        # get the common part of the name, if it exists; otherwise, give the name the line index
        for file_index, file_name in enumerate(comp_files):
            base_name = os.path.splitext(os.path.basename(file_name))[0]
            if file_index == 0:
                run_name = base_name
            else:
                run_name = longest_common_substring(run_name, base_name)
        if run_name == '':
            # because will use run_name as a string, need to convert it
            run_name = str(line_num) + "_"

        for c_file in comp_files:
            new_dict = read_csv_to_dict(c_file, col_name)
            if dict_keys is None:
                dict_keys = new_dict.keys()
            else:
                dict_keys = set(dict_keys).intersection(new_dict.keys())
            new_dict_keys = six.next(six.itervalues(new_dict)).keys()
            # Get the keys for the inner dictionary; diff methods for python 2 and 3 so use six
            # expect to only get new headers when making a new file (write_mode == 'w')
            # for the next file, will not gather more headers. When printed, extra cols will be skipped, and
            #    missing columns will have no data shown
            if write_mode == 'w':
                for key in new_dict_keys:
                    if key in headers:
                        # okay if already have header if the header is the column.
                        # If we are going to append, we also expect to already have the header name
                        if key != col_name:
                            warning("Non-unique column name {} found in {}. "
                                    "Values will be overwritten.".format(key, c_file))
                    else:
                        headers.append(key)
            for new_key in new_dict.items():
                all_dicts[new_key[0]].update(new_key[1])

        final_dict = []
        for key in sorted(dict_keys):
            final_dict.append(all_dicts[key])
            # final_dict.append(all_dicts[key].update({RUN_NAME: run_name}))

        if add_run_name:
            for each_dict in final_dict:
                each_dict.update({RUN_NAME: run_name})

        # Possible to have no overlap in align column
        if len(final_dict) > 0:
            # make sure col_name appears first by taking it out before sorting
            if sep_out_flag:
                prefix = run_name
                if prefix == '' or prefix in prefix_used:
                    prefix = str(line_num) + "_"
            # have a consistent output by sorting the headers, but keep the aligning column first
            # only needs to be done for printing the first time
            if write_mode == 'w':
                headers.remove(col_name)
                headers = [col_name] + sorted(headers)
                if add_run_name:
                    headers.remove(RUN_NAME)
                    headers = [RUN_NAME] + headers
            f_name = create_out_fname(base_out_name, prefix=prefix, base_dir=out_location)
            prefix_used.append(prefix)
            write_csv(final_dict, f_name, headers, mode=write_mode)
            if not sep_out_flag and write_mode == 'w':
                write_mode = 'a'
        else:
            raise InvalidDataError("No common values found for column {} among files: {}"
                                   "".format(col_name, ", ".join(comp_files)))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    try:
        process_files(args.compare_file_list, args.col_name, args.out_name,
                      args.delimiter, args.sep_out, args.output_location)
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
