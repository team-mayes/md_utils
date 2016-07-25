#!/usr/bin/env python
"""
Get selected info from the file
"""

from __future__ import print_function
import re
import sys
import argparse

from md_utils.md_common import InvalidDataError, warning, create_out_fname, process_cfg, print_qm_kind
try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser


__author__ = 'hmayes'


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
CHK_FILE_LIST = 'evb_chk_file_list'
LAST_EXCLUDE_ID = 'exclude_atom_ids_through'
OUT_BASE_DIR = 'output_base_directory'
EXPECTED_CHARGE = 'expected_charge'

# data file info


# Defaults
DEF_CFG_FILE = 'evb_chk_get_info.ini'
# Set notation
DEF_CFG_VALS = {LAST_EXCLUDE_ID: 0, OUT_BASE_DIR: None,
                EXPECTED_CHARGE: None,
                }
REQ_KEYS = {CHK_FILE_LIST: str,
            }

# Sections
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'

# Content
NUM_ATOMS = 'num_atoms'
HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'


def read_cfg(floc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param floc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser()
    good_files = config.read(floc)
    if not good_files:
        raise IOError('Could not read file {}'.format(floc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)
    if main_proc[EXPECTED_CHARGE] is not None:
        main_proc[EXPECTED_CHARGE] = int(main_proc[EXPECTED_CHARGE])
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Grabs selected info from the designated file. '
                                                 'The required input file provides the location of the file. '
                                                 'Optional info is an atom index for the last atom not to consider.')
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


def print_vmd_list(atom_ids, fname, mode='w'):
    # Change to base zero for VMD
    vmd_atom_ids = [a_id - 1 for a_id in atom_ids]
    with open(fname, mode) as m_file:
        m_file.write('{}'.format(' '.join(map(str, vmd_atom_ids))))
    print("Wrote file: {}".format(fname))


def process_file(cfg):

    chk_list_loc = cfg[CHK_FILE_LIST]
    num_atoms_pat = re.compile(r"^ATOMS (\d+).*")
    last_exclude_id = cfg[LAST_EXCLUDE_ID]

    with open(chk_list_loc) as f:
        for chk_file in f:
            chk_file = chk_file.strip()
            with open(chk_file) as d:
                chk_data = {HEAD_CONTENT: [], ATOMS_CONTENT: [], TAIL_CONTENT: []}

                section = SEC_HEAD
                o_ids = []
                h_ids = []

                for line in d:
                    line = line.strip()
                    # head_content to contain Everything before 'Atoms' section
                    # also capture the number of atoms
                    if section == SEC_HEAD:
                        chk_data[HEAD_CONTENT].append(line)

                        atoms_match = num_atoms_pat.match(line)
                        if atoms_match:
                            # regex is 1-based
                            # print(atoms_match.group(1))
                            chk_data[NUM_ATOMS] = int(atoms_match.group(1))
                            section = SEC_ATOMS

                    elif section == SEC_ATOMS:
                        if len(line) == 0:
                            continue
                        split_line = line.split()
                        index = int(split_line[0])
                        atom_num = int(split_line[1])
                        x, y, z = map(float, split_line[2:5])
                        atom_type = split_line[5]
                        atom_struct = [index, atom_num, x, y, z, atom_type]
                        chk_data[ATOMS_CONTENT].append(atom_struct)
                        if atom_num > last_exclude_id:
                            if atom_type == 'O':
                                o_ids.append(atom_num)
                            elif atom_type == 'H':
                                h_ids.append(atom_num)
                            else:
                                raise InvalidDataError("Expected atom types are 'O' and 'H' (looking for water "
                                                       "molecules only). Found type '{}' for line:\n {}\n"
                                                       "Use the '{}' keyword to specify the last atom to exclude (i.e. "
                                                       "the last protein atom)."
                                                       "".format(atom_type, line, LAST_EXCLUDE_ID))

                        if len(chk_data[ATOMS_CONTENT]) == chk_data[NUM_ATOMS]:
                            section = SEC_TAIL
                    # tail_content to contain everything after the 'Atoms' section
                    elif section == SEC_TAIL:
                        break

            # Data validation: checking total charge
            num_o = len(o_ids)
            num_h = len(h_ids)
            total_charge = num_h - 2 * num_o
            if cfg[EXPECTED_CHARGE] is None:
                print("Found {} oxygen atoms and {} hydrogen atoms for a total charge of {}."
                      "".format(num_o, num_h, add_sign(total_charge)))
            else:
                if total_charge != cfg[EXPECTED_CHARGE]:
                    raise InvalidDataError("Expected a total charge of {} but found {} for file: {}"
                                           "".format(add_sign(cfg[EXPECTED_CHARGE]), add_sign(total_charge), chk_file))

            # printing!
            f_name = create_out_fname(chk_file, prefix='water_', ext='.dat', base_dir=cfg[OUT_BASE_DIR],
                                      remove_prefix='CHK_')
            print_qm_kind(h_ids, 'H', f_name)
            print_qm_kind(o_ids, 'O', f_name, mode='a')
            f_name = create_out_fname(chk_file, prefix='vmd_water_', ext='.dat', base_dir=cfg[OUT_BASE_DIR],
                                      remove_prefix='CHK_')
            print_vmd_list(o_ids+h_ids, f_name)


def add_sign(val):
    if val > 0:
        return "+" + str(val)
    else:
        return val


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    # Read template and data files
    cfg = args.config

    try:
        process_file(cfg)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    # print(psf_data_content[ATOMS_CONTENT])
    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
