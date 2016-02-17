#!/usr/bin/env python
"""
Get selected info from the file
"""

from __future__ import print_function

import ConfigParser
import copy
import logging
import re
import csv
from md_utils.md_common import list_to_file, InvalidDataError, seq_list_to_file, create_out_suf_fname, warning
import sys
import argparse

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('evb_chk_get_info')
logging.basicConfig(filename='evb_chk_get_info.log', filemode='w', level=logging.DEBUG)
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
CHK_FILE = 'evb_chk_file'
LAST_EXCLUDE_ID = 'last_exclude_id'

# data file info


# Defaults
DEF_CFG_FILE = 'evb_chk_get_info.ini'
# Set notation
DEF_CFG_VALS = { LAST_EXCLUDE_ID: 0
}
REQ_KEYS = {CHK_FILE: str,
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


def to_int_list(raw_val):
    return_vals = []
    for val in raw_val.split(','):
        return_vals.append(int(val.strip()))
    return return_vals


def conv_raw_val(param, def_val):
    """
    Converts the given parameter into the given type (default returns the raw value).  Returns the default value
    if the param is None.
    :param param: The value to convert.
    :param def_val: The value that determines the type to target.
    :return: The converted parameter value.
    """
    if param is None:
        return def_val
    if isinstance(def_val, bool):
        return bool(param)
    if isinstance(def_val, int):
        return int(param)
    if isinstance(def_val, long):
        return long(param)
    if isinstance(def_val, float):
        return float(param)
    if isinstance(def_val, list):
        return to_int_list(param)
    return param


def process_cfg(raw_cfg):
    """
    Converts the given raw configuration, filling in defaults and converting the specified value (if any) to the
    default value's type.
    :param raw_cfg: The configuration map.
    :return: The processed configuration.
    """
    proc_cfg = {}
    try:
        for key, def_val in DEF_CFG_VALS.items():
            proc_cfg[key] = conv_raw_val(raw_cfg.get(key), def_val)
    except Exception as e:
        logger.error('Problem with default config vals on key %s: %s', key, e)
    try:
        for key, type_func in REQ_KEYS.items():
            proc_cfg[key] = type_func(raw_cfg[key])
    except Exception as e:
        logger.error('Problem with required config vals on key %s: %s', key, e)


    # If I needed to make calculations based on values, get the values as below, and then
    # assign to calculated config values
    return proc_cfg


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
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)))
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Grabs selected info from the designated file.'
                                                 'The required input file provides the location of the '
                                                 'file. Optional info is an atom index for the last atom not to consider.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini "
                                               "format. See the example file /test/test_data/evbd2d/evb_chk_get_info.ini"
                                               "The default file name is evb_chk_get_info.ini, located in the "
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


def print_qm_kind(int_list, element_name):
    print('    &QM_KIND {}'.format(element_name))
    print('        MM_INDEX {}'.format(' '.join(map(str,int_list))))
    print('    &END QM_KIND')
    return


def print_qm_links(resid, dict):
    print('    &LINK \n       MM_INDEX  {}\n       QM_INDEX  {}\n       LINK_TYPE  IMOMM\n       ALPHA_IMOMM  1.5\n    &END LINK '.format(dict['CA'],dict['CB']))
    return


def process_data_tpl(cfg):

    chk_loc = cfg[CHK_FILE]
    chk_data = {}
    chk_data[HEAD_CONTENT] = []
    chk_data[ATOMS_CONTENT] = []
    chk_data[TAIL_CONTENT] = []
    last_exclude_id = cfg[LAST_EXCLUDE_ID]

    section = SEC_HEAD
    num_atoms_pat = re.compile(r"^ATOMS (\d+).*")

    o_ids = []
    h_ids = []

    vmd_atom_ids = []

    with open(chk_loc) as f:
        for line in f.readlines():
            line = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                chk_data[HEAD_CONTENT].append(line)

                atoms_match = num_atoms_pat.match(line)
                if atoms_match:
                    # regex is 1-based
                    print(atoms_match.group(1))
                    chk_data[NUM_ATOMS] = int(atoms_match.group(1))
                    section = SEC_ATOMS

            elif section == SEC_ATOMS:
                if len(line) == 0:
                    continue
                split_line = line.split()
                index = int(split_line[0])
                atom_num = int(split_line[1])
                x, y, z = map(float,split_line[2:5])
                atom_type = split_line[5]
                atom_struct = [index, atom_num, x, y, z, atom_type]
                chk_data[ATOMS_CONTENT].append(atom_struct)
                if atom_num > last_exclude_id:
                    vmd_atom_ids.append(atom_num -1)
                    if atom_type == 'O':
                        o_ids.append(atom_num)
                    elif atom_type == 'H':
                        h_ids.append(atom_num)
                    else:
                        raise InvalidDataError('Expected atom types are O and H. Found type {} for line:\n {}.'.format(atom_type,line))

                if len(chk_data[ATOMS_CONTENT]) == chk_data[NUM_ATOMS]:
                    section = SEC_TAIL
            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                chk_data[TAIL_CONTENT].append(line)

    # if logger.isEnabledFor(logging.DEBUG):
    #     print_data(chk_data[HEAD_CONTENT], chk_data[ATOMS_CONTENT], chk_data[TAIL_CONTENT], 'reproduced.data')

    print_qm_kind(h_ids,'H')
    print_qm_kind(o_ids,'O')

    print('index {}'.format(' '.join(map(str,vmd_atom_ids))))

    print(chk_data)
    return chk_data

def print_data(head, data, tail, f_name):
    list_to_file(head, f_name)
    seq_list_to_file(data, f_name, mode='a')
    list_to_file(tail, f_name, mode='a')
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
        psf_data_content = process_data_tpl(cfg)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data template:", e)
        return INVALID_DATA

    # print(psf_data_content[ATOMS_CONTENT])

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
