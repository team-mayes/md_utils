#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fills in a template evb/rmd parameter files
"""
import argparse
import os
import sys
from collections import OrderedDict

import itertools

from md_utils.md_common import (InvalidDataError, GOOD_RET, INPUT_ERROR, warning, IO_ERROR, process_cfg, read_tpl,
                                create_out_fname, str_to_file, TemplateNotReadableError, MISSING_SEC_HEADER_ERR_MSG)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

# Constants #
TPL_FILE = 'tpl_file'
FILLED_TPL_FNAME = 'filled_tpl_name'
OUT_DIR = 'out_dir'

# Config File Sections
MAIN_SEC = 'main'
TPL_VALS_SEC = 'tpl_vals'
TPL_EQS_SEC = 'tpl_equations'
VALID_SEC_NAMES = [MAIN_SEC, TPL_VALS_SEC, TPL_EQS_SEC]

# for storing template values
TPL_VALS = 'parameter_values'
TPL_EQ_PARAMS = 'calculated_parameter_names'

# Defaults
DEF_CFG_FILE = 'fill_tpl.ini'
DEF_TPL = 'fill_tpl.tpl'
DEF_CFG_VALS = {TPL_FILE: DEF_TPL, OUT_DIR: None, FILLED_TPL_FNAME: None,
                }
REQ_KEYS = {}


# Logic #

# CLI Processing #

def process_tpl_vals(raw_key_val_tuple_list):
    """
    In case there are multiple (comma-separated) values, split on comma and strip. Do not convert to int or float;
       that will be done later if needed for equations
    The program creates the val_dict and multi_val_param_list (fed in empty)

    @param raw_key_val_tuple_list: key-value dict read from configuration file
    @return val_dict: a dictionary of values (strings); check for commas to indicate multiple parameters
    """
    val_dict = OrderedDict()
    for key, val in raw_key_val_tuple_list:
        val_dict[key] = [x.strip() for x in val.split(',')]
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
        raise IOError('Could not read file {}'.format(f_loc))

    # Start with empty template value dictionaries to be filled
    proc = {TPL_VALS: OrderedDict(), TPL_EQ_PARAMS: OrderedDict()}

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
            val_ordered_dict = process_tpl_vals(config.items(section))
            if section == TPL_EQS_SEC:
                # just keep the names, so we know special processing is required
                proc[TPL_EQ_PARAMS] = val_ordered_dict.keys()
            proc[TPL_VALS].update(val_ordered_dict)
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
    parser = argparse.ArgumentParser(description='Fills in a template evb file with parameter values.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)
    parser.add_argument("-f", "--filled_tpl_name", help="File name for new file to be created by filling the template "
                                                        "file. It can also be specified in the configuration file. "
                                                        "If specified in both places, the command line option will "
                                                        "take precedence.",
                        default=None)

    args = None
    try:
        args = parser.parse_args(argv)
        if not os.path.isfile(args.config[TPL_FILE]):
            if args.config[TPL_FILE] == DEF_TPL:
                error_message = "Check input for the configuration key '{}'; " \
                                "could not find the default template file: {}"
            else:
                error_message = "Could not find the template file specified with " \
                                "the configuration key '{}': {}"
            raise IOError(error_message.format(TPL_FILE, args.config[TPL_FILE]))
        if args.filled_tpl_name is not None:
            args.config[FILLED_TPL_FNAME] = args.filled_tpl_name
        if args.config[FILLED_TPL_FNAME] is None:
            raise InvalidDataError("Missing required key '{}', which can be specified in the "
                                   "required either in the command line for configuration file."
                                   "".format(FILLED_TPL_FNAME))
    except (KeyError, InvalidDataError, IOError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


def fill_save_tpl(cfg, tpl_str, tpl_vals_dict):
    """
    use the dictionary to make the file name and filled template. Then save the file.
    @param cfg: configuration for run
    @param tpl_str: the string to be filled to make the filled tpl file
    @param tpl_vals_dict: dictionary of tpl keys and vals
    """
    try:
        filled_tpl_str = tpl_str.format(**tpl_vals_dict)
    except KeyError as e:
        raise KeyError("Key '{}' not found in the configuration but required for template file: {}"
                       "".format(e.message, cfg[TPL_FILE]))

    try:
        filled_fname_str = cfg[FILLED_TPL_FNAME].format(**tpl_vals_dict)
    except KeyError as e:
        raise KeyError("Key '{}' not found in the configuration but required for filled template file name: {}"
                       "".format(e.message, cfg[FILLED_TPL_FNAME]))

    new_par_fname = create_out_fname(filled_fname_str, base_dir=cfg[OUT_DIR])
    str_to_file(filled_tpl_str, new_par_fname, print_info=True)


def make_tpl(cfg):
    """
    Combines the dictionary and template file to create the new file(s)
    @param cfg: configuration for the run
    """

    tpl_str = read_tpl(cfg[TPL_FILE])
    tpl_vals_dict = {}

    for value_set in itertools.product(*cfg[TPL_VALS].values()):
        for param, val in zip(cfg[TPL_VALS].keys(), value_set):
            tpl_vals_dict[param] = val
        for eq_param in cfg[TPL_EQ_PARAMS]:
            try:
                string_to_eval = tpl_vals_dict[eq_param].format(**tpl_vals_dict)
            except KeyError as e:
                raise KeyError("Missing parameter value {} needed to evaluate '{}' for the parameter '{}'."
                               "".format(e, tpl_vals_dict[eq_param], eq_param))
            try:
                tpl_vals_dict[eq_param] = eval(string_to_eval)
            except NameError:
                raise InvalidDataError("Could not evaluate the string '{}' specifying the value for the parameter "
                                       "'{}'. Check order of equation entry and/or input parameter values."
                                       "".format(string_to_eval, eq_param))

        fill_save_tpl(cfg, tpl_str, tpl_vals_dict)


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
        make_tpl(cfg)
    except (TemplateNotReadableError, IOError) as e:
        warning("Problems reading file: {}".format(e))
        return IO_ERROR
    except (KeyError, InvalidDataError) as e:
        warning(e)
        return IO_ERROR

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
