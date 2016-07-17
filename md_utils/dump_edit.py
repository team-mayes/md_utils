#!/usr/bin/env python
"""
Make a new dump file with a specified max number of timesteps and reorders atoms.
"""

from __future__ import print_function
# noinspection PyCompatibility
import ConfigParser
import logging
import sys
import argparse
import numpy as np

from md_utils.md_common import InvalidDataError, create_out_fname, warning, \
    process_cfg, find_dump_section_state, read_int_dict, silent_remove


__author__ = 'hmayes'


# Logging
logger = logging.getLogger('dump_edit')
logging.basicConfig(filename='dump_edit.log', filemode='w', level=logging.DEBUG)
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
DUMPS_FILE = 'dump_list_file'
ATOM_REORDER_FILE = 'atom_reorder_old_new_file'
ATOM_TYPE_FILE = 'atom_type_old_new_file'
MOL_RENUM_FILE = 'mol_renum_old_new_file'
OUT_BASE_DIR = 'output_directory'
MAX_STEPS = 'max_steps'
OUT_FREQ = 'output_every_n_steps'
RENUM_SHIFT = 'shift_mol_num_by'
RENUM_START_MOL = 'first_shift_mol_num'

# Defaults
DEF_CFG_FILE = 'dump_edit.ini'
# Set notation
DEF_CFG_VALS = {DUMPS_FILE: 'dump_list.txt',
                OUT_BASE_DIR: None,
                ATOM_REORDER_FILE: None,
                ATOM_TYPE_FILE: None,
                MOL_RENUM_FILE: None,
                MAX_STEPS: -1,
                OUT_FREQ: 1,
                RENUM_START_MOL: -1,
                RENUM_SHIFT: 0,
                }
REQ_KEYS = {}

# From data template file
NUM_ATOMS = 'num_atoms'
TAIL_CONTENT = 'tail_content'
ATOMS_CONTENT = 'atoms_content'
HEAD_CONTENT = 'head_content'

# For data template file processing
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'


# For dump file processing
SEC_TIMESTEP = 'timestep'
SEC_NUM_ATOMS = 'dump_num_atoms'
SEC_BOX_SIZE = 'dump_box_size'

# For deciding if a float is close enough to a value
TOL = 0.000001
# Bundle of headers for calculating charge


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
    parser = argparse.ArgumentParser(description='Creates new lammps dump files from existing files, with new order, '
                                                 'keeping every specified number of timesteps, and stopping at a '
                                                 'max number of timesteps.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini "
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


def print_to_dump_file(head_content, atoms_struct, fname, mode='a'):
    """
    Writes the list of sequences to the given file in the specified format for a PDB.
    @param head_content: content to repeat for all files
    @param atoms_struct: The list atoms to write to file.
    @param fname: The location of the file to write.
    @param mode: to append or write new file
    """
    with open(fname, mode) as w_file:
        for line in head_content:
            w_file.write(line + '\n')
        for line in atoms_struct:
            w_file.write(' '.join(map(str, line)) + '\n')


def process_dump_file(cfg, dump_file, atom_num_dict, atom_type_dict, mol_num_dict):
    section = None
    box = np.zeros((3,))
    counter = 1
    num_atoms = 0
    head_content = []
    steps_count = 0
    step_stop = cfg[MAX_STEPS] * cfg[OUT_FREQ]
    timestep = None
    with open(dump_file) as d:
        d_out = create_out_fname(dump_file, suffix='_reorder', base_dir=cfg[OUT_BASE_DIR])
        silent_remove(d_out)
        for line in d:
            line = line.strip()

            if section == SEC_ATOMS:
                split_line = line.split()
                # If there is an incomplete line in a dump file, move on to the next file
                if len(split_line) < 7:
                    break

                atom_num = int(split_line[0])
                if atom_num in atom_num_dict:
                    atom_num = atom_num_dict[atom_num]

                mol_num = int(split_line[1])
                if mol_num in mol_num_dict:
                    mol_num = mol_num_dict[mol_num]
                # Default RENUM_START_MOL is neg 1; if still less than zero, user did not specify renumbering
                if 0 <= cfg[RENUM_START_MOL] <= mol_num:
                    mol_num += cfg[RENUM_SHIFT]

                atom_type = int(split_line[2])
                if atom_type in atom_type_dict:
                    atom_type = atom_type_dict[atom_type]

                charge = float(split_line[3])
                x, y, z = map(float, split_line[4:7])
                atom_struct = [atom_num, mol_num, atom_type, charge, x, y, z]
                atom_data.append(atom_struct)
                if counter == num_atoms:
                    if len(atom_num_dict) > 0:
                        atom_data = sorted(atom_data, key=lambda atom: atom[0])
                    steps_count += 1
                    if steps_count % cfg[OUT_FREQ] == 0:
                        print_to_dump_file(head_content, atom_data, d_out)
                    if steps_count == step_stop:
                        print("Reached the maximum number of steps ({})".format(cfg[MAX_STEPS]))
                        counter = 1
                        break
                    # reset for next timestep
                    head_content = []
                    counter = 0
                    section = None
                counter += 1

            else:
                head_content.append(line)
                if section is None:
                    section = find_dump_section_state(line)
                    if section is None:
                        raise InvalidDataError('Unexpected line in file {}: {}'.format(d, line))
                elif section == SEC_TIMESTEP:
                    timestep = line
                    # Reset variables
                    atom_data = []
                    section = None
                elif section == SEC_NUM_ATOMS:
                    num_atoms = int(line)
                    section = None
                elif section == SEC_BOX_SIZE:
                    split_line = line.split()
                    diff = float(split_line[1]) - float(split_line[0])
                    box[counter - 1] = diff
                    if counter == 3:
                        counter = 0
                        section = None
                    counter += 1
    if counter == 1:
        print("Completed reading dumpfile {}.".format(dump_file))
    else:
        warning("Dump file {} step {} did not have the full list of atom numbers. "
                "Continuing program.".format(dump_file, timestep))


def process_dump_files(cfg, atom_num_dict, atom_type_dict, mol_num_dict):
    with open(cfg[DUMPS_FILE]) as f:
        for dump_file in f:
            dump_file = dump_file.strip()
            # ignore blank lines in dump file list
            if len(dump_file) == 0:
                continue
            else:
                process_dump_file(cfg, dump_file, atom_num_dict, atom_type_dict, mol_num_dict)


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    # Read template and dump files
    cfg = args.config
    try:
        atom_num_dict = read_int_dict(cfg[ATOM_REORDER_FILE])
        atom_type_dict = read_int_dict(cfg[ATOM_TYPE_FILE], one_to_one=False)
        mol_num_dict = read_int_dict(cfg[MOL_RENUM_FILE], one_to_one=False)
        process_dump_files(cfg, atom_num_dict, atom_type_dict, mol_num_dict)
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
