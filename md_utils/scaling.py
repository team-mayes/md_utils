import argparse
import subprocess
import matplotlib.pyplot as plt
import sys

def make_file(basename, n_list):
    for n in n_list:
        with open(filename, 'w') as fout:
            #makes the file
        subprocess.call(["qsub", filename])
    #TODO: Make this work
    return jobfile

def make_analysis(basename, n_list):
    #TODO: I'm not sure what this will look like yet, but it will include namd_log_proc and the python plotting bit
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
    #TODO: Add description and arguments, should include name, config file, runtime, maybe a template job file?
    parser = argparse.ArgumentParser(description='Command-line NAMD template script editor.')
    parser.add_argument("-t", "--type", help="The type of job needed. Valid options are {}. "
                                             "The default option is {}.".format(TYPES, DEF_TYPE),
                        choices=TYPES, default=DEF_TYPE)

    args = None
    try:
        args = parser.parse_args(argv)
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
