#!/usr/bin/env python
"""
To prepare for EVBFit:
Read cp2k force output files
--There are three sections, all starting with "ATOMIC FORCES in [a.u.]"
----The first is MM only
----The second is QM only
----The third is QMMM
--Keep only the third section, and reprint after converting from [a.u.] to kcal/mol
----1 a.u. force = 8.2387225(14)x10-8 N ; 1 J / m = 1 N  ; 1.0e-10 m = 1 A ;  6.022140857E+23 particles / mol ; 1 kcal = 4.1484 J
--- Thus, 1185.820922 a.u. force = 1 kcal/mol

CALC_OH_DIST: the hydroxyl OH distance on the protonateable residue (when protonated)
"""

from __future__ import print_function
import ConfigParser
import logging
import os
import re
import sys
import argparse

import numpy as np

from md_utils.md_common import InvalidDataError, create_out_suf_fname, pbc_dist, warning, process_cfg, find_dump_section_state, write_csv, seq_list_to_file, ThrowingArgumentParser


__author__ = 'hmayes'


# Logging
logger = logging.getLogger('hydroxyl_oh_dist')
logging.basicConfig(filename='hydroxyl_oh_dist.log', filemode='w', level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)


# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3

# Constants #
au_to_N = 1185.820922

# # Config File Sections
# MAIN_SEC = 'main'
#
# # Config keys
# DUMPS_FILE = 'dump_list_file'

# PROT_RES_MOL_ID = 'prot_res_mol_id'
# PROT_H_TYPE = 'prot_h_type'
# PROT_IGNORE = 'prot_ignore_atom_nums'
# PROT_O_IDS = 'prot_carboxy_oxy_atom_nums'
# WAT_O_TYPE = 'water_o_type'
# WAT_H_TYPE = 'water_h_type'
# OUT_BASE_DIR = 'output_directory'
#
# # for g(r) calcs
# GOFR_MAX = 'max_dist_for_gofr'
# GOFR_DR = 'delta_r_for_gofr'
# GOFR_BINS = 'bins_for_gofr'
# GOFR_RAW_HIST = 'raw_histogram_for_gofr'
# GOFR_R = 'gofr_r'
# GOFR_HO = 'gofr_ho'
# HO_BIN_COUNT = 'ho_bin_count'
# STEPS_COUNTED = 'steps_counted'
#
# # Types of calculations allowed
# CALC_OH_DIST = 'calc_hydroxyl_dist_flag'
# CALC_HO_GOFR = 'calc_hstar_o_gofr_flag'

# # Defaults
DEF_FILE_LIST = 'cp2k_force_list.txt'
OUT_FILE_PREFIX = 'REF_'
# DEF_CFG_FILE = 'lammps_proc_data.ini'
# # Set notation
# DEF_CFG_VALS = {DUMPS_FILE: 'list.txt',
#                 PROT_IGNORE: [],
#                 PROT_O_IDS: [],
#                 OUT_BASE_DIR: None,
#                 CALC_OH_DIST: False,
#                 CALC_HO_GOFR: False,
#                 GOFR_MAX: -1.1,
#                 GOFR_DR: -1.1,
#                 GOFR_BINS: [],
#                 GOFR_RAW_HIST: [],
#                 }
# REQ_KEYS = {PROT_RES_MOL_ID: int,
#             PROT_H_TYPE: int,
#             WAT_O_TYPE: int, WAT_H_TYPE: int,
#             }

