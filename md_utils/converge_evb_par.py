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
                                conv_num, write_csv)
from md_utils.fill_tpl import (OUT_DIR, MAIN_SEC, TPL_VALS_SEC, TPL_EQS_SEC,
                               TPL_VALS, TPL_EQ_PARAMS, NEW_FNAME, fill_save_tpl)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

# Constants #
# config keys #
MAX_VALS = 'max_vals'
MIN_VALS = 'min_vals'
INITIAL_DIR = 'initial_dir'
VALID_SEC_NAMES = [MAIN_SEC, TPL_VALS_SEC, TPL_EQS_SEC, MAX_VALS, MIN_VALS]
TRIAL_NAME = 'trial_name'
PAR_TPL = 'par_tpl'
PAR_COPY_NAME = 'par_copy'
PAR_FILE_NAME = 'par_name'
RESULT_FILE = 'driver_output_file_name'
RESULT_COPY = 'driver_output_copy_name'
FITTING_SUM_FNAME = 'fitting_summary_file_name'
COPY_DIR = 'copy_dir'
BASH_DRIVER = 'bash_driver'
CONV_CUTOFF = 'converge_tolerance'
MAX_ITER = 'max_iterations'
NUM_PARAM_DECIMALS = 'num_decimals'
PRINT_INFO = 'print_status'
SCIPY_OPT_METHOD = 'scipy_opt_method'
PRINT_CONV_ALL = 'print_conv_all'

# for storing config data
OPT_PARAMS = 'opt_params'
RESID = 'resid'

# Defaults
DEF_CFG_FILE = 'conv_evb_par.ini'
DEF_TPL = 'evb_par.tpl'
DEF_CONV_CUTOFF = 1.0
DEF_MAX_ITER = None
DEF_PARAM_DEC = 6
DEF_OPT_METHOD = 'Powell'
# for setting up the "direc" option with Powell, i.e. direc=([1,0,0],[0,0.1,0],[0,0,1])
DEF_DIR = 1.0
DEF_PENALTY = 1000000.0
DEF_CFG_VALS = {TRIAL_NAME: None, PAR_TPL: DEF_TPL, OUT_DIR: None, PAR_FILE_NAME: None,
                PAR_COPY_NAME: None, COPY_DIR: None, CONV_CUTOFF: DEF_CONV_CUTOFF, MAX_ITER: DEF_MAX_ITER,
                PRINT_INFO: False, NUM_PARAM_DECIMALS: DEF_PARAM_DEC, RESULT_FILE: None,
                RESULT_COPY: None, OPT_PARAMS: [], SCIPY_OPT_METHOD: DEF_OPT_METHOD,
                FITTING_SUM_FNAME: None, PRINT_CONV_ALL: False,
                }
REQ_KEYS = {BASH_DRIVER: str}


# Logic #

# CLI Processing #

def process_conv_tpl_keys(raw_key_val_tuple_list):
    """
    In case there are multiple (comma-separated) values, split on comma and strip. If possible, convert to int or float;
       otherwise. Return the tuple as a processed ordered dict

    @param raw_key_val_tuple_list: key-value dict read from configuration file;
       check for commas to indicate multiple parameters, and converted to int
       or floats if amenable
    @return val_dict: a dictionary of values
    @return dir_dict: a dictionary of initial directions for minimization
    """
    val_dict = OrderedDict()
    dir_dict = {}
    for key, val in raw_key_val_tuple_list:
        val_list = [x.strip() for x in val.split(',')]
        val_num = len(val_list)
        if val_num == 1:
            # if it can be converted, do so; this helps with my printing formatting
            val_dict[key] = conv_num(val_list[0])
            dir_dict[key] = DEF_DIR
        elif val_num == 2:
            # if there are two values, assume that it is a float with the ability to be optimized
            try:
                val_dict[key] = float(val_list[0])
                dir_dict[key] = float(val_list[1])
            except ValueError:
                raise InvalidDataError("For key '{}', read '{}', which could not be converted to floats. When two "
                                       "values are provided, they are read as an initial float that may be optimized, "
                                       "and the initial search direction for optimization.".format(key, val))
        else:
            raise InvalidDataError("For key '{}', {} values were found ({}). Each parameter should have either one or "
                                   "two specified values (x0, optionally followed by initial search direction, which "
                                   "defaults to {}.".format(key, val_num, val, DEF_DIR))
    return val_dict, dir_dict


