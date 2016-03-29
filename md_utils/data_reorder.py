#!/usr/bin/env python
"""
Reorders a lammps data file
"""

from __future__ import print_function

import ConfigParser
import logging
import re
import csv
from md_utils.md_common import list_to_file, InvalidDataError, create_out_fname, warning, conv_raw_val, process_cfg
import sys
import argparse

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('reorder_lammps_data')
logging.basicConfig(filename='reorder_lammps_data.log', filemode='w', level=logging.DEBUG)
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
DATAS_FILE = 'data_list_file'
ATOM_ID_DICT_FILE = 'atom_reorder_dict_filename'

# data file info


# Defaults
DEF_CFG_FILE = 'data_reorder.ini'
# Set notation
DEF_CFG_VALS = {DATAS_FILE: 'data_list.txt',
                ATOM_ID_DICT_FILE: 'reorder_old_new.csv',
                }
REQ_KEYS = {
             }

# For data template file processing
SEC_HEAD = 'head_section'
SEC_MASSES = 'masses_section'
SEC_PAIR_COEFF = 'pair_coeff_section'
SEC_BOND_COEFF = 'bond_coeff_section'
SEC_ANGL_COEFF = 'angle_coeff_section'
SEC_IMPR_COEFF = 'improp_coeff_section'
SEC_DIHE_COEFF = 'dihe_coeff_section'
SEC_ATOMS = 'atoms_section'
SEC_BONDS = 'bonds_section'
SEC_ANGLS = 'angles_section'
SEC_DIHES = 'dihedrals_section'
SEC_IMPRS = 'impropers_section'
SEC_VELOS = 'velos_section'

NUM_ATOMS = 'num_atoms'
NUM_BONDS = 'num_bonds'
NUM_ANGLS = 'num_angls'
NUM_DIHES = 'num_dihes'
NUM_IMPRS = 'num_imprs'
NUM_ATOM_TYP = 'num_atom_typ'
NUM_BOND_TYP = 'num_bond_typ'
NUM_ANGL_TYP = 'num_angl_typ'
NUM_DIHE_TYP = 'num_dihe_typ'
NUM_IMPR_TYP = 'num_impr_typ'


def to_int_list(raw_val):
    return_vals = []
    for val in raw_val.split(','):
        return_vals.append(int(val.strip()))
    return return_vals


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
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reorders atom ids in a lammps data file, given a dictionary to reorder '
                                                 'the atoms (each line contains the old index (0-based) followed by the'
                                                 'new, in csv format.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format."
                                               "See the example file /test/test_data/data_reorder/data_reorder.ini. "
                                               "The default file name is data_reorder.ini, located in the "
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


def find_section_state(line, current_section):
    masses_pat = re.compile(r"^Masses.*")
    bond_pat = re.compile(r"^Bond Coe.*")
    pair_pat = re.compile(r"^Pair Coe.*")
    angl_pat = re.compile(r"^Angle Coe.*")
    dihe_pat = re.compile(r"^Dihedral Coe.*")
    impr_pat = re.compile(r"^Improper Coe.*")
    atoms_pat = re.compile(r"^Atoms.*")
    velos_pat = re.compile(r"^Velocities.*")
    bonds_pat = re.compile(r"^Bonds.*")
    angls_pat = re.compile(r"^Angles.*")
    dihes_pat = re.compile(r"^Dihedrals.*")
    imprs_pat = re.compile(r"^Impropers.*")
    if masses_pat.match(line):
        return SEC_MASSES
    elif pair_pat.match(line):
        return SEC_PAIR_COEFF
    elif bond_pat.match(line):
        return SEC_BOND_COEFF
    elif angl_pat.match(line):
        return SEC_ANGL_COEFF
    elif dihe_pat.match(line):
        return SEC_DIHE_COEFF
    elif impr_pat.match(line):
        return SEC_IMPR_COEFF
    elif atoms_pat.match(line):
        return SEC_ATOMS
    elif velos_pat.match(line):
        return SEC_VELOS
    elif bonds_pat.match(line):
        return SEC_BONDS
    elif angls_pat.match(line):
        return SEC_ANGLS
    elif dihes_pat.match(line):
        return SEC_DIHES
    elif imprs_pat.match(line):
        return SEC_IMPRS
    else:
        return current_section

