#!/usr/bin/env python
"""
Creates lammps data files from pdb files. The reason for making this script is that the cpp file already available
changes the xyz coordinates. I used VMD to wrap and center coordinates, and want that preserved in the new data files.

Provide template data file
List of pdb files to convert
"""

from __future__ import print_function

import ConfigParser
from collections import defaultdict
import copy
import logging
import re
import numpy as np
import csv
from md_utils.md_common import list_to_file, InvalidDataError, seq_list_to_file, create_out_suf_fname, str_to_file, create_out_fname, process_cfg, warning, write_csv

import sys
import argparse

__author__ = 'hmayes'

# Logging
logger = logging.getLogger('pdb2data')
logging.basicConfig(filename='pdb2data.log', filemode='w', level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)


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
DATA_TPL_FILE = 'data_tpl_file'
PDBS_FILE = 'pdb_list_file'
ATOM_DICT_FILE = 'atom_dict_filename'
# PDB file info
PDB_SECTION_LAST_CHAR = 'pdb_section_last_char'
PDB_ATOM_NUM_LAST_CHAR = 'pdb_atom_num_last_char'
PDB_ATOM_INFO_LAST_CHAR = 'pdb_atom_info_last_char'
PDB_MOL_NUM_LAST_CHAR = 'pdb_mol_num_last_char'
PDB_X_LAST_CHAR = 'pdb_x_last_char'
PDB_Y_LAST_CHAR = 'pdb_y_last_char'
PDB_Z_LAST_CHAR = 'pdb_z_last_char'
PDB_FORMAT = 'pdb_print_format'

# Defaults
DEF_CFG_FILE = 'pdb2data.ini'
DEF_CFG_VALS = {PDBS_FILE: 'pdb_list.txt',
                ATOM_DICT_FILE: 'atom_types.csv',
                PDB_SECTION_LAST_CHAR: 6,
                PDB_ATOM_NUM_LAST_CHAR: 12,
                PDB_ATOM_INFO_LAST_CHAR: 22,
                PDB_MOL_NUM_LAST_CHAR: 28,
                PDB_X_LAST_CHAR: 38,
                PDB_Y_LAST_CHAR: 46,
                PDB_Z_LAST_CHAR: 54,
                }
REQ_KEYS = {DATA_TPL_FILE: str,
             }

# From data template file
NUM_ATOMS = 'num_atoms'
HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'
ATOM_TYPE_DICT = 'atom_type_dict'

# For data template file processing
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'

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
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)),def_cfg_vals=DEF_CFG_VALS, req_keys=REQ_KEYS)
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates lammps data files from pdb files, given a template data file.'
                                                 'The required input file provides the name/location of the '
                                                 'template file and a file with a list of data files to convert.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini "
                                               "format. See the example file /test/test_data/pdb2data/pdb2data.ini. "
                                               "The default file name is pdb2data.ini, located in the "
                                               "base directory where the program as run.",
                        default=DEF_CFG_FILE, type=read_cfg)
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

    return args, GOOD_RET

def process_data_tpl(cfg):
    tpl_loc = cfg[DATA_TPL_FILE]
    tpl_data = {}
    tpl_data[HEAD_CONTENT] = []
    tpl_data[ATOMS_CONTENT] = []
    tpl_data[TAIL_CONTENT] = []
    tpl_data[ATOM_TYPE_DICT] = {}
    section = SEC_HEAD
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    atoms_pat = re.compile(r"^Atoms.*")
    bond_pat = re.compile(r"^Bond.*")
    masses_pat = re.compile(r"^Masses.*")
    pair_pat = re.compile(r"^Pair.*")
    read_atom_types = False
    with open(tpl_loc) as f:
        for line in f.readlines():
            line = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                tpl_data[HEAD_CONTENT].append(line)
                # Check before it can be set to True so don't get text line
                if read_atom_types == True:
                    if pair_pat.match(line):
                        read_atom_types = False
                    else:
                        split_line = line.split()
                        if len(split_line) > 0:
                            tpl_data[ATOM_TYPE_DICT][split_line[3]] = [int(split_line[0]) , float(split_line[1])]
                if NUM_ATOMS not in tpl_data:
                    atoms_match = num_atoms_pat.match(line)
                    if atoms_match:
                        # regex is 1-based
                        tpl_data[NUM_ATOMS] = int(atoms_match.group(1))
                if masses_pat.match(line):
                    read_atom_types = True
                elif pair_pat.match(line):
                    read_atom_types = False
                elif atoms_pat.match(line):
                    section = SEC_ATOMS
                    tpl_data[HEAD_CONTENT].append('')

            # atoms_content to contain everything but the xyz: atom_num, mol_num, atom_type, charge'
            elif section == SEC_ATOMS:
                if len(line) == 0:
                    continue
                if bond_pat.match(line):
                    section = SEC_TAIL
                    # Append one new line
                    tpl_data[TAIL_CONTENT].append('')
                    tpl_data[TAIL_CONTENT].append(line)
                    continue
                split_line = line.split()
                atom_num = int(split_line[0])
                mol_num = int(split_line[1])
                atom_type = int(split_line[2])
                charge = float(split_line[3])
                atom_struct = [atom_num, mol_num, atom_type, charge]
                tpl_data[ATOMS_CONTENT].append(atom_struct)
            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                tpl_data[TAIL_CONTENT].append(line)

    # Validate data section
    if len(tpl_data[ATOMS_CONTENT]) != tpl_data[NUM_ATOMS]:
        raise InvalidDataError('The length of the "Atoms" section ({}) does not equal ' \
                               'the number of atoms ({}).'.format(len(tpl_data[ATOMS_CONTENT]), tpl_data[NUM_ATOMS]))

    if logger.isEnabledFor(logging.DEBUG):
        list_to_file(tpl_data[HEAD_CONTENT], 'head.txt')
        seq_list_to_file(tpl_data[ATOMS_CONTENT], 'atoms.txt')
        list_to_file(tpl_data[TAIL_CONTENT], 'tail.txt')
    print(tpl_data[ATOM_TYPE_DICT])
    return tpl_data


