#!/usr/bin/env python
"""
Creates pdb data files from lammps data files, given a template pdb file.
"""

from __future__ import print_function
import os
from collections import defaultdict
import copy
import json
import logging
import re
import sys
import argparse
from md_utils.md_common import (InvalidDataError, warning, process_cfg, create_out_fname, list_to_file, process_pdb_tpl,
                                HEAD_CONTENT, ATOMS_CONTENT, TAIL_CONTENT, PDB_FORMAT, NUM_ATOMS)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('data2pdb')
# logging.basicConfig(filename='data2pdb.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

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
DATA_FILES_FILE = 'data_list_file'
DATA_FILES = 'data_files_list'
DATA_FILE = 'data_file'
ATOM_TYPE_DICT_FILE = 'atom_type_dict_file'
CENTER_ATOM = 'center_to_atom_num'

LAST_PROT_ID = 'last_prot_atom'
OUT_BASE_DIR = 'output_directory'
MAKE_DICT_BOOL = 'make_dictionary_flag'
CHECK_ATOM_TYPE = 'use_atom_dict_flag'

ATOMS_PAT = re.compile(r"^Atoms.*")
NUM_ATOMS_PAT = re.compile(r"(\d+).*atoms$")

# data file info

# Defaults
DEF_CFG_FILE = 'data2pdb.ini'
# Set notation
DEF_CFG_VALS = {DATA_FILES_FILE: 'data_list.txt', ATOM_TYPE_DICT_FILE: 'atom_dict.json',
                LAST_PROT_ID: 0,
                OUT_BASE_DIR: None,
                MAKE_DICT_BOOL: False,
                CHECK_ATOM_TYPE: False,
                DATA_FILE: None,
                }
REQ_KEYS = {PDB_TPL_FILE: str,
            }

# For data template file processing
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'


