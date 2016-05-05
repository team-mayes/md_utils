#!/usr/bin/env python
"""
Creates lammps data files from pdb files. The reason for making this script is that the cpp file already available
changes the xyz coordinates. I used VMD to wrap and center coordinates, and want that preserved in the new data files.

Provide template data file
List of pdb files to convert
"""

from __future__ import print_function
import ConfigParser
import logging
import re
import csv
import sys
import argparse

from md_utils.md_common import list_to_file, InvalidDataError, create_out_fname, process_cfg, warning

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
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), def_cfg_vals=DEF_CFG_VALS, req_keys=REQ_KEYS)
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
    parser.add_argument("-c", "--config", help="The location of the configuration file. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
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
    dict_loc = cfg[ATOM_DICT_FILE]
    tpl_loc = cfg[DATA_TPL_FILE]
    tpl_data = {HEAD_CONTENT: [], ATOMS_CONTENT: [], TAIL_CONTENT: [], ATOM_TYPE_DICT: {}}
    section = SEC_HEAD
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    atoms_pat = re.compile(r"^Atoms.*")
    bond_pat = re.compile(r"^Bond.*")

    with open(dict_loc) as csv_file:
        for line in csv.reader(csv_file):
            try:
                tpl_data[ATOM_TYPE_DICT][line[0]] = int(line[1])
            except ValueError as e:
                logger.debug("{}: Could not convert value {} to int.".format(e, line[1]))

    with open(tpl_loc) as f:
        for line in f.readlines():
            line = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                tpl_data[HEAD_CONTENT].append(line)
                if NUM_ATOMS not in tpl_data:
                    atoms_match = num_atoms_pat.match(line)
                    if atoms_match:
                        # regex is 1-based
                        tpl_data[NUM_ATOMS] = int(atoms_match.group(1))
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
                end = ' '.join(split_line[7:])
                # atom_struct = [atom_num, mol_num, atom_type, charge,end]
                # tpl_data[ATOMS_CONTENT].append(atom_struct)
                tpl_data[ATOMS_CONTENT].append([atom_num, mol_num, atom_type, charge, end])
            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                tpl_data[TAIL_CONTENT].append(line)

    # Validate data section
    if len(tpl_data[ATOMS_CONTENT]) != tpl_data[NUM_ATOMS]:
        raise InvalidDataError('The length of the "Atoms" section ({}) does not equal '
                               'the number of atoms ({}).'.format(len(tpl_data[ATOMS_CONTENT]), tpl_data[NUM_ATOMS]))

    if logger.isEnabledFor(logging.DEBUG):
        list_to_file(tpl_data[HEAD_CONTENT], 'head.txt')
        list_to_file(tpl_data[ATOMS_CONTENT], 'atoms.txt')
        list_to_file(tpl_data[TAIL_CONTENT], 'tail.txt')

    return tpl_data


def process_pdb_files(cfg, data_tpl_content):
    # # For printing a dictionary
    # new_atom_type_dict = {}
    with open(cfg[PDBS_FILE]) as f:
        for pdb_file in f.readlines():
            pdb_atom_line = []
            pdb_file = pdb_file.strip()
            with open(pdb_file) as d:
                atom_num = 0
                for line in d.readlines():
                    pdb_section = line[:cfg[PDB_SECTION_LAST_CHAR]]
                    if pdb_section == 'ATOM  ':
                        # atom_nums = line[cfg[PDB_SECTION_LAST_CHAR]:cfg[PDB_ATOM_NUM_LAST_CHAR]]
                        # atom_type = line[cfg[PDB_ATOM_NUM_LAST_CHAR]:cfg[PDB_ATOM_INFO_LAST_CHAR]]
                        # There is already a try when calling the subroutine, so maybe I don't need to?
                        # mol_num = int(line[cfg[PDB_ATOM_INFO_LAST_CHAR]:cfg[PDB_MOL_NUM_LAST_CHAR]])
                        pdb_x = float(line[cfg[PDB_MOL_NUM_LAST_CHAR]:cfg[PDB_X_LAST_CHAR]])
                        pdb_y = float(line[cfg[PDB_X_LAST_CHAR]:cfg[PDB_Y_LAST_CHAR]])
                        pdb_z = float(line[cfg[PDB_Y_LAST_CHAR]:cfg[PDB_Z_LAST_CHAR]])
                        # last_cols = line[cfg[PDB_Z_LAST_CHAR]:]
                        # if data_tpl_content[ATOMS_CONTENT][atom_num][2] !=data_tpl_content[ATOM_TYPE_DICT][atom_type]:
                        #     print(atom_num,atom_type, data_tpl_content[ATOMS_CONTENT][atom_num][2],
                        # data_tpl_content[ATOM_TYPE_DICT][atom_type])
                        # # For printing a dictionary
                        # new_atom_type_dict[atom_type] = data_tpl_content[ATOMS_CONTENT][atom_num][2]
                        pdb_atom_line.append(data_tpl_content[ATOMS_CONTENT][atom_num][:4] +
                                             [pdb_x, pdb_y, pdb_z] + data_tpl_content[ATOMS_CONTENT][atom_num][4:])
                        atom_num += 1
            if atom_num != data_tpl_content[NUM_ATOMS]:
                raise InvalidDataError('The length of the "Atoms" section ({}) in the pdb does not equal '
                                       'the number of atoms in the data template file ({}).'
                                       ''.format(len(atom_num),
                                                 data_tpl_content[NUM_ATOMS]))
            d_out = create_out_fname(pdb_file, suffix='_from_py', ext='.data')
            list_to_file(data_tpl_content[HEAD_CONTENT] + pdb_atom_line + data_tpl_content[TAIL_CONTENT],
                         d_out)
            print('Wrote file: {}'.format(d_out))


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
