#!/usr/bin/env python
"""
Given a file with an xyz vector (space separated, no other data), return the maximum x, y, and z coordinates, plus the
values after a buffer distance is added
"""

from __future__ import print_function
import ConfigParser

import numpy as np
from md_utils.md_common import InvalidDataError, warning, process_cfg
import sys
import argparse

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
DA_GAUSS_SEC = 'DA_Gaussian'

# Config keys
SECTIONS = 'sections'
GROUP_NAMES = 'group_names'
VALS = 'vals'

DEF_CFG_VALS = {}
REQ_KEY_DEFS = {GROUP_NAMES: str, VALS: str}


# Config keys
VII_FIT = 'vii_fit_flag'
DA_GAUSS_GROUPS = 'DA_Gaussian_group_names'
C1_LOW = 'c1_low'
C1_HIGH = 'c1_high'
C2_LOW = 'c2_low'
C2_HIGH = 'c2_high'
C3_LOW = 'c3_low'
C3_HIGH = 'c3_high'
VII_GROUP = 'VII_group_name'
VII_LOW = 'Vii_low'
VII_HIGH = 'Vii_high'
REP1_GROUP = 'repulsive_group_name'
CAP_B_LOW = 'B_low'
CAP_B_HIGH = 'B_high'
B_LOW = 'b_low'
B_HIGH = 'b_high'
B_PRIME_LOW = 'b_prime_low'
B_PRIME_HIGH = 'b_prime_high'
D_OO_LOW = 'd_OO_low'
D_OO_HIGH = 'd_OO_high'
CAP_C_LOW = 'C_low'
CAP_C_HIGH = 'C_high'
C_LOW = 'c_low'
C_HIGH = 'c_high'
D_OH_LOW = 'd_OH_low'
D_OH_HIGH = 'd_OH_high'
CUTOFF_OO_LOW_LOW = 'cutoff_OO_low_low'
CUTOFF_OO_LOW_HIGH = 'cutoff_OO_low_high'
CUTOFF_OO_HIGH_LOW = 'cutoff_OO_high_low'
CUTOFF_OO_HIGH_HIGH = 'cutoff_OO_high_high'
CUTOFF_HO_LOW_LOW = 'cutoff_OH_low_low'
CUTOFF_HO_LOW_HIGH = 'cutoff_OH_low_high'
CUTOFF_HO_HIGH_LOW = 'cutoff_OH_high_low'
CUTOFF_HO_HIGH_HIGH = 'cutoff_OH_high_high'

C1 = '_c1'
C2 = '_c2'
C3 = '_c3'
VII = 'Vii'
CAP_B = 'B MS-EVB3 diabatic-correction'
B = 'b'
B_PRIME = "b'"
D_OO = 'd_OO'
CAP_C = 'C'
C = 'c'
D_OH = 'd_OH'
CUTOFF_OO_LOW = 'cutoff_OO_low'
CUTOFF_OO_HIGH = 'cutoff_OO_high'
CUTOFF_HO_LOW = 'cutoff_HO_low'
CUTOFF_HO_HIGH = 'cutoff_HO_high'

LOW = 'low'
HIGH = 'high'
DESCRIP = 'descrip'
PROP_LIST = [LOW, HIGH, DESCRIP]

DA_GAUSS_KEYS = [C1, C2, C3]
VII_KEYS = [VII]
REP1_KEYS =  [CAP_B, B, B_PRIME, D_OO, CAP_C, C, D_OH,
                  CUTOFF_OO_LOW, CUTOFF_OO_HIGH,
                  CUTOFF_HO_LOW, CUTOFF_HO_HIGH, ]



PARAM_LIST = [C1_LOW, C1_HIGH,
              C2_LOW, C2_HIGH,
              C3_LOW, C3_HIGH,
              VII_LOW, VII_HIGH,
              CAP_B_LOW, CAP_B_HIGH,
              B_LOW, B_HIGH,
              B_PRIME_LOW, B_PRIME_HIGH,
              D_OO_LOW, D_OO_HIGH,
              CAP_C_LOW, CAP_C_HIGH,
              C_LOW, C_HIGH,
              D_OH_LOW, D_OH_HIGH,
              CUTOFF_OO_LOW_LOW, CUTOFF_OO_LOW_HIGH,
              CUTOFF_OO_HIGH_LOW, CUTOFF_OO_HIGH_HIGH,
              CUTOFF_HO_LOW_LOW, CUTOFF_HO_LOW_HIGH,
              CUTOFF_HO_HIGH_LOW, CUTOFF_HO_HIGH_HIGH, ]
