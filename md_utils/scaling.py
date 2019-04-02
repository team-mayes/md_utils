import argparse
import subprocess
import matplotlib.pyplot as plt
import sys
import os
import pandas as pd
from shutil import which
import numpy as np
import re
from md_utils.fill_tpl import OUT_DIR, TPL_VALS, fill_save_tpl
from md_utils.md_common import (InvalidDataError, warning,
                                IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, read_tpl)

# This line switches to a non-Gui backend, allowing plotting on PSC Bridges
plt.switch_backend('agg')

CONF_EXT = '.conf'
LOG_EXT = '.log'

# Dictionary Keywords
WALLTIME = 'walltime'
nprocs = 'nprocs'
MEM = 'mem'
JOB_NAME = 'job_name'
NUM_NODES = 'nnodes'
NUM_PROCS = 'nprocs'
OUT_FILE = 'file_out_name'
PARTITION = 'partition'
MAX_BRIDGES = 28
BRIDGES_SHARED = 'RM-shared'
BRIDGES_RM = 'RM'
BRIDGES_FULLNODE = "2\n#SBATCH --cpus-per-task=14"
RUN_NAMD_PBS = "namd2 +p {} {} >& {}"
RUN_NAMD_BRIDGES = "module load namd\nmpirun -np 1 namd2 +ppn $SLURM_NPROCS {} >& {}"
RUN_NAMD_BRIDGES_FULLNODE = "module load namd\nmpirun -np $SLURM_NTASKS namd2 +ppn 12 +pemap 1-6,15-20,8-13,22-27 " \
                            "+commap 0,14,7,21 {} >& {}"
ANALYZE_NAMD = "namd_log_proc -p -l ${basename}_log_list"
NAMD_OUTNAME = "outputName          {} \n"
# Patterns
NAMD_OUT_PAT = re.compile(r"^outputName.*")
FILE_PAT = re.compile(r"^files=.*")
BASE_PAT = re.compile(r"^basename=.*")
ANALYSIS_PAT = re.compile(r"^analysis=.*")
NAMD_TIMING_PAT = re.compile(r"^outputTiming.*", re.IGNORECASE)
NAMD_RUN_PAT = re.compile(r"^run.*")
NAMD_NUMSTEPS_PAT = re.compile(r"^numsteps.*")

# Defaults
DEF_NAME = 'scaling'
TPL_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__))) + '/skel/tpl')
DEF_NPROCS_FLUX = [1, 2, 4, 8, 12]
DEF_NPROCS_BRIDGES = [1, 2, 4, 8, 14, 28]
DEF_NPROCS_COMET = [1, 2, 4, 8, 12, 24]  # TODO: Confirm this with someone who uses Comet
DEF_NNODES = "1"
DEF_WALLTIME = 10
DEF_MEM = 1
TYPES = ['namd', 'amber']
DEF_TYPE = 'namd'
SCHEDULER_TYPES = ['pbs', 'slurm']
CLUSTERS = ['bridges', 'flux', 'comet']


def proc_args(keys):
    tpl_vals = {}

    tpl_vals[WALLTIME] = keys.walltime
    tpl_vals[nprocs] = keys.nprocs
    tpl_vals[MEM] = keys.memory
    tpl_vals[JOB_NAME] = keys.basename
    tpl_vals[NUM_NODES] = keys.nnodes
    tpl_vals[NUM_PROCS] = keys.nprocs

    return tpl_vals


