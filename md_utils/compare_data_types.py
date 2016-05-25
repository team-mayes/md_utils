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
import csv
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
DATA_FILES = 'data_list_file'
ATOM_TYPE_DICT_FILE = 'atom_type_dict_filename'
BOND_TYPE_DICT_FILE = 'bond_type_dict_filename'
ANGL_TYPE_DICT_FILE = 'angle_type_dict_filename'
DIHE_TYPE_DICT_FILE = 'dihe_type_dict_filename'
IMPR_TYPE_DICT_FILE = 'impr_type_dict_filename'
MAKE_DICT = 'make_dictionary_flag'

# Defaults
DEF_CFG_FILE = 'compare_data_types.ini'
# Set notation
DEF_CFG_VALS = {DATA_FILES: 'data_list.txt', MAKE_DICT: False,
                ATOM_TYPE_DICT_FILE: 'atom_type_dict_old_new.csv',
                BOND_TYPE_DICT_FILE: 'bond_type_dict_old_new.csv',
                ANGL_TYPE_DICT_FILE: 'angle_type_dict_old_new.csv',
                DIHE_TYPE_DICT_FILE: 'dihe_type_dict_old_new.csv',
                IMPR_TYPE_DICT_FILE: 'impr_type_dict_old_new.csv',
                }
REQ_KEYS = {}

