#!/usr/bin/env python
"""
Creates pdb data files from lammps data files, given a template pdb file.
"""

from __future__ import print_function
# noinspection PyCompatibility
import ConfigParser
from collections import defaultdict
import logging
import re
import sys
import argparse

from md_utils.md_common import InvalidDataError, warning, process_cfg

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('data2pdb')
logging.basicConfig(filename='data2pdb.log', filemode='w', level=logging.DEBUG)
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
# DATA_TPL_FILE = 'data_tpl_file'
DATA_FILES = 'data_list_file'
# ATOM_TYPE_DICT_FILE = 'atom_type_dict_filename'

# data file info


# Defaults
DEF_CFG_FILE = 'compare_data.ini'
# Set notation
DEF_CFG_VALS = {DATA_FILES: 'data_list.txt',
                }
REQ_KEYS = {}

# From data template file
NUM_ATOMS = 'num_atoms'
HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'
ATOM_TYPE_DICT = 'atom_type_dict'
ATOM_ID_DICT = 'atom_id_dict'

# For data template file processing
SEC_HEAD = 'head_section'
SEC_MASSES = 'masses_section'
SEC_PAIR_COEFF = 'pair_coeff_section'
SEC_ANGL_COEFF = 'angle_coeff_section'
SEC_IMPR_COEFF = 'improp_coeff_section'
SEC_DIHE_COEFF = 'dihe_coeff_section'
SEC_ATOMS = 'atoms_section'
SEC_BONDS = 'bonds_section'
SEC_ANGLS = 'angles_section'
SEC_DIHES = 'dihedrals_section'
SEC_IMPRS = 'impropers_section'
SEC_VELOS = 'velos_section'


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
    parser = argparse.ArgumentParser(description='Compares parts of data files to determine differences.')
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


def find_section_state(line, current_section):
    masses_pat = re.compile(r"^Masses.*")
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


