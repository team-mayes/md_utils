from __future__ import print_function
import numpy as np
import os
import pyemma.plots as mplt
import argparse
import matplotlib.pyplot as plt
import mdtraj as md
from glob import glob
import csv
import sys
import warnings
from scipy.stats import gaussian_kde
from md_utils.md_common import IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, InvalidDataError, warning, \
    file_rows_to_list

# This line allows for plotting on PSC Bridges
plt.switch_backend('agg')

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError

DEF_IG_FILE = 'IG_indices.txt'
DEF_EG_FILE = 'EG_indices.txt'
DEF_COM_FILE = 'sugar_protein_indices.txt'
DEF_TRAJ = '*dcd'
DEF_TOP = '../step5_assembly.xplor_ext.psf'
DEF_NAME = 'PCA'
DEF_STRIDE = 1

plt.rcParams.update({'font.size': 12})


def save_figure(name, out_dir=None):
    # change these if desired
    if out_dir is None:
        fig_dir = './'
    else:
        fig_dir = out_dir
    plt.savefig(fig_dir + '/' + name, bbox_inches='tight')


def com_distance(traj, indexfile):
    # this function accepts a trajectory and a file with two rows of
    # 0 indexed indices to compute the center of mass for 2 groups
    with open(indexfile, newline='') as file:
        rows = csv.reader(file, delimiter=' ', quotechar='|')
        ind_list = []
        for row in rows:
            ind_list.append(row)
    fronthalf = np.array(ind_list[0], int)
    backhalf = np.array(ind_list[1], int)
    traj1 = traj.atom_slice(fronthalf)
    traj2 = traj.atom_slice(backhalf)
    com1 = md.compute_center_of_mass(traj1)
    com2 = md.compute_center_of_mass(traj2)

    n = com1.shape[0]
    distance = np.empty([n], float)
    for i in range(0, n):
        distance[i] = abs(np.linalg.norm(com1[i, :] - com2[i, :])) * 10
    return distance


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Plot trajectory files projected onto EG and IG dimensions')
    parser.add_argument("-t", "--traj",
                        help='Trajectory file or files for analysis. Wildcard arguments such as "*dcd" '
                             'are permitted but must be written as a string',
                        default=DEF_TRAJ)
    parser.add_argument("-l", "--list",
                        help="List of trajectory files to process. Use this option instead of glob "
                             "if memory is a concern.",
                        default=None)
    parser.add_argument("-p", "--top", help="Topology file for the given trajectory files.",
                        default=DEF_TOP)
    parser.add_argument("-i", "--indices", help="Separate files with the EG and IG indices.", default=None, nargs='+')
    parser.add_argument("-n", "--name", help="Name for the saved plot. Default name is {}".format(DEF_NAME),
                        default=DEF_NAME)
    parser.add_argument("-o", "--outdir", help="Directory to save the figure to, default is current directory.",
                        default=None)
    parser.add_argument("-f", "--file", help="Text file containing logged distances to plot.", default=None)
    parser.add_argument("-w", "--write_dist",
                        help="Flag to log distances as a csv file rather than generate plot. "
                             "Useful when dealing with large trajectories or limited memory.",
                        action='store_true', default=False)
    parser.add_argument("-s", "--stride",
                        help="Frequency with which to read in frames from trajectory files. Default is {}.".format(
                            DEF_STRIDE), type=int, default=DEF_STRIDE)
    parser.add_argument("-c", "--com", help="Flag to switch to a 1D CoM plot instead of a 2D PCA plot.",
                        action='store_true', default=False)

    args = None
    try:
        args = parser.parse_args(argv)
        args.traj_list = []
        args.index_list = []
        # If a log file is read in, trajectory information is not required
        if args.file:
            args.traj_list.append("None")
        else:
            if args.list:
                args.traj_list += file_rows_to_list(args.list)
            else:
                args.traj_list.append(args.traj)
            if len(args.traj_list) < 1:
                raise InvalidDataError(
                    "Found no traj file names to process. Specify one or more files as specified in "
                    "the help documentation ('-h').")
            if not os.path.isfile(args.top):
                raise IOError("Could not find specified file: {}".format(args.top))
            # Process index information
            if args.indices == None and not args.com:
                args.index_list.append(DEF_EG_FILE)
                args.index_list.append(DEF_IG_FILE)
            elif args.indices == None and args.com:
                args.index_list.append(DEF_COM_FILE)
            else:
                for index in args.indices:
                    args.index_list.append(index)
            for index in args.index_list:
                if not os.path.isfile(index):
                    raise IOError("Could not find specified index file: {}".format(index))
        # Check for stride error
        if args.stride < 1:
            raise InvalidDataError("Input error: the integer value for '{}' must be > 1.".format(args.stride))
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except (KeyError, InvalidDataError, SystemExit) as e:
        if hasattr(e, 'code') and e.code == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


