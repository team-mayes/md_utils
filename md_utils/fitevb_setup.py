#!/usr/bin/env python
"""
Given a file with an xyz vector (space separated, no other data), return the maximum x, y, and z coordinates, plus the
values after a buffer distance is added
"""

from __future__ import print_function

import os
import sys
import argparse
import numpy as np
from md_utils.md_common import (InvalidDataError, warning, create_out_fname, write_csv, IO_ERROR, INPUT_ERROR,
                                GOOD_RET, INVALID_DATA)


try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser

__author__ = 'hmayes'


# Constants #
TOL = 0.0000001

# Config File Sections
SECTIONS = 'sections'
MAIN_SEC = 'main'
ARQ_SEC = 'ARQ'
ARQ2_SEC = 'ARQ2'
DA_GAUSS_SEC = 'DA_Gaussian'
VII_SEC = 'VII'
REP1_SEC = 'REP1'
PARAM_SECS = [DA_GAUSS_SEC, ARQ_SEC, ARQ2_SEC, VII_SEC, REP1_SEC]

# Config keys
GROUP_NAMES = 'group_names'
# NB: the config reader will read in capitalized letters as lower case. Thus, if any of these parameters use
# uppercase letters, they will not match input values! Thus, all these parameter names use exclusively lowercase
# letters, using the prefix "cap" to specify capitalized parameter names (from the corresponding paper). For example,
# to disambiguate the parameters 'B' and 'b', I use "cap_b" and "b"
FIT_PARAMS = {ARQ_SEC: ['r0_sc', 'lambda', 'r0_da', 'c', 'alpha', 'a_da', 'beta',
                        'b_da', 'epsinal', 'c_da', 'gamma', 'vij_const'],
              ARQ2_SEC: ['gamma', 'p', 'k', 'd_oo', 'beta',
                         'cap_r0_oo', 'p_prime', 'alpha', 'r0_oo', 'vij_const'],
              DA_GAUSS_SEC: ['c1', 'c2', 'c3'],
              VII_SEC: ['vii'],
              REP1_SEC: ['cap_b', 'b', 'b_prime', 'd_oo', 'cap_c', 'c', 'd_oh', 'cutoff_oo_low', 'cutoff_oo_high',
                         'cutoff_ho_low', 'cutoff_ho_high']
              }
SEC_PARAMS = 'parameters'
INP_FILE = 'new_input_file_name'
OUT_BASE_DIR = 'output_directory'
PARAM_NUM = 'param_num'
BEST_FILE = 'best_param_file'
SUMMARY_FILE = 'summary_file'
RESID_IN_BEST = 'resid_printed_in_best'
RESIDUAL = 'residual'

LOW = 'low'
HIGH = 'high'
DESCRIP = 'descrip'
PROP_LIST = [LOW, HIGH, DESCRIP]

# Defaults
MAIN_SEC_DEF_CFG_VALS = {INP_FILE: 'fit.inp',
                         OUT_BASE_DIR: None,
                         BEST_FILE: None,
                         PARAM_NUM: 0,
                         SUMMARY_FILE: None,
                         SECTIONS: None,
                         RESID_IN_BEST: False,
                         }
PARAM_SEC_REQ_CFG_VALS = {GROUP_NAMES: str,
                          }

DEF_CFG_FILE = 'fitevb_setup.ini'
DEF_BEST_FILE = 'fit.best'
DEF_GROUP_NAME = ''
DEF_DESCRIP = ''
PRINT_FORMAT = '{:12.6f}  {:12.6f}  : {}\n'