def process_pdb_files(cfg, data_tpl_content):
    # # For printing a dictionary
    # new_atom_type_dict = {}
    # If reading a dictionary
    with open(cfg[PDBS_FILE]) as f:
        for pdb_file in f.readlines():
            pdb_file = pdb_file.strip()
            with open(pdb_file) as d:
                atom_num = 0
                for line in d.readlines():
                    pdb_section = line[:cfg[PDB_SECTION_LAST_CHAR]]
                    if pdb_section == 'ATOM  ':
                        atom_nums = line[cfg[PDB_SECTION_LAST_CHAR]:cfg[PDB_ATOM_NUM_LAST_CHAR]]
                        atom_type = line[cfg[PDB_ATOM_NUM_LAST_CHAR]:cfg[PDB_ATOM_INFO_LAST_CHAR]]
                        # TODO: check with Chris: I was going to put a try here (both for making int and float); not needed?
                        # There is already a try when calling the subroutine, so maybe I don't need to?
                        mol_num = int(line[cfg[PDB_ATOM_INFO_LAST_CHAR]:cfg[PDB_MOL_NUM_LAST_CHAR]])
                        pdb_x = float(line[cfg[PDB_MOL_NUM_LAST_CHAR]:cfg[PDB_X_LAST_CHAR]])
                        pdb_y = float(line[cfg[PDB_X_LAST_CHAR]:cfg[PDB_Y_LAST_CHAR]])
                        pdb_z = float(line[cfg[PDB_Y_LAST_CHAR]:cfg[PDB_Z_LAST_CHAR]])
                        last_cols = line[cfg[PDB_Z_LAST_CHAR]:]
                        if atom_num < 10:
                            print(atom_type, data_tpl_content[ATOMS_CONTENT][atom_num][2])
                        # # For printing a dictionary
                        # new_atom_type_dict[atom_type] = data_tpl_content[ATOMS_CONTENT][atom_num][2]
                        atom_num += 1
                if atom_num != data_tpl_content[NUM_ATOMS]:
                    raise InvalidDataError('The length of the "Atoms" section ({}) in the pdb does not equal ' \
                               'the number of atoms in the data template file ({}).'.format(len(atom_num),
                                data_tpl_content[NUM_ATOMS]))
    # # For printing a dictionary
    # dict_list = []
    # for key in new_atom_type_dict:
    #     dict_list.append(key + ',' + str(new_atom_type_dict[key]))
    # list_to_file(dict_list, 'atom_types.csv', mode='w')



                    # line = line.split()
                    # if line[0] == 'ATOM':
                    #     atom_nums = line[cfg[PDB_SECTION_LAST_CHAR]:cfg[PDB_ATOM_NUM_LAST_CHAR]]
                    #     atom_type = line[cfg[PDB_ATOM_NUM_LAST_CHAR]:cfg[PDB_ATOM_INFO_LAST_CHAR]]
                    #     # TODO: check with Chris: I was going to put a try here (both for making int and float); not needed?
                    #     # There is already a try when calling the subroutine, so maybe I don't need to?
                    #     mol_num = int(line[cfg[PDB_ATOM_INFO_LAST_CHAR]:cfg[PDB_MOL_NUM_LAST_CHAR]])
                    #     pdb_x = float(line[cfg[PDB_MOL_NUM_LAST_CHAR]:cfg[PDB_X_LAST_CHAR]])
                    #     pdb_y = float(line[cfg[PDB_X_LAST_CHAR]:cfg[PDB_Y_LAST_CHAR]])
                    #     pdb_z = float(line[cfg[PDB_Y_LAST_CHAR]:cfg[PDB_Z_LAST_CHAR]])
                    #     last_cols = line[cfg[PDB_Z_LAST_CHAR]:]
                        # print(line[2])
                    # if line[2] in data_tpl_content[ATOM_TYPE_DICT]:
                    #     if data_tpl_content[ATOM_TYPE_DICT][line[2]][0] != data_tpl_content[ATOMS_CONTENT][atom_num][2]:
                    #         print(data_tpl_content[ATOM_TYPE_DICT][line[2]][0] , data_tpl_content[ATOMS_CONTENT][atom_num][2])
                    #         # raise InvalidDataError('The atom type of atom number {} in the pdb does match the '
                    #         #                        'expected type from the data template file.'.format(atom_num))




                # atom_struct = [atom_num, mol_num, atom_type, charge]
                # tpl_data[ATOMS_CONTENT].append(atom_struct)
    return


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    # Read template and pdb files
    cfg = args.config
    try:
        data_tpl_content = process_data_tpl(cfg)
        process_pdb_files(cfg, data_tpl_content)
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