def read_cfg(f_loc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param f_loc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser()
    good_files = config.read(f_loc)

    if not good_files:
        raise IOError('Could not read file {}'.format(f_loc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)

    # To fix; have this as default!
    main_proc[DATA_FILES] = []
    if os.path.isfile(main_proc[DATA_FILES_FILE]):
        with open(main_proc[DATA_FILES_FILE]) as f:
            for data_file in f:
                main_proc[DATA_FILES].append(data_file.strip())
    if main_proc[DATA_FILE] is not None:
        main_proc[DATA_FILES].append(main_proc[DATA_FILE])
    if len(main_proc[DATA_FILES]) == 0:
        raise InvalidDataError("No files to process: no '{}' specified and "
                               "no list of files found for: {}".format(DATA_FILE, main_proc[DATA_FILES_FILE]))

    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates pdb files from lammps data, given a template pdb file.')
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
    except (KeyError, InvalidDataError, MissingSectionHeaderError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def make_dict(cfg, data_tpl_content):
    atoms_pat = re.compile(r"^Atoms.*")
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    matched_atom_types = {}
    atom_type_dict = defaultdict(list)
    non_unique_charmm = []
    pdb_atom_num = len(data_tpl_content[ATOMS_CONTENT])
    for data_file in cfg[DATA_FILES]:
        with open(data_file) as d:
            section = SEC_HEAD
            atom_id = 0
            num_atoms = None
            for line in d:
                line = line.strip()
                # not currently keeping anything from the header; just check num atoms
                if section == SEC_HEAD:
                    if atoms_pat.match(line):
                        section = SEC_ATOMS
                    elif num_atoms is None:
                        atoms_match = num_atoms_pat.match(line)
                        if atoms_match:
                            # regex is 1-based
                            num_atoms = int(atoms_match.group(1))
                            if num_atoms != pdb_atom_num:
                                raise InvalidDataError("Mismatched numbers of atoms: \n"
                                                       "  Found {} atoms in file: {}\n"
                                                       "    and {} atoms in file: {}\n"
                                                       "".format(pdb_atom_num, cfg[PDB_TPL_FILE],
                                                                 num_atoms, data_file))
                elif section == SEC_ATOMS:
                    if len(line) == 0:
                        continue
                    split_line = line.split()

                    # keep lammps types as strings, because json saves as strings to be portable
                    lammps_atom_type = split_line[2]
                    # combine atom type with molecules/resid type
                    charmm_atom_type = (data_tpl_content[ATOMS_CONTENT][atom_id][2] +
                                        data_tpl_content[ATOMS_CONTENT][atom_id][3])

                    # Making the dictionary; use charmm as unique key. Do this first to verify library.
                    if charmm_atom_type in matched_atom_types:
                        # Check that we don't have conflicting matching
                        if lammps_atom_type != matched_atom_types[charmm_atom_type]:
                            if charmm_atom_type not in non_unique_charmm:
                                print('Verify that this charmm type can have multiple lammps types: ',
                                      charmm_atom_type)
                                print('First collision for this charmm type occurred on atom:', atom_id + 1)
                                non_unique_charmm.append(charmm_atom_type)
                    else:
                        matched_atom_types[charmm_atom_type] = lammps_atom_type

                    # Don't add if already there
                    if charmm_atom_type not in atom_type_dict[lammps_atom_type]:
                        atom_type_dict[lammps_atom_type].append(charmm_atom_type)

                    atom_id += 1
                    # Check after increment because the counter started at 0
                    if atom_id == num_atoms:
                        # Since the tail will come only from the template, nothing more is needed.
                        break
        print('Finished looking for dictionary values in file ', data_file)

    with open(cfg[ATOM_TYPE_DICT_FILE], 'w') as d_file:
        json.dump(atom_type_dict, d_file)

    print('Completed making dictionary and saved it to {}'.format(cfg[ATOM_TYPE_DICT_FILE]))


def process_data_files(cfg, data_tpl_content):
    # Don't want to change the original template data when preparing to print the new file:

    chk_atom_type = cfg[CHECK_ATOM_TYPE]
    data_dict = {}

    if chk_atom_type:
        try:
            with open(cfg[ATOM_TYPE_DICT_FILE], 'r') as d_file:
                data_dict = json.load(d_file)
        except IOError as e:
            warning("Problems reading dictionary file: {}\n"
                    "The program will continue without checking atom types.".format(cfg[ATOM_TYPE_DICT_FILE]), e)
            chk_atom_type = False

    for data_file in cfg[DATA_FILES]:
        process_data_file(cfg, chk_atom_type, data_dict, data_file, data_tpl_content)


def process_data_file(cfg, chk_atom_type, data_dict, data_file, pdb_tpl_content):
    with open(data_file) as d:
        pdb_data_section = copy.deepcopy(pdb_tpl_content[ATOMS_CONTENT])
        section = SEC_HEAD
        atom_id = 0
        num_atoms = None
        atom_types = []

        for line in d:
            line = line.strip()
            # not currently keeping anything from the header; just check num atoms
            if section == SEC_HEAD:
                if ATOMS_PAT.match(line):
                    section = SEC_ATOMS
                elif num_atoms is None:
                    atoms_match = NUM_ATOMS_PAT.match(line)
                    if atoms_match:
                        # regex is 1-based
                        num_atoms = int(atoms_match.group(1))
                        if num_atoms != pdb_tpl_content[NUM_ATOMS]:
                            raise InvalidDataError("Mismatched numbers of atoms: \n"
                                                   "  Found {} atoms in file: {}\n"
                                                   "    and {} atoms in file: {}\n"
                                                   "".format(pdb_tpl_content[NUM_ATOMS], cfg[PDB_TPL_FILE],
                                                             num_atoms, data_file))

            # atoms_content to contain only xyz; also perform some checking
            elif section == SEC_ATOMS:
                if len(line) == 0:
                    continue
                split_line = line.split()

                # Not currently checking molecule number
                # If decide to do so, should make a count from 1 as the PDB is read; the PDB does not
                # have to start from 1, but the data file counts molecules from 1. For now, decided
                # checking atom type is a sufficient check
                # mol_num = int(split_line[1])

                # Keep as string; json save as string and this helps compare
                atom_types.append(split_line[2])
                pdb_data_section[atom_id][5:8] = map(float, split_line[4:7])
                atom_id += 1
                # Check after increment because the counter started at 0
                if atom_id == num_atoms:
                    # Since the tail will come only from the template, nothing more is needed.
                    break

    # Now that finished reading the file...
    if atom_id != num_atoms:
        raise InvalidDataError('In data file: {}\n'
                               '  header section lists {} atoms, but found {} atoms'.format(data_file,
                                                                                            num_atoms, atom_id))
    if chk_atom_type:
        for data_type, atom in zip(atom_types, pdb_data_section):
            try:
                pdb_type = atom[2] + atom[3]
                if pdb_type not in data_dict[data_type]:
                    warning('Did not find type {} in dictionary of values for atom_type {}: ({})'
                            ''.format(pdb_type, data_type, data_dict[data_type]))
                    # print("atom", atom_type, data_dict[atom_type])
            except KeyError:
                warning('Did not find data file atom type {} in the atom type dictionary {}'
                        ''.format(data_type, cfg[ATOM_TYPE_DICT_FILE]))
    f_name = create_out_fname(data_file, ext='.pdb', base_dir=cfg[OUT_BASE_DIR])
    list_to_file(pdb_tpl_content[HEAD_CONTENT] + pdb_data_section + pdb_tpl_content[TAIL_CONTENT],
                 f_name, list_format=PDB_FORMAT)


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config

    # Read template and data files
    try:
        pdb_tpl_content = process_pdb_tpl(cfg[PDB_TPL_FILE])
        # TODO: Test and use dictionary
        if cfg[MAKE_DICT_BOOL]:
            make_dict(cfg, pdb_tpl_content)
        process_data_files(cfg, pdb_tpl_content)
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
