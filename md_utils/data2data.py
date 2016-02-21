#!/usr/bin/env python
"""
Creates pdb data files from lammps data files, given a template pdb file.
"""

from __future__ import print_function

import ConfigParser
import copy
import logging
import re
import csv
from md_utils.md_common import list_to_file, InvalidDataError, seq_list_to_file, create_out_suf_fname, warning, conv_raw_val, process_cfg
import sys
import argparse

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
DATA_TPL_FILE = 'data_tpl_file'
DATAS_FILE = 'data_list_file'
ATOM_TYPE_DICT_FILE = 'atom_type_dict_filename'
MAKE_DICT = 'make_dictionary_flag'

# data file info


# Defaults
DEF_CFG_FILE = 'data2data.ini'
# Set notation
DEF_CFG_VALS = {DATAS_FILE: 'data_list.txt', ATOM_TYPE_DICT_FILE: 'atom_type_dict_old_new.csv',
                MAKE_DICT: False,
}
REQ_KEYS = {DATA_TPL_FILE: str,
}

# From data template file
NUM_ATOMS = 'num_atoms'
HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'
ATOM_TYPE_DICT = 'atom_type_dict'
ATOM_ID_DICT = 'atom_id_dict'

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
    parser = argparse.ArgumentParser(description='Creates data files from lammps data in the format of a template data '
                                                 'file. The required input file provides the location of the '
                                                 'template file, a file with a list of data files to convert, and '
                                                 'a dictionary mapping old data types to new, to allow checks that the '
                                                 'order is the same in the files to convert and the template file.'
                                                 'Note: Dictionaries of data types can be made, **assuming the atom'
                                                 'numbers correspond**. The check on whether they do can be used to '
                                                 'make a list of which atom numbers require remapping.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini "
                                               "format. See the example file /test/test_data/data2data/data2data.ini. "
                                               "The default file name is data2data.ini, located in the "
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
    tpl_data[ATOM_ID_DICT] = {}
    section = SEC_HEAD
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    atoms_pat = re.compile(r"^Atoms.*")

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
                split_line = line.split()
                atom_num = int(split_line[0])
                mol_num = int(split_line[1])
                atom_type = int(split_line[2])
                charge = float(split_line[3])
                # Make space for xyz coords and periodic box id. Make them zeros.
                xyz_pbc_ids = [0.0, 0.0, 0.0, 0, 0, 0]
                # Read in CHARMM type info
                end = split_line[7:]
                # end = ' '.join(split_line[7:])
                # atom_struct = [atom_num, mol_num, atom_type, charge,end]
                # tpl_data[ATOMS_CONTENT].append(atom_struct)
                tpl_data[ATOMS_CONTENT].append([atom_num, mol_num, atom_type, charge] + xyz_pbc_ids + end)
                if len(tpl_data[ATOMS_CONTENT]) == tpl_data[NUM_ATOMS]:
                    section = SEC_TAIL
            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                tpl_data[TAIL_CONTENT].append(line)

    if logger.isEnabledFor(logging.DEBUG):
        print_data(tpl_data[HEAD_CONTENT], tpl_data[ATOMS_CONTENT], tpl_data[TAIL_CONTENT], 'reproduced.data')

    return tpl_data

def print_data(head, data, tail, f_name):
    list_to_file(head, f_name)
    seq_list_to_file(data, f_name, mode='a')
    list_to_file(tail, f_name, mode='a')
    return


def make_atom_dict(cfg, data_tpl_content):
    atoms_pat = re.compile(r"^Atoms.*")
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    # Don't want to change the original template data when preparing to print the new file:

    with open(cfg[DATAS_FILE]) as f:
        for data_file in f.readlines():
            data_file = data_file.strip()
            with open(data_file) as d:
                section = SEC_HEAD
                atom_id = 0
                num_atoms = None
                match_atom_type = {}

                for line in d.readlines():
                    line = line.strip()
                    # Only look for number of atoms in header, so know when to exit reading loop
                    if section == SEC_HEAD:
                        if atoms_pat.match(line):
                            section = SEC_ATOMS
                        elif num_atoms is None:
                            atoms_match = num_atoms_pat.match(line)
                            if atoms_match:
                                # regex is 1-based
                                num_atoms = int(atoms_match.group(1))
                    # atoms_content to contain only xyz; also perform some checking
                    elif section == SEC_ATOMS:
                        if len(line) == 0:
                            continue
                        split_line = line.split()

                        old_atom_type = int(split_line[2])
                        new_atom_type = data_tpl_content[ATOMS_CONTENT][atom_id][2]

                        # Making the dictionary
                        if old_atom_type in match_atom_type:
                            # Check that we don't have conflicting matching
                            if new_atom_type != match_atom_type[old_atom_type]:
                                print('error on line: ', line)
                        else:
                            match_atom_type[old_atom_type] = new_atom_type

                        atom_id += 1
                        # Check after addition because the counter started at 0
                        if atom_id == num_atoms:
                            # Since the tail will come only from the template, nothing more is needed.
                            break

            # Now that finished reading the file...

            # Write dictionary
            with open(cfg[ATOM_TYPE_DICT_FILE], 'w') as myfile:
                for line in match_atom_type.items():
                    myfile.write('%d,%d' % line + '\n')

            print('Completed making atom dictionary.')

    return match_atom_type


def process_data_files(cfg, data_tpl_content):
    atoms_pat = re.compile(r"^Atoms.*")
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    # Don't want to change the original template data when preparing to print the new file:
    new_data_section = copy.deepcopy(data_tpl_content[ATOMS_CONTENT])

    # Read in the dictionaries
    atom_type_dict_loc = cfg[ATOM_TYPE_DICT_FILE]
    atom_type_dict = {}
    # TODO: make it okay if it does not exist, and then just don't do checking
    with open(atom_type_dict_loc) as csvfile:
        for line in csv.reader(csvfile):
            try:
                atom_type_dict[int(line[0])] = int(line[1])
            except ValueError as e:
                logger.debug("Could not convert line %s of file %s to two integers.", line, csvfile)

    with open(cfg[DATAS_FILE]) as f:
        for data_file in f.readlines():
            data_file = data_file.strip()
            with open(data_file) as d:
                section = SEC_HEAD
                atom_id = 0
                num_atoms = None
                for line in d.readlines():
                    line = line.strip()
                    # not keeping anything from the header
                    if section == SEC_HEAD:
                        if atoms_pat.match(line):
                            section = SEC_ATOMS
                        elif num_atoms is None:
                            atoms_match = num_atoms_pat.match(line)
                            if atoms_match:
                                # regex is 1-based
                                num_atoms = int(atoms_match.group(1))
                                if num_atoms != len(data_tpl_content[ATOMS_CONTENT]):
                                    raise InvalidDataError('The number of atoms listed in the data file {} ({}) does ' \
                                                           'not equal the number of atoms in the template file ({}).'.format(
                                        num_atoms, len(data_tpl_content[ATOMS_CONTENT]), data_file))
                    # atoms_content to grab xyz and pbc rep; also perform some checking
                    elif section == SEC_ATOMS:
                        if len(line) == 0:
                            continue
                        split_line = line.split()

                        # Not currently checking molecule number; the number may be wrong and the data still correct,
                        # because of the reordering I did to match the template ordering.
                        # Thus, I don't need:
                        # mol_num = int(split_line[1])

                        # Perform checking that the atom type in the corresponding line of the template file matches
                        # the curent file
                        old_atom_type = int(split_line[2])
                        new_atom_type = data_tpl_content[ATOMS_CONTENT][atom_id][2]
                        matching_new_atom_type = atom_type_dict[old_atom_type]

                        if new_atom_type != matching_new_atom_type:
                            print('Data mismatch on (base 1) atom_id : ', atom_id + 1,
                                  'The template file line and current file lines are:')
                            print(data_tpl_content[ATOMS_CONTENT][atom_id])
                            print(line)
                            print('')
                            # Add in the xyz coordinates and pbc ids
                        new_data_section[atom_id][4:10] = map(float, split_line[4:7]) + map(int, split_line[7:10])
                        atom_id += 1
                        # Check after increment because the counter started at 0
                        if atom_id == num_atoms:
                            # Since the tail will come only from the template, nothing more is needed.
                            break

            # Now that finished reading the file...
            # Check total length
            # (will be wrong if got to tail before reaching num_atoms)
            if atom_id != num_atoms:
                raise InvalidDataError('The number of atoms read from the file {} ({}) does not equal ' \
                                       'the listed number of atoms ({}).'.format(data_file,atom_id, num_atoms))
            # Now make new file
            f_name = create_out_suf_fname(data_file, '_new', ext='.data')
            print_data(data_tpl_content[HEAD_CONTENT], new_data_section, data_tpl_content[TAIL_CONTENT],
                       f_name)
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

    # TODO, did not read in file correctly
    cfg[MAKE_DICT] = False


    try:
        data_tpl_content = process_data_tpl(cfg)
        if cfg[MAKE_DICT]:
            make_atom_dict(cfg, data_tpl_content)
        else:
            process_data_files(cfg, data_tpl_content)
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