VII_PARAM_LIST = [VII_LOW, VII_HIGH,]
NOT_VII_PARAM_LIST = [C1_LOW, C1_HIGH,
              C2_LOW, C2_HIGH,
              C3_LOW, C3_HIGH,
              CAP_B_LOW, CAP_B_HIGH,
              B_LOW, B_HIGH,
              B_PRIME_LOW, B_PRIME_HIGH,
              D_OO_LOW, D_OO_HIGH,
              CAP_C_LOW, CAP_C_HIGH,
              C_LOW, C_HIGH,
              D_OH_LOW, D_OH_HIGH,
              CUTOFF_OO_LOW_LOW, CUTOFF_OO_LOW_HIGH,
              CUTOFF_OO_HIGH_LOW, CUTOFF_OO_HIGH_HIGH,
              CUTOFF_HO_LOW_LOW, CUTOFF_HO_LOW_HIGH,
              CUTOFF_HO_HIGH_LOW, CUTOFF_HO_HIGH_HIGH, ]

INP_FILE = 'new_input_file_name'
FORMAT = '%12.6f  %12.6f  : %s\n'

# DEF_CFG_VALS = {VII_FIT: False,
#                 DA_GAUSS_GROUPS: 'GLU-P_H2O H3O_GLU-E',
#                 C1_LOW: -50.00,
#                 C1_HIGH: -15.00,
#                 C2_LOW: 2.00,
#                 C2_HIGH: 6.00,
#                 C3_LOW: 1.00,
#                 C3_HIGH: 2.00,
#                 VII_GROUP: 'GLU-P',
#                 VII_LOW: -30.0,
#                 VII_HIGH: 10.0,
#                 REP1_GROUP: 'GLU-E',
#                 CAP_B_LOW: 0.001,
#                 CAP_B_HIGH: 0.100,
#                 B_LOW: 0.1,
#                 B_HIGH: 2.000,
#                 B_PRIME_LOW: 0.001,
#                 B_PRIME_HIGH: 2.000,
#                 D_OO_LOW: 2.400,
#                 D_OO_HIGH: 2.400,
#                 CAP_C_LOW: 0.010,
#                 CAP_C_HIGH: 5.00,
#                 C_LOW: 0.05,
#                 C_HIGH: 5.00,
#                 D_OH_LOW: 1.00,
#                 D_OH_HIGH: 1.00,
#                 CUTOFF_OO_LOW_LOW: 3.500,
#                 CUTOFF_OO_LOW_HIGH: 3.500,
#                 CUTOFF_OO_HIGH_LOW: 4.000,
#                 CUTOFF_OO_HIGH_HIGH: 4.000,
#                 CUTOFF_HO_LOW_LOW: 3.500,
#                 CUTOFF_HO_LOW_HIGH: 3.500,
#                 CUTOFF_HO_HIGH_LOW: 4.000,
#                 CUTOFF_HO_HIGH_HIGH: 4.000,
#                 INP_FILE: 'fit.inp',
#                 }

# Defaults
DEF_CFG_FILE = 'fit_evb_setup.ini'
DEF_BEST_FILE = 'fit.best'
DEF_VII_FIT_FLAG = False

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
    proc = {}
    for section in config.sections():
        temp = config.items(section)
        print(temp)
        # proc[section] = cfg_proc(dict(config.items(section), DEF_CFG_VALS, REQ_KEY_DEFS))
    # main_proc = cfg_proc(dict(config.items(MAIN_SEC)), MAIN_DEF_CFGS, MAIN_REQ_KEY_DEFS)
    # for each in sections():

    print(proc)

    # main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)
    return proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in best output file and generates new input files.'
                                                 ' .')
    parser.add_argument("-f", "--file", help="The fit evb output file to read. The default is {}".format(DEF_BEST_FILE),
                        default=DEF_BEST_FILE)
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "See the example file /test/test_data/evbd2d/process_evb.ini. "
                                               "The default file name is lammps_dist_pbc.ini, located in the "
                                               "base directory where the program as run.",
                        default=DEF_CFG_FILE, type=read_cfg)
    # parser.add_argument("-v", "--fit_vii", help="If flag is false (default), fits everything but Vii. Otherwise, "
    #                                             "the reverse.",
    #                     default=DEF_VII_FIT_FLAG)
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