def find_header_values(line, dict):
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    num_bonds_pat = re.compile(r"(\d+).*bonds$")
    num_angl_pat = re.compile(r"(\d+).*angles$")
    num_dihe_pat = re.compile(r"(\d+).*dihedrals$")
    num_impr_pat = re.compile(r"(\d+).*impropers$")

    num_atom_typ_pat = re.compile(r"(\d+).*atom types$")
    num_bond_typ_pat = re.compile(r"(\d+).*bond types$")
    num_angl_typ_pat = re.compile(r"(\d+).*angle types$")
    num_dihe_typ_pat = re.compile(r"(\d+).*dihedral types$")
    num_impr_typ_pat = re.compile(r"(\d+).*improper types$")

    if dict[NUM_ATOMS] is None:
        atoms_match = num_atoms_pat.match(line)
        if atoms_match:
            # regex is 1-based
            dict[NUM_ATOMS] = int(atoms_match.group(1))
            return
    if dict[NUM_ATOM_TYP] is None:
        atom_match = num_atom_typ_pat.match(line)
        if atom_match:
            # regex is 1-based
            dict[NUM_ATOM_TYP] = int(atom_match.group(1))
            return
    if dict[NUM_BONDS] is None:
        bonds_match = num_bonds_pat.match(line)
        if bonds_match:
            # regex is 1-based
            dict[NUM_BONDS] = int(bonds_match.group(1))
            return
    if dict[NUM_BOND_TYP] is None:
        bond_match = num_bond_typ_pat.match(line)
        if bond_match:
            # regex is 1-based
            dict[NUM_BOND_TYP] = int(bond_match.group(1))
            return
    if dict[NUM_ANGLS] is None:
        angls_match = num_angl_pat.match(line)
        if angls_match:
            # regex is 1-based
            dict[NUM_ANGLS] = int(angls_match.group(1))
            return
    if dict[NUM_ANGL_TYP] is None:
        angl_match = num_angl_typ_pat.match(line)
        if angl_match:
            # regex is 1-based
            dict[NUM_ANGL_TYP] = int(angl_match.group(1))
            return
    if dict[NUM_DIHES] is None:
        dihes_match = num_dihe_pat.match(line)
        if dihes_match:
            # regex is 1-based
            dict[NUM_DIHES] = int(dihes_match.group(1))
            return
    if dict[NUM_DIHE_TYP] is None:
        dihe_match = num_dihe_typ_pat.match(line)
        if dihe_match:
            # regex is 1-based
            dict[NUM_DIHE_TYP] = int(dihe_match.group(1))
            return
    if dict[NUM_IMPRS ] is None:
        imprs_match = num_impr_pat.match(line)
        if imprs_match:
            # regex is 1-based
            dict[NUM_IMPRS ] = int(imprs_match.group(1))
            return
    if dict[NUM_IMPR_TYP] is None:
        impr_match = num_impr_typ_pat.match(line)
        if impr_match:
            # regex is 1-based
            dict[NUM_IMPR_TYP] = int(impr_match.group(1))
            return



