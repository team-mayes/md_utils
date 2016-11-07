#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Given an initial set of parameters, it will create a parameter file and a copy of it for records.
"""
import argparse
import os
import sys
import shutil
import numpy as np
from scipy.optimize import minimize
from collections import OrderedDict
from subprocess import check_output

from md_utils.md_common import (InvalidDataError, GOOD_RET, INPUT_ERROR, warning, IO_ERROR, process_cfg,
                                TemplateNotReadableError, MISSING_SEC_HEADER_ERR_MSG, create_out_fname, read_tpl,
                                conv_num)
from md_utils.fill_tpl import (OUT_DIR, MAIN_SEC, TPL_VALS_SEC, TPL_EQS_SEC,
                               VALID_SEC_NAMES, TPL_VALS, TPL_EQ_PARAMS, NEW_FNAME, fill_save_tpl)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

# Constants #
# config keys #
TRIAL_NAME = 'trial_name'
PAR_TPL = 'par_tpl'
PAR_COPY_NAME = 'par_copy'
PAR_FILE_NAME = 'par_name'
COPY_DIR = 'copy_dir'
BASH_DRIVER = 'bash_driver'
CONV_CUTOFF = 'converge_tolerance'
MAX_ITER = 'max_iterations'
NUM_PARAM_DECIMALS = 'num_decimals'
PRINT_INFO = 'print_status'

# for storing config data
MAX_STEP = 'max_step_size'
MIN_STEP = 'min_step_size'

# Defaults
DEF_CFG_FILE = 'conv_evb_par.ini'
DEF_TPL = 'evb_par.tpl'
DEF_CONV_CUTOFF = 0.001
DEF_MAX_ITER = 25
DEF_PARAM_DEC = 6
DEF_CFG_VALS = {TRIAL_NAME: None, PAR_TPL: DEF_TPL, OUT_DIR: None, PAR_FILE_NAME: None,
                PAR_COPY_NAME: None, COPY_DIR: None, CONV_CUTOFF: DEF_CONV_CUTOFF, MAX_ITER: DEF_MAX_ITER,
                PRINT_INFO: False, NUM_PARAM_DECIMALS: DEF_PARAM_DEC,
                }
REQ_KEYS = {BASH_DRIVER: str}


# Logic #

# CLI Processing #

def process_conv_tpl_keys(raw_key_val_tuple_list):
    """
    In case there are multiple (comma-separated) values, split on comma and strip. Do not convert to int or float;
       that will be done later if needed for equations
    The program creates the val_dict and multi_val_param_list (fed in empty)

    @param raw_key_val_tuple_list: key-value dict read from configuration file
    @return val_dict: a dictionary of values (strings); check for commas to indicate multiple parameters
    """
    val_dict = OrderedDict()
    max_step_dict = OrderedDict()
    min_step_dict = {}
    for key, val in raw_key_val_tuple_list:
        val_list = [x.strip() for x in val.split(',')]
        val_num = len(val_list)
        if val_num == 1:
            # if it can be converted, do so; this helps with my printing formatting
            val_dict[key] = conv_num(val_list[0])
        elif val_num == 3:
            val_list = map(float, val_list)
            if abs(val_list[2]) > abs(val_list[1]):
                raise InvalidDataError("For key '{}', read '{}' which specifies a smaller max_step_size is than "
                                       "the min_step_size (for each key to be optimized, provide x_0, "
                                       "max_step_size, min_step_size). Check input data.".format(key, val))
            val_dict[key] = val_list[0]
            max_step_dict[key] = val_list[1]
            min_step_dict[key] = abs(val_list[2])
        else:
            raise InvalidDataError("For key '{}', {} values were found ({}). However, each key must have either one "
                                   "value to be used, or three comma-separated values (x_0, max_step_size, "
                                   "min_step_size) indicating that the parameter is to be optimized. "
                                   "Check input data.".format(key, val_num, val))
    return val_dict, max_step_dict, min_step_dict


def read_cfg(f_loc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param f_loc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser()
    try:
        good_files = config.read(f_loc)
    except MissingSectionHeaderError:
        raise InvalidDataError(MISSING_SEC_HEADER_ERR_MSG.format(f_loc))
    if not good_files:
        raise IOError('Could not read file {}'.format(f_loc))

    # Start with empty data structures to be filled
    proc = {TPL_VALS: {}, TPL_EQ_PARAMS: [], MAX_STEP: OrderedDict(), MIN_STEP: {}}

    if MAIN_SEC not in config.sections():
        raise InvalidDataError("The configuration file is missing the required '{}' section".format(MAIN_SEC))

    for section in config.sections():
        if section == MAIN_SEC:
            try:
                proc.update(cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS))
            except InvalidDataError as e:
                if 'Unexpected key' in e.message:
                    raise InvalidDataError(e.message + " Does this belong \nin a template value section such as '[{}]'?"
                                                       "".format(TPL_VALS_SEC))
        elif section in [TPL_VALS_SEC, TPL_EQS_SEC]:
            val_dict, max_step_dict, min_step_dict = process_conv_tpl_keys(config.items(section))
            if section == TPL_EQS_SEC:
                # just keep the names, so we know special processing is required
                proc[TPL_EQ_PARAMS] = val_dict.keys()
            proc[TPL_VALS].update(val_dict)
            proc[MAX_STEP].update(max_step_dict)
            proc[MIN_STEP].update(min_step_dict)
        else:
            raise InvalidDataError("Section name '{}' in not one of the valid section names: {}"
                                   "".format(section, VALID_SEC_NAMES))
    return proc


def parse_cmdline(argv=None):
    """
    Returns the parsed argument list and return code.
    :param argv: A list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates evb parameter files to converge parameters.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)
    parser.add_argument("-f", "--par_name", help="File name for the parameter file to be created by filling the "
                                                 "evb parameter template file. It can also be specified in the "
                                                 "configuration file. If specified in both places, the command line "
                                                 "option will take precedence.",
                        default=None)

    args = None
    try:
        args = parser.parse_args(argv)
        if not os.path.isfile(args.config[PAR_TPL]):
            if args.config[PAR_TPL] == DEF_TPL:
                error_message = "Check input for the configuration key '{}'; " \
                                "could not find the default template file: {}"
            else:
                error_message = "Could not find the template file specified with " \
                                "the configuration key '{}': {}"
            raise IOError(error_message.format(PAR_TPL, args.config[PAR_TPL]))
        if args.par_name is not None:
            args.config[PAR_FILE_NAME] = args.par_name
        if args.config[PAR_FILE_NAME] is None:
            raise InvalidDataError("Missing required key '{}', which can be specified in the "
                                   "required either in the command line for configuration file."
                                   "".format(PAR_FILE_NAME))
        for config_param in [BASH_DRIVER]:
            if not os.path.isfile(args.config[config_param]):
                raise IOError("Missing file specified for key '{}': {}".format(config_param, args.config[config_param]))
    except (KeyError, InvalidDataError, IOError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


def copy_par_file(cfg, tpl_vals_dict, print_info=False):
    """
    To keep a copy of a par file, make the new file name and copy the previously created par file
    @param cfg: configuration for run
    @param tpl_vals_dict: dictionary to fill strings
    @param print_info: boolean to determine if to print to standard out that a copy was made
    @return: KeyError if required variable is not defined
    """
    if cfg[TRIAL_NAME] is not None:
        try:
            tpl_vals_dict[TRIAL_NAME] = cfg[TRIAL_NAME].format(**tpl_vals_dict)
        except KeyError as e:
            raise KeyError("Missing key name {} required for '{}': '{}'. Program will terminate."
                           "".format(e, TRIAL_NAME, cfg[TRIAL_NAME]))

    try:
        par_copy = cfg[PAR_COPY_NAME].format(**tpl_vals_dict)
    except KeyError as e:
        raise KeyError("Missing key name {} required for '{}': '{}'. Copy of par file will not be made."
                       "".format(e, PAR_COPY_NAME, cfg[PAR_COPY_NAME]))
    par_copy_fname = create_out_fname(par_copy, base_dir=cfg[COPY_DIR])
    shutil.copyfile(tpl_vals_dict[NEW_FNAME], par_copy_fname)
    if print_info:
        print(" Copied to: {}".format(par_copy_fname))


def eval_eqs(cfg, tpl_vals_dict):
    """
    Evaluates equations based on
    @param cfg: configuration for the run
    @param tpl_vals_dict: dictionary of variable values to be used to evaluate equations and fill templates
    """
    for eq_param in cfg[TPL_EQ_PARAMS]:
        try:
            string_to_eval = cfg[TPL_VALS][eq_param].format(**tpl_vals_dict)
        except KeyError as e:
            raise KeyError("Missing parameter value {} needed to evaluate '{}' for the parameter '{}'."
                           "".format(e, tpl_vals_dict[eq_param], eq_param))
        try:
            tpl_vals_dict[eq_param] = eval(string_to_eval)
        except NameError:
            raise InvalidDataError("Could not evaluate the string '{}' specifying the value for the parameter "
                                   "'{}'. Check equation order, equations, and/or parameter values."
                                   "".format(string_to_eval, eq_param))


def min_convex_param(cfg, iteration_dict, tpl_dict, tpl_str):
    # this allows us to skip an unneeded evaluation when moving from an optimized parameter to the next in line
    next_param = False
    total_iter_num = 0
    for final_param in range(len(iteration_dict), 0, -1):
        for key, step in iteration_dict.items()[0:final_param]:
            best_result = np.inf
            min_val = None
            mid_val = None
            max_val = None
            iter_num = 0
            while abs(step) >= cfg[MIN_STEP][key]:
                if not next_param:
                    eval_eqs(cfg, tpl_dict)
                    fill_save_tpl(cfg, tpl_str, tpl_dict, cfg[PAR_TPL], cfg[PAR_FILE_NAME])
                    if cfg[PAR_COPY_NAME] is not None:
                        copy_par_file(cfg, tpl_dict)

                trial_val = tpl_dict[key]

                if next_param:
                    next_param = False
                else:
                    trial_result = float(check_output([cfg[BASH_DRIVER]]).strip())
                iter_num += 1
                total_iter_num += 1
                if abs(trial_result - best_result) < cfg[CONV_CUTOFF]:
                    print("Minimized '{}' within the specified convergence tolerance ({}). Best parameter: {}. "
                          "Best result: {}. "
                          "Program will continue.".format(key, cfg[CONV_CUTOFF], trial_val, trial_result))
                    next_param = True
                    break
                elif iter_num > cfg[MAX_ITER]:
                    print("Reached the maximum number of iterations ({}) while minimizing '{}'. Best result: {}. "
                          "Program will continue.".format(cfg[MAX_ITER], key, best_result))
                    next_param = True
                    break
                elif trial_result < best_result:
                    best_result = trial_result
                # Todo: delete print line
                print("yo", key, step, trial_val, trial_result)

                # when just getting started..
                if min_val is None and mid_val is None:
                    min_val = (trial_val, trial_result)
                    tpl_dict[key] = trial_val + step
                elif mid_val is None and max_val is None:
                    if trial_result < min_val[1]:
                        mid_val = (trial_val, trial_result)
                        tpl_dict[key] = trial_val + step
                    else:
                        max_val = (trial_val, trial_result)
                        mid_val = min_val
                        min_val = None
                        tpl_dict[key] = mid_val[0] - step
                # Now I should have run the script at least 3 times, with exactly one val as None
                else:
                    if max_val is None:
                        max_val = (trial_val, trial_result)
                    elif min_val is None:
                        min_val = (trial_val, trial_result)
                    else:
                        mid_val = (trial_val, trial_result)
                    # if mid has the lowest result, time to reduce the step size
                    if mid_val[1] < min_val[1] and mid_val[1] < max_val[1]:
                        step /= 2.0
                        if abs(step) < cfg[MIN_STEP][key]:
                            print("Minimized '{}' within specified tolerance (min step size) of {}. "
                                  "Best parameter: {}. Best result: {}. Program will continue."
                                  "".format(key, cfg[MIN_STEP][key], mid_val[0], mid_val[1]))
                            next_param = True
                            break
                        if min_val[1] < max_val[1]:
                            tpl_dict[key] = mid_val[0] - step
                            max_val = mid_val
                        else:
                            tpl_dict[key] = mid_val[0] + step
                            min_val = mid_val
                        mid_val = None
                    # otherwise, shift values around
                    elif min_val[1] < max_val[1]:
                        max_val = mid_val
                        mid_val = min_val
                        min_val = None
                        tpl_dict[key] = mid_val[0] - step
                    else:
                        min_val = mid_val
                        mid_val = max_val
                        max_val = None
                        tpl_dict[key] = mid_val[0] + step
    print("Total number of iterations: {}".format(total_iter_num))


def obj_fun(x0, cfg, tpl_dict, tpl_str):
    """Objective function to be minimized"""
    for param_num, param_name in enumerate(cfg[MAX_STEP]):
        tpl_dict[param_name] = round(x0[param_num], cfg[NUM_PARAM_DECIMALS])

    eval_eqs(cfg, tpl_dict)
    fill_save_tpl(cfg, tpl_str, tpl_dict, cfg[PAR_TPL], cfg[PAR_FILE_NAME], print_info=cfg[PRINT_INFO])
    if cfg[PAR_COPY_NAME] is not None:
        copy_par_file(cfg, tpl_dict, print_info=cfg[PRINT_INFO])
    trial_result = float(check_output([cfg[BASH_DRIVER], tpl_dict[NEW_FNAME]]).strip())
    if cfg[PRINT_INFO]:
        print(x0, trial_result)
    return trial_result


def min_params(cfg, tpl_dict, tpl_str):
    num_opt_params = len(cfg[MAX_STEP])
    x0 = np.empty(num_opt_params)
    for param_num, param_name in enumerate(cfg[MAX_STEP]):
        x0[param_num] = cfg[TPL_VALS][param_name]

    res = minimize(obj_fun, x0, args=(cfg, tpl_dict, tpl_str), method='Powell',
                   options={'xtol': 1e-3, 'disp': True})
    print(res.x)


def main(argv=None):
    """
    Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config

    try:
        tpl_str = read_tpl(cfg[PAR_TPL])
        tpl_dict = dict(cfg[TPL_VALS])
        num_params_to_min = len(cfg[MAX_STEP])
        if num_params_to_min == 0:
            warning("No parameters will be optimized, as no keys specified a max and min step size following the "
                    "initial value (format is x_0, max_step_size, min_step_size).")
            eval_eqs(cfg, tpl_dict)
            fill_save_tpl(cfg, tpl_str, tpl_dict, cfg[PAR_TPL], cfg[PAR_FILE_NAME], print_info=cfg[PRINT_INFO])
            if cfg[PAR_COPY_NAME] is not None:
                copy_par_file(cfg, tpl_dict)
            trial_result = float(check_output([cfg[BASH_DRIVER]]).strip())
            print("Result without optimizing parameters: {}".format(trial_result))
        else:
            min_params(cfg, tpl_dict, tpl_str)

    except (TemplateNotReadableError, IOError) as e:
        warning("Problems reading file: {}".format(e))
        return IO_ERROR
    except (KeyError, InvalidDataError, ValueError) as e:
        warning(e)
        return IO_ERROR

    return GOOD_RET


if __name__ == '__main__':
    status = main()
    sys.exit(status)
