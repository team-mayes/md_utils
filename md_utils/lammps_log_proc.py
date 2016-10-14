#!/usr/bin/env python
"""
From lammps logs file(s), finds key output such as system energy and temperature
"""

from __future__ import print_function

import argparse
import os
import sys

import re

from md_utils.md_common import (InvalidDataError, warning, file_rows_to_list, IO_ERROR, GOOD_RET, INPUT_ERROR,
                                INVALID_DATA, get_fname_root, create_out_fname, write_csv)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError

__author__ = 'hmayes'


# Constants #

# For log file processing
SEC_TIMESTEP = 'timestep'

# For evb processing and output
FILE_NAME = 'filename'
TIMESTEP = 'timestep'
STEP_PAT = re.compile(r"^---------------- Step.*")
TOTENG = 'TotEng'
POTENG = 'PotEng'
E_DIHED = 'E_dihed'
E_COUL = 'E_coul'
KINENG = 'KinEng'
E_BOND = 'E_bond'
E_IMPRO = 'E_impro'
E_LONG = 'E_long'
TEMP = 'Temp'
E_ANGL = 'E_angl'
E_VDWL = 'E_vdwl'
PRESS = 'Press'

LOG_FIELDNAMES = [FILE_NAME, TIMESTEP, TOTENG, POTENG, E_DIHED, E_COUL,
                  KINENG, E_BOND, E_IMPRO, E_LONG,
                  TEMP, E_ANGL, E_VDWL, PRESS, ]


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='For each timestep, gather the energy information output by LAMMPS '
                                                 'in the log file.')
    parser.add_argument("-f", "--file", help="The log file to be processed.",
                        default=None)
    parser.add_argument("-l", "--list_file", help="The a file with a list of log files to be processes.",
                        default=None)
    args = None
    try:
        args = parser.parse_args(argv)
        if args.file is None:
            args.file_list = []
        else:
            if os.path.isfile(args.file):
                args.file_list = [args.file]
                args.source_name = args.file
            else:
                raise IOError("Could not find specified log file: {}".format(args.file))
        if args.list_file is not None:
            args.file_list += file_rows_to_list(args.list_file)
            args.source_name = args.list_file
        if len(args.file_list) < 1:
            raise InvalidDataError("Found no log file names to process. Specify one or more files as specified in "
                                   "the help documentation ('-h').")
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except (KeyError, InvalidDataError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


def process_log(log_file):
    """
    Gather key info from lammps log file
    @param log_file: name of log file
    @return: lists of dicts of key data extracted; 1 dict per timestep
    """
    result_list = []
    file_root = get_fname_root(log_file)

    with open(log_file) as l_file:
        reading_steps = False
        result_dict = {}
        for line in l_file:
            line = line.strip()
            if STEP_PAT.match(line):
                reading_steps = True
                result_dict[FILE_NAME] = file_root
                result_dict[TIMESTEP] = int(line.split()[2])
            elif reading_steps:
                if len(line) == 0:
                    break
                s_line = line.split()
                if s_line[0] == TOTENG:
                    for key_id, key in enumerate([TOTENG, KINENG, TEMP]):
                        result_dict[key] = float(s_line[2 + key_id * 3])
                elif s_line[0] == POTENG:
                    for key_id, key in enumerate([POTENG, E_BOND, E_ANGL]):
                        result_dict[key] = float(s_line[2 + key_id * 3])
                elif s_line[0] == E_DIHED:
                    for key_id, key in enumerate([E_DIHED, E_IMPRO, E_VDWL]):
                        result_dict[key] = float(s_line[2 + key_id * 3])
                elif s_line[0] == E_COUL:
                    for key_id, key in enumerate([E_COUL, E_LONG, PRESS]):
                        result_dict[key] = float(s_line[2 + key_id * 3])
                    result_list.append(dict(result_dict))
                else:
                    # when stop matching, done reading file (either by normal or abnormal termination)
                    break

    return result_list


def process_log_files(source_name, log_file_list):
    """
    Loops through all files and prints output
    @param source_name: the source name to use as the base for creating an outfile name
    @param log_file_list: list of file names to read and process
    """

    result_list = []
    out_fname = create_out_fname(source_name, suffix='_sum', ext=".csv")

    for log_file in log_file_list:
        result_list += process_log(log_file)

    if len(result_list) == 0:
        warning("Found no lammps log data to process from: {}".format(source_name))
    else:
        write_csv(result_list, out_fname, LOG_FIELDNAMES, extrasaction="ignore")


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    try:
        process_log_files(args.source_name, args.file_list, )
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
