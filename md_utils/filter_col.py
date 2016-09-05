#!/usr/bin/env python
"""
Given a file with columns of data (comma or space separated):
return a file that has lines filtered by specified min and max values
"""

from __future__ import print_function

import argparse
import sys
import numpy as np
from md_utils.md_common import (InvalidDataError, warning,
                                create_out_fname, process_cfg, read_csv_to_list,
                                list_to_csv, round_to_print, IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA)
try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError, ParsingError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError, ParsingError

__author__ = 'hbmayes'


# Constants #

# Config File Sections
MAIN_SEC = 'main'
MAX_SEC = 'max_vals'
MIN_SEC = 'min_vals'
BIN_SEC = 'bin_settings'
SUB_SECTIONS = [MAX_SEC, MIN_SEC, BIN_SEC]
SECTIONS = [MAIN_SEC] + SUB_SECTIONS

# Defaults
DEF_CFG_FILE = 'filter_col.ini'
DEF_ARRAY_FILE = 'column_data.csv'
DEF_DELIMITER = ','
FILTER_HEADERS = 'filter_col_names'

DEF_CFG_VALS = {}
REQ_KEYS = {}

BINS = 'bin_array'
MOD = 'modulo'
QUOT = 'quotient'


def check_vals(config, sec_name):
    """
    Reads the max or min vals section of the given config file,
    returning a dict containing the original string key paired with a float representing the max or min value.
    If there is no specified section, an empty dict is returned.  Invalid values result in DataExceptions.
    :param config: The parsed config file that contains a max and/or min section.
    :param sec_name: the name of the section with string/float pairs to digest
    :return: A dict mapping the original column key to the float limit value.
    """
    limit_vals = {}
    limit_val = np.nan
    col_name = None
    try:
        for col_name, limit_val in config.items(sec_name):
            # I don't test for non-unique column name because, if a col_name appears twice, the parser has already
            # handled it by overwriting the value for that key
            limit_vals[col_name] = float(limit_val)
    except NoSectionError:
        # not a problem
        pass
    except ValueError:
        raise InvalidDataError("For section '{}' key '{}', could not convert value '{}' to a float."
                               .format(sec_name, col_name, limit_val, ))
    return limit_vals


def get_bin_data(config, sec_name):
    """
    Reads the section with information on how rows are to be binned
    returning a dict containing the original string key paired with:
      min_bin value (float)
      max_bin value (float)
      num_bins (integer)
      max_per_bin (None if not specified)
    If there is no specified section, an empty dict is returned.  Invalid values result in DataExceptions.
    Only one column can be specified by binning
    :param config: The parsed config file that contains a BIN_SEC
    :param sec_name: the name of the section with string/float pairs to digest
    :return: A dict mapping the original column key to the .
    """
    col_name = None
    bin_data = None
    convert_val = None
    convert_to = None
    bin_vals = {}
    try:
        for col_name, bin_data in config.items(sec_name):
            bin_list = [entry.strip() for entry in bin_data.split(',')]
            len_bin_list = len(bin_list)
            if len_bin_list not in [3, 4]:
                raise InvalidDataError("Expected a comma-separated list of length 3 or 4 for section '{}' key '{}'. "
                                       "Read: {}".format(sec_name, col_name, bin_data))
            for list_index in range(4):
                # if nothing provided for the optional max number, lengthen the list with None
                # convert all numbers that are provided (index 0 & 1 to float, 2 & 3 (optional) to int
                if list_index == 3:
                    if len_bin_list == 3:
                        bin_list.append(None)
                        break
                    else:
                        convert_to = int
                elif list_index == 2:
                    convert_to = int
                else:
                    convert_to = float
                # using variables for type of conversion what and what converting to use in error message, if needed
                convert_val = bin_list[list_index]
                converted_val = convert_to(convert_val)
                if convert_to == int and converted_val < 1:
                    raise InvalidDataError("In reading configuration section '{}' key '{}', input '{}': "
                                           "positive integers are required for number of bins and the max number of "
                                           "rows per bin (3rd and 4th list entries)."
                                           .format(sec_name, col_name, bin_data))
                bin_list[list_index] = converted_val

            bin_vals[col_name] = bin_list
    except ValueError:
        raise InvalidDataError("In reading configuration section '{}' key '{}', input '{}', "
                               "could not convert '{}' to {}."
                               .format(sec_name, col_name, bin_data, convert_val, convert_to))
    except NoSectionError:
        # it is okay if there is no such section
        pass
    return bin_vals


