import argparse
import subprocess
import matplotlib.pyplot as plt
import sys
import os

from md_utils.fill_tpl import OUT_DIR, TPL_VALS, fill_save_tpl
from md_utils.md_common import (InvalidDataError, warning,
                                IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, read_tpl)

TPL_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__))) + '/tests/test_data/scaling')
## Dictionary Keywords
WALLTIME = 'walltime'
NUM_PROCS = 'num_procs'
MEM = 'mem'
JOB_NAME = 'job_name'
NUM_NODES = 'num_nodes'


def proc_args(keys):
    tpl_vals = {}

    tpl_vals[WALLTIME] = keys.walltime
    tpl_vals[NUM_PROCS] = keys.num_procs
    tpl_vals[MEM] = keys.memory
    tpl_vals[JOB_NAME] = keys.job_name
    tpl_vals[NUM_NODES] = keys.num_nodes

    return tpl_vals

def make_file(basename, n_list):
    for n in n_list:
        with open(filename, 'w') as fout:
            #makes the file
        subprocess.call(["qsub", filename])
    #TODO: Make this work
    #TODO: Loop over nodes and processors, but only use full multiple nodes

def make_analysis(basename, n_list, scheduler):
    #TODO: I'm not sure what this will look like yet, but it will include namd_log_proc and the python plotting bit
    #Decision: will the analysis wait for 10 minutes, wait for the largest job, or otherwise?
    # set variables based on the scheduler type
    if scheduler=='pbs':
        ext = '.pbs'
        submit = 'qsub'
        tpl = os.path.join(TPL_PATH)
    elif scheduler=='slurm':
        ext = '.job'
        submit = 'sbatch'
    analysis_jobfile = basename + '_analysis' + ext
    with open(analysis_jobfile, 'w') as fout:
    # "for file in ${files[@]}
    # "do
    # "   namd_log_proc --stats -p file
    # "done

def plot_scaling():
    #TODO: Make a beautiful scaling plot
    #TODO: Some preprocessing needs to be done with output from namd_log_proc

def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    #TODO: Add description and arguments, should include name, config file, runtime, maybe a template job file? Also scheduler but we can try to autodetect it as well
    parser = argparse.ArgumentParser(description='Command-line NAMD template script editor.')
    parser.add_argument("-t", "--type", help="The type of job needed. Valid options are {}. "
                                             "The default option is {}.".format(TYPES, DEF_TYPE),
                        choices=TYPES, default=DEF_TYPE)

    args = None
    try:
        args = parser.parse_args(argv)
        if not args.scheduler:
            if which('qsub'):
                args.scheduler = 'pbs'
            elif which('sbatch'):
                args.scheduler = 'slurm'
    except IOError as e:
        warning(e)
        parser.print_help()
        return args, IO_ERROR
    except (InvalidDataError, SystemExit) as e:
        if hasattr(e, 'code') and e.code == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    submit_list = []
    try:
        # generate and submit job files
        submit = make_file(num_procs)


        make_analysis()
        subprocess.call(["qsub", analysis_script])
        #qsub -a $(date -d '5 minutes' "+%H%M") resubmit.pbs
        #sbatch --begin=now+10minutes

    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except (ValueError, InvalidDataError) as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