def read_cfg(floc):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param floc: The location of the file to read.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser()
    good_files = config.read(floc)
    if not good_files:
        raise IOError('Could not read file {}'.format(floc))
    proc = {}
    if MAIN_SEC not in config.sections():
        proc[MAIN_SEC] = []
    else:
        proc[MAIN_SEC] = config.items(MAIN_SEC)
    proc[MAIN_SEC].append([SECTIONS])
    for section in config.sections():
        if section != MAIN_SEC:
            raw_configs = config.items(section)
            proc[section] = raw_configs
            if len(proc[MAIN_SEC][-1]) == 1:
                proc[MAIN_SEC][-1].append([section])
            else:
                proc[MAIN_SEC][-1][1] = proc[MAIN_SEC][-1][1] + [section]
    return proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in best output file and generates new input files.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run. See example files in the test "
                                               "directory ({}). Note that in FitEVB, 'ARQ' is the same ARQ as in "
                                               "the evb parameter file and corresponds to the off-diagonal term from "
                                               "Maupin 2006 (http://pubs.acs.org/doi/pdf/10.1021/jp053596r). "
                                               "'ARQ2' corresponds to 'PT' with "
                                               "option 1 ('1-symmetric') and no exchange charges."
                                               "".format(DEF_CFG_FILE, 'tests/test_data/fitevb'),
                        default=DEF_CFG_FILE, type=read_cfg)
    parser.add_argument("-f", "--file", help="The fitevb output file to read, if some values are to be obtained from "
                                             "a previous fitEVB run.",
                        default=None)
    parser.add_argument("-r", "--resid", help="Flag to specify that the residual is printed at the end of the "
                                              "'best.inp' file, and thus should be accounted for in reading this file. "
                                              "The default is false.",
                        action='store_true')
    parser.add_argument("-s", "--summary_file", help="If a summary file name is specified, the program will append "
                                                     "results to a summary file and specify parameter value changes.",
                        default=None)
    parser.add_argument("-v", "--vii_fit", help="Flag to specify fitting the VII term. The default "
                                                "is false.",
                        action='store_true')
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
    except SystemExit as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    if args.file is not None and not os.path.isfile(args.file):
        if args.file == DEF_BEST_FILE:
            warning("Problems reading specified default fitevb output file ({}) in current directory. "
                    "A different name or directory can be specified with the optional "
                    "-f or --file arguments".format(args.file))
        else:
            warning("Problems reading specified fitevb output file: {}".format(args.file))
        parser.print_help()
        return args, IO_ERROR

    return args, GOOD_RET


def process_output_file(cfg):
    """
    Reads in an initial set of parameters values from a space-separated list, as provided by 'fit.best' output from
    fitEVB. The order is important; thus read through the sections and parameters from the (ordered) lists (specified
    in the constants
    @param cfg: the configuration for this run
    @return: initial values to use in fitting, with both the high and low values set to that initial value
    """
    vals = {}
    best_file = cfg[MAIN_SEC][BEST_FILE]
    if best_file is not None:
        raw_vals = np.loadtxt(best_file, dtype=np.float64)
        if len(raw_vals) != cfg[MAIN_SEC][PARAM_NUM]:
            raise InvalidDataError("The total number of parameters for the specified sections ({}) does not "
                                   "equal the total number of values ({}) in the specified fitEVB output file: {}"
                                   "".format(cfg[MAIN_SEC][PARAM_NUM], len(raw_vals), best_file))
        param_index = 0
        if best_file is not None:
            for section in cfg[MAIN_SEC][SECTIONS]:
                vals[section] = {}
                for param in FIT_PARAMS[section]:
                    vals[section][param] = {LOW: raw_vals[param_index], HIGH: raw_vals[param_index]}
                    param_index += 1
    return vals


def make_inp(initial_vals, cfg, fit_vii_flag):
    """
    cfg has the sections, default ranges for each parameter, and parameter descriptions
    Use that to seed the inp_vals (used for printing) and overwrite with initial values if a parameter
    is not to be fit in the current step.
    @param initial_vals: parameter values from last fitting iteration
    @param cfg: configuration values, whether the Vii parameter is to be fit
    @param fit_vii_flag: boolean which will specify which of two output options to use
    @return: nothing; will have written a new fit_evb input file when done
    """
    # dict to collect data to print; copy config values and (if specified) overwrite with values from fitEVB output
    inp_vals = {}

    for section in cfg[MAIN_SEC][SECTIONS]:
        inp_vals[section] = cfg[section].copy()
        if len(initial_vals) > 0:
            if section == VII_SEC:
                if not fit_vii_flag:
                    for param in FIT_PARAMS[section]:
                        for prop in initial_vals[section][param]:
                            inp_vals[section][param][prop] = initial_vals[section][param][prop]
            else:
                # if fit_vii_flag, all other parameters set to initial values
                if fit_vii_flag:
                    for param in FIT_PARAMS[section]:
                        for prop in initial_vals[section][param]:
                            inp_vals[section][param][prop] = initial_vals[section][param][prop]

    with open(cfg[MAIN_SEC][INP_FILE], 'w') as inp_file:
        for section in cfg[MAIN_SEC][SECTIONS]:
            inp_file.write('FIT  {} {}\n'.format(section, cfg[section][GROUP_NAMES]))
            for param in FIT_PARAMS[section]:
                inp_file.write(PRINT_FORMAT.format(inp_vals[section][param][LOW], inp_vals[section][param][HIGH],
                                                   inp_vals[section][param][DESCRIP]))
    print("Wrote file: {}".format(cfg[MAIN_SEC][INP_FILE]))


