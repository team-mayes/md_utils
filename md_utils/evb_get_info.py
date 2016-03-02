#!/usr/bin/env python
"""
Grabs selected data from evb output files:
Total number of states; states in each shell; summary of these states (max, min, avg, std)
For each step:
timestep, highest prot ci^2, 2 highest water ci^2, identity of water molecules

STATES [ id | parent | shell | mol_A | mol_B | react | path | extra_cpl ]
            0     -1      0     -1    352     -1     -1     -1
            1      0      1    352     84      1      2      0
            2      0      1    352    363      1      3      0
            3      0      1    352      2      2      1      0
            4      0      1    352      2      2      4      0
            5      1      2     84    353      1      2      0
            6      2      2    363    393      1      2      0


8.7995E-01 1.6785E-01 1.4918E-01 2.3097E-02 4.1799E-01 5.2724E-04 5.4624E-04 7.6832E-04 1.0254E-06 5.0091E-06 5.0375E-06 1.4359E-07 7.1592E-07


TODO: option: get CEC coordinate per timestep
# CEC_COORDINATE
# -11.836903 11.874760 12.125849

TODO: option: get mol number for aligning H*-O distance with ci^2value

For right now:
just get highest prot ci^2, highest wat ci^2


"""

from __future__ import print_function
import ConfigParser
from operator import itemgetter
import re
import sys
import argparse

import numpy as np
from md_utils.md_common import InvalidDataError, warning, create_out_suf_fname, process_cfg, write_csv


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
EVBS_FILE = 'evb_list_file'
PROT_RES_MOL_ID = 'prot_res_mol_id'
# TODO: allow specify input base directory
IN_BASE_DIR = 'output_directory'
OUT_BASE_DIR = 'output_directory'
PRINT_CI_SUBSET = 'print_ci_subset_flag'
PRINT_CEC = 'print_cec_coords_flag'
MIN_MAX_CI_SQ = 'min_max_ci_sq'
PRINT_PER_FILE = 'print_output_each_file'
PRINT_PER_LIST = 'print_output_file_list'

# Defaults
DEF_CFG_FILE = 'evb_get_info.ini'
# Set notation
DEF_CFG_VALS = {EVBS_FILE: 'evb_list.txt',
                OUT_BASE_DIR: None,
                PRINT_CI_SUBSET: False,
                PRINT_CEC: False,
                MIN_MAX_CI_SQ: 0.475,
                PRINT_PER_FILE: True,
                PRINT_PER_LIST: False,
                }
REQ_KEYS = {PROT_RES_MOL_ID: int, }

# For evb file processing
SEC_TIMESTEP = 'timestep'
SEC_COMPLEX = 'complex_section'
SEC_STATES = 'states_section'
SEC_EIGEN = 'eigen_vector_section'
SEC_CEC = 'cec_coord_section'
SEC_DIAG = 'diagonal_energy_section'
SEC_END = 'end_of_timestep'