def read_cfg(floc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param floc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser()
    try:
        good_files = config.read(floc)
    except ParsingError as e:
        raise InvalidDataError(e)
    if not good_files:
        raise IOError('Could not read file {}'.format(floc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS, int_list=False)
    # Check that there is a least one subsection, or this script won't do anything. Check that all sections given
    # are expected or alert user that a given section is ignored (thus catches types, etc.)
    no_work_to_do = True
    for section in config.sections():
        if section in SECTIONS:
            if section in SUB_SECTIONS:
                if len(config.items(section)) > 0:
                    no_work_to_do = False
        else:
            warning("Found section '{}', which will be ignored. Expected section names are: {}"
                    .format(section, ", ".join(SECTIONS)))
    if no_work_to_do:
        warning("No filtering will be applied as no criteria were found for the expected subsections ({})."
                "".format(", ".join(SUB_SECTIONS)))
    for section in [MAX_SEC, MIN_SEC]:
        main_proc[section] = check_vals(config, section)
    main_proc[BIN_SEC] = get_bin_data(config, BIN_SEC)
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in a file containing a header with columns of data. Using '
                                                 'specifications from a configuration file, it filters rows based '
                                                 'on column min and/or max values, and prints a file of the filtered '
                                                 'data.')

    parser.add_argument("-f", "--file", help="The location of the file with the dimensions with one line per vector, "
                                             "space-separated, containing at least two lines. The default file is {}, "
                                             "located in the current directory".format(DEF_ARRAY_FILE),
                        default=DEF_ARRAY_FILE)

    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)

    parser.add_argument("-d", "--delimiter", help="Delimiter separating columns in the FILE to be filtered. "
                                                  "The default is: '{}'".format(DEF_DELIMITER),
                        default=DEF_DELIMITER)

    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning(e)
        parser.print_help()
        return args, IO_ERROR
    except (InvalidDataError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def process_file(data_file,  mcfg, delimiter=','):
    list_vectors, headers = read_csv_to_list(data_file, delimiter=delimiter, header=True)

    col_index_dict = {}
    for section in SUB_SECTIONS:
        col_index_dict[section] = {}
        for key, val in mcfg[section].items():
            if key in headers:
                # Parser already made sure that unique entries
                col_index_dict[section][headers.index(key)] = val
            else:
                raise InvalidDataError("Key '{}' found in configuration file but not in data file: "
                                       "{}".format(key, data_file))

    # set up bins, if needed
    bin_arrays = {}
    bin_labels = {}
    bin_counts = {}
    bin_ctrs = {}
    max_bins = {}
    for bin_col, col_bin_data in col_index_dict[BIN_SEC].items():
        bin_min = col_bin_data[0]
        bin_max = col_bin_data[1]
        num_bins = col_bin_data[2]
        max_bins[bin_col] = col_bin_data[3]
        # already checked that 1 or more bins, so will not divide by zero
        bin_width = (bin_max - bin_min) / num_bins
        # set up for np.searchsorted, not np.histogram
        col_bins = np.arange(bin_min + bin_width, bin_max, bin_width)
        # set up for recording assigned bin center
        bin_ctrs[bin_col] = [round_to_print(ctr) for ctr in np.arange(bin_min + bin_width/2, bin_max, bin_width)]
        bin_counts[bin_col] = [0] * len(bin_ctrs[bin_col])
        bin_arrays[bin_col] = col_bins
        bin_labels[bin_col] = '{0}_bin'.format(headers[bin_col])
        headers = [bin_labels[bin_col]] + headers
        # allow filtering based on min and max
        col_index_dict[MIN_SEC][bin_col] = bin_min
        col_index_dict[MAX_SEC][bin_col] = bin_max

    initial_row_num = len(list_vectors)
    filtered_vectors = []
    for row in list_vectors:
        keep_row = True
        for col, max_val in col_index_dict[MAX_SEC].items():
            if row[col] > max_val:
                keep_row = False
        for col, min_val in col_index_dict[MIN_SEC].items():
            if row[col] < min_val:
                keep_row = False
        if keep_row:
            for col_id, col_bins in bin_arrays.items():
                bin_index = np.searchsorted(col_bins, row[col_id])
                row = [bin_ctrs[col_id][bin_index]] + row
                bin_counts[col_id][bin_index] += 1
            filtered_vectors.append(row)
    print("Keeping {} of {} rows based on filtering criteria".format(len(filtered_vectors), initial_row_num))

    # Print output and determine if the output needs to be adjusted because of a max number of entries per bin
    ctr_format = "{:^11} {:^8}"
    ctr_format_max = "{:^11} {:^8} {:^7}"
    excess_bins = {}
    for col_bin in bin_arrays:
        print("Histogram data for column '{}': ".format(bin_labels[col_bin]))
        if max_bins[col_bin] is None:
            print(ctr_format.format('bin_ctr', 'count'))
            for bin_index, bin_ctr in enumerate(bin_ctrs[col_bin]):
                print(ctr_format.format(bin_ctr, bin_counts[col_bin][bin_index]))
        else:
            bin_max = max_bins[col_bin]
            excess_bins[col_bin] = {}
            print(ctr_format_max.format('bin_ctr', 'found', 'keep'))
            for bin_index, bin_ctr in enumerate(bin_ctrs[col_bin]):
                num_found = bin_counts[col_bin][bin_index]
                if num_found > bin_max:
                    num_keep = bin_max
                    # use bin_ctr as key because that is what is saved on the row
                    excess_bins[col_bin][bin_ctrs[col_bin][bin_index]] = {QUOT: num_found / bin_max,
                                                                          MOD: num_found % bin_max}
                else:
                    num_keep = num_found
                print(ctr_format_max.format(bin_ctr, num_found, num_keep))

    if len(excess_bins) == 1:
        count_bin = {}
        delete_rows = []
        mod_r = {}
        quot_r = {}
        for col_bin in excess_bins:
            for bin_remove, bin_dict in excess_bins[col_bin].items():
                mod_r[bin_remove] = bin_dict[MOD]
                quot_r[bin_remove] = bin_dict[QUOT]
                count_bin[bin_remove] = 0
            r_count = 0
            for row_id, row in enumerate(filtered_vectors):
                bin_name = row[0]
                # print(bin_name)
                if bin_name in excess_bins[col_bin]:
                    count_bin[bin_name] += 1
                    if count_bin[bin_name] % quot_r[bin_name] != 0 or count_bin[bin_name] <= mod_r[bin_name]:
                        delete_rows.append(row_id)
                        # print(row_id)
                r_count += 1
            filtered_vectors = [row for row_id, row in enumerate(filtered_vectors) if row_id not in delete_rows]
    if len(excess_bins) > 1:
        warning("No filtering based on a max number of entries will be done; this feature is currently implemented "
                "only for binning with one column's values.")

    f_name = create_out_fname(data_file, prefix='filtered_', ext='.csv')
    list_to_csv([headers] + filtered_vectors, f_name, delimiter=',')


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config
    try:
        process_file(args.file, cfg, delimiter=args.delimiter)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except (ValueError, InvalidDataError) as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