def process_raw_cfg(raw_cfg, resid_in_best, last_best_file, summary_file_name):
    """
    Add default information and perform error checking
    @param raw_cfg: configuration read by config parser
    @param resid_in_best: boolean to specify if an additional output (resid) is in the fit.best
    @param last_best_file: None or file location
    @param summary_file_name: None or file location
    @return: processed, error-checked config
    """
    cfgs = {}
    # Process raw values
    for section in raw_cfg:
        section_dict = {}
        if section == MAIN_SEC:
            for entry in raw_cfg[section]:
                section_dict[entry[0]] = entry[1]
        else:
            section_dict = {}
            for entry in raw_cfg[section]:
                if entry[0] == GROUP_NAMES:
                    section_dict[entry[0]] = entry[1]
                else:
                    vals = [x.strip() for x in entry[1].split(',')]
                    if len(vals) == 2:
                        vals.append(DEF_DESCRIP)
                    try:
                        section_dict[entry[0]] = {LOW: float(vals[0]), HIGH: float(vals[1]), DESCRIP: vals[2]}
                    except ValueError:
                        raise InvalidDataError("Check input. In configuration file section '{}', expected "
                                               "comma-separated numerical lower range value, upper-range value, and "
                                               "(optional) description (i.e. '-10,10,d_OO') for key '{}'. "
                                               "Found: {}".format(section, entry[0], entry[1]))
        cfgs[section] = section_dict

    # Check for defaults
    for section in cfgs:
        if section == MAIN_SEC:
            for cfg in MAIN_SEC_DEF_CFG_VALS:
                if cfg not in cfgs[section]:
                    cfgs[section][cfg] = MAIN_SEC_DEF_CFG_VALS[cfg]
        else:
            if section in PARAM_SECS:
                for param in PARAM_SEC_REQ_CFG_VALS:
                    if param not in cfgs[section]:
                        raise InvalidDataError("In configuration file section '{}', missing parameter '{}'."
                                               "".format(section, param))
            else:
                raise InvalidDataError("Found section '{}' in the configuration file. This program expects only the "
                                       "following sections: {}".format(section, [MAIN_SEC] + PARAM_SECS))
    # Add main section with defaults if the optional main section is missing
    if MAIN_SEC not in cfgs:
        cfgs[MAIN_SEC] = MAIN_SEC_DEF_CFG_VALS
    if resid_in_best:
        cfgs[MAIN_SEC][PARAM_NUM] = 1
        cfgs[MAIN_SEC][RESID_IN_BEST] = True
    else:
        cfgs[MAIN_SEC][PARAM_NUM] = 0
        cfgs[MAIN_SEC][RESID_IN_BEST] = False
    # Ensure all required info is present for specified sections.
    for section in cfgs:
        if section == MAIN_SEC:
            for param in cfgs[section]:
                if param not in MAIN_SEC_DEF_CFG_VALS:
                    raise InvalidDataError("The configuration file contains parameter '{}' in section '{}'; expected "
                                           "only the following parameters for this section: {}"
                                           "".format(param, section, MAIN_SEC_DEF_CFG_VALS.keys()))
            if cfgs[section][OUT_BASE_DIR] is None:
                cfgs[section][OUT_BASE_DIR] = ""

            cfgs[section][INP_FILE] = os.path.abspath(os.path.join(cfgs[section][OUT_BASE_DIR],
                                                                   cfgs[section][INP_FILE]))
            if not os.path.exists(os.path.dirname(cfgs[section][INP_FILE])):
                raise IOError("Invalid directory provided in configuration section '{}' "
                              "parameter '{}': {}".format(section, OUT_BASE_DIR, cfgs[section][OUT_BASE_DIR]))
        else:
            for param in FIT_PARAMS[section]:
                cfgs[MAIN_SEC][PARAM_NUM] += 1
                if param not in cfgs[section]:
                    raise InvalidDataError("The configuration file is missing parameter '{}' in section '{}'. "
                                           "Check input.".format(param, section))
            for param in cfgs[section]:
                if param not in FIT_PARAMS[section] and param != GROUP_NAMES:
                    raise InvalidDataError("The configuration file contains parameter '{}' in section '{}'; expected "
                                           "only the following parameters for this section: {}"
                                           "".format(param, section, FIT_PARAMS[section]))

    if last_best_file is not None:
        if os.path.exists(last_best_file):
            cfgs[MAIN_SEC][BEST_FILE] = last_best_file
        else:
            raise IOError("Invalid '{}' provided".format(last_best_file))
    if summary_file_name is not None:
        if cfgs[MAIN_SEC][BEST_FILE] is None:
            raise InvalidDataError("No '{}' specified, which is required with a specified '{}'"
                                   "".format(BEST_FILE, SUMMARY_FILE))
        if os.path.exists(summary_file_name):
            cfgs[MAIN_SEC][SUMMARY_FILE] = summary_file_name
        else:
            raise IOError("Invalid '{}' provided".format(summary_file_name))

    return cfgs


