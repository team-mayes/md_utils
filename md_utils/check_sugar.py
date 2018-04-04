# This script accepts a topology file and trajectory to check if
# a sugar remains bound over the course of the simulation using call_vmd to execute check_sugar.tcl
import os
import argparse
import csv
import sys
from md_utils.call_vmd import call_vmd
from md_utils.md_common import warning, GOOD_RET, InvalidDataError, INPUT_ERROR, IO_ERROR, INVALID_DATA

DEF_CHECK_SUGAR = '~/md_utils/tests/test_data/call_vmd/sugar_check.tcl'
DEF_FREQ = '100'
DEF_TOP_FILE = '../step5_assembly.xplor_ext.psf'
DEF_DIR = './'

def read_output(dist_file, keep):
    bound = True
    with open(dist_file, newline='') as file:
        rows = csv.reader(file)
        for row in rows:
            if float(row[0]) > 20:
                bound = False
                keep = True

    if bound:
        print("Sugar is bound in all frames of the trajectory.")
    elif not bound:
        print("Sugar is unbound in the trajectory.")
    if not keep:
        os.remove(dist_file)


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(
        description='Calls VMD to execute sugar_check.tcl and returns whether or not the sugar remains bound.')
    parser.add_argument("-t", "--traj", help="Trajectory file for analysis.")
    parser.add_argument("-p", "--top", help="Topology file for analysis.The default is {}.".format(DEF_TOP_FILE),
                        default=DEF_TOP_FILE)
    parser.add_argument("-n", "--name", help="Name of output file. Default is the base filename.", default=None)
    parser.add_argument("-o", "--outdir",
                        help="Output directory. Default is current directory. Relative path must begin with './'",
                        default=DEF_DIR)
    parser.add_argument("-s", "--script", help="Location of the sugar_check tcl script.", default=DEF_CHECK_SUGAR)
    parser.add_argument("-a", "--args", help="Additional arguments, required by some tcl scripts.", default=DEF_FREQ)
    parser.add_argument("-k", "--keep",
                        help="Flag to retain distance measurement file. "
                             "Default is to delete if bound and retain for further analysis if unbound.",
                        action='store_true', default=False)

    args = None
    try:
        args = parser.parse_args(argv)
        if not args.traj:
            raise InvalidDataError("Found no trajectory file to process. Specify a trajectory file as specified in "
                                   "the help documentation ('-h').")

        for file in [args.top, args.traj]:
            if not os.path.isfile(file):
                raise IOError("Could not find specified file: {}".format(file))

    except IOError as e:
        warning(e)
        parser.print_help()
        return args, IO_ERROR
    except (KeyError, InvalidDataError, SystemExit) as e:
        if hasattr(e, 'code') and e.code == 0:
            return args, GOOD_RET
        warning("Input data missing:", e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    # Read and execute sugar_check script
    if args.name:
        file_path = (args.outdir + '/' + args.name)
    else:
        file_path = (args.outdir + '/' + os.path.splitext(os.path.basename(args.traj))[0] + '.txt')
    try:
        call_vmd(args.top, args.traj, args.script, file_path, args.args)
        read_output(file_path, args.keep)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except (InvalidDataError, ValueError) as e:
        warning("Problems with input:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
