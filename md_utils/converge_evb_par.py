#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Given an initial set of parameters, it will create a parameter file and a copy of it for records.
"""
import argparse
import os
import sys
from collections import OrderedDict

import shutil

from md_utils.md_common import (InvalidDataError, GOOD_RET, INPUT_ERROR, warning, IO_ERROR, process_cfg,
                                TemplateNotReadableError, MISSING_SEC_HEADER_ERR_MSG, create_out_fname)
from md_utils.fill_tpl import (OUT_DIR, MAIN_SEC, TPL_VALS_SEC, TPL_EQS_SEC,
                               VALID_SEC_NAMES, TPL_VALS, TPL_EQ_PARAMS, process_tpl_vals, make_tpl, NEW_FNAME)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

# Constants #
TRIAL_NAME = 'trial_name'
PAR_TPL = 'par_tpl'
PAR_COPY_NAME = 'par_copy'
PAR_FILE_NAME = 'par_name'
COPY_DIR = 'copy_dir'

# Defaults
DEF_CFG_FILE = 'conv_evb_par.ini'
DEF_TPL = 'evb_par.tpl'
DEF_CFG_VALS = {TRIAL_NAME: None, PAR_TPL: DEF_TPL, OUT_DIR: None, PAR_FILE_NAME: None,
                PAR_COPY_NAME: None, COPY_DIR: None,
                }
REQ_KEYS = {}


# Logic #

# CLI Processing #

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
    except (KeyError, InvalidDataError, IOError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


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
        tpl_dict = make_tpl(cfg, cfg[PAR_TPL], cfg[PAR_FILE_NAME], return_dict=True)
        if cfg[TRIAL_NAME] is not None:
            try:
                tpl_dict[TRIAL_NAME] = cfg[TRIAL_NAME].format(**tpl_dict)
            except KeyError as e:
                raise KeyError("Missing key name {} required for '{}': '{}'. Program will terminate."
                               "".format(e, TRIAL_NAME, cfg[TRIAL_NAME]))
        if cfg[PAR_COPY_NAME] is not None:
            try:
                par_copy = cfg[PAR_COPY_NAME].format(**tpl_dict)
            except KeyError as e:
                raise KeyError("Missing key name {} required for '{}': '{}'. Copy of par file will not be made."
                               "".format(e, PAR_COPY_NAME, cfg[PAR_COPY_NAME]))
            par_copy_fname = create_out_fname(par_copy, base_dir=cfg[COPY_DIR])
            shutil.copyfile(tpl_dict[NEW_FNAME], par_copy_fname)
            print(" Copied to: {}".format(par_copy_fname))

    except (TemplateNotReadableError, IOError) as e:
        warning("Problems reading file: {}".format(e))
        return IO_ERROR
    except (KeyError, InvalidDataError) as e:
        warning(e)
        return IO_ERROR

    return GOOD_RET


if __name__ == '__main__':
    status = main()
    sys.exit(status)