# For evb processing and output
TIMESTEP = 'timestep'
MOL_A = 'mol_A'
MOL_B = 'mol_B'
MAX_PROT_CI_SQ = 'max_prot_ci2'
MAX_HYD_CI_SQ = 'max_hyd_ci2'
MAX_PROT_STATE_NUM = 'max_prot_state_num'
MAX_HYD_STATE_NUM = 'max_state_num'
MAX_PROT_STATE_COUL = 'max_prot_state_coul'
MAX_HYD_STATE_COUL = 'max_state_coul'
MAX_CI_SQ_DIFF = 'max_ci_sq_diff'
COUL_DIFF = 'coul_diff'
MAX_PROT_CLOSE_WAT = 'max_prot_close_water_mol'
CEC_X = 'cec_x'
CEC_Y = 'cec_y'
CEC_Z = 'cec_z'
CI_FIELDNAMES = [TIMESTEP, MAX_PROT_CI_SQ, MAX_HYD_CI_SQ, MAX_PROT_STATE_COUL, MAX_HYD_STATE_COUL, MAX_CI_SQ_DIFF, COUL_DIFF]
CEC_COORD_FIELDNAMES = [TIMESTEP, CEC_X, CEC_Y, CEC_Z]

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
    cec_pat = re.compile(r"^CEC_COORDINATE.*")
    diag_pat = re.compile(r"^DIAGONAL .*")
    end_pat = re.compile(r"END_OF_COMPLEX 1.*")
    if time_pat.match(line):
        return SEC_TIMESTEP
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
        section = None
        # cec_array = np.zeros(3)
        states_array = None
        data_to_print = []
        subset_to_print = []
        for line in d:
            line = line.strip()
            if section is None:
                section = find_section_state(line)
                # print("hello {}".format(section))
                # If no state found, advance to next line.
                # Also advance to next line if the first line of a state does not contain data needed
                #   otherwise, go to next if block to get data from that line
                if section in [None, SEC_STATES, SEC_EIGEN, SEC_CEC, SEC_DIAG]:
                    continue
            if section == SEC_TIMESTEP:
                split_line = line.split()
                timestep = split_line[1]
                result = {TIMESTEP: timestep}
                # Reset variables
                # Start with an entry so the atom-id = index
                num_states = 0
                state_count = 0
                state_list = []
                max_prot_ci_sq = 0.0
                max_hyd_ci_sq = 0.0
                max_prot_state = None
                max_hyd_state = None
                section = None
            elif section == SEC_COMPLEX:
                split_line = line.split()
                num_states = int(split_line[2])
                states_per_shell = np.array(itemgetter(2, 5,7,9,11)(split_line), dtype=int)
                if states_array is None:
                    states_array =  states_per_shell
                else:
                    states_array = np.vstack((states_array, states_per_shell))
                section = None
            elif section == SEC_STATES:
                split_line = line.split()
                state_list.append({MOL_A: int(split_line[3]), MOL_B: int(split_line[4])})
                mol_B = int(split_line[4])
                # print('state: {}, mol_B: {}'.format(state_count, split_line))
                # if mol_B == cfg[PROT_RES_MOL_ID]:
                #     prot_state.append(state_count)
                # else:
                #     hyd_state.append(state_count)
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
            elif section == SEC_EIGEN:
                eigen_vector = map(float,line.split())
                eigen_sq = np.square(eigen_vector)
                for index, state in enumerate(state_list):
                    if state[MOL_B] == cfg[PROT_RES_MOL_ID]:
                        if eigen_sq[index] > max_prot_ci_sq:
                            max_prot_ci_sq = eigen_sq[index]
                            max_prot_state = index
                    else:
                        if state[MOL_A] == cfg[PROT_RES_MOL_ID]:
                            if eigen_sq[index] > max_hyd_ci_sq:
                                max_hyd_ci_sq = eigen_sq[index]
                                max_hyd_state = index
                result.update({MAX_PROT_CI_SQ: max_prot_ci_sq, MAX_HYD_CI_SQ: max_hyd_ci_sq,
                               MAX_CI_SQ_DIFF: max_prot_ci_sq - max_hyd_ci_sq})
                section = None
            elif section == SEC_CEC:
                # cec_array = np.vstack((cec_array, np.string2array(line)))
                cec_array = np.fromstring(line, sep=' ')
                result.update({CEC_X: cec_array[0], CEC_Y: cec_array[1], CEC_Z: cec_array[2]})
                section = None
            elif section == SEC_END:
                if max_prot_state is None:
                    prot_coul = np.nan
                # sometimes, there is only one state, so the diagonal array is a vector
                elif len(diag_array.shape) == 1:
                    prot_coul = diag_array[3] + diag_array[8]
                else:
                    prot_coul = diag_array[max_prot_state][3] + diag_array[max_prot_state][8]
                if max_hyd_state is None:
                    hyd_coul = np.nan
                elif len(diag_array.shape) == 1:
                    hyd_coul = diag_array[3] + diag_array[3]
                else:
                    hyd_coul = diag_array[max_hyd_state][3] + diag_array[max_hyd_state][8]
                result.update({MAX_PROT_STATE_COUL: prot_coul, MAX_HYD_STATE_COUL: hyd_coul, COUL_DIFF: hyd_coul - prot_coul})
                data_to_print.append(result)
                if cfg[PRINT_CI_SUBSET]:
                    if max_prot_ci_sq > cfg[MIN_MAX_CI_SQ] and max_hyd_ci_sq > cfg[MIN_MAX_CI_SQ]:
                        subset_to_print.append(result)
                section = None
    return data_to_print, subset_to_print


def process_evb_files(cfg):
    """
    Want to grab the timestep and highest prot ci^2, highest wat ci^2, and print them
    @param cfg: configuration data read from ini file
    @return: @raise InvalidDataError:
    """
    first_file_flag = True
    with open(cfg[EVBS_FILE]) as f:
        for evb_file in f:
            evb_file = evb_file.strip()
            if len(evb_file) > 0:
                data_to_print, subset_to_print = process_evb_file(evb_file, cfg)
                if cfg[PRINT_PER_FILE] is True:
                    f_out = create_out_suf_fname(evb_file, '_ci_sq', ext='.csv', base_dir=cfg[OUT_BASE_DIR])
                    write_csv(data_to_print, f_out, CI_FIELDNAMES, extrasaction="ignore")
                    print('Wrote file: {}'.format(f_out))
                    if cfg[PRINT_CI_SUBSET]:
                        f_out = create_out_suf_fname(evb_file, '_ci_sq_ts', ext='.csv', base_dir=cfg[OUT_BASE_DIR])
                        write_csv(subset_to_print, f_out, CI_FIELDNAMES, extrasaction="ignore")
                        print('Wrote file: {}'.format(f_out))
                    if cfg[PRINT_CEC]:
                        f_out = create_out_suf_fname(evb_file, '_cec', ext='.csv', base_dir=cfg[OUT_BASE_DIR])
                        write_csv(data_to_print, f_out, CEC_COORD_FIELDNAMES, extrasaction="ignore")
                        print('Wrote file: {}'.format(f_out))
                if cfg[PRINT_PER_LIST]:
                    if first_file_flag:
                        print_mode = 'w'
                        first_file_flag = False
                    else:
                        print_mode = 'a'
                    f_out = create_out_suf_fname(cfg[EVBS_FILE], '_ci_sq', ext='.csv', base_dir=cfg[OUT_BASE_DIR])
                    write_csv(data_to_print, f_out, CI_FIELDNAMES, extrasaction="ignore", mode=print_mode)
                    print('Wrote file: {}'.format(f_out))
                    if cfg[PRINT_CI_SUBSET]:
                        f_out = create_out_suf_fname(cfg[EVBS_FILE], '_ci_sq_ts', ext='.csv', base_dir=cfg[OUT_BASE_DIR])
                        write_csv(subset_to_print, f_out, CI_FIELDNAMES, extrasaction="ignore", mode=print_mode)
                        print('Wrote file: {}'.format(f_out))



def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

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
