#!/usr/bin/env python
# coding=utf-8
"""
Edit a pdb file to provide missing data
"""

from __future__ import print_function
# noinspection PyCompatibility
import ConfigParser
import logging
import os
import sys
import argparse
import numpy as np
from md_utils.md_common import list_to_file, InvalidDataError, warning, process_cfg, create_out_fname, read_csv_dict

__author__ = 'hmayes'

# Logging
logger = logging.getLogger('pdb_edit')
logging.basicConfig(filename='pdb_edit.log', filemode='w', level=logging.DEBUG)
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
PDB_FILE = 'pdb_file'
PDB_NEW_FILE = 'new_pdb_name'
ATOM_REORDER_FILE = 'atom_reorder_old_new_file'
MOL_RENUM_FILE = 'mol_renum_old_new_file'
RENUM_MOL = 'mol_renum_flag'
FIRST_ADD_ELEM = 'first_atom_add_element'
LAST_ADD_ELEM = 'last_atom_add_element'
FIRST_WAT_ID = 'first_wat_atom'
LAST_WAT_ID = 'last_wat_atom'
ADD_ELEMENTS = 'add_element_types'
ELEMENT_DICT_FILE = 'atom_type_element_dict_file'
OUT_BASE_DIR = 'output_directory'

# PDB file info
PDB_LINE_TYPE_LAST_CHAR = 'pdb_line_type_last_char'
PDB_ATOM_NUM_LAST_CHAR = 'pdb_atom_num_last_char'
PDB_ATOM_TYPE_LAST_CHAR = 'pdb_atom_type_last_char'
PDB_RES_TYPE_LAST_CHAR = 'pdb_res_type_last_char'
PDB_MOL_NUM_LAST_CHAR = 'pdb_mol_num_last_char'
PDB_X_LAST_CHAR = 'pdb_x_last_char'
PDB_Y_LAST_CHAR = 'pdb_y_last_char'
PDB_Z_LAST_CHAR = 'pdb_z_last_char'
PDB_LAST_T_CHAR = 'pdb_last_temp_char'
PDB_LAST_ELEM_CHAR = 'pdb_last_element_char'
PDB_FORMAT = 'pdb_print_format'

# Defaults
DEF_CFG_FILE = 'pdb_edit.ini'
DEF_ELEM_DICT_FILE = os.path.join(os.path.dirname(__file__), 'cfg', 'charmm36_atoms_elements.txt')
DEF_CFG_VALS = {ATOM_REORDER_FILE: None,
                MOL_RENUM_FILE: None,
                ELEMENT_DICT_FILE: None,
                RENUM_MOL: False,
                FIRST_ADD_ELEM: 1,
                LAST_ADD_ELEM: np.inf,
                FIRST_WAT_ID: np.nan,
                LAST_WAT_ID: np.nan,
                OUT_BASE_DIR: None,
                PDB_NEW_FILE: None,
                PDB_FORMAT: '{:6s}{:>5}{:^6s}{:5s}{:>4}    {:8.3f}{:8.3f}{:8.3f}{:22s}{:>2s}{:s}',
                PDB_LINE_TYPE_LAST_CHAR: 6,
                PDB_ATOM_NUM_LAST_CHAR: 11,
                PDB_ATOM_TYPE_LAST_CHAR: 17,
                PDB_RES_TYPE_LAST_CHAR: 22,
                PDB_MOL_NUM_LAST_CHAR: 28,
                PDB_X_LAST_CHAR: 38,
                PDB_Y_LAST_CHAR: 46,
                PDB_Z_LAST_CHAR: 54,
                PDB_LAST_T_CHAR: 76,
                PDB_LAST_ELEM_CHAR: 78,
                ADD_ELEMENTS: False,
                }
REQ_KEYS = {PDB_FILE: str,
            }

HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'


# This is used when need to add atom types to PDB file
C_ATOMS = ' C'
O_ATOMS = ' O'
H_ATOMS = ' H'
N_ATOMS = ' N'
P_ATOMS = ' P'
S_ATOMS = ' S'
CL_ATOMS = 'CL'
NA_ATOMS = 'NA'
K_ATOMS = ' K'
LI_ATOMS = 'LI'
MG_ATOMS = 'MG'
CA_ATOMS = 'CA'
RB_ATOMS = 'RB'
CS_ATOMS = 'CS'
BA_ATOMS = 'BA'
ZN_ATOMS = 'ZN'
CD_ATOMS = 'CD'


