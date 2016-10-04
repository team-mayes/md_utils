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

#
#
# def read_dump_file(dump_file, cfg, data_to_print, gofr_data, out_fieldnames, write_mode):
#     with open(dump_file) as d:
#         # spaces here allow file name to line up with the "completed reading" print line
#         print("{:>17}: {}".format('Reading', dump_file))
#         section = None
#         box = np.zeros((3,))
#         box_counter = 1
#         atom_counter = 1
#         timesteps_read = 0
#         num_atoms = 0
#         timestep = None
#         for line in d:
#             line = line.strip()
#             if section is None:
#                 section = find_dump_section_state(line)
#                 if section is None and len(line) > 0:
#                     raise InvalidDataError('Unexpected line in file {}: {}'.format(dump_file, line))
#             elif section == SEC_TIMESTEP:
#                 # Reset variables
#                 section = None
#                 dump_atom_data = []
#                 try:
#                     timestep = int(line)
#                 except ValueError as e:
#                     raise InvalidDataError("Encountered error tryig to read an integer timestep, : {}".format(e))
#                 timesteps_read += 1
#                 if timesteps_read > cfg[MAX_TIMESTEPS]:
#                     print("Reached the maximum timesteps per dumpfile ({}). "
#                           "To increase this number, set a larger value for {}. "
#                           "Continuing program.".format(cfg[MAX_TIMESTEPS], MAX_TIMESTEPS))
#                     break
#                 if timesteps_read % cfg[PRINT_TIMESTEPS] == 0:
#                     if cfg[PER_FRAME_OUTPUT]:
#                         print_per_frame(dump_file, cfg, data_to_print, out_fieldnames, write_mode)
#                         data_to_print = []
#                         write_mode = 'a'
#                     if cfg[GOFR_OUTPUT]:
#                         print_gofr(cfg, gofr_data)
#                 result = {FILE_NAME: os.path.basename(dump_file),
#                           TIMESTEP: timestep}
#             elif section == SEC_NUM_ATOMS:
#                 num_atoms = int(line)
#                 section = None
#             elif section == SEC_BOX_SIZE:
#                 split_line = line.split()
#                 diff = float(split_line[1]) - float(split_line[0])
#                 box[box_counter - 1] = diff
#                 if box_counter == 3:
#                     box_counter = 0
#                     section = None
#                 box_counter += 1
#             elif section == SEC_ATOMS:
#                 split_line = line.split()
#                 # If there is an incomplete line in a dump file, move on to the next file
#                 if len(split_line) < 7:
#                     break
#                 atom_num = int(split_line[0])
#                 mol_num = int(split_line[1])
#                 atom_type = int(split_line[2])
#                 charge = float(split_line[3])
#                 x, y, z = map(float, split_line[4:7])
#                 # Here, the atoms counting starts at 1. However, the template counted from zero
#                 atom_struct = {ATOM_NUM: atom_num,
#                                MOL_NUM: mol_num,
#                                ATOM_TYPE: atom_type,
#                                CHARGE: charge,
#                                XYZ_COORDS: [x, y, z], }
#                 dump_atom_data.append(atom_struct)
#                 if atom_counter == num_atoms:
#                     result.update(process_atom_data(cfg, dump_atom_data, box, timestep, gofr_data))
#                     data_to_print.append(result)
#                     atom_counter = 0
#                     section = None
#                 atom_counter += 1
#     if atom_counter == 1:
#         print("Completed reading: {}".format(dump_file))
#     else:
#         warning("FYI: dump file {} step {} did not have the full list of atom numbers. "
#                 "Continuing to next dump file.".format(dump_file, timestep))


# def print_per_frame(dump_file, cfg, data_to_print, out_fieldnames, write_mode):
#     f_out = create_out_fname(dump_file, suffix='_sum', ext='.csv', base_dir=cfg[OUT_BASE_DIR])
#     write_csv(data_to_print, f_out, out_fieldnames, extrasaction="ignore", mode=write_mode)


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
    @param source_name: the source name to use as the base for creating an ourfile name
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