def submit_files(keys):
    for i, file in enumerate(keys.filelist):
        jobfile = file + keys.job_ext
        configfile = file + CONF_EXT
        logfile = file + LOG_EXT
        total_procs = int(file.split('_')[-1])
        ppn = int(keys.nprocs[-1])
        if os.path.isfile(logfile):
            print("{} exists. Will not submit a new scaling run".format(logfile))
            continue
        if total_procs <= ppn:
            keys.tpl_vals[NUM_NODES] = 1
            keys.tpl_vals[NUM_PROCS] = keys.nprocs[i]
        else:
            keys.tpl_vals[NUM_NODES] = str(int(total_procs / ppn))
            keys.tpl_vals[NUM_PROCS] = str(ppn)
        if keys.cluster == 'bridges':
            if total_procs < MAX_BRIDGES:
                keys.tpl_vals[PARTITION] = BRIDGES_SHARED
            else:
                keys.tpl_vals[PARTITION] = BRIDGES_RM
                keys.tpl_vals[NUM_PROCS] = BRIDGES_FULLNODE
                keys.run = RUN_NAMD_BRIDGES_FULLNODE
        config = {OUT_DIR: os.path.dirname(jobfile), TPL_VALS: keys.tpl_vals, OUT_FILE: jobfile}
        JOB_TPL_PATH = os.path.join(TPL_PATH, "template" + keys.job_ext)
        fill_save_tpl(config, read_tpl(JOB_TPL_PATH), keys.tpl_vals, JOB_TPL_PATH, jobfile, print_info=False)

        with open(jobfile, 'a') as fout:
            if keys.software == 'namd' and keys.cluster == 'bridges':
                fout.write(keys.run.format(configfile, logfile))
            elif keys.software == 'namd':
                fout.write(keys.run.format(total_procs, configfile, logfile))
            elif keys.software == 'amber':
                print("Uh oh, this should never be printed.")
        timing = False
        with open(configfile, 'w') as fout:
            with open(keys.config, 'r') as fin:
                for line in fin:
                    if keys.out_pat.match(line):
                        fout.write(keys.output.format(file))
                    elif keys.software == 'namd':
                        if not timing and (NAMD_RUN_PAT.match(line) or NAMD_NUMSTEPS_PAT.match(line)):
                            fout.write("outputTiming        100\n")
                            timing = True
                            fout.write(line)
                        elif NAMD_TIMING_PAT.match(line):
                            timing = True
                            fout.write(line)
                        else:
                            fout.write(line)
                    else:
                        fout.write(line)
        if keys.debug or keys.scheduler == 'none':
            print("subprocess.call([{}, {}])".format(keys.sub_command, jobfile))
        else:
            subprocess.call([keys.sub_command, jobfile])


def submit_analysis(keys):
    # One could argue parsing the scheduler output is more robust, but that's a feature for another day
    # This anlysis is cheap so I won't worry about checking what has already been done
    analysis_jobfile = keys.basename + '_analysis' + keys.job_ext
    with open(analysis_jobfile, 'w') as fout:
        with open(os.path.join(TPL_PATH, 'analysis_tpl' + keys.job_ext), 'r') as fin:
            for line in fin:
                if FILE_PAT.match(line):
                    fout.write('files="{}"\n'.format(' '.join(keys.filelist)))
                elif ANALYSIS_PAT.match(line):
                    fout.write("{}\n".format(keys.analysis))
                elif BASE_PAT.match(line):
                    fout.write("basename={}\n".format(keys.basename))
                else:
                    fout.write(line)

    resubmit_jobfile = keys.basename + '_resubmit' + keys.job_ext
    with open(resubmit_jobfile, 'w') as fout:
        with open(os.path.join(TPL_PATH, 'resubmit_tpl' + keys.job_ext), 'r') as fin:
            for line in fin:
                if FILE_PAT.match(line):
                    fout.write('files="{}"\n'.format(' '.join(keys.filelist)))
                elif BASE_PAT.match(line):
                    fout.write("basename={}\n".format(keys.basename))
                else:
                    fout.write(line)

    if keys.debug or keys.scheduler == 'none':
        print("subprocess.call([{}, {}])".format(keys.sub_command, resubmit_jobfile))
    else:
        subprocess.call([keys.sub_command, resubmit_jobfile])


