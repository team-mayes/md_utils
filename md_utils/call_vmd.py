import subprocess

def call_vmd(psf,pdb,script,name):
    subprocess.call(["/Applications/VMD 1.9.3.app/Contents/Resources/VMD.app/Contents/MacOS/VMD", "-e", script, "-dispdev", "text", psf, pdb])


PSF="../tests/test_data/call_vmd/open_xylose.psf"
PDB="../tests/test_data/call_vmd/open_xylose.pdb"
SCRIPT="../../../bin/tcl_scripts/prot.tcl"
NAME="hello"
call_vmd(PSF,PDB,SCRIPT,NAME)
# subprocess.call(["/Applications/VMD 1.9.3.app/Contents/Resources/VMD.app/Contents/MacOS/VMD", "-e", "../../../bin/tcl_scripts/prot.tcl", "-dispdev", "text", "../tests/test_data/call_vmd/open_xylose.psf", "../tests/test_data/call_vmd/open_xylose.pdb"])

def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Calls VMD to execute a tcl script.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)
    args = None
    try:
        args = parser.parse_args(argv)
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

    cfg = args.config

    # Read and process FEP files
    try:
        process_FEP(cfg)
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
