#!/usr/bin/env python
"""
Grabs selected data from evb output files
"""

from __future__ import print_function

import ConfigParser
import logging
import re
import os
import numpy as np
from md_utils.md_common import list_to_file, InvalidDataError, warning

import sys
import argparse

__author__ = 'mayes'


# Logging
logger = logging.getLogger('process_evb')
logging.basicConfig(filename='process_evb.log', filemode='w', level=logging.DEBUG)
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
EVBS_FILE = 'evb_list_file'

PROT_RES_MOL_ID = 'prot_res_mol_id'

# Defaults
DEF_CFG_FILE = 'process_evb.ini'
# Set notation
DEF_CFG_VALS = {EVBS_FILE: 'evb_list.txt', }
REQ_KEYS = {PROT_RES_MOL_ID: int, }

# For evb file processing
SEC_TIMESTEP = 'timestep'
SEC_COMPLEX = 'complex_section'
SEC_STATES = 'states_section'
SEC_EIGEN = 'eigen_vector_section'


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


def create_out_suf_fname(src_file, suffix, base_dir=None, ext=None):
    """Creates an outfile name for the given source file.

    :param src_file: The file to process.
    :param suffix: The file suffix to append.
    :param base_dir: The base directory to use; defaults to `src_file`'s directory.
    :param ext: The extension to use instead of the source file's extension;
        defaults to the `scr_file`'s extension.
    :return: The output file name.
    """
    if base_dir is None:
        base_dir = os.path.dirname(src_file)

    base_name = os.path.splitext(src_file)[0]

    if ext is None:
        ext = os.path.splitext(src_file)[1]

    return os.path.abspath(os.path.join(base_dir, base_name + suffix + ext ))


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
    parser = argparse.ArgumentParser(description='For each timestep, find the protonated state (if appears) and its '
                                                 'ci^2 value. '
                                                 'Currently, this script expects only one protonatable residue.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "See the example file /test/test_data/evbd2d/process_evb.ini. "
                                               "The default file name is lammps_dist_pbc.ini, located in the "
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


def find_section_state(line):
    time_pat = re.compile(r"^TIMESTEP.*")
    complex_pat = re.compile(r"^COMPLEX 1:.*")
    state_pat = re.compile(r"^STATES.*")
    eigen_pat = re.compile(r"^EIGEN_VECTOR.*")
    if time_pat.match(line):
        return SEC_TIMESTEP
    elif complex_pat.match(line):
        return SEC_COMPLEX
    elif state_pat.match(line):
        return SEC_STATES
    elif eigen_pat.match(line):
        return SEC_EIGEN
    else:
        return None


def process_evb_files(cfg):
    """
    Want to grab the timestep, first and 2nd mole found, first and 2nd ci^2
    print the timestep, residue ci^2
    @param cfg: configuration data read from ini file
    @return: @raise InvalidDataError:
    """
    with open(cfg[EVBS_FILE]) as f:
        for evb_file in f.readlines():
            evb_file = evb_file.strip()
            with open(evb_file) as d:
                section = None
                to_print = ['timestep,prot_state_ci_squared']
                for line in d.readlines():
                    line = line.strip()
                    if section is None:
                        section = find_section_state(line)
                        #logger.debug("In process_dump_files, set section to %s.", section)
                        # If no state found, advance to next line.
                        # Also advance to next line if the first line of a state does not contain data needed
                        #   otherwise, go to next if block to get data from that line
                        if section in [None, SEC_STATES, SEC_EIGEN]:
                            continue
                    if section == SEC_TIMESTEP:
                        split_line = line.split()
                        timestep = split_line[1]
                        # Reset variables
                        # Start with an entry so the atom-id = index
                        num_states = 0
                        state_count = 0
                        prot_state = None
                        section = None
                    elif section == SEC_COMPLEX:
                        split_line = line.split()
                        num_states = int(split_line[2])
                        section = None
                    elif section == SEC_STATES:
                        split_line = line.split()
                        mol_B = int(split_line[4])
                        # print('state: {}, mol_B: {}'.format(state_count, split_line))
                        if mol_B == cfg[PROT_RES_MOL_ID]:
                            if prot_state is None:
                                prot_state = state_count
                            else:
                                print('Multiple protonated states found')
                        state_count += 1
                        if state_count == num_states:
                            section = None
                    elif section == SEC_EIGEN:
                        eigen_vector = map(float,line.split())
                        if prot_state is None:
                            prot_ci_sq = 'nan'
                        else:
                            prot_ci_sq = np.square(eigen_vector[prot_state])
                        print('timestep: {}, states: {}, prot_state: {}, prot_ci_sq {}'.format(timestep, num_states, prot_state, prot_ci_sq))
                        to_print.append(str(timestep)+','+str(prot_ci_sq))
                        section = None
                # Now that finished reading all atom lines...

            d_out = create_out_suf_fname(evb_file, '_prot_ci_sq', ext='.csv')
            list_to_file(to_print, d_out)
            print('Wrote file: {}'.format(d_out))
    return


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    # TODO: did not show the expected behavior when I didn't have a required cfg in the ini file
    if ret != GOOD_RET:
        return ret

    # TODO: in generated data files, print atom types and provide new header based on where this came from

    # Read template and dump files
    cfg = args.config
    try:
        process_evb_files(cfg)
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