def process_data_files(cfg):

    atom_id_dict_loc = cfg[ATOM_ID_DICT_FILE]
    atom_id_dict = {}

    # Read in the reordering dictionary
    # Note: the dictionary is base 1.
    with open(atom_id_dict_loc) as csvfile:
        for line in csv.reader(csvfile):
            try:
                atom_id_dict[int(line[0])] = int(line[1])
            except ValueError as e:
                logger.debug("Could not convert line %s of file %s to two integers.", line, csvfile)
        print('Completed reading atom dictionary.')

    # Easier to pass when contained in a dictionary
    nums_dict = {}
    num_dict_headers = [NUM_ATOMS, NUM_ATOM_TYP, NUM_BONDS, NUM_BOND_TYP, NUM_ANGLS, NUM_ANGL_TYP,
                        NUM_DIHES, NUM_DIHE_TYP, NUM_IMPRS, NUM_IMPR_TYP]
    with open(cfg[DATAS_FILE]) as f:
        for data_file in f.readlines():
            data_file = data_file.strip()
            if len(data_file) == 0:
                continue
            with open(data_file) as d:
                section = SEC_HEAD
                count = 0
                for key in num_dict_headers:
                    nums_dict[key] = None
                head_content = []
                atoms_content = []
                tail_content = []
                reorder_data = {}
                # TODO: Make printing velocities an option
                # We are not printing velocities.
                last_read_velos = False
                # Now read the data
                for line in d.readlines():
                    line = line.strip()
                    if section is None:
                        section = find_section_state(line, section)
                        count = 0
                        if section == None:
                            # If we are skipping velocities and it was the last-read section, skip the buffer.
                            # Otherwise, add it to the head if haven't finished reading atoms, tail otherwise
                            if last_read_velos:
                               last_read_velos = False
                            elif len(atoms_content) < nums_dict[NUM_ATOMS]:
                                head_content.append(line)
                            else:
                                tail_content.append(line)
                            continue
                    # Not an elif because want to continue from above if section state changed
                    if section == SEC_HEAD:
                        head_content.append(line)
                        section = find_section_state(line, section)
                        if section == SEC_HEAD:
                            find_header_values(line,nums_dict)
                        else:
                            # Count starts at 1 because the title of the next section is already printed in the header
                            # For all the rest, it is not
                            count = 1
                            # Upon exiting header, made sure have all the data we need.
                            for key in nums_dict:
                                if key is None:
                                    raise InvalidDataError('Did not find a value for {} in the header of '
                                                           'file {}'.format(key, data_file))
                    elif section in [SEC_MASSES, SEC_PAIR_COEFF]:
                        head_content.append(line)
                        if count == nums_dict[NUM_ATOM_TYP]:
                            section = None
                        if len(line) != 0:
                            count += 1
                    elif section == SEC_BOND_COEFF:
                        head_content.append(line)
                        if count == nums_dict[NUM_BOND_TYP]:
                            section = None
                        if len(line) != 0:
                            count += 1
                    elif section == SEC_ANGL_COEFF:
                        head_content.append(line)
                        if count == nums_dict[NUM_ANGL_TYP]:
                            section = None
                        if len(line) != 0:
                            count += 1
                    elif section == SEC_DIHE_COEFF:
                        head_content.append(line)
                        if count == nums_dict[NUM_DIHE_TYP]:
                            section = None
                        if len(line) != 0:
                            count += 1
                    elif section == SEC_IMPR_COEFF:
                        head_content.append(line)
                        if count == nums_dict[NUM_IMPR_TYP]:
                            section = None
                        if len(line) != 0:
                            count += 1
                    elif section == SEC_ATOMS:
                        if count == 0:
                            head_content.append(line)
                        else:
                            atoms_content.append(line)
                            if len(line) == 0:
                                continue
                            if count in atom_id_dict:
                                reorder_data[count] = line
                            if count == nums_dict[NUM_ATOMS]:
                                section = None
                        if len(line) != 0:
                            count += 1
                    elif section == SEC_VELOS:
                        # TODO: Don't really need velocities; They will be skipped. Not yet tested.
                        # split_line = line.split
                        # atom_id = int(split_line)
                        # if atom_id in atom_id_dict:
                        #     atom_id = atom_id_dict[atom_id]
                        # tail_content.append(' '.join([str(atom_id)]+ split_line[1:]))
                        last_read_velos = True
                        if count == nums_dict[NUM_ATOMS]:
                            section = None
                        if len(line) != 0:
                            count += 1
                    elif section == SEC_BONDS:
                        if count == nums_dict[NUM_BONDS]:
                            section = None
                        if len(line) == 0:
                            tail_content.append(line)
                        else:
                            split_line = line.split()
                            atoms  = map(int,split_line[2:4])
                            new_atoms = atoms
                            for id,atom_id in enumerate(atoms):
                                if atom_id in atom_id_dict:
                                    new_atoms[id] = atom_id_dict[atom_id]
                                else:
                                    new_atoms[id] = atom_id
                            tail_content.append(' '.join(split_line[0:2] + map(str,new_atoms) + split_line[4:]))
                            count += 1
                    elif section == SEC_ANGLS:
                        if count == nums_dict[NUM_ANGLS]:
                            section = None
                        if len(line) == 0:
                            tail_content.append(line)
                        else:
                            split_line = line.split()
                            atoms  = map(int,split_line[2:5])
                            new_atoms = atoms
                            for id,atom_id in enumerate(atoms):
                                if atom_id in atom_id_dict:
                                    new_atoms[id] = atom_id_dict[atom_id]
                                else:
                                    new_atoms[id] = atom_id
                            tail_content.append(' '.join(split_line[0:2] + map(str,new_atoms) + split_line[5:]))
                            count += 1
                    elif section == SEC_DIHES:
                        if count == nums_dict[NUM_DIHES]:
                            section = None
                        if len(line) == 0:
                            tail_content.append(line)
                        else:
                            split_line = line.split()
                            atoms = map(int,split_line[2:6])
                            new_atoms = atoms
                            for id,atom_id in enumerate(atoms):
                                if atom_id in atom_id_dict:
                                    new_atoms[id] = atom_id_dict[atom_id]
                                else:
                                    new_atoms[id] = atom_id
                            tail_content.append(' '.join(split_line[0:2] + map(str,new_atoms) + split_line[6:]))
                            count += 1
                    elif section == SEC_IMPRS:
                        if count == nums_dict[NUM_IMPRS]:
                            section = None
                        if len(line) == 0:
                            tail_content.append(line)
                        else:
                            split_line = line.split()
                            atoms  = map(int,split_line[2:6])
                            new_atoms = atoms
                            for id,atom_id in enumerate(atoms):
                                if atom_id in atom_id_dict:
                                    new_atoms[id] = atom_id_dict[atom_id]
                                else:
                                    new_atoms[id] = atom_id
                            tail_content.append(' '.join(split_line[0:2] + map(str,new_atoms) + split_line[6:]))
                            count += 1
                    else:
                        tail_content.append(line)
                        print("Note: unexpected content added to end of file:", line)

            # Now that finished reading the file...
            # Do any necessary reordering
            for atom in reorder_data:
                atoms_content[atom_id_dict[atom]] = reorder_data[atom]
            # renumber atoms:
            renumbered = ['']
            new_atom_id = 1
            # new_mapping = []
            for line in atoms_content:
                if len(line) != 0:
                    split_line = line.split()
                    # old_atom_id = int(split_line[0])
                    # if old_atom_id != new_atom_id:
                    #     new_mapping.append([old_atom_id,new_atom_id])
                    renumbered.append(' '.join([str(new_atom_id)]+split_line[1:]))
                    new_atom_id += 1

            # # Write dictionary
            # with open('new_mapping.csv', 'w') as myfile:
            #     for line in new_mapping:
            #         myfile.write('%d,%d' % tuple(line) + '\n')

            f_name = create_out_fname(data_file, suffix='_ord', ext='.data')
            list_to_file(head_content+renumbered+tail_content, f_name)
            print('Completed writing {}'.format(f_name))
    return

def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    # TODO: did not show the expected behavior when I didn't have a required cfg in the ini file
    if ret != GOOD_RET:
        return ret

    # Read template and data files
    cfg = args.config
    try:
        process_data_files(cfg)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading file:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