def process_max_min_vals(raw_key_val_tuple_list, default_penalty):
    """
    Convert tuple to a dictionary with float values
    @param raw_key_val_tuple_list:
    @param default_penalty: default penalty for the flat-bottomed potential
    @return: dictionary of keys and float values
    """
    val_dict = {}
    for key, val in raw_key_val_tuple_list:
        try:
            val_list = [float(x.strip()) for x in val.split(',')]
            if len(val_list) == 2:
                val_dict[key] = val_list
            elif len(val_list) == 1:
                val_dict[key] = val_list + [default_penalty]
            else:
                raise InvalidDataError("For key '{}' in max or min section, read: {}. \nExpected 1 or 2 values: "
                                       "either the edge of the potential and the penalty stiffness, or only the "
                                       "edge of the potential, which will be used with "
                                       "the default penalty for the flat-bottomed potential"
                                       "".format(key, val))
        except ValueError as e:
            raise InvalidDataError("Error in reading max or min value provided for key '{}': {}"
                                   "".format(key, e.message))
    return val_dict


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
        raise IOError("Could not read file '{}'".format(f_loc))

    # Start with empty data structures to be filled
    proc = {TPL_VALS: {}, TPL_EQ_PARAMS: [], MAX_VALS: {}, MIN_VALS: {}, INITIAL_DIR: {}}

    if MAIN_SEC not in config.sections():
        raise InvalidDataError("The configuration file is missing the required '{}' section".format(MAIN_SEC))

    for section in config.sections():
        if section == MAIN_SEC:
            try:
                proc.update(cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS, int_list=False))
                if proc[MAX_ITER] is not None:
                    proc[MAX_ITER] = int(proc[MAX_ITER])
            except InvalidDataError as e:
                if 'Unexpected key' in e.message:
                    raise InvalidDataError(e.message + " Does this belong \nin a template value section such as '[{}]'?"
                                                       "".format(TPL_VALS_SEC))
            except ValueError as e:
                raise InvalidDataError(e)
        elif section in [TPL_VALS_SEC, TPL_EQS_SEC]:
            val_dict, dir_dict = process_conv_tpl_keys(config.items(section))
            if section == TPL_EQS_SEC:
                # just keep the names, so we know special processing is required
                proc[TPL_EQ_PARAMS] = val_dict.keys()
            proc[TPL_VALS].update(val_dict)
            proc[INITIAL_DIR].update(dir_dict)
        elif section in [MAX_VALS, MIN_VALS]:
            val_dict = process_max_min_vals(config.items(section), DEF_PENALTY)
            proc[section].update(val_dict)
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
                raise IOError("Missing file specified with key '{}': {}"
                              "".format(config_param, args.config[config_param]))
        if args.config[RESULT_COPY] is not None:
            if args.config[RESULT_FILE] is None:
                raise InvalidDataError("A bash driver output file name ('{}') is required when a name for a copy "
                                       "of this file is specified ('{}').".format(RESULT_FILE, RESULT_COPY))
    except (KeyError, InvalidDataError, IOError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


def copy_par_result_file(cfg, tpl_vals_dict, print_info=False):
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

    for copy_name in [PAR_COPY_NAME, RESULT_COPY]:
        if cfg[copy_name] is not None:
            try:
                base_name = cfg[copy_name].format(**tpl_vals_dict)
            except KeyError as e:
                raise KeyError("Missing key name {} required for '{}': '{}'. File will not be copied."
                               "".format(e, copy_name, cfg[copy_name]))
            new_fname = create_out_fname(base_name, base_dir=cfg[COPY_DIR])
            if copy_name == PAR_COPY_NAME:
                shutil.copyfile(tpl_vals_dict[NEW_FNAME], new_fname)
            else:
                # if os.path.isfile(tpl_vals_dict[RESULT_FILE]):
                shutil.copyfile(cfg[RESULT_FILE], new_fname)

            if print_info:
                print(" Copied to: {}".format(new_fname))


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


def obj_fun(x0, cfg, tpl_dict, tpl_str, fitting_sum, result_dict, result_headers):
    """
    Objective function to be minimized. Also used to save trial input and output.
    @param x0: initial parameter values
    @param cfg: configuration for the run
    @param tpl_dict: dictionary of values for filling in template strings
    @param tpl_str: template string (read from file)
    @param fitting_sum: list of dicts for saving all trial values (to be appended, if needed)
    @param result_dict: a dictionary of results already found, to keep the program from unnecessarily running
                the expensive function when we already have solved for that parameter set
    @param result_headers: list of headers for printing results
    @return: the result for the set of values being tested, obtained from the bash script specified in cfg
    """
    resid_dict = {}
    penalty = 0
    for param_num, param_name in enumerate(cfg[OPT_PARAMS]):
        tpl_dict[param_name] = round(x0[param_num], cfg[NUM_PARAM_DECIMALS])
        resid_dict[param_name] = tpl_dict[param_name]
        if param_name in cfg[MIN_VALS]:
            min_val = cfg[MIN_VALS][param_name][0]
            stiffness = cfg[MIN_VALS][param_name][1]
            if x0[param_num] < min_val:
                penalty += stiffness * np.square(x0[param_num] - min_val)
        if param_name in cfg[MAX_VALS]:
            max_val = cfg[MAX_VALS][param_name][0]
            stiffness = cfg[MAX_VALS][param_name][1]
            if x0[param_num] > max_val:
                penalty += stiffness * np.square(x0[param_num] - max_val)

    eval_eqs(cfg, tpl_dict)
    fill_save_tpl(cfg, tpl_str, tpl_dict, cfg[PAR_TPL], cfg[PAR_FILE_NAME], print_info=cfg[PRINT_INFO])
    # Note: found that the minimizer calls the function with the same inputs multiple times!
    #       only call this expensive function if we don't already have that answer, determined by checking for it in
    #       the result dictionary
    # to make the input hashable for a dictionary
    x0_str = str(x0)
    if x0_str in result_dict:
        trial_result = result_dict[x0_str]
    else:
        trial_result = float(check_output([cfg[BASH_DRIVER], tpl_dict[NEW_FNAME]]).strip())
        trial_result += penalty
        result_dict[x0_str] = trial_result
        tpl_dict[RESID] = round(trial_result, cfg[NUM_PARAM_DECIMALS])
        if cfg[PAR_COPY_NAME] is not None or cfg[RESULT_COPY] is not None:
            copy_par_result_file(cfg, tpl_dict, print_info=cfg[PRINT_INFO])
        if cfg[FITTING_SUM_FNAME] is not None:
            write_csv(fitting_sum, cfg[FITTING_SUM_FNAME], result_headers, print_message=cfg[PRINT_INFO],
                      round_digits=cfg[NUM_PARAM_DECIMALS])
    if cfg[PRINT_INFO]:
        print("Resid: {:11f} for parameters: {}".format(trial_result, ",".join(["{:11f}".format(x) for x in x0])))
    if cfg[FITTING_SUM_FNAME] is not None:
        resid_dict[RESID] = trial_result
        fitting_sum.append(resid_dict)
    return trial_result


def min_params(cfg, tpl_dict, tpl_str):
    num_opt_params = len(cfg[OPT_PARAMS])
    x0 = np.empty(num_opt_params)
    ini_direc = np.zeros((num_opt_params, num_opt_params))
    result_dict = {}
    fitting_sum = []
    result_sum_headers = [RESID]
    for param_num, param_name in enumerate(cfg[OPT_PARAMS]):
        x0[param_num] = cfg[TPL_VALS][param_name]
        ini_direc[param_num, param_num] = cfg[INITIAL_DIR][param_name]
        result_sum_headers.append(param_name)

    res = minimize(obj_fun, x0, args=(cfg, tpl_dict, tpl_str, fitting_sum, result_dict, result_sum_headers),
                   method=cfg[SCIPY_OPT_METHOD],
                   options={'xtol': cfg[CONV_CUTOFF], 'ftol': cfg[CONV_CUTOFF],
                            'maxiter': cfg[MAX_ITER], 'maxfev': cfg[MAX_ITER], 'disp': cfg[PRINT_INFO],
                            'direc': ini_direc,
                            # 'full_output': cfg[PRINT_CONV_ALL],
                            'return_all': cfg[PRINT_CONV_ALL],
                            })
    x_final = res.x
    if x_final.size > 1:
        if cfg[FITTING_SUM_FNAME] is not None:
            write_csv(fitting_sum, cfg[FITTING_SUM_FNAME], result_sum_headers, print_message=cfg[PRINT_INFO],
                      round_digits=cfg[NUM_PARAM_DECIMALS])
        print("Optimized parameters:")
        for param_num, param_name in enumerate(cfg[OPT_PARAMS]):
            print("{:>11} = {:11f}".format(param_name, x_final[param_num]))
    else:
        print("Optimized parameter:\n{:>11}: {:11f}".format(cfg[OPT_PARAMS][0], x_final.tolist()))


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
        if len(cfg[OPT_PARAMS]) == 0:
            warning("No parameters will be optimized, as no parameters were listed for the keyword '{}' "
                    "in the '{}' section of the configuration file.".format(OPT_PARAMS, MAIN_SEC))
            eval_eqs(cfg, tpl_dict)
            fill_save_tpl(cfg, tpl_str, tpl_dict, cfg[PAR_TPL], cfg[PAR_FILE_NAME], print_info=cfg[PRINT_INFO])
            trial_result = float(check_output([cfg[BASH_DRIVER], tpl_dict[NEW_FNAME]]).strip())
            if cfg[PAR_COPY_NAME] is not None or cfg[RESULT_COPY] is not None:
                copy_par_result_file(cfg, tpl_dict)
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