def plot_trajectories(traj, topfile, indices, plot_name, stride, out_dir=None, log_file=None, write=False, com=False):
    if log_file:
        print("Reading data from log file: {}.".format(log_file))
        traj = []
        if com:
            COM_list = []
            log = open(log_file)
            data = log.readlines()
            # a sad sad double for-loop of sadness. I don't know any better!
            for row in data:
                s_data = row.split(sep=',')
                if s_data[0][0] == '#':
                    traj.append(s_data[0].rstrip("\n"))
                else:
                    for i in s_data:
                        COM_list.append(i)
            log.close()
            COM_distance = np.array(COM_list, float)
        else:
            EG_list = []
            IG_list = []
            logging = 'eg'
            log = open(log_file)
            data = log.readlines()
            # a sad sad double for-loop of sadness. I don't know any better!
            for row in data:
                s_data = row.split(sep=',')
                if s_data[0][0] == '#':
                    traj.append(s_data[0].rstrip("\n"))
                elif logging == 'eg':
                    for i in s_data:
                        EG_list.append(i)
                    logging = 'ig'
                else:
                    for i in s_data:
                        IG_list.append(i)
                    logging = 'eg'
            log.close()
            EG_distance = np.array(EG_list, float)
            IG_distance = np.array(IG_list, float)

    else:
        # TODO: Restructure to more easily change to a different CV
        print("Reading data from trajectory: {}.".format(traj))
        trajfile = glob(traj)
        t = md.load(trajfile, top=topfile, stride=stride)

        if com:
            COM_distance = com_distance(t, indices[0])
        else:
            # TODO: Add some resiliency to the eg/ig file determination
            eg_file = indices[0]
            ig_file = indices[1]
            EG_distance = com_distance(t, eg_file)
            IG_distance = com_distance(t, ig_file)
        del t

    if write:
        if out_dir is None:
            csv_dir = './'
        else:
            csv_dir = out_dir
        csv_name = csv_dir + '/' + plot_name + '.csv'
        if os.path.isfile(csv_name):
            print("Appended file: ", csv_name)
        else:
            print("Wrote file: ", csv_name)
        with open(csv_name, 'a') as csvfile:
            dist_writer = csv.writer(csvfile, delimiter=',')
            csvfile.write("#")
            csvfile.write(''.join(traj))
            csvfile.write('\n')
            if com:
                dist_writer.writerow(COM_distance)
            else:
                dist_writer.writerow(EG_distance)
                dist_writer.writerow(IG_distance)
    else:
        figure, ax = plt.subplots()
        if com:
            ax.set_ylim(0, 20)
            dummy = np.linspace(min(COM_distance), max(COM_distance), COM_distance.size)
            density = gaussian_kde(COM_distance)
            density.covariance_factor = lambda: .25
            density._compute_covariance()
            ydummy = density(dummy)
            xlabel = "Timestep"
            ylabel = "CoM Distance ($\AA$)"
            plt.plot(COM_distance)
            ax2 = ax.twiny()
            ax.set_xlim(0)
            ax2.set_xlim(0, 1)
            ax2.plot(ydummy, dummy, antialiased=True, linewidth=2)
            ax2.fill_between(ydummy, dummy, alpha=.5, zorder=5, antialiased=True)
            # plt.hist(COM_distance, normed=1, facecolor='blue', alpha=0.5, orientation='horizontal')
        else:
            ax.set_xlim(7.5, 15)
            ax.set_ylim(7, 17)
            xlabel = "EG Distance ($\AA$)"
            ylabel = "IG Distance ($\AA$)"

            # Suppress the error associated with a larger display window than is sampled
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mplt.plot_free_energy(EG_distance, IG_distance, avoid_zero_count=False, ax=ax, kT=2.479, cmap="winter",
                                      cbar_label=None,
                                      cbar=False)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        save_figure(plot_name, out_dir)
        print("Wrote file: {}".format(plot_name + '.png'))
        plt.close("all")


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    try:
        for file in args.traj_list:
            plot_trajectories(file, args.top, args.index_list, args.name, args.stride, args.outdir,
                              args.file, args.write_dist, args.com)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
