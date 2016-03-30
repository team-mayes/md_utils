#!/usr/bin/env python
"""
Edit a pdb file to provide missing data
"""

from __future__ import print_function
import ConfigParser
import csv
import logging
import re
import sys
import argparse

from md_utils.md_common import list_to_file, InvalidDataError, warning, process_cfg, create_out_fname, read_int_dict

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
PDB_TPL_FILE = 'pdb_tpl_file'
PDB_NEW_FILE = 'pdb_new_file'
ATOM_REORDER_FILE = 'atom_reorder_old_new_file'
# PDB file info
PDB_LINE_TYPE_LAST_CHAR = 'pdb_line_type_last_char'
PDB_ATOM_NUM_LAST_CHAR = 'pdb_atom_num_last_char'
PDB_ATOM_TYPE_LAST_CHAR = 'pdb_atom_type_last_char'
PDB_RES_TYPE_LAST_CHAR = 'pdb_res_type_last_char'
PDB_MOL_NUM_LAST_CHAR = 'pdb_mol_num_last_char'
PDB_X_LAST_CHAR = 'pdb_x_last_char'
PDB_Y_LAST_CHAR = 'pdb_y_last_char'
PDB_Z_LAST_CHAR = 'pdb_z_last_char'
PDB_FORMAT = 'pdb_print_format'
LAST_PROT_ID = 'last_prot_atom'
OUT_BASE_DIR = 'output_directory'

# data file info

# Defaults
DEF_CFG_FILE = 'pdb_edit.ini'
# Set notation
DEF_CFG_VALS = {ATOM_REORDER_FILE: None,
                PDB_NEW_FILE: 'new.pdb',
                PDB_FORMAT: '%s%s%s%s%4d    %8.3f%8.3f%8.3f%s',
                PDB_LINE_TYPE_LAST_CHAR: 6,
                PDB_ATOM_NUM_LAST_CHAR: 11,
                PDB_ATOM_TYPE_LAST_CHAR: 17,
                PDB_RES_TYPE_LAST_CHAR: 22,
                PDB_MOL_NUM_LAST_CHAR: 28,
                PDB_X_LAST_CHAR: 38,
                PDB_Y_LAST_CHAR: 46,
                PDB_Z_LAST_CHAR: 54,
                LAST_PROT_ID: 0,
                OUT_BASE_DIR: None,
                }
REQ_KEYS = {PDB_TPL_FILE: str,
            }

HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'


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
        raise IOError('Could not read file {}'.format(f_loc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates a new version of a pdb file.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
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


def pdb_atoms_to_file(pdb_format, list_val, fname, mode='w'):
    """
    Writes the list of sequences to the given file in the specified format for a PDB.

    :param list_val: The list of sequences to write.
    :param fname: The location of the file to write.
    """
    with open(fname, mode) as w_file:
        for line in list_val:
            w_file.write(pdb_format % tuple(line) + '\n')


def print_pdb(head_data, atoms_data, tail_data, file_name, file_format):
    list_to_file(head_data, file_name)
    pdb_atoms_to_file(file_format, atoms_data, file_name, mode='a')
    list_to_file(tail_data, file_name, mode='a')
    return


def make_atom_type_element_dict(atom_section, last_prot_atom):
    """
    To make a lists of PDB atom types according to element type
    Used if need to fill in the last column of a PDB

    @param atom_section: assumes the atom type is in entry index 2
    """
    prot_atom_types = set()

    c_pat = re.compile(r"^C.*")
    c_atoms = []
    h_pat = re.compile(r"^H.*")
    h_atoms = []
    o_pat = re.compile(r"^O.*")
    o_atoms = []
    n_pat = re.compile(r"^N.*")
    n_atoms = []
    s_pat = re.compile(r"^S.*")
    s_atoms = []

    for atom_id, entry in enumerate(atom_section):
        if atom_id < last_prot_atom:
            prot_atom_types.add(entry[2])

    for atom in prot_atom_types:
        atom_strip = atom.strip()
        c_match = c_pat.match(atom_strip)
        o_match = o_pat.match(atom_strip)
        h_match = h_pat.match(atom_strip)
        n_match = n_pat.match(atom_strip)
        s_match = s_pat.match(atom_strip)
        if c_match:
            c_atoms.append(atom)
        elif o_match:
            o_atoms.append(atom)
        elif h_match:
            h_atoms.append(atom)
        elif n_match:
            n_atoms.append(atom)
        elif s_match:
            s_atoms.append(atom)
        else:
            raise InvalidDataError('Please add atom type {} to a dictionary of elements.'.format(atom))
            # atom_type_dict

    # This printing is to check with VMD
    print(' '.join(c_atoms))
    print(' '.join(o_atoms))
    print(' '.join(h_atoms))
    print(' '.join(n_atoms))
    print(' '.join(s_atoms))
    # lists for python
    print(c_atoms)
    print(o_atoms)
    print(h_atoms)
    print(n_atoms)
    print(s_atoms)


# noinspection PyUnboundLocalVariable
def process_pdb_tpl(cfg, atom_num_dict):
    tpl_loc = cfg[PDB_TPL_FILE]
    tpl_data = {HEAD_CONTENT: [], ATOMS_CONTENT: [], TAIL_CONTENT: []}
    atoms_content = []

    last_prot_atom = cfg[LAST_PROT_ID]

    atom_count = 0

    # Added this because my template did not have these types....
    # c_atoms = ['  CA  ', '  CE3 ', '  CZ2 ', '  CB  ', '  CE  ', '  CD2 ', '  CD  ', '  CH2 ', '  CG1 ', '  CG  ',
    #            '  CD1 ', '  CZ3 ', '  CE1 ', '  CE2 ', '  CZ  ', '  CG2 ', '  C   ']
    # o_atoms = ['  OG1 ', '  OT2 ', '  OG  ', '  OE1 ', '  OH  ', '  OD1 ', '  OT1 ', '  O   ', '  OE2 ', '  OD2 ']
    # h_atoms = ['  HZ1 ', ' HD23 ', ' HG12 ', '  HD1 ', '  HE3 ', '  HA2 ', ' HD21 ', ' HH11 ', '  HG  ', '  HB2 ',
    #            '  HE  ', '  HE1 ', '  HT1 ', '  HT2 ', '  HA  ', ' HG11 ', ' HE21 ', '  HG2 ', '  HD3 ', '  HZ3 ',
    #            ' HG22 ', '  HB  ', '  HN  ', ' HD22 ', '  HA1 ', '  HE2 ', ' HE22 ', '  HB3 ', ' HD13 ', '  HD2 ',
    #            ' HH12 ', '  HH  ', ' HH22 ', '  HB1 ', ' HD11 ', '  HH2 ', '  HG1 ', '  HT3 ', ' HD12 ', ' HH21 ',
    #            ' HG21 ', '  HZ  ', '  HZ2 ', ' HG13 ', ' HG23 ']
    # n_atoms = ['  ND1 ', '  NH2 ', '  N   ', '  NE2 ', '  ND2 ', '  NE1 ', '  NH1 ', '  NE  ', '  NZ  ']
    # s_atoms = ['  SD  ', '  SG  ']

    with open(tpl_loc) as f:
        wat_count = 0
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            line_head = line[:cfg[PDB_LINE_TYPE_LAST_CHAR]]

            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if line_head == 'REMARK' or line_head == 'CRYST1':
                tpl_data[HEAD_CONTENT].append(line)

            # atoms_content to contain everything but the xyz
            elif line_head == 'ATOM  ':

                # My template PDB has ***** after atom_count 99999. Thus, I'm renumbering. Otherwise, this this:
                # atom_num = line[cfg[PDB_LINE_TYPE_LAST_CHAR]:cfg[PDB_ATOM_NUM_LAST_CHAR]]
                # For renumbering, making sure prints in the correct format, including num of characters:
                atom_count += 1

                # Allow for reordering
                if atom_count in atom_num_dict:
                    atom_id = atom_num_dict[atom_count]
                else:
                    atom_id = atom_count

                if atom_id > 99999:
                    atom_num = format(atom_id, 'x')
                else:
                    atom_num = '{:5d}'.format(atom_id)

                atom_type = line[cfg[PDB_ATOM_NUM_LAST_CHAR]:cfg[PDB_ATOM_TYPE_LAST_CHAR]]
                res_type = line[cfg[PDB_ATOM_TYPE_LAST_CHAR]:cfg[PDB_RES_TYPE_LAST_CHAR]]
                mol_num = int(line[cfg[PDB_RES_TYPE_LAST_CHAR]:cfg[PDB_MOL_NUM_LAST_CHAR]])
                pdb_x = float(line[cfg[PDB_MOL_NUM_LAST_CHAR]:cfg[PDB_X_LAST_CHAR]])
                pdb_y = float(line[cfg[PDB_X_LAST_CHAR]:cfg[PDB_Y_LAST_CHAR]])
                pdb_z = float(line[cfg[PDB_Y_LAST_CHAR]:cfg[PDB_Z_LAST_CHAR]])
                last_cols = line[cfg[PDB_Z_LAST_CHAR]:]
                element = ''

                # if atom_count < last_prot_atom:
                #     print([last_cols])
                if atom_count > last_prot_atom:
                    if (wat_count % 3) == 0:
                        current_mol = mol_num
                        if atom_type != '  OH2 ':
                            print("erzors!")
                        # last_cols = '  0.00  0.00      S2   O'
                    else:
                        if current_mol != mol_num:
                            print('water not in order', line_struct)
                        if (wat_count % 3) == 1:
                            if atom_type != '  H1  ':
                                print("erzors!")
                        else:
                            if atom_type != '  H2  ':
                                print("erzors!")
                        # last_cols = '  0.00  0.00      S2   H'
                    wat_count += 1

                    # if atom_count <= last_prot_atom:
                    #     print(atom_type)
                    # if atom_type in c_atoms:
                    #     element = '   C'
                    # elif atom_type in o_atoms:
                    #     element = '   O'
                    # elif atom_type in h_atoms:
                    #     element = '   H'
                    # elif atom_type in n_atoms:
                    #     element = '   N'
                    # elif atom_type in s_atoms:
                    #     element = '   S'
                    # else:
                    #     raise InvalidDataError('Please add atom type {} to dictionary of elements.'.format(atom_type))

                # # For renumbering molecules
                # # If this is wanted, need to handle when molid must switch to hex; probably make
                # # a new variable for sending to line structure that is a string, as done with atom
                # # number, switch to hex at 9999 molecules.
                # if last_mol_num is None:
                #     last_mol_num = mol_num
                #     new_mol_num = mol_num
                #     print(new_mol_num)
                # if mol_num == last_mol_num:
                #     continue
                # else:
                #     new_mol_num += 1
                #     print(mol_num,new_mol_num)
                # last_mol_num = mol_num
                # mol_num = new_mol_num
                line_struct = [line_head, atom_num, atom_type, res_type, mol_num, pdb_x, pdb_y, pdb_z,
                               last_cols + element]
                atoms_content.append(line_struct)

            # tail_content to contain everything after the 'Atoms' section
            else:
                tpl_data[TAIL_CONTENT].append(line)

    if len(atom_num_dict) > 0:
        tpl_data[ATOMS_CONTENT] = sorted(atoms_content, key=lambda line: line[1])
    else:
        tpl_data[ATOMS_CONTENT] = atoms_content

    f_name = create_out_fname(cfg[PDB_NEW_FILE], base_dir=cfg[OUT_BASE_DIR])
    print_pdb(tpl_data[HEAD_CONTENT], tpl_data[ATOMS_CONTENT], tpl_data[TAIL_CONTENT],
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
        atom_num_dict = read_int_dict(cfg[ATOM_REORDER_FILE])
        process_pdb_tpl(cfg,atom_num_dict)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems with input information:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
