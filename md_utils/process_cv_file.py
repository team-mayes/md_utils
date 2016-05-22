#!/usr/bin/env python
"""
Converts plumed cv output to evb cv output style
(keep only the first 2 columns; multiply the first by 1000 (ps to fs) and make an int
"""

from __future__ import print_function
import ConfigParser
import logging
import os
import sys
import argparse

from md_utils.md_common import list_to_file, InvalidDataError, warning, create_out_fname, process_cfg

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('proc_cv')
logging.basicConfig(filename='proc_cv.log', filemode='w', level=logging.DEBUG)


# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3


# Constants #

# Config File Sections
MAIN_SEC = 'main'

# Config keys
CV_FILE_LIST = 'cv_file_list'
DEF_FILE_LIST = 'cv_list.txt'

# Defaults
# Set notation
DEF_CFG_VALS = {CV_FILE_LIST: 'evb_list.txt', }
REQ_KEYS = {}


def read_cfg(floc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param floc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser.ConfigParser()
    good_files = config.read(floc)
    if not good_files:
        raise IOError('Could not read file {}'.format(floc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    :param argv: is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Converts plumed cv list to align with lammps/evb cv list: '
                                                 'first column as timestep (int) in fs; second column as cv value.')
    parser.add_argument("-f", "--file_list", help="The location of the file with the list of cv files (one per line). "
                                                  "The default name is {} in the folder where the program is "
                                                  "run.".format(DEF_FILE_LIST), default=DEF_FILE_LIST)
    parser.add_argument("-t", "--timestep_col", help="The column with the timestep (base zero): default is {}"
                                                     "".format(0), default=0)
    parser.add_argument("-tc", "--timestep_conv", help="Multiplication factor to convert timestep. default is {}"
                                                       "".format(1000), default=1000)
    parser.add_argument("-cv", "--cv_col", help="The column with the cv value (base zero): default is {}"
                                                "".format(1), default=1)
    parser.add_argument('-s', "--skip_header_row", help='Skips the first row as a header: default is True'
                                                        '', default=True)

    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except KeyError as e:
        warning("Input data missing:", e)
        parser.print_help()
        return args, INPUT_ERROR

    if not os.path.isfile(args.file_list):
        if args.file_list == DEF_FILE_LIST:
            warning("Default file list {} is missing.".format(DEF_FILE_LIST))
        else:
            warning("Specified file list {} is missing.".format(args.file_list))
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def process_cv_file(cv_file, time_col, cv_col, row_index, time_conv):
    data_to_print = []
    with open(cv_file) as f:
        for line in f:
            if row_index == 0:
                row_index = 1
            else:
                data = [x.strip() for x in line.split()]
                try:
                    timestep = int(float(data[time_col]) * time_conv)
                    cv = float(data[cv_col])
                    data_to_print.append([timestep, cv])
                except ValueError as e:
                    warning("Excepted a number for the time_column ({}) and cv column({}). Found {} and {}."
                            "".format(time_col, cv_col, data[time_col]), data[cv_col], e)
                    return INVALID_DATA
    d_out = create_out_fname(cv_file, suffix='_converted', ext='.txt')
    list_to_file(data_to_print, d_out)
    print('Wrote file: {}'.format(d_out))

    d_out = create_out_fname(cv_file, suffix='_converted', ext='.csv')
    list_to_file(data_to_print, d_out, delimiter=',')
    print('Wrote file: {}'.format(d_out))


def process_files(cfg):
    """
    Want to grab the timestep and cv column
    """
    if cfg.skip_header_row is True:
        row_index = 0
    else:
        row_index = 1
    with open(cfg.file_list) as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            if os.path.isfile(line):
                process_cv_file(line, cfg.timestep_col, cfg.cv_col, row_index, cfg.timestep_conv)
            else:
                warning("In file list {}, file {} was not found.".format(cfg.file_list, line))

    #         files = [x.strip() for x in file_line.split(',')]
    #         print(files)
    #         time_dict = {}
    #         print_lines = []
    #         with open(files[0]) as d:
    #             for line in d:
    #                 split_line = [x.strip() for x in line.split(',')]
    #                 time_dict[split_line[0]] = split_line[1:]
    #         with open(files[1]) as e:
    #             for line in e:
    #                 split_line = [x.strip() for x in line.split(',')]
    #                 if split_line[0] in time_dict:
    #                     print_lines.append(','.join([split_line[0]] + time_dict[split_line[0]] + split_line[1:]))
    #                 else:
    #                     logger.debug("Timestep {} found in second file, but not first. Will discard second file "
    #                                  "line {}.".format(split_line[0], line.strip()))
    #
    #         d_out = create_out_suf_fname(files[0], suffix='_plus', ext='.csv')
    #         list_to_file(print_lines, d_out)
    #         print('Wrote file: {}'.format(d_out))
    return


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    # Read template and dump files
    try:
        process_files(args)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data template:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