def create_element_dict(dict_file):
    # This is used when need to add atom types to PDB file
    element_dict = {}
    if dict_file is not None:
        return read_csv_dict(dict_file, pdb_dict=True)
    return element_dict


def read_cfg(f_loc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param f_loc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser.ConfigParser()
    good_files = config.read(f_loc)
    if not good_files:
        raise IOError('Could not read file: {}'.format(f_loc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)

    # Assume that elements should be added if a dict file is give
    if main_proc[ADD_ELEMENTS] and main_proc[ELEMENT_DICT_FILE] is None:
        main_proc[ELEMENT_DICT_FILE] = DEF_ELEM_DICT_FILE
    if main_proc[ELEMENT_DICT_FILE] is not None:
        main_proc[ADD_ELEMENTS] = True

    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates a new version of a pdb file. Atoms will be numbered '
                                                 'starting from one. Options include renumbering molecules.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)
    args = None
    try:
        args = parser.parse_args(argv)
    except (IOError, InvalidDataError) as e:
        warning(e)
        parser.print_help()
        return args, IO_ERROR
    except KeyError as e:
        warning("Input data missing:", e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def pdb_atoms_to_file(pdb_format, list_val, fname, mode='w'):
    """
    Writes the list of sequences to the given file in the specified format for a PDB

    @param pdb_format: provides correct formatting
    @param list_val: The list of sequences to write.
    @param fname: The location of the file to write.
    @param mode: default is to write; can allow to append
    """
    with open(fname, mode) as w_file:
        for line in list_val:
            w_file.write(pdb_format.format(*line) + '\n')


def print_pdb(head_data, atoms_data, tail_data, file_name, file_format):
    list_to_file(head_data, file_name)
    pdb_atoms_to_file(file_format, atoms_data, file_name, mode='a')
    list_to_file(tail_data, file_name, mode='a', print_message=False)


def process_pdb(cfg, atom_num_dict, mol_num_dict, element_dict):
    pdb_loc = cfg[PDB_FILE]
    pdb_data = {HEAD_CONTENT: [], ATOMS_CONTENT: [], TAIL_CONTENT: []}
    # to allow warning to be printed once and only once
    missing_types = []

    with open(pdb_loc) as f:
        wat_count = 0
        atom_count = 0
        mol_count = 1

        current_mol = None
        last_mol_num = None
        atoms_content = []

        for line in f:
            line = line.strip()
            line_len = len(line)
            if line_len == 0:
                continue
            line_head = line[:cfg[PDB_LINE_TYPE_LAST_CHAR]]
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if line_head == 'REMARK' or line_head == 'CRYST1':
                pdb_data[HEAD_CONTENT].append(line)

            # atoms_content to contain everything but the xyz
            elif line_head == 'ATOM  ':

                # My template PDB has ***** after atom_count 99999. Thus, I'm renumbering. Otherwise, this this:
                # atom_num = line[cfg[PDB_LINE_TYPE_LAST_CHAR]:cfg[PDB_ATOM_NUM_LAST_CHAR]]
                # For renumbering, making sure prints in the correct format, including num of characters:
                atom_count += 1

                # For reordering atoms
                if atom_count in atom_num_dict:
                    atom_id = atom_num_dict[atom_count]
                else:
                    atom_id = atom_count

                if atom_id > 99999:
                    atom_num = format(atom_id, 'x')
                    if len(atom_num) > 5:
                        warning("Hex representation of {} is {}, which is greater than 5 characters. This"
                                "will affect the PDB output formatting.".format(atom_id, atom_num))
                else:
                    atom_num = '{:5d}'.format(atom_id)

                atom_type = line[cfg[PDB_ATOM_NUM_LAST_CHAR]:cfg[PDB_ATOM_TYPE_LAST_CHAR]]
                res_type = line[cfg[PDB_ATOM_TYPE_LAST_CHAR]:cfg[PDB_RES_TYPE_LAST_CHAR]]
                mol_num = int(line[cfg[PDB_RES_TYPE_LAST_CHAR]:cfg[PDB_MOL_NUM_LAST_CHAR]])
                pdb_x = float(line[cfg[PDB_MOL_NUM_LAST_CHAR]:cfg[PDB_X_LAST_CHAR]])
                pdb_y = float(line[cfg[PDB_X_LAST_CHAR]:cfg[PDB_Y_LAST_CHAR]])
                pdb_z = float(line[cfg[PDB_Y_LAST_CHAR]:cfg[PDB_Z_LAST_CHAR]])
                occ_t = line[cfg[PDB_Z_LAST_CHAR]:cfg[PDB_LAST_T_CHAR]]
                element = line[cfg[PDB_LAST_T_CHAR]:cfg[PDB_LAST_ELEM_CHAR]]
                last_cols = line[cfg[PDB_LAST_ELEM_CHAR]:]

                # For user-specified changing of molecule number
                if mol_num in mol_num_dict:
                    mol_num = mol_num_dict[mol_num]

                # If doing water molecule checking...
                if cfg[FIRST_WAT_ID] <= atom_count <= cfg[LAST_WAT_ID]:
                    if (wat_count % 3) == 0:
                        current_mol = mol_num
                        if atom_type != '  OH2 ':
                                warning('Expected an OH2 atom to be the first atom of a water molecule. '
                                        'Check line: {}'.format(line))
                        # last_cols = '  0.00  0.00      S2   O'
                    else:
                        if current_mol != mol_num:
                            warning('Water not in order on line:', line)
                        if (wat_count % 3) == 1:
                            if atom_type != '  H1  ':
                                warning('Expected an H1 atom to be the second atom of a water molecule. '
                                        'Check line: {}'.format(line))
                        else:
                            if atom_type != '  H2  ':
                                warning('Expected an H2 atom to be the second atom of a water molecule. '
                                        'Check line: {}'.format(line))
                    wat_count += 1

                if cfg[ADD_ELEMENTS] and atom_count <= cfg[LAST_ADD_ELEM]:
                    if atom_type in element_dict:
                        element = element_dict[atom_type]
                    else:
                        if atom_type not in missing_types:
                            warning("Please add atom type '{}' to dictionary of elements. Will not write/overwrite "
                                    "element type in the pdb output.".format(atom_type))
                            missing_types.append(atom_type)

                # For numbering molecules from 1 to end
                if cfg[RENUM_MOL]:
                    if last_mol_num is None:
                        last_mol_num = mol_num

                    if mol_num != last_mol_num:
                        last_mol_num = mol_num
                        mol_count += 1
                        if mol_count == 10000:
                            warning("Molecule numbers greater than 9999 will be printed in hex")

                    # Due to PDB format constraints, need to print in hex starting at 9999 molecules.
                    if mol_count > 9999:
                        mol_num = format(mol_count, 'x')
                        if len(mol_num) > 4:
                            warning("Hex representation of {} is {}, which is greater than 4 characters. This"
                                    "will affect the PDB output formatting.".format(atom_id, atom_num))
                    else:
                        mol_num = '{:4d}'.format(mol_count)

                line_struct = [line_head, atom_num, atom_type, res_type, mol_num, pdb_x, pdb_y, pdb_z,
                               occ_t, element, last_cols]
                atoms_content.append(line_struct)

            # tail_content to contain everything after the 'Atoms' section
            else:
                pdb_data[TAIL_CONTENT].append(line)

    # Only sort if there is renumbering
    if len(atom_num_dict) > 0:
        pdb_data[ATOMS_CONTENT] = sorted(atoms_content, key=lambda entry: entry[1])
    else:
        pdb_data[ATOMS_CONTENT] = atoms_content

    if cfg[PDB_NEW_FILE] is None:
        f_name = create_out_fname(cfg[PDB_FILE], suffix="_new", base_dir=cfg[OUT_BASE_DIR])
    else:
        f_name = create_out_fname(cfg[PDB_NEW_FILE], base_dir=cfg[OUT_BASE_DIR])
    print_pdb(pdb_data[HEAD_CONTENT], pdb_data[ATOMS_CONTENT], pdb_data[TAIL_CONTENT],
              f_name, cfg[PDB_FORMAT])

    return


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    cfg = args.config

    # Read and process pdb files
    try:
        atom_num_dict = read_csv_dict(cfg[ATOM_REORDER_FILE])
        mol_num_dict = read_csv_dict(cfg[MOL_RENUM_FILE], one_to_one=False)
        element_dict = create_element_dict(cfg[ELEMENT_DICT_FILE])
        process_pdb(cfg, atom_num_dict, mol_num_dict, element_dict)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except (InvalidDataError, ValueError) as e:
        warning("Problems with input:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