def process_data_files(cfg):

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

    # Create dictionaries
    masses = {}
    pairs = {}
    angl_coef = {}
    dihe_coef = {}
    impr_coef = {}
    atoms = {}
    # No unique key for the following
    bonds = defaultdict(list)
    angls = defaultdict(list)
    dihes = defaultdict(list)
    imprs = defaultdict(list)

    first_file = True
    with open(cfg[DATA_FILES]) as f:
        for data_file in f.readlines():
            data_file = data_file.strip()
            with open(data_file) as d:
                section = SEC_HEAD
                num_atoms = None
                num_bonds = None
                num_angls = None
                num_dihes = None
                num_imprs = None
                num_atom_typ = None
                num_bond_typ = None
                num_angl_typ = None
                num_dihe_typ = None
                num_impr_typ = None
                count = 0
                for line in d.readlines():
                    line = line.strip()
                    if len(line) == 0:
                        continue
                    if section is None:
                        section = find_section_state(line, section)
                        count = 0
                        continue
                    elif section == SEC_HEAD:
                        section = find_section_state(line, section)
                        if section != SEC_HEAD:
                            # TODO: check if any of the numbers are missing
                            continue
                        if num_atoms is None:
                            atoms_match = num_atoms_pat.match(line)
                            if atoms_match:
                                # regex is 1-based
                                num_atoms = int(atoms_match.group(1))
                        if num_atom_typ is None:
                            atom_match = num_atom_typ_pat.match(line)
                            if atom_match:
                                # regex is 1-based
                                num_atom_typ = int(atom_match.group(1))
                        if num_bonds is None:
                            bonds_match = num_bonds_pat.match(line)
                            if bonds_match:
                                # regex is 1-based
                                num_bonds = int(bonds_match.group(1))
                        if num_bond_typ is None:
                            bond_match = num_bond_typ_pat.match(line)
                            if bond_match:
                                # regex is 1-based
                                num_bond_typ = int(bond_match.group(1))
                        if num_angls is None:
                            angls_match = num_angl_pat.match(line)
                            if angls_match:
                                # regex is 1-based
                                num_angls = int(angls_match.group(1))
                        if num_angl_typ is None:
                            angl_match = num_angl_typ_pat.match(line)
                            if angl_match:
                                # regex is 1-based
                                num_angl_typ = int(angl_match.group(1))
                        if num_dihes is None:
                            dihes_match = num_dihe_pat.match(line)
                            if dihes_match:
                                # regex is 1-based
                                num_dihes = int(dihes_match.group(1))
                        if num_dihe_typ is None:
                            dihe_match = num_dihe_typ_pat.match(line)
                            if dihe_match:
                                # regex is 1-based
                                num_dihe_typ = int(dihe_match.group(1))
                        if num_imprs is None:
                            imprs_match = num_impr_pat.match(line)
                            if imprs_match:
                                # regex is 1-based
                                num_imprs = int(imprs_match.group(1))
                        if num_impr_typ is None:
                            impr_match = num_impr_typ_pat.match(line)
                            if impr_match:
                                # regex is 1-based
                                num_impr_typ = int(impr_match.group(1))
                    elif section == SEC_MASSES:
                        count += 1
                        split_line = line.split()
                        if first_file:
                            masses[split_line[0]] = split_line[1]
                        else:
                            if split_line[0] in masses:
                                if masses[split_line[0]] != split_line[1]:
                                    print(count, num_atom_typ)
                                    print('Error: masses to not match for line: ', line)
                                    print(masses[split_line[0]], split_line[1])
                                    break
                            else:
                                print('Key for this line does not match first file:', line)
                        # Check after increment because the counter started at 0

                        if count == num_atom_typ:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_PAIR_COEFF:
                        count += 1
                        split_line = line.split()
                        pair_line = map(float, split_line[1:5])
                        pair_line = [round(x, 5) for x in pair_line]
                        if first_file:
                            pairs[split_line[0]] = pair_line
                        else:
                            if split_line[0] in pairs:
                                if pairs[split_line[0]] != pair_line:
                                    print('Error: masses to not match for line: ', line)
                                    print(pairs[split_line[0]], split_line[1:5])
                                    break
                            else:
                                print('Key for this line does not match first file:', line)
                        # Check after increment because the counter started at 0
                        if count == num_atom_typ:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_ANGL_COEFF:
                        count += 1
                        split_line = line.split()
                        angl_line = map(float, split_line[1:5])
                        angl_line = [round(x, 3) for x in angl_line]
                        if first_file:
                            angl_coef[split_line[0]] = angl_line
                        else:
                            if split_line[0] in angl_coef:
                                if angl_coef[split_line[0]] != angl_line:
                                    warning('Error: mismatch on line: {}\n{} {}'.format(line,
                                                                                        angl_coef[split_line[0]],
                                                                                        angl_line))
                                    break
                            else:
                                warning('Key for this line does not match first file: {}'.format(line))
                                break
                        # Check after increment because the counter started at 0
                        if count == num_angl_typ:
                            print('Completed reading section {}'.format(section))
                            section = None
                    elif section == SEC_ATOMS:
                        count += 1
                        split_line = line.split()
                        # atoms_line = map(int,split_line[1:3]) + [round(x, 4) for x in  map(float,split_line[3:7])]
                        atom_id = split_line[0]
                        # noinspection PyTypeChecker
                        atoms_line = map(int, split_line[1:3]) + [round(float(split_line[3]), 4)]
                        if first_file:
                            atoms[atom_id] = atoms_line
                        else:
                            if split_line[0] in atoms:
                                if atoms[atom_id] != atoms_line:
                                    warning("check atom id {}. First file has type '{}' while second has '{}'"
                                            ".".format(atom_id, atoms[atom_id], atoms_line))
                            else:
                                warning('Key for this line does not match first file:\n{}\n{}{}'
                                        ''.format(atoms_line, atom_id, atoms[atom_id]))
                        # Check after increment because the counter started at 0
                        if count == num_atoms:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_BONDS:
                        count += 1
                        split_line = line.split()
                        bond_type = int(split_line[1])
                        bond_line = map(int, split_line[2:4])
                        if first_file:
                            bonds[bond_type].append(bond_line)
                        else:
                            if bond_type in bonds:
                                if bond_line not in bonds[bond_type]:
                                    print('Did not find listing in first file:', bond_type, bond_line)
                            else:
                                print('Did not find listing in first file:', bond_type, bond_line)
                        if count == num_bonds:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_ANGLS:
                        count += 1
                        split_line = line.split()
                        angle_type = int(split_line[1])
                        angls_line = map(int, split_line[2:5])
                        if first_file:
                            angls[angle_type].append(angls_line)
                        else:
                            if angle_type in angls:
                                if angls_line not in angls[angle_type]:
                                    print('Did not find listing in first file:', angle_type, angls_line)
                            else:
                                print('Did not find listing in first file:', angle_type, angls_line)
                        # if count == nums_dict[NUM_ANGLS]:
                        if count == num_angls:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_DIHE_COEFF:
                        count += 1
                        split_line = line.split()
                        dihe_line = [round(x, 3) for x in map(float, split_line[1:5])]
                        if first_file:
                            dihe_coef[split_line[0]] = dihe_line
                        else:
                            if split_line[0] in dihe_coef:
                                if dihe_coef[split_line[0]] != dihe_line:
                                    print('Error: mismatch on line: ', line)
                                    print(dihe_coef[split_line[0]], dihe_line)
                                    break
                            else:
                                print('Key for this line does not match first file:', line)
                                break
                        # Check after increment because the counter started at 0
                        if count == num_dihe_typ:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_DIHES:
                        count += 1
                        split_line = line.split()
                        dihe_type = int(split_line[1])
                        dihes_line = map(int, split_line[2:6])
                        if first_file:
                            dihes[dihe_type].append(dihes_line)
                        else:
                                if dihe_type in dihes:
                                    if dihes_line not in dihes[dihe_type]:
                                        print('Did not find listing in first file:', dihe_type, dihes_line)
                                else:
                                    print('Did not find listing in first file:', dihe_type, dihes_line)
                        if count == num_dihes:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_IMPR_COEFF:
                        count += 1
                        split_line = line.split()
                        impr_line = map(float, split_line[1:3])
                        impr_line = [round(x, 3) for x in impr_line]
                        if first_file:
                            impr_coef[split_line[0]] = impr_line
                        else:
                            if split_line[0] in impr_coef:
                                if impr_coef[split_line[0]] != impr_line:
                                    print('Error: mismatch on line: ', line)
                                    print(impr_coef[split_line[0]], impr_line)
                                    break
                            else:
                                print('Key for this line does not match first file:', line)
                                break
                        if count == num_impr_typ:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_IMPRS:
                        count += 1
                        split_line = line.split()
                        impr_type = int(split_line[1])
                        imprs_line = map(int, split_line[2:6])
                        if first_file:
                            imprs[impr_type].append(imprs_line)
                        else:
                            if impr_type in imprs:
                                if imprs_line not in imprs[impr_type]:
                                    print('Did not find listing in first file:', impr_type, imprs_line)
                            else:
                                print('Did not find listing in first file:', impr_type, imprs_line)
                        if count == num_imprs:
                            print('Completed reading', section)
                            # for index,item in enumerate(imprs):
                            #     item_split = item.split()
                            #     if '14006' in item_split:
                            #         print(item)
                            section = None
                    # Don't need to compare velocities
                    elif section == SEC_VELOS:
                        count += 1
                        if count == num_atoms:
                            print('Completed reading', section)
                            section = None
            first_file = False
            # print(num_atoms, num_bonds, num_angls, num_dihes, num_imprs)
            print('Completed reading {}.\n'.format(data_file))


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
        warning("Problems reading data template:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