def process_file(data_file):
    raw_vals = np.loadtxt(data_file,dtype=np.float64)
    vals = {}
    for index, val in enumerate(raw_vals):
        vals[PARAM_LIST[index*2]] = val
        vals[PARAM_LIST[index*2+1]] = val
    return vals


def make_diag_inp(initial_vals, cfg):
    inp_vals = {}
    if cfg[VII_FIT]:
        for param in NOT_VII_PARAM_LIST:
            inp_vals[param] = initial_vals[param]
        for param in VII_PARAM_LIST:
            inp_vals[param] = cfg[param]
    else:
        for param in NOT_VII_PARAM_LIST:
            inp_vals[param] = cfg[param]
        for param in VII_PARAM_LIST:
            inp_vals[param] = initial_vals[param]
    to_print = []
    # print(NEW_PARAM_LIST)
    # for item in NEW_PARAM_LIST:
    #     to_print.append([inp_vals["{}_LOW".format(item)], inp_vals["{}_HIGH".format(item)], item])
    # to_print.append([inp_vals[C1_LOW], inp_vals[C1_HIGH], C1])
    # to_print.append([inp_vals[C2_LOW], inp_vals[C2_HIGH], C2])
    # to_print.append([inp_vals[C3_LOW], inp_vals[C3_HIGH], C3])
    # to_print.append([inp_vals[VII_LOW], inp_vals[VII_HIGH], VII])
    #
    # to_print.append([inp_vals[CAP_B_LOW], inp_vals[CAP_B_HIGH], CAP_B])
    # to_print.append([inp_vals[B_LOW], inp_vals[B_HIGH], B])
    # to_print.append([inp_vals[B_PRIME_LOW], inp_vals[B_PRIME_HIGH], B_PRIME])
    # to_print.append([inp_vals[D_OO_LOW], inp_vals[D_OO_HIGH], D_OO])
    # to_print.append([inp_vals[CAP_C_LOW], inp_vals[CAP_C_HIGH], C])
    # to_print.append([inp_vals[C_LOW], inp_vals[C_HIGH], C])
    # to_print.append([inp_vals[D_OH_LOW], inp_vals[D_OH_HIGH], D_OH])
    # to_print.append([inp_vals[CUTOFF_OO_LOW_LOW], inp_vals[CUTOFF_OO_LOW_HIGH], CUTOFF_OO_LOW])
    # to_print.append([inp_vals[CUTOFF_OO_HIGH_LOW], inp_vals[CUTOFF_OO_HIGH_HIGH], CUTOFF_OO_HIGH])
    # to_print.append([inp_vals[CUTOFF_HO_LOW_LOW], inp_vals[CUTOFF_HO_LOW_HIGH], CUTOFF_HO_LOW])
    # to_print.append([inp_vals[CUTOFF_HO_HIGH_LOW], inp_vals[CUTOFF_HO_HIGH_HIGH], CUTOFF_HO_HIGH])
    with open(cfg[INP_FILE], 'w') as inpfile:
        inpfile.write('FIT  DA_Gaussian {}\n'.format(cfg[DA_GAUSS_GROUPS]))
        for line in to_print[0:3]:
            inpfile.write(FORMAT % tuple(line))
        inpfile.write('\nFIT  VII {}\n'.format(cfg[VII_GROUP]))
        inpfile.write(FORMAT % tuple(to_print[3]))
        inpfile.write('\nFIT  REP1 {}\n'.format(cfg[REP1_GROUP]))
        for line in to_print[4:]:
            inpfile.write(FORMAT % tuple(line))



def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    cfg = args.config
    # try:
    #     initial_vals = process_file(args.file)
    #     make_diag_inp(initial_vals, cfg)
    # except IOError as e:
    #     warning("Problems reading file:", e)
    #     return IO_ERROR
    # except InvalidDataError as e:
    #     warning("Problems reading data:", e)
    #     return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
