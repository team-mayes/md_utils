import subprocess
import argparse
from md_utils.FEP_edit import read_cfg
from md_utils.md_common import warning, GOOD_RET, InvalidDataError, INPUT_ERROR, IO_ERROR
import os

DEF_TOP_FILE = '../step5_assembly.xplor_ext.psf'
DEF_NAME = 'output'
DEF_DIR = './'


# DEF_CFG_FILE = 'vmd.ini'

def call_vmd(psf, pdb, script, name, args):
    subprocess.call(["vmd", psf, pdb, "-dispdev", "text", "-e", script, "-args", name, "".join(args)])


def call_catdcd(traj, number):
    subprocess.call(["catdcd -num", traj])


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Calls VMD to execute a tcl script.')
    parser.add_argument("-t", "--traj", help="Trajectory file for analysis.")
    parser.add_argument("-p", "--top", help="Topology file for analysis.The default is {}.".format(DEF_TOP_FILE),
                        default=DEF_TOP_FILE)
    parser.add_argument("-s", "--script", help="Tcl script to run through VMD")
    parser.add_argument("-n", "--name", help="Name of output file. Default is {}.".format(DEF_NAME), default=DEF_NAME)
    parser.add_argument("-o", "--outdir",
                        help="Output directory. Default is current directory. Relative path must begin with './'",
                        default=DEF_DIR)
    parser.add_argument("-a", "--args", help="Additional arguments, required by some tcl scripts.", default=[])
    # parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
    #                                            "The default file name is {}, located in the "
    #                                            "base directory where the program as run.".format(DEF_CFG_FILE),
    #                     default=DEF_CFG_FILE, type=read_cfg)
    args = None
    try:
        args = parser.parse_args(argv)
        if not args.traj:
            raise InvalidDataError("Found no trajectory file to process. Specify a trajectory file as specified in "
                                   "the help documentation ('-h').")
        elif not args.script:
            raise InvalidDataError("Found no tcl script to apply. Specify a tcl file as specified in "
                                   "the help documentation ('-h').")
        for file in [args.top, args.traj, args.script]:
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

    # cfg = args.config

    # Read and execute VMD scripts
    file_path = (args.outdir + '/' + args.name)
    try:
        call_vmd(args.top, args.traj, args.script, file_path, args.args)
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
