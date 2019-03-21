import argparse
import subprocess
import matplotlib.pyplot as plt
import sys
import os
import pandas as pd
from shutil import which
import re
from md_utils.fill_tpl import OUT_DIR, TPL_VALS, fill_save_tpl
from md_utils.md_common import (InvalidDataError, warning,
                                IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, read_tpl)

CONF_EXT = '.conf'
LOG_EXT = '.log'

## Dictionary Keywords
WALLTIME = 'walltime'
nprocs = 'nprocs'
MEM = 'mem'
JOB_NAME = 'job_name'
NUM_NODES = 'nnodes'
NUM_PROCS = 'nprocs'
OUT_FILE = 'file_out_name'
RUN_NAMD = "namd2 +p {} {} >& {}"
# Patterns
NAMD_OUT_PAT = re.compile(r"^set outputname.*")

# Defaults
DEF_NAME = 'scaling'
TPL_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__))) + '/skel/tpl')
DEF_NPROCS = "1 2 4 8 12"
DEF_NNODES = "1 2"
DEF_WALLTIME = 10
DEF_MEM = 4
TYPES = ['namd']
DEF_TYPE = 'namd'
SCHEDULER_TYPES = ['pbs', 'slurm']


def proc_args(keys):
    tpl_vals = {}

    tpl_vals[WALLTIME] = keys.walltime
    tpl_vals[nprocs] = keys.nprocs
    tpl_vals[MEM] = DEF_MEM
    # tpl_vals[MEM] = keys.mem
    tpl_vals[JOB_NAME] = keys.name
    tpl_vals[NUM_NODES] = keys.nnodes
    tpl_vals[NUM_PROCS] = keys.nprocs

    return tpl_vals


def make_file(keys):
    for i, file in enumerate(keys.filelist):
        jobfile = file + keys.job_ext
        configfile = file + CONF_EXT
        logfile = file + LOG_EXT
        total_procs = int(file.split('_')[-1])
        ppn = int(keys.nprocs[-1])
        # TODO: Check if file already exists. If it does, provide a message and exit
        if total_procs <= ppn:
            keys.tpl_vals[NUM_NODES] = 1
            keys.tpl_vals[NUM_PROCS] = keys.nprocs[i]
        else:
            keys.tpl_vals[NUM_NODES] = str(int(total_procs / ppn))
            keys.tpl_vals[NUM_PROCS] = str(ppn)
        config = {OUT_DIR: os.path.dirname(jobfile), TPL_VALS: keys.tpl_vals, OUT_FILE: jobfile}
        JOB_TPL_PATH = os.path.join(TPL_PATH, "template" + keys.job_ext)
        fill_save_tpl(config, read_tpl(JOB_TPL_PATH), keys.tpl_vals, JOB_TPL_PATH, jobfile)

        with open(jobfile, 'a') as fout:
            if keys.software == 'namd':
                fout.write(RUN_NAMD.format(total_procs, configfile, logfile))
                out_pat = NAMD_OUT_PAT
        with open(configfile, 'w') as fout:
            with open(keys.config, 'r') as fin:
                for line in fin:
                    if out_pat.match(line):
                        fout.write("set outputname\t\t{} \n".format(file))
                    else:
                        fout.write(line)
        if keys.debug:
            print('subprocess.call(["qsub", jobfile])')
        elif keys.scheduler == 'pbs':
            subprocess.call(["qsub", jobfile])
        elif keys.scheduler == 'slurm':
            subprocess.call(["sbatch", jobfile])
        else:
            print('subprocess.call(["sbatch", jobfile])')