# From data file
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
    parser = argparse.ArgumentParser(description='Compares parameters (i.e. bond coeffs) of data files to '
                                                 'determine differences. The first is read to align with the first'
                                                 'column in the dictionary; the rest to the second.')
    parser.add_argument("-c", "--config", help='The location of the configuration file in ini format. See the '
                                               'example file /test/test_data/evbd2d/compare_data_types.ini. '
                                               'The default file name is compare_data_types.ini, located in the '
                                               'base directory where the program as run.',
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


def read_2int_dict(dict_file):
    """ Reads a two-field csv of integer values from dictionary and passes back as a dictionary
    """
    two_item_dict = {}
    with open(dict_file) as csv_file:
        for line in csv.reader(csv_file):
            if len(line) == 0:
                continue
            if len(line) != 2:
                raise ValueError('Expected two entries per line on dictionary file file {}'.format(csv_file))
            try:
                two_item_dict[int(line[0])] = int(line[1])
            except ValueError:
                warning("Could not convert line the following line to two integers: {}\n "
                        "in file: {}".format(line, csv_file))
    return two_item_dict


def find_header_values(line, num_dict):
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

    if num_dict[NUM_ATOMS] is None:
        atoms_match = num_atoms_pat.match(line)
        if atoms_match:
            # regex is 1-based
            num_dict[NUM_ATOMS] = int(atoms_match.group(1))
            return
    if num_dict[NUM_ATOM_TYP] is None:
        atom_match = num_atom_typ_pat.match(line)
        if atom_match:
            # regex is 1-based
            num_dict[NUM_ATOM_TYP] = int(atom_match.group(1))
            return
    if num_dict[NUM_BONDS] is None:
        bonds_match = num_bonds_pat.match(line)
        if bonds_match:
            # regex is 1-based
            num_dict[NUM_BONDS] = int(bonds_match.group(1))
            return
    if num_dict[NUM_BOND_TYP] is None:
        bond_match = num_bond_typ_pat.match(line)
        if bond_match:
            # regex is 1-based
            num_dict[NUM_BOND_TYP] = int(bond_match.group(1))
            return
    if num_dict[NUM_ANGLS] is None:
        angls_match = num_angl_pat.match(line)
        if angls_match:
            # regex is 1-based
            num_dict[NUM_ANGLS] = int(angls_match.group(1))
            return
    if num_dict[NUM_ANGL_TYP] is None:
        angl_match = num_angl_typ_pat.match(line)
        if angl_match:
            # regex is 1-based
            num_dict[NUM_ANGL_TYP] = int(angl_match.group(1))
            return
    if num_dict[NUM_DIHES] is None:
        dihes_match = num_dihe_pat.match(line)
        if dihes_match:
            # regex is 1-based
            num_dict[NUM_DIHES] = int(dihes_match.group(1))
            return
    if num_dict[NUM_DIHE_TYP] is None:
        dihe_match = num_dihe_typ_pat.match(line)
        if dihe_match:
            # regex is 1-based
            num_dict[NUM_DIHE_TYP] = int(dihe_match.group(1))
            return
    if num_dict[NUM_IMPRS] is None:
        imprs_match = num_impr_pat.match(line)
        if imprs_match:
            # regex is 1-based
            num_dict[NUM_IMPRS] = int(imprs_match.group(1))
            return
    if num_dict[NUM_IMPR_TYP] is None:
        impr_match = num_impr_typ_pat.match(line)
        if impr_match:
            # regex is 1-based
            num_dict[NUM_IMPR_TYP] = int(impr_match.group(1))
            return


def print_2int_dict(file_name, dict_list):
    with open(file_name, 'w') as d_file:
        # noinspection PyCompatibility
        for key, value in dict_list.iteritems():
            d_file.write('%d,%d' % (key, value) + '\n')


def process_data_files(cfg):
    # Create dictionaries

    nums_dict = {}
    num_dict_headers = [NUM_ATOMS, NUM_ATOM_TYP, NUM_BONDS, NUM_BOND_TYP, NUM_ANGLS, NUM_ANGL_TYP,
                        NUM_DIHES, NUM_DIHE_TYP, NUM_IMPRS, NUM_IMPR_TYP]

    # TODO Fix flag reading
    # cfg[MAKE_DICT] = False

    if cfg[MAKE_DICT]:
        atoms = {}
        atom_match = {}
        bonds = {}
        bond_match = {}
        angls = {}
        angle_match = {}
        # dihes can have more than one type assigned.
        dihes = defaultdict(list)
        dihe_match = defaultdict(set)
        dihe_dict = {}
        imprs = {}
        impr_match = {}
    else:
        masses = {}
        pairs = {}
        angl_coef = {}
        dihe_coef = {}
        impr_coef = {}
        atom_type_dict = read_2int_dict(cfg[ATOM_TYPE_DICT_FILE])
        # bond_type_dict = read_2int_dict(cfg[BOND_TYPE_DICT_FILE])
        angl_type_dict = read_2int_dict(cfg[ANGL_TYPE_DICT_FILE])
        dihe_type_dict = read_2int_dict(cfg[DIHE_TYPE_DICT_FILE])
        impr_type_dict = read_2int_dict(cfg[IMPR_TYPE_DICT_FILE])

    first_file = True
    with open(cfg[DATA_FILES]) as f:
        for data_file in f.readlines():
            data_file = data_file.strip()
            with open(data_file) as d:
                # Variables to initialize for each data file
                section = SEC_HEAD
                count = 0
                for key in num_dict_headers:
                    nums_dict[key] = None
                    # Now read the data
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
                            for key in nums_dict:
                                if key is None:
                                    raise InvalidDataError('Did not find a value for {} in the header of '
                                                           'file {}'.format(key, data_file))
                            continue
                        find_header_values(line, nums_dict)
                    elif section == SEC_MASSES:
                        count += 1
                        if not(cfg[MAKE_DICT]):
                            split_line = line.split()
                            atom_type = int(split_line[0])
                            mass = float(split_line[1])
                            if first_file:
                                if atom_type in atom_type_dict:
                                    new_atom_type = atom_type_dict[atom_type]
                                    masses[new_atom_type] = mass
                                else:
                                    print('atom type {} does not appear in the dictionary. Its mass is {}:'.format(
                                        atom_type, mass))
                            else:
                                if atom_type in masses:
                                    if masses[atom_type] != mass:
                                        print('Masses do not match for new data type: ', atom_type)
                                        print('   Expected {}; found {}.'.format(masses[atom_type], mass))
                                else:
                                    print('Did not find this atom type in the dictionary:', line)
                                    # Check after increment because the counter started at 0
                        if count == nums_dict[NUM_ATOM_TYP]:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_PAIR_COEFF:
                        count += 1
                        if not(cfg[MAKE_DICT]):
                            split_line = line.split()
                            atom_type = int(split_line[0])
                            pair_line = map(float, split_line[1:5])
                            pair_line = [round(x, 5) for x in pair_line]
                            if first_file:
                                if atom_type in atom_type_dict:
                                    new_atom_type = atom_type_dict[atom_type]
                                    pairs[new_atom_type] = pair_line
                                else:
                                    print('atom type {} does not appear in the dictionary. Its coeffs are {}:'.format(
                                        atom_type, pair_line))
                            else:
                                if atom_type in pairs:
                                    if pairs[atom_type] != pair_line:
                                        print('Error: pair types do not match for line: ', line)
                                        print(pairs[atom_type], split_line[1:5])
                                        break
                                else:
                                    print('Key for this line does not match first file:', line)
                                    # Check after increment because the counter started at 0
                        if count == nums_dict[NUM_ATOM_TYP]:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_ANGL_COEFF:
                        count += 1
                        if not(cfg[MAKE_DICT]):
                            split_line = line.split()
                            angle_type = int(split_line[0])
                            angl_line = map(float, split_line[1:5])
                            angl_line = [round(x, 3) for x in angl_line]
                            if first_file:
                                if angle_type in angl_type_dict:
                                    new_angl_type = angl_type_dict[angle_type]
                                    angl_coef[new_angl_type] = angl_line
                                else:
                                    print('Angl type {} does not appear in the dictionary. Its coeff are {}:'
                                          ''.format(angle_type, angl_line))
                            else:
                                if angle_type in angl_coef:
                                    if angl_coef[angle_type] != angl_line:
                                        print('Error: mismatch on line: ', line)
                                        print(angl_coef[angle_type], angl_line)
                                        break
                                else:
                                    print('Key for this line does not match first file:', line)
                                    break
                        if count == nums_dict[NUM_ANGL_TYP]:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_DIHE_COEFF:
                        count += 1
                        if not(cfg[MAKE_DICT]):
                            split_line = line.split()
                            dihe_type = int(split_line[0])
                            dihe_line = map(float, split_line[1:5])
                            dihe_line = [round(x, 3) for x in dihe_line]
                            if first_file:
                                if dihe_type in dihe_type_dict:
                                    new_dihe_type = dihe_type_dict[dihe_type]
                                    dihe_coef[new_dihe_type] = dihe_line
                                else:
                                    print('Dihe type {} does not appear in the dictionary. Its coeff are: {}'.format(
                                        dihe_type, dihe_line))
                            else:
                                if dihe_type in dihe_coef:
                                    if dihe_coef[dihe_type] != dihe_line:
                                        print('Error: mismatch on line: ', line)
                                        print(dihe_coef[dihe_type], dihe_line)
                                        break
                                else:
                                    print('Dihe type {} does not appear in the dictionary. Its coeff are: {}'.format(
                                        dihe_type, dihe_line))
                        # Check after increment because the counter started at 0
                        if count == nums_dict[NUM_DIHE_TYP]:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_IMPR_COEFF:
                        count += 1
                        # TODO: Why am I not reading this section for the second file??
                        print('hello hello!')
                        if not(cfg[MAKE_DICT]):
                            split_line = line.split()
                            impr_type = int(split_line[0])
                            impr_line = map(float, split_line[1:3])
                            impr_line = [round(x, 3) for x in impr_line]
                            if first_file:
                                if impr_type in impr_type_dict:
                                    new_impr_type = impr_type_dict[impr_type]
                                    impr_coef[new_impr_type] = impr_line
                                else:
                                    print('impr type {} does not appear in the dictionary. Its coeff are: {}'.format(
                                        impr_type, impr_line))
                            else:
                                print(impr_type)
                                if impr_type in impr_coef:
                                    if impr_coef[impr_type] != impr_line:
                                        print('Error: mismatch on line: ', line)
                                        print(impr_coef[impr_type], impr_line)
                                        break
                                    else:
                                        print(impr_type, impr_line, impr_coef[impr_type], 'good')
                                else:
                                    print('impr type {} does not appear in the dictionary. Its coeff are: {}'.format(
                                        impr_type, impr_line))
                        if count == nums_dict[NUM_IMPR_TYP]:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_ATOMS:
                        count += 1
                        if cfg[MAKE_DICT]:
                            split_line = line.split()
                            atom_type = int(split_line[2])
                            atoms_id = int(split_line[0])
                            if first_file:
                                if atoms_id in atoms:
                                    print('Warning: non-unique atom id: ', atoms_id)
                                else:
                                    atoms[atoms_id] = atom_type
                            else:
                                if atoms_id in atoms:
                                    old_atom_type = atoms[atoms_id]
                                    # Have a match! If old_type in dictionary, not matched to a different new type, ok.
                                    # If not there yet, add to the dictionary.
                                    if old_atom_type in atom_match:
                                        if atom_type != atom_match[old_atom_type]:
                                            print('    conflict! on atom:', atoms_id)
                                            print('        matched to type {}, but expected {}.'.format(
                                                atom_match[old_atom_type], atom_type))
                                    else:
                                        atom_match[old_atom_type] = atom_type
                                else:
                                    # Don't have a match
                                    print('    Did not find atom listing in first file:', atom_type, atoms_id)
                        if count == nums_dict[NUM_ATOMS]:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_BONDS:
                        count += 1
                        if cfg[MAKE_DICT]:
                            split_line = line.split()
                            bond_type = int(split_line[1])
                            bonds_line = ' '.join(split_line[2:4])
                            if first_file:
                                if bonds_line in bonds:
                                    print('Warning: non-unique bond: ', bonds_line)
                                else:
                                    bonds[bonds_line] = bond_type
                            else:
                                opp_bonds_line = ' '.join([split_line[3], split_line[2]])
                                if (bonds_line in bonds) or (opp_bonds_line in bonds):
                                    if bonds_line in bonds:
                                        old_bond_type = bonds[bonds_line]
                                    else:
                                        old_bond_type = bonds[opp_bonds_line]
                                    # Have a match! If old_type in dictionary, not matched to a different new type, ok.
                                    # If not there yet, add to the dictionary.
                                    if old_bond_type in bond_match:
                                        # check that no conflict!
                                        if bond_type != bond_match[old_bond_type]:
                                            print('    conflict! on bond:', bonds_line)
                                            print('        matched to type {}, but expected {}.'.format(
                                                bond_match[old_bond_type], bond_type))
                                    else:
                                        bond_match[old_bond_type] = bond_type
                                else:
                                    # Don't have a match
                                    print('    Did not find bond listing in first file:', bond_type, bonds_line)
                        if count == nums_dict[NUM_BONDS]:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_ANGLS:
                        count += 1
                        if cfg[MAKE_DICT]:
                            split_line = line.split()
                            angle_type = int(split_line[1])
                            angls_line = ' '.join(split_line[2:5])
                            if first_file:
                                if angls_line in angls:
                                    print('Warning: non-unique angle: ', angls_line)
                                else:
                                    angls[angls_line] = angle_type
                            else:
                                opp_angls_line = ' '.join([split_line[4], split_line[3], split_line[2]])
                                if (angls_line in angls) or (opp_angls_line in angls):
                                    if angls_line in angls:
                                        old_angle_type = angls[angls_line]
                                    else:
                                        old_angle_type = angls[opp_angls_line]
                                    if old_angle_type in angle_match:
                                        if angle_type != angle_match[old_angle_type]:
                                            print('    conflict! on angle:', angls_line)
                                            print('        matched to type {}, but expected {}.'.format(
                                                angle_match[old_angle_type], angle_type))
                                    else:
                                        angle_match[old_angle_type] = angle_type
                                else:
                                    # Don't have a match
                                    print('    Did not find listing in first file:', angle_type, angls_line)
                        if count == nums_dict[NUM_ANGLS]:
                            print('Completed reading', section)
                            section = None
                    elif section == SEC_DIHES:
                        count += 1
                        if cfg[MAKE_DICT]:
                            split_line = line.split()
                            dihe_type = int(split_line[1])
                            dihes_line = ' '.join(split_line[2:6])
                            if first_file:
                                # More than one type can be assigned to the same dihedral
                                dihes[dihes_line].append(dihe_type)
                            else:
                                opp_dihes_line = ' '.join([split_line[5], split_line[4], split_line[3], split_line[2]])
                                if (dihes_line in dihes) or (opp_dihes_line in dihes):
                                    if dihes_line in dihes:
                                        old_dihe_type = dihes[dihes_line]
                                    else:
                                        old_dihe_type = dihes[opp_dihes_line]
                                    for item in old_dihe_type:
                                        dihe_match[item].add(dihe_type)
                                else:
                                    # Don't have a match
                                    print('    Did not find dihe listing in first file:', dihe_type, dihes_line)
                            if count == nums_dict[NUM_DIHES]:
                                for key in dihe_match:
                                    if key in dihe_match[key]:
                                        dihe_dict[key] = key
                                    else:
                                        print('New dihedral type for {}: {}'.format(key, dihe_match[key]))
                                print('Completed reading', section)
                                section = None
                    elif section == SEC_IMPRS:
                        count += 1
                        if cfg[MAKE_DICT]:
                            split_line = line.split()
                            impre_type = int(split_line[1])
                            imprs_line = ' '.join(split_line[2:6])
                            if first_file:
                                if imprs_line in imprs:
                                    print('Warning: non-unique impre: ', imprs_line)
                                else:
                                    imprs[imprs_line] = impre_type
                            else:
                                opp_imprs_line = ' '.join([split_line[5], split_line[4], split_line[3], split_line[2]])
                                if (imprs_line in imprs) or (opp_imprs_line in imprs):
                                    if imprs_line in imprs:
                                        old_impr_type = imprs[imprs_line]
                                    else:
                                        old_impr_type = imprs[opp_imprs_line]
                                    if old_impr_type in impr_match:
                                        if impre_type != impr_match[old_impr_type]:
                                            print('    conflict! on impr:', imprs_line)
                                            print('        matched to type {}, but expected {}.'.format(
                                                impr_match[old_impr_type], impre_type))
                                    else:
                                        impr_match[old_impr_type] = impre_type
                                else:
                                    # Don't have a match
                                    print('    Did not find impr listing in first file:', impre_type, imprs_line)
                        if count == nums_dict[NUM_IMPRS]:
                            print('Completed reading', section)
                            section = None
                    # Don't need to compare velocities
                    elif section == SEC_VELOS:
                        count += 1
                        if count == nums_dict[NUM_ATOMS]:
                            print('Completed reading', section)
                            section = None
            first_file = False
            if cfg[MAKE_DICT]:
                print_2int_dict(cfg[ATOM_TYPE_DICT_FILE], atom_match)
                print_2int_dict(cfg[BOND_TYPE_DICT_FILE], bond_match)
                print_2int_dict(cfg[ANGL_TYPE_DICT_FILE], angle_match)
                print_2int_dict(cfg[DIHE_TYPE_DICT_FILE], dihe_dict)
                print_2int_dict(cfg[IMPR_TYPE_DICT_FILE], impr_match)
            print('Completed reading', data_file)
            print('')
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
        if cfg[MAKE_DICT]:
            pass
            # TODO: use code from data2data to make atom type dict
            # data_tpl_content = process_data_tpl(cfg)
            # make_dict(cfg, data_tpl_content)
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