# # For cp2k file processing
# SEC_TIMESTEP = 'timestep'
# SEC_NUM_ATOMS = 'dump_num_atoms'
# SEC_BOX_SIZE = 'dump_box_size'
# SEC_ATOMS = 'atoms_section'
# ATOM_NUM = 'atom_num'
# MOL_NUM = 'mol_num'
# ATOM_TYPE = 'atom_type'
# CHARGE = 'charge'
# XYZ_COORDS = 'x,y,z'
#
# # Values to output
# TIMESTEP = 'timestep'
# OH_MIN = 'oh_min'
# OH_MAX = 'oh_max'
# OH_DIFF = 'oh_diff'
# OUT_FIELDNAMES = [TIMESTEP]
# OH_FIELDNAMES = [OH_MIN, OH_MAX, OH_DIFF]


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in a list of cp2k output force files. For each file, '
                                                 'prints the 3rd set of forces only (combined QMMM) converted '
                                                 'from a.u. force units to kcal/mol-Angstrom. These files '
                                                 'have no headers. The first column is the atom index followed'
                                                 'by the forces in the x, y, and z directions.')
    parser.add_argument("-l", "--file_list", help="The location of the text file that list cp2k output files to "
                                                  "process. The default file name is {}, located in the base "
                                                  "directory where the program as run.".format(DEF_FILE_LIST),
                        default=DEF_FILE_LIST, )
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
            warning("Default file {} listing of cp2k force files missing.".format(DEF_FILE_LIST))
        else:
            warning("Specified file {} listing cp2k force files missing.".format(args.file_list))
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def read_dump_file(dump_file):
    with open(dump_file) as d:
        section = None
        box = np.zeros((3,))
        box_counter = 1
        atom_counter = 1
    #     for line in d.readlines():
    #         line = line.strip()
    #         if section is None:
    #             section = find_dump_section_state(line)
    #             #logger.debug("In process_dump_files, set section to %s.", section)
    #             if section is None:
    #                 raise InvalidDataError('Unexpected line in file {}: {}'.format(d, line))
    #         elif section == SEC_TIMESTEP:
    #             timestep = line
    #             # Reset variables
    #             dump_atom_data = []
    #             result = { TIMESTEP: timestep }
    #             section = None
    #         elif section == SEC_NUM_ATOMS:
    #             num_atoms = int(line)
    #             section = None
    #         elif section == SEC_BOX_SIZE:
    #             split_line = line.split()
    #             diff = float(split_line[1]) - float(split_line[0])
    #             box[box_counter - 1] = diff
    #             if box_counter == 3:
    #                 box_counter = 0
    #                 section = None
    #             box_counter += 1
    #         elif section == SEC_ATOMS:
    #             split_line = line.split()
    #             # If there is an incomplete line in a dump file, move on to the next file
    #             if len(split_line) < 7:
    #                 break
    #             atom_num = int(split_line[0])
    #             mol_num = int(split_line[1])
    #             atom_type = int(split_line[2])
    #             charge = float(split_line[3])
    #             x, y, z = map(float, split_line[4:7])
    #             # Here, the atoms counting starts at 1. However, the template counted from zero
    #             atom_struct = {ATOM_NUM: atom_num,
    #                            MOL_NUM: mol_num,
    #                            ATOM_TYPE: atom_type,
    #                            CHARGE: charge,
    #                            XYZ_COORDS: [x,y,z], }
    #             dump_atom_data.append(atom_struct)
    #             if atom_counter == num_atoms:
    #                 result.update(process_atom_data(cfg, dump_atom_data, box, timestep, gofr_data))
    #                 data_to_print.append(result)
    #                 atom_counter = 0
    #                 section = None
    #             atom_counter += 1
    # if atom_counter == 1:
    #     print("Completed reading dumpfile {}.".format(dump_file))
    # else:
    #     warning("FYI: dump file {} step {} did not have the full list of atom numbers. Continuing to next dump file.".format(dump_file, timestep))


def convert_forces(xyz):
    print(xyz)


def read_cp2k_force_file(file):
    forces_pat = re.compile(r"^ATOMIC FORCES in .*")
    comment_pat = re.compile(r"^#.*")
    sum_pat = re.compile(r"^SUM.*")
    sums = np.zeros(4)
    # if line == 'ITEM: TIMESTEP':
    #     return sec_timestep
    # elif line == 'ITEM: NUMBER OF ATOMS':
    #     return sec_num_atoms
    # elif line == 'ITEM: BOX BOUNDS pp pp pp':
    #     return sec_box_size
    # elif atoms_pat.match(line):
    #     return sec_atoms
    force_count = 0
    keep_lines = False
    line_count = 0
    f_out = OUT_FILE_PREFIX
    with open(file) as f:
        print('Reading file {}'.format(file))
        for line in f.readlines():
            line = line.strip()
            if len(line) == 0:
                continue
            if forces_pat.match(line):
                force_count += 1
                if force_count == 3:
                    keep_lines = True
            elif keep_lines:
                line_count += 1
                split_line = line.split()
                if comment_pat.match(split_line[0]):
                    continue
                try:
                    if sum_pat.match(split_line[0]):
                        sums = np.asarray(map(float,split_line[4:])) * au_to_N
                        print('Summed forces (X Y Z Total) in kcal/mol are: {}'.format(' '.join('%6.3f'%F for F in sums)))
                        return
                except ValueError as e:
                    warning('Check file {} sum line in the third ATOMIC FORCES section, as it does not '
                                          'appear to contain the expected data: \n {}\n'
                                          'Continuing to the next line in the file list'.format(file, line), e)
                    return


                try:
                    atom_num = int(split_line[0])
                    kind = int(split_line[1])
                    element = split_line[2]
                    xyz = np.asarray(map(float,split_line[3:]))
                    if atom_num < 4:
                        convert_forces(xyz)
                except ValueError as e:
                    warning('Check file {} line {} in the third ATOMIC FORCES section, as it does not '
                                          'appear to contain all six expected columns of data '
                                          '(Atom Kind Element X Y Z): \n {}\n'
                                          'Continuing to the next line in the file list'.format(file, line_count, line), e)
                    return
    warning('Reached end of file {} without encountering a third SUM OF ATOMIC FORCES section. '
            'Continuing to the next line in the file list.'.format(file))


def read_file_list(file_list):
    """
    @param file_list: the list of files to be read
    """

    with open(file_list) as f:
        for file in f.readlines():
            file = file.strip()
            if len(file) == 0:
                continue
            elif os.path.isfile(file):
                read_cp2k_force_file(file)
            else:
                warning('Could not read file {} in file list {}. '
                        'Continuing to the next line in file list.'.format(file,file_list))

def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET:
        return ret

    # Read template and dump files

    try:
        read_file_list(args.file_list)
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