def make_analysis(basename, n_list, scheduler):
    # TODO: I'm not sure what this will look like yet, but it will include namd_log_proc and the python plotting bit
    # I actually think it will be simpler to read all of the data into the plotting function rather than preprocessing with col_stats, which loses the filename
    # Decision: job that searches for the existence of all the logs. If it finds them, submit analysis job for 10 minutes later, otherwise resubmit itself.
    # This solution is somewhat vulnerable to failed jobs, but that's the user's responsibility.
    # Alternatively we could learn how to parse the scheduler output
    # set variables based on the scheduler type
    if scheduler == 'pbs':
        ext = '.pbs'
        submit = 'qsub'
        tpl = os.path.join(TPL_PATH)
    elif scheduler == 'slurm':
        ext = '.job'
        submit = 'sbatch'
    analysis_jobfile = basename + '_analysis' + ext
    with open(analysis_jobfile, 'w') as fout:
        print("hello world")


# "for file in ${files[@]}
# "do
# "   namd_log_proc --stats -p file
# "done

def plot_scaling(list_of_files):
    # TODO: Make a beautiful scaling plot
    # TODO: Some preprocessing needs to be done with output from namd_log_proc
    list = []
    for file in list_of_files:
        df = pd.read_csv(file, header=0, index_col=None)
        list.append(df)
    frame = pd.concat(list, ignore_index=True)


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    # TODO: Add an option to just replot
    # TODO: Add memory as a user parameter (analogous to walltime)
    # TODO: Adjust defaults for flux vs slurm (furthermore comet vs bridges)
    parser = argparse.ArgumentParser(
        description='Automated submission and analysis of scaling data for a provided program')
    parser.add_argument("-b", "--name", help="Basename for the scaling files. Default is {}.".format(DEF_NAME),
                        default=DEF_NAME)
    parser.add_argument("-d", "--debug", help="Flag to generate but not submit the script.",
                        default=False, action='store_true')  # Mostly for testing
    parser.add_argument("-c", "--config", help="Configuraton file name and extension",
                        type=str)
    parser.add_argument("-p", "--nprocs", type=lambda s: [int(item) for item in s.split(' ')],
                        help="List of numbers of processors to test. Default is: {}".format(DEF_NPROCS),
                        default=DEF_NPROCS)
    parser.add_argument("-n", "--nnodes", type=lambda s: [int(item) for item in s.split(' ')],
                        help="List of numbers of nodes to test. Nodes size will be assumed from max processor number. Default is {}".format(
                            DEF_NNODES),
                        default=DEF_NNODES)
    parser.add_argument("-w", "--walltime", type=int,
                        help="Integer number of minutes to run scaling job. Default is {}".format(DEF_WALLTIME),
                        default=DEF_WALLTIME)
    parser.add_argument("-s", "--software",
                        help="Program for performing scaling analysis. Valid options are: {}. Default is {}".format(
                            TYPES, DEF_TYPE), default=DEF_TYPE, choices=TYPES)
    parser.add_argument("--scheduler",
                        help="Scheduler type for jobfiles. Valid options are: {}. Automatic detection will be attempted by default".format(
                            TYPES))

    args = None
    try:
        args = parser.parse_args(argv)
        # Automatic scheduler detection
        if not args.scheduler:
            if which('qsub'):
                args.scheduler = 'pbs'
                args.job_ext = '.pbs'
            elif which('sbatch'):
                args.scheduler = 'slurm'
                args.job_ext = '.job'
            else:
                args.scheduler = 'none'
                args.job_ext = '.job'

        args.filelist = []
        for nproc in args.nprocs:
            filename = args.name + '_' + str(nproc)
            args.filelist.append(filename)
        for nnode in args.nnodes:
            if int(nnode) > 1:
                total_procs = str(nnode * args.nprocs[-1])
                filename = args.name + '_' + total_procs
                args.filelist.append(filename)
        args.tpl_vals = proc_args(args)
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

    try:
        make_file(args)
        # TODO: Analysis
        # TODO: Plotting
    #     make_analysis()
    #     subprocess.call(["qsub", analysis_script])
    #     # qsub -a $(date -d '5 minutes' "+%H%M") resubmit.pbs
    #     # sbatch --begin=now+10minutes
    #
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
