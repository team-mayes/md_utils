#!/usr/bin/env python
"""
Collects selected data from evb output files:
Total number of states; states in each shell; summary of these states (max, min, avg, std)
For each step:
timestep, highest prot ci^2, 2 highest water ci^2, identity of water molecules

TODO: option: get CEC coordinate per timestep
# CEC_COORDINATE
# -11.836903 11.874760 12.125849

TODO: option: get mol number for aligning H*-O distance with ci^2value

For right now:
just get highest prot ci^2, highest wat ci^2

"""

from __future__ import print_function

import os
from collections import OrderedDict
from operator import itemgetter
import copy
import re
import sys
import argparse
import numpy as np
from md_utils.md_common import (InvalidDataError, warning, create_out_fname, process_cfg, write_csv,
                                IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser

__author__ = 'hmayes'

# Constants #
NUM_DECIMALS = 12

# Config File Sections
MAIN_SEC = 'main'

# Config keys
EVB_FILES = 'evb_list_file'
EVB_FILE = 'evb_file'
PROT_RES_MOL_ID = 'prot_res_mol_id'
# IN_BASE_DIR = 'input_directory'
OUT_BASE_DIR = 'output_directory'
PRINT_CI_SQ = 'print_ci_summary_flag'
PRINT_CI_SUBSET = 'print_ci_subset_flag'
PRINT_WAT_MOL = 'print_ci_water_molid_flag'
PRINT_CEC = 'print_cec_coords_flag'
MIN_MAX_CI_SQ = 'min_max_ci_sq'
PRINT_PER_FILE = 'print_output_each_file'
PRINT_PER_LIST = 'print_output_file_list'
PRINT_KEY_PROPS = 'print_key_props_flag'
SKIP_ONE_STATE = 'skip_one_state_flag'

# Defaults
DEF_CFG_FILE = 'evb_get_info.ini'
# Set notation
DEF_CFG_VALS = {EVB_FILES: 'evb_list.txt',
                EVB_FILE: None,
                OUT_BASE_DIR: None,
                PRINT_CI_SQ: True,
                PRINT_CI_SUBSET: False,
                PRINT_WAT_MOL: False,
                PRINT_CEC: False,
                MIN_MAX_CI_SQ: 0.475,
                PRINT_PER_FILE: True,
                PRINT_PER_LIST: False,
                PRINT_KEY_PROPS: False,
                SKIP_ONE_STATE: True,
                }
REQ_KEYS = {PROT_RES_MOL_ID: int, }

# For evb file processing
SEC_TIMESTEP = 'timestep'
SEC_ENE_TOTAL = 'ene_total'
SEC_COMPLEX = 'complex_section'
SEC_STATES = 'states_section'
SEC_EIGEN = 'eigen_vector_section'
SEC_CEC = 'cec_coord_section'
SEC_DIAG = 'diagonal_energy_section'
SEC_END = 'end_of_timestep'

# For evb processing and output
FILE_NAME = 'filename'
TIMESTEP = 'timestep'
MOL_A = 'mol_A'
MOL_B = 'mol_B'
MAX_PROT_CI_SQ = 'max_prot_ci2'
MAX_HYD_CI_SQ = 'max_hyd_ci2'
NEXT_MAX_HYD_CI_SQ = 'next_max_hyd_ci2'
MAX_PROT_E = 'max_prot_energy'
MAX_HYD_E = 'max_hyd_energy'
NEXT_MAX_HYD_E = 'next_max_hyd_energy'
MAX_HYD_MOL = 'max_hyd_mol'
NEXT_MAX_HYD_MOL = 'next_max_hyd_mol'
MAX_PROT_STATE_NUM = 'max_prot_state_num'
MAX_HYD_STATE_NUM = 'max_state_num'
MAX_PROT_STATE_COUL = 'max_prot_state_coul'
MAX_HYD_STATE_COUL = 'max_hyd_state_coul'
MAX_CI_SQ_DIFF = 'max_ci_sq_diff'
COUL_DIFF = 'coul_diff'
MAX_PROT_CLOSE_WAT = 'max_prot_close_water_mol'
CEC_X = 'cec_x'
CEC_Y = 'cec_y'
CEC_Z = 'cec_z'
STATES_TOT = 'evb_states_total'
STATES_SHELL1 = 'evb_states_shell_1'
STATES_SHELL2 = 'evb_states_shell_2'
STATES_SHELL3 = 'evb_states_shell_3'
ENE_TOTAL = 'ene_total'
CI_FIELDNAMES = [TIMESTEP, ENE_TOTAL,
                 MAX_PROT_CI_SQ, MAX_HYD_CI_SQ, NEXT_MAX_HYD_CI_SQ, MAX_CI_SQ_DIFF,
                 MAX_PROT_E, MAX_HYD_E, NEXT_MAX_HYD_E,
                 MAX_PROT_STATE_COUL, MAX_HYD_STATE_COUL, COUL_DIFF]
KEY_PROPS_FIELDNAMES = [TIMESTEP, STATES_TOT, STATES_SHELL1, STATES_SHELL2, STATES_SHELL3,
                        MAX_PROT_CI_SQ, MAX_HYD_CI_SQ, CEC_X, CEC_Y, CEC_Z]
CEC_COORD_FIELDNAMES = [TIMESTEP, CEC_X, CEC_Y, CEC_Z]
PROT_WAT_FIELDNAMES = [TIMESTEP, MAX_HYD_CI_SQ, MAX_HYD_MOL, NEXT_MAX_HYD_CI_SQ, NEXT_MAX_HYD_MOL]

OPT_FIELD_NAME_DICT = OrderedDict([(PRINT_CI_SQ, CI_FIELDNAMES),
                                   (PRINT_KEY_PROPS, KEY_PROPS_FIELDNAMES),
                                   (PRINT_CEC, CEC_COORD_FIELDNAMES),
                                   (PRINT_WAT_MOL, PROT_WAT_FIELDNAMES)])


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
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='For each timestep, find the highest protonated state ci^2 and '
                                                 'highest ci^2 for a hydronium. '
                                                 'Currently, this script expects only one protonatable residue.')
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
    except (KeyError, InvalidDataError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


def find_section_state(line):
    time_pat = re.compile(r"^TIMESTEP.*")
    ene_total_pat = re.compile(r"^ENE_TOTAL.*")
    complex_pat = re.compile(r"^COMPLEX 1:.*")
    state_pat = re.compile(r"^STATES.*")
    eigen_pat = re.compile(r"^EIGEN_VECTOR.*")
    cec_pat = re.compile(r"^CEC_COORDINATE.*")
    diag_pat = re.compile(r"^DIAGONAL .*")
    end_pat = re.compile(r"END_OF_COMPLEX 1.*")
    if time_pat.match(line):
        return SEC_TIMESTEP
    if ene_total_pat.match(line):
        return SEC_ENE_TOTAL
    elif complex_pat.match(line):
        return SEC_COMPLEX
    elif state_pat.match(line):
        return SEC_STATES
    elif eigen_pat.match(line):
        return SEC_EIGEN
    elif cec_pat.match(line):
        return SEC_CEC
    elif diag_pat.match(line):
        return SEC_DIAG
    elif end_pat.match(line):
        return SEC_END
    else:
        return None


def process_evb_file(evb_file, cfg):
    with open(evb_file) as d:
        base_file_name = os.path.basename(evb_file)
        section = None
        # cec_array = np.zeros(3)
        states_array = None
        data_to_print = []
        subset_to_print = []
        prot_wat_to_print = []
        state_count = 0
        one_state = False
        max_max_prot_mol_a = np.nan
        max_hyd_wat_mol = np.nan
        next_max_hyd_wat_mol = np.nan
        timestep = None
        states_per_shell = [np.nan]
        # not really needed here, but guarantees that these exist even if there is no timestep found
        max_hyd_ci_sq = 0.0
        next_max_hyd_ci_sq = 0.0
        for line in d:
            line = line.strip()
            if section is None:
                section = find_section_state(line)
                # If no state found, advance to next line.
                # Also advance to next line if the first line of a state does not contain data needed
                #   otherwise, go to next if block to get data from that line
                if section in [None, SEC_STATES, SEC_EIGEN, SEC_CEC, SEC_DIAG]:
                    continue
            if section == SEC_TIMESTEP:
                split_line = line.split()
                timestep = int(split_line[1])
                result = {FILE_NAME: base_file_name,
                          TIMESTEP: timestep}
                # Reset variables
                # Start with an entry so the atom-id = index
                num_states = 0
                state_count = 0
                state_list = []
                prot_state_list = []
                hyd_state_list = []
                hyd_state_mol_dict = {}
                max_prot_ci_sq = 0.0
                max_hyd_ci_sq = 0.0
                next_max_hyd_ci_sq = 0.0
                max_prot_state = None
                max_hyd_state = None
                next_max_hyd_state = None
                section = None
            elif section == SEC_ENE_TOTAL:
                split_line = line.split()
                ene_total = float(split_line[1])
                result[ENE_TOTAL] = ene_total
                section = None
            elif section == SEC_COMPLEX:
                split_line = line.split()
                num_states = int(split_line[2])
                states_per_shell = np.array(itemgetter(2, 5, 7, 9, 11)(split_line), dtype=int)
                result.update({STATES_TOT: states_per_shell[0], STATES_SHELL1: states_per_shell[2],
                               STATES_SHELL2: states_per_shell[3], STATES_SHELL3: states_per_shell[4]})
                if states_array is None:
                    states_array = states_per_shell
                else:
                    states_array = np.vstack((states_array, states_per_shell))
                section = None
            elif section == SEC_STATES:
                split_line = line.split()
                mol_b = int(split_line[4])
                if mol_b == cfg[PROT_RES_MOL_ID]:
                    prot_state_list.append(state_count)
                else:
                    hyd_state_list.append(state_count)
                state_list.append({MOL_A: int(split_line[3]), MOL_B: mol_b})
                state_count += 1
                if state_count == num_states:
                    section = None
                    state_count = 0
            elif section == SEC_DIAG:
                diag_energies = np.fromstring(line, sep=' ')
                if state_count == 0:
                    diag_array = diag_energies
                else:
                    diag_array = np.vstack((diag_array, diag_energies))
                state_count += 1
                if state_count == num_states:
                    section = None
                    state_count = 0
                    if len(diag_array.shape) == 1:
                        one_state = True
                    else:
                        one_state = False
            elif section == SEC_EIGEN:
                eigen_vector = map(float, line.split())
                eigen_sq = np.square(eigen_vector)
                for state in prot_state_list:
                    if eigen_sq[state] > max_prot_ci_sq:
                        max_prot_ci_sq = eigen_sq[state]
                        max_prot_state = state
                        max_max_prot_mol_a = state_list[state][MOL_A]
                for state in hyd_state_list:
                    water_molid = state_list[state][MOL_B]
                    if eigen_sq[state] > max_hyd_ci_sq:
                        if max_hyd_ci_sq > next_max_hyd_ci_sq:
                            next_max_hyd_ci_sq = copy.copy(max_hyd_ci_sq)
                            next_max_hyd_state = copy.copy(max_hyd_state)
                            next_max_hyd_wat_mol = copy.copy(max_hyd_wat_mol)
                        max_hyd_ci_sq = eigen_sq[state]
                        max_hyd_state = state
                        max_hyd_wat_mol = water_molid
                    elif eigen_sq[state] > next_max_hyd_ci_sq:
                        next_max_hyd_ci_sq = eigen_sq[state]
                        next_max_hyd_state = state
                        next_max_hyd_wat_mol = water_molid
                    if cfg[PRINT_WAT_MOL]:
                        if state_list[state][MOL_A] == cfg[PROT_RES_MOL_ID] or water_molid == max_max_prot_mol_a:
                            if water_molid in hyd_state_mol_dict:
                                if eigen_sq[state] > hyd_state_mol_dict[water_molid]:
                                    hyd_state_mol_dict[water_molid] = eigen_sq[state]
                            else:
                                hyd_state_mol_dict[water_molid] = eigen_sq[state]
                result.update({MAX_PROT_CI_SQ: max_prot_ci_sq, MAX_HYD_CI_SQ: max_hyd_ci_sq,
                               NEXT_MAX_HYD_CI_SQ: next_max_hyd_ci_sq, MAX_CI_SQ_DIFF: max_prot_ci_sq - max_hyd_ci_sq,
                               MAX_HYD_MOL: max_hyd_wat_mol, NEXT_MAX_HYD_MOL: next_max_hyd_wat_mol,
                               })
                if cfg[PRINT_WAT_MOL]:
                    if len(hyd_state_mol_dict) == 0 and cfg[SKIP_ONE_STATE] is False:
                        prot_wat_to_print.append({FILE_NAME: base_file_name, TIMESTEP: timestep, MOL_B: np.nan,
                                                  MAX_HYD_CI_SQ: np.nan})
                    for mol in hyd_state_mol_dict:
                        prot_wat_to_print.append({FILE_NAME: base_file_name, TIMESTEP: timestep, MOL_B: mol,
                                                  MAX_HYD_CI_SQ: hyd_state_mol_dict[mol]})
                section = None
            elif section == SEC_CEC:
                # cec_array = np.vstack((cec_array, np.string2array(line)))
                cec_array = np.fromstring(line, sep=' ')
                result.update({CEC_X: cec_array[0], CEC_Y: cec_array[1], CEC_Z: cec_array[2]})
                section = None
            elif section == SEC_END:
                section = None
                if max_prot_state is None:
                    prot_coul = np.nan
                    prot_e = np.nan
                # sometimes, there is only one state, so the diagonal array is a vector
                elif one_state:
                    prot_coul = diag_array[3] + diag_array[8]
                    prot_e = diag_array[1]
                else:
                    prot_coul = diag_array[max_prot_state][3] + diag_array[max_prot_state][8]
                    prot_e = diag_array[max_prot_state][1]
                if max_hyd_state is None:
                    hyd_coul = np.nan
                    max_hyd_e = np.nan
                elif one_state:
                    hyd_coul = diag_array[3] + diag_array[3]
                    max_hyd_e = diag_array[1]
                else:
                    hyd_coul = diag_array[max_hyd_state][3] + diag_array[max_hyd_state][8]
                    max_hyd_e = diag_array[max_hyd_state][1]
                if next_max_hyd_state is None:
                    next_max_hyd_e = np.nan
                elif one_state:
                    next_max_hyd_e = diag_array[1]
                else:
                    next_max_hyd_e = diag_array[next_max_hyd_state][1]
                result.update({MAX_PROT_STATE_COUL: prot_coul, MAX_HYD_STATE_COUL: hyd_coul,
                               COUL_DIFF: hyd_coul - prot_coul,
                               MAX_PROT_E: prot_e, MAX_HYD_E: max_hyd_e, NEXT_MAX_HYD_E: next_max_hyd_e})
                if cfg[SKIP_ONE_STATE] and states_per_shell[0] == 1:
                    continue
                data_to_print.append(result)
                if cfg[PRINT_CI_SUBSET]:
                    if max_prot_ci_sq > cfg[MIN_MAX_CI_SQ] and max_hyd_ci_sq > cfg[MIN_MAX_CI_SQ]:
                        subset_to_print.append(result)

    return data_to_print, subset_to_print, prot_wat_to_print


def process_evb_files(cfg, selected_fieldnames):
    """
    Want to grab the timestep and highest prot ci^2, highest wat ci^2, and print them
    @param selected_fieldnames: list of field names for output based on user-selected options
    @param cfg: configuration data read from ini file
    @return: @raise InvalidDataError:
    """
    first_file_flag = True
    evb_file_list = []

    if cfg[EVB_FILE] is not None:
        evb_file_list.append(cfg[EVB_FILE])

    # Separate try-catch block here because want it to continue rather than exit; exit below if there are no files to
    # process
    try:
        with open(cfg[EVB_FILES]) as f:
            for evb_file in f:
                evb_file_list.append(evb_file.strip())
    except IOError as e:
        warning("Problems reading file:", e)

    if len(evb_file_list) == 0:
        raise InvalidDataError("Found no evb file names to read. Specify one file with the keyword '{}' or \n"
                               "a file containing a list of evb files with the keyword '{}'.".format(EVB_FILE,
                                                                                                     EVB_FILES))

    for evb_file in evb_file_list:
        data_to_print, subset_to_print, wat_mol_data_to_print = process_evb_file(evb_file, cfg)
        if cfg[PRINT_PER_FILE] is True:
            if len(data_to_print) > 0:
                f_out = create_out_fname(evb_file, suffix='_evb_info', ext='.csv',
                                         base_dir=cfg[OUT_BASE_DIR])
                write_csv(data_to_print, f_out, selected_fieldnames, extrasaction="ignore")
            if cfg[PRINT_CI_SUBSET]:
                if len(subset_to_print) > 0:
                    f_out = create_out_fname(evb_file, suffix='_ci_sq_ts', ext='.csv',
                                             base_dir=cfg[OUT_BASE_DIR])
                    write_csv(subset_to_print, f_out, CI_FIELDNAMES, extrasaction="ignore")
                else:
                    warning("'{}' set to true, but found no data from: {} \n"
                            "No output will be printed for this file."
                            "".format(PRINT_CI_SUBSET, evb_file))
        if cfg[PRINT_PER_LIST]:
            if first_file_flag:
                print_mode = 'w'
                first_file_flag = False
            else:
                print_mode = 'a'
            if cfg[PRINT_CI_SUBSET]:
                if len(subset_to_print) > 0:
                    f_out = create_out_fname(cfg[EVB_FILES], suffix='_ci_sq_ts', ext='.csv',
                                             base_dir=cfg[OUT_BASE_DIR])
                    write_csv(subset_to_print, f_out, [FILE_NAME] + CI_FIELDNAMES,
                              extrasaction="ignore", mode=print_mode)
                else:
                    warning("'{}' set to true, but found no data meeting criteria."
                            "".format(PRINT_CI_SUBSET))
            f_out = create_out_fname(cfg[EVB_FILES], suffix='_evb_info', ext='.csv',
                                     base_dir=cfg[OUT_BASE_DIR])
            write_csv(data_to_print, f_out, [FILE_NAME] + selected_fieldnames,
                      extrasaction="ignore", mode=print_mode)


def gather_out_field_names(cfg):
    """
    Based on user options, determine which field names to use in printing output
    @param cfg: configuration for run
    @return: list of field names to be printed for selected options
    """
    selected_field_names = []
    for option_name, fieldnames in OPT_FIELD_NAME_DICT.items():
        if cfg[option_name]:
            for f_name in fieldnames:
                if f_name not in selected_field_names:
                    selected_field_names.append(f_name)
    if len(selected_field_names) > 0:
        return selected_field_names
    else:
        raise InvalidDataError('None of the following options were selected, so no data will be collected: {}'
                               ''.format(OPT_FIELD_NAME_DICT.keys()))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    # Read template and dump files
    cfg = args.config
    try:
        out_field_names = gather_out_field_names(cfg)
        process_evb_files(cfg, out_field_names)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except (InvalidDataError, ValueError) as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
