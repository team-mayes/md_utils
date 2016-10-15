#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fills in a template evb/rmd parameter files
"""
import argparse
import os
import sys

from md_utils.md_common import (InvalidDataError, GOOD_RET, INPUT_ERROR, warning, IO_ERROR, process_cfg, read_tpl,
                                create_out_fname, str_to_file, TemplateNotReadableError)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser

# Constants #
TPL_FILE = 'tpl_file'
FILLED_TPL_FNAME = 'filled_tpl_name'
OUT_DIR = 'out_dir'

# Config File Sections
MAIN_SEC = 'main'
TPL_VALS = 'tpl_vals'

# Defaults
DEF_CFG_FILE = 'fill_tpl.ini'
DEF_TPL = 'fill_tpl.tpl'
DEF_CFG_VALS = {TPL_FILE: DEF_TPL, OUT_DIR: None, FILLED_TPL_FNAME: None,
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
    good_files = config.read(f_loc)
    if not good_files:
        raise IOError('Could not read file {}'.format(f_loc))
    proc = {TPL_VALS: {}}
    for section in config.sections():
        if section == MAIN_SEC:
            try:
                proc.update(cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS))
            except InvalidDataError as e:
                if 'Unexpected key' in e.message:
                    raise InvalidDataError(e.message + ' Note: template keys must \nbe in a '
                                                       'configuration file section other than '
                                                       '[main]. Any other section name will '
                                                       'suffice; \nthey can be used to organize '
                                                       'parameters if desired.')
        else:
            proc[TPL_VALS].update(dict(config.items(section)))

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


def make_tpl(cfg):
    """
    Combines the dictionary and template file to create the new file
    @param cfg:
    @return:
    """

    tpl_str = read_tpl(cfg[TPL_FILE])
    test_dict = cfg[TPL_VALS]
    try:
        filled_tpl_str = tpl_str.format(**test_dict)
    except KeyError as e:
        raise KeyError("Key '{}' not found in the configuration but required for template file: {}"
                       "".format(e.message, cfg[TPL_FILE]))
    new_par_fname = create_out_fname(cfg[FILLED_TPL_FNAME], base_dir=cfg[OUT_DIR])
    str_to_file(filled_tpl_str, new_par_fname)


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