def plot_scaling(filename):
    frame = pd.read_csv(filename + '_log_list_performance.csv', header=0, index_col=None)
    means = []
    for file in frame.filename.unique():
        means.append(frame['time/ns'][frame['filename'] == file].mean())
    nprocs = np.asarray([item.split('_')[-1] for item in frame.filename.unique()], dtype=int)
    fig, ax = plt.subplots()
    ax1 = ax.twinx()
    speedup = np.asarray([means[0] / i for i in means])
    x = np.linspace(1, nprocs[-1])

    ax.plot(nprocs, np.asarray(means), label='time/ns', marker='^')
    ax1.plot(x, x, 'k', label="Perfect Scaling", linestyle='--')
    ax1.plot(nprocs, speedup, 'r', label="Speedup", marker='o')

    ax.set_xlabel("Number of Processors")
    ax.set_ylabel("hours/ns")
    ax1.set_ylabel("Speedup")
    fig.legend(loc='upper center')
    fig_name = filename + '.png'
    plt.savefig(fig_name)
    print("Wrote file: {}".format(fig_name))
    # TODO: output stats alongside figure?


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(
        description='Automated submission and analysis of scaling data for a provided program')
    parser.add_argument("-b", "--basename", help="Basename for the scaling files. Default is {}.".format(DEF_NAME),
                        default=DEF_NAME)
    parser.add_argument("-d", "--debug", help="Flag to generate but not submit the script.",
                        default=False, action='store_true')  # Mostly for testing
    parser.add_argument("-c", "--config", help="Configuraton file name and extension",
                        type=str)
    parser.add_argument("-p", "--nprocs", type=lambda s: [int(item) for item in s.split(' ')],
                        help="List of numbers of processors to test. Default chosen based on cluster. "
                             "Flux default is {}, Bridges default is {}, Comet default is {}".format(
                            DEF_NPROCS_FLUX, DEF_NPROCS_BRIDGES, DEF_NPROCS_COMET), default=None)
    parser.add_argument("-n", "--nnodes", type=lambda s: [int(item) for item in s.split(' ')],
                        help="List of numbers of nodes to test. Nodes size will be assumed from max processor number. "
                             "Default is {}".format(
                            DEF_NNODES),
                        default=DEF_NNODES)
    parser.add_argument("-w", "--walltime", type=int,
                        help="Integer number of minutes to run scaling job. Default is {}".format(DEF_WALLTIME),
                        default=DEF_WALLTIME)
    parser.add_argument("-s", "--software",
                        help="Program for performing scaling analysis. Valid options are: {}. Default is {}".format(
                            TYPES, DEF_TYPE), default=DEF_TYPE, choices=TYPES)
    parser.add_argument("--scheduler",
                        help="Scheduler type for jobfiles. Valid options are: {}. "
                             "Automatic detection will be attempted by default".format(
                            SCHEDULER_TYPES))
    parser.add_argument("--plot", default=False, action='store_true', help="Flag to only plot the specified files")
    parser.add_argument("--cluster",
                        help="Cluster where scaling is to be performed. Options are: {}. "
                             "This is especially important if running namd on Bridges".format(
                            CLUSTERS), default=None)
    parser.add_argument("-m", "--memory", help="Memory (in Gb) requested per core. Default is: {}".format(DEF_MEM),
                        default=DEF_MEM, type=int)

    args = None
    try:
        args = parser.parse_args(argv)
        # Automatic scheduler detection
        if not args.config and not args.plot:
            raise InvalidDataError("No config file provided. This is required unless data is only being plotted.")
        if not args.scheduler and not args.cluster:
            if which('qsub'):
                args.scheduler = 'pbs'
                args.job_ext = '.pbs'
                args.sub_command = 'qsub'
                if not args.nprocs:
                    args.nprocs = DEF_NPROCS_FLUX
            elif which('sbatch'):
                args.scheduler = 'slurm'
                args.job_ext = '.job'
                args.sub_command = 'sbatch'
            else:
                args.scheduler = 'none'
                args.job_ext = '.pbs'
                args.sub_command = 'submit'
                if not args.nprocs:
                    args.nprocs = DEF_NPROCS_FLUX
        elif args.cluster == 'bridges' or args.scheduler == 'slurm':
            args.scheduler = 'slurm'
            args.job_ext = '.job'
            args.sub_command = 'sbatch'
            if not args.nprocs:
                args.nprocs = DEF_NPROCS_BRIDGES
        elif args.cluster == 'comet':
            if not args.nprocs:
                DEF_NPROCS_COMET
            raise InvalidDataError(
                "Scaling.py does not currently have a template for comet. "
                "Please contact xadams@umich.edu to learn how you can add this functionality.")
        elif args.cluster == 'flux' or args.scheduler == 'pbs':
            args.scheduler = 'pbs'
            args.job_ext = '.pbs'
            args.sub_command = 'qsub'
            if not args.nprocs:
                args.nprocs = DEF_NPROCS_FLUX

        args.filelist = []
        print(args.filelist)
        for nproc in args.nprocs:
            filename = args.basename + '_' + str(nproc)
            args.filelist.append(filename)
        for nnode in args.nnodes:
            if int(nnode) > 1:
                total_procs = str(nnode * args.nprocs[-1])
                filename = args.basename + '_' + total_procs
                args.filelist.append(filename)
        args.tpl_vals = proc_args(args)
        print("Hello WOrld")
        print(args.filelist)
        if args.software == 'namd':
            if args.cluster == 'bridges':
                args.run = RUN_NAMD_BRIDGES
            else:
                args.run = RUN_NAMD_PBS
            args.analysis = ANALYZE_NAMD
            args.out_pat = NAMD_OUT_PAT
            args.output = NAMD_OUTNAME
        elif args.software == 'amber':
            raise InvalidDataError(
                "The functionality of scaling with amber scripts has not been added yet. "
                "Please contact xadams@umich.edu if you would like to assist.")
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
        if not args.plot:
            submit_files(args)
            submit_analysis(args)
        if args.plot:
            plot_scaling(args.basename)

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
