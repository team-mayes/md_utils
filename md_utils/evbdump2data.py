#!/usr/bin/env python
from __future__ import print_function

import ConfigParser

"""
Creates lammps data files from lammps dump files, given a template lammps data file.
"""

import sys
import argparse

__author__ = 'mayes'

# Constants #

DEF_CFG_FILE = 'evbd2d.ini'

# Config File Sections
MAIN_SEC = 'main'

def warning(*objs):
    """Writes a message to stderr."""
    print("WARNING: ", *objs, file=sys.stderr)

def process_cfg(raw_cfg):
    """
    Converts the given raw configuration, filling in defaults and converting the specified value (if any) to the
    default value's type.
    :param raw_cfg: The configuration map.
    :return: The processed configuration.
    """
    proc_cfg = {}
    for key, def_val in DEF_CFG_VALS.iteritems():
        proc_cfg[key] = conv_raw_val(raw_cfg.get(key), def_val)

    steps = proc_cfg[STEPS_KEY]
    burn_in = proc_cfg[BURN_IN_KEY]
    kbest_samples = proc_cfg[KBEST_SAMPLES_KEY]
    kbest_depth = proc_cfg[KBEST_DEPTH_KEY]
    sim_runs = proc_cfg[SIM_RUN_COUNT_KEY]
    samples = proc_cfg[SAMPLE_NUMBER_KEY]

    exp_cl_rate = proc_cfg[EXP_CL_RATE_KEY]
    exp_cl_unc = proc_cfg[EXP_CL_UNC_KEY]
    stoich = proc_cfg[STOICH_KEY]
    stoich_unc = proc_cfg[STOICH_UNC_KEY]
    ph = proc_cfg[EXP_PH_KEY]

    # Calculated config params
    proc_cfg[KBEST_STRIDE_KEY] = max(1, int(steps * (1 - burn_in) / kbest_samples * kbest_depth * sim_runs))
    proc_cfg[SAMPLE_STRIDE_KEY] = max(1, int((1 - burn_in) * steps * sim_runs / samples))

    proc_cfg[EXP_H_RATE_KEY] = exp_cl_rate / stoich
    proc_cfg[PROTON_CONC_KEY] = 10 ** -ph
    # This comes from error propogation analysis
    proc_cfg[EXP_H_UNC_KEY] = math.sqrt(1. / exp_cl_rate ** 2 * exp_cl_unc ** 2 +
                                        (exp_cl_rate ** 2 / stoich ** 4) * stoich_unc ** 2)
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
        raise IOError('Could not read file {0}'.format(floc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)))
    main_proc[KA_KEY] = calc_ka(config)
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    # TODO: Add description
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini "
                                               "format. See the example file /test/test_data/markovian.ini. "
                                               "The default file name is markovian.ini, located in the "
                                               "base directory where the program as run.",
                        default=DEF_CFG_FILE, type=read_cfg)
    # parser.add_argument("-i", "--input_rates", help="The location of the input rates file",
    #                     default=DEF_IRATE_FILE, type=read_input_rates)
    args = None
    try:
        args = parser.parse_args(argv)
    except IOError, e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, 2

    return args, 0


def main(argv=None):
    args, ret = parse_cmdline(argv)
    if ret != 0:
        return ret
    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