def get_param_info(cfg):
    """
    Convert to tracking by location rather than section
    @param cfg: configuration for run
    @return: param info by order found in fit.best
    """
    headers = []
    low = []
    high = []
    for section in cfg[MAIN_SEC][SECTIONS]:
        for param in FIT_PARAMS[section]:
            low.append(cfg[section][param][LOW])
            high.append(cfg[section][param][HIGH])
            headers.append(cfg[section][param][DESCRIP])
    if cfg[MAIN_SEC][RESID_IN_BEST]:
        low.append(0)
        high.append(np.inf)
        headers.append(RESIDUAL)
    return np.array(low), np.array(high), headers


def make_summary(cfg):
    """
    If the option is specified, add the last best fit output file to the list of outputs and evaluate changes
    @param cfg: configuration for the run
    @return:
    """
    best_file = cfg[MAIN_SEC][BEST_FILE]
    summary_file = cfg[MAIN_SEC][SUMMARY_FILE]

    low, high, headers = get_param_info(cfg)
    latest_output = np.loadtxt(best_file, dtype=np.float64)

    if os.path.isfile(summary_file):
        last_row = None
        percent_diffs = []
        previous_output = np.loadtxt(summary_file, dtype=np.float64)
        all_output = np.vstack((previous_output, latest_output))
        for row in all_output:
            if last_row is not None:
                diff = row - last_row
                percent_diff = {}
                # Check data for small values, hitting upper or lower bound, and calc % diff
                for index, val in enumerate(np.nditer(row)):
                    if abs(val) < TOL:
                        warning("Small value ({}) encountered for parameter {} (col {})"
                                "".format(val, headers[index], index))
                    if abs(diff[index]) > TOL:
                        if abs(last_row[index]) > TOL:
                            percent_diff[headers[index]] = round(diff[index] / last_row[index] * 100, 2)
                        else:
                            if abs(diff[index]) > TOL:
                                percent_diff[headers[index]] = np.inf
                        if abs(val-low[index]) < TOL:
                            warning("Value ({}) near lower bound ({}) encountered for parameter {} (col {})."
                                    "".format(val, low[index], headers[index], index))
                        if abs(val-high[index]) < TOL:
                            warning("Value ({}) near upper bound ({}) encountered for parameter {} (col {})."
                                    "".format(val, high[index], headers[index], index))
                percent_diffs.append(percent_diff)
            last_row = row
        if len(percent_diffs) > 0:
            max_percent_diff = 0
            max_diff_param = None
            for param, val in percent_diffs[-1].items():
                if abs(val) > abs(max_percent_diff):
                    max_percent_diff = val
                    max_diff_param = param
            print("Maximum (absolute value) percent difference from last read line is {} % for parameter '{}'."
                  "".format(max_percent_diff, max_diff_param))
            if cfg[MAIN_SEC][RESID_IN_BEST]:
                print("Percent change in residual: {} %".format(percent_diffs[-1][RESIDUAL]))

        # format for gnuplot and np.loadtxt
        f_out = create_out_fname(summary_file, suffix='_perc_diff', ext='.csv', base_dir=cfg[MAIN_SEC][OUT_BASE_DIR])
        write_csv(percent_diffs, f_out, headers, extrasaction="ignore")

        f_out = create_out_fname(summary_file, ext='.csv', base_dir=cfg[MAIN_SEC][OUT_BASE_DIR])
        with open(f_out, 'w') as s_file:
            s_file.write(','.join(headers)+'\n')
            np.savetxt(s_file, all_output, fmt='%8.6f', delimiter=',')
        print('Wrote file: {}'.format(f_out))

        # in addition to csv (above), print format for gnuplot and np.loadtxt
        with open(summary_file, 'w') as s_file:
            np.savetxt(s_file, all_output, fmt='%12.6f')
        print("Wrote file: {}".format(summary_file))
    else:
        # have this as sep statement, because now printing a 1D array, handled differently than 2D array (newline=' ')
        with open(summary_file, 'w') as s_file:
            np.savetxt(s_file, latest_output, fmt='%12.6f', newline=' ')
        print("Wrote results from {} to new summary file {}".format(best_file, summary_file))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret
    raw_cfg = args.config

    try:
        cfg = process_raw_cfg(raw_cfg, args.resid, args.file, args.summary_file)
        initial_vals = process_output_file(cfg)
        if args.summary_file is not None:
            make_summary(cfg)
        make_inp(initial_vals, cfg, args.vii_fit)
    except IOError as e:
        warning("IOError:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Invalid data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
