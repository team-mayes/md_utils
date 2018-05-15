from __future__ import print_function
import numpy as np
import os
import pyemma.plots as mplt
import argparse
import matplotlib.pyplot as plt
from matplotlib import gridspec
from scipy.stats import gaussian_kde
import mdtraj as md
from glob import glob
import csv
import sys
import warnings
import copy as copy
from md_utils.fill_tpl import read_cfg
from md_utils.md_common import IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, InvalidDataError, warning, \
    file_rows_to_list

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

# This line switches to a non-Gui backend, allowing plotting on PSC Bridges
plt.switch_backend('agg')

HISTOGRAMS = False
LINE_GRAPHS = False
DELTA_PHI = True

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError

DEF_IG_FILE = 'IG_indices.txt'
DEF_EG_FILE = 'EG_indices.txt'
DEF_COM_FILE = 'sugar_protein_indices.txt'
DEF_TOP = '../step5_assembly.xplor_ext.psf'
DEF_NAME = 'PCA'
DEF_STRIDE = 1
DEF_CFG_FILE = "plot_pca.ini"
DEF_QUAT_FILE = "orientation.log"

MAIN_SEC = 'main'
TPL_VALS_SEC = 'tpl_vals'
VALID_SEC_NAMES = [MAIN_SEC, TPL_VALS_SEC]
TPL_VALS = 'parameter_values'

plt.rcParams.update({'font.size': 12})


def save_figure(name, out_dir=None):
    # change these if desired
    if out_dir is None:
        fig_dir = './'
    else:
        fig_dir = out_dir
    plt.savefig(fig_dir + '/' + name, bbox_inches='tight')


def unit_vector(vector):
    return vector / np.linalg.norm(vector)


def angle_between(v1, v2):
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)) * 180 / np.pi


def com_distance(traj, group1, group2):
    # this function accepts a trajectory and a file with two rows of
    # 0 indexed indices to compute the center of mass for 2 groups

    traj1 = traj.atom_slice(group1)
    traj2 = traj.atom_slice(group2)
    com1 = md.compute_center_of_mass(traj1)
    com2 = md.compute_center_of_mass(traj2)

    n = com1.shape[0]
    distance = np.empty([n], float)
    for i in range(0, n):
        distance[i] = abs(np.linalg.norm(com1[i, :] - com2[i, :])) * 10  # convert from nm to Angstroms
    return distance


def parse_cmdline(argv=None):
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
                        default=None)
    parser.add_argument("-l", "--list",
                        help="List of trajectory files to process. Use this option instead of glob "
                             "if memory is a concern.",
                        default=None)
    parser.add_argument("-p", "--top", help="Topology file for the given trajectory files.",
                        default=DEF_TOP)
    parser.add_argument("-i", "--indices", help="Separate files with the EG and IG indices.", default=None, nargs='+')
    parser.add_argument("-n", "--name", help="Name for the saved plot. "
                                             "Default name is the input file name with _com or _2D "
                                             "depending on whether a 1 or 2D plot is generated",
                        default=None)
    parser.add_argument("--outdir", help="Directory to save the figure to, default is current directory.",
                        default=None)
    parser.add_argument("-f", "--file", help="Text file containing logged distances to plot.", default=[], nargs='+')
    # parser.add_argument("-w", "--write_dist",
    #                     help="Flag to log distances as a csv file rather than generate plot. "
    #                          "Useful when dealing with large trajectories or limited memory. "
    #                          "Default is True for reading from trajectory files.",
    #                     action='store_true', default=False)
    parser.add_argument("-s", "--stride",
                        help="Frequency with which to read in frames from trajectory files. Default is {}.".format(
                            DEF_STRIDE), type=int, default=DEF_STRIDE)
    parser.add_argument("-c", "--com", help="Flag to switch to a 1D CoM plot instead of a 2D PCA plot.",
                        action='store_true', default=False)
    parser.add_argument("--config",
                        help="Filename to pass arguments to plot_PCA as a config file. Default is {}".format(
                            DEF_CFG_FILE), default=DEF_CFG_FILE, type=read_cfg)
    parser.add_argument("-o", "--orientation",
                        help="Flag to switch to plot quaternion orientations of 2 or more protein domains. "
                             "If no file is provided (-f), will use default of {}".format(DEF_QUAT_FILE),
                        action='store_true', default=False)

    args = None
    # TODO: if index files don't exist, automatically generate them
    # TODO: If worthwhile, add capability to read in quat trajectories or write out files
    try:
        args = parser.parse_args(argv)
        args.traj_list = []
        args.index_list = []
        args.write_dist = False
        if args.orientation and args.com:
            raise InvalidDataError(
                "Cannot flag both for 1D CoM plot (-c) and quaternion orientation (-o).")
        elif args.orientation and args.traj:
            raise InvalidDataError(
                "plot_PCA is not currently configured to extract orientation data from trajectories."
            )
        elif args.orientation and args.write_dist:
            raise InvalidDataError(
                "plot_PCA is not currently configured to write orientation data to a file."
            )
        elif args.orientation and bool(args.file) is False:
            args.file.append(DEF_QUAT_FILE)
        if args.config is not None:
            if args.name is None and args.config['filled_tpl_name']:
                args.name = args.config['filled_tpl_name']
            if args.indices is None and bool(args.config['parameter_values']['indices']) is True:
                for index in args.config['parameter_values']['indices']:
                    args.index_list.append(index)
            if args.top is DEF_TOP and bool(args.config['parameter_values']['top']) is True:
                args.top = args.config['parameter_values']['top'][0]
        # If a log file is read in, trajectory information is not required
        if not args.file:
            args.write_dist = True
            if args.list:
                if args.name is None:
                    args.name = os.path.splitext(args.list)[0].split('/')[-1]
                args.traj_list += file_rows_to_list(args.list)
            else:
                args.traj_list.append(args.traj)
                if args.name is None:
                    args.name = os.path.splitext(args.traj)[0].split('/')[-1]
            if len(args.traj_list) < 1:
                raise InvalidDataError(
                    "Found no traj file names to process. Specify one or more files as specified in "
                    "the help documentation ('-h').")
            for traj in args.traj_list:
                if not os.path.isfile(traj):
                    raise IOError("Could not find specified file: {}".format(traj))
            if not os.path.isfile(args.top):
                raise IOError("Could not find specified file: {}".format(args.top))
            # Process index information
            if bool(args.index_list) is False:
                if args.indices is None and not args.com:
                    args.index_list.append(DEF_EG_FILE)
                    args.index_list.append(DEF_IG_FILE)
                elif args.indices is None and args.com:
                    args.index_list.append(DEF_COM_FILE)
                else:
                    for index in args.indices:
                        args.index_list.append(index)
                    if "IG" in args.index_list[0]:
                        print("Detected index file {} as IG index. Swapping now.".format(args.index_list[0]))
                        args.index_list[0], args.index_list[1] = args.index_list[1], args.index_list[0]
            for index in args.index_list:
                if not os.path.isfile(index):
                    raise IOError("Could not find specified index file: {}".format(index))
        if args.name is None:
            args.name = os.path.splitext(args.file[0])[0].split('/')[-1]
        elif os.path.splitext(args.name)[1] != '':
            print("Removing extension")
            args.name = args.name.split(".")[:-1][0]
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


def plot_trajectories(traj, topfile, indices, plot_name, stride, out_dir=None, log_file=None, write=False, com=False,
                      orient=False, ax=None):
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

        elif orient:
            q1_6_angles = []
            q7_12_angles = []
            delta1_6_angles = []
            delta7_12_angles = []

            with open(log_file, "rt") as fin:
                U = np.array([0.9647, 0.2503, 0.0815]) # Referenced Unbiased opening rotation axis
                for line in fin:
                    if line != '\n' and line[0] != '#':
                        s_line = line.split()
                        q1_6, q7_12 = 2 * 180 * np.arccos(float(s_line[2])) / np.pi, 2 * 180 * np.arccos(
                            float(s_line[11])) / np.pi
                        if DELTA_PHI:
                            v1_6 = np.array([s_line[4], s_line[6], s_line[8]], float)
                            v7_12 = np.array([s_line[13], s_line[15], s_line[17]], float)
                            delta1_6 = angle_between(v1_6, U)
                            delta7_12 = angle_between(v7_12, U)
                            delta1_6_angles.append(delta1_6), delta7_12_angles.append(delta7_12)
                            if delta1_6 > 150:
                                q1_6 *= -1
                            elif delta1_6 > 30:
                                q1_6 = 0
                            if delta7_12 > 150:
                                q7_12 *= -1
                            elif delta7_12 > 30:
                                q7_12 = 0

                        q1_6_angles.append(q1_6), q7_12_angles.append(q7_12)

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

        ind_list = []
        for indexfile in indices:
            with open(indexfile, newline='') as file:
                rows = csv.reader(file, delimiter=' ', quotechar='|')
                for row in rows:
                    ind_list.append(row)
        # compress to 1D list. Would love to hear an alternative way to do this
        atom_indices = np.array([j for i in ind_list for j in i], int)

        trajfile = glob(traj)
        t = md.load(trajfile, top=topfile, stride=stride, atom_indices=atom_indices)

        if com:
            group_indices = np.linspace(0, atom_indices.size - 1, atom_indices.size)
            group1 = group_indices[0:len(ind_list[0])].astype(int)
            group2 = group_indices[len(ind_list[0]):].astype(int)
            COM_distance = com_distance(t, group1, group2)
        else:
            # don't look at it, it's hideous
            group_indices = np.linspace(0, atom_indices.size - 1, atom_indices.size)
            group1 = group_indices[0:len(ind_list[0])].astype(int)
            group2 = group_indices[len(ind_list[0]):len(ind_list[0]) + len(ind_list[1])].astype(int)
            group3 = group_indices[
                     len(ind_list[0]) + len(ind_list[1]):len(ind_list[0]) + len(ind_list[1]) + len(ind_list[2])].astype(
                int)
            group4 = group_indices[len(ind_list[0]) + len(ind_list[1]) + len(ind_list[2]):].astype(int)
            EG_distance = com_distance(t, group1, group2)
            IG_distance = com_distance(t, group3, group4)
        del t

    if write:
        if out_dir is None:
            csv_dir = './'
        else:
            csv_dir = out_dir
        if com:
            csv_name = csv_dir + '/' + plot_name + '_com' + '.csv'
        else:
            csv_name = csv_dir + '/' + plot_name + '_2D' + '.csv'
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
    elif not write:
        if com:
            ax[0].plot(COM_distance, label=log_file)
            if HISTOGRAMS:
                dummy = np.linspace(min(COM_distance), max(COM_distance), COM_distance.size)
                density = gaussian_kde(COM_distance)
                density.covariance_factor = lambda: .25
                density._compute_covariance()
                ydummy = density(dummy)
                ax[1].plot(ydummy, dummy, antialiased=True, linewidth=2)
                ax[1].fill_between(ydummy, dummy, alpha=.5, zorder=5, antialiased=True)

        elif orient:
            ax[0].plot(q1_6_angles, label='N (static)-domain')
            ax[0].plot(q7_12_angles, label='C (mobile)-domain')
            ax[0].legend()
            # with warnings.catch_warnings():
            #     warnings.simplefilter("ignore")
            #     mplt.plot_free_energy(q1_6_angles, q7_12_angles, avoid_zero_count=False, ax=ax[0], kT=2.479,
            #                           cmap="Reds",
            #                           cbar_label=None,
            #                           cbar=True)
            if DELTA_PHI:
                ax[1].plot(delta1_6_angles, label='N (static)-domain')
                ax[1].plot(delta7_12_angles, label='C (mobile)-domain')
                ax[1].axhline(y=150,linestyle='--')
                ax[1].axhline(y=30,linestyle='--')
                ax[1].legend()


        else:
            # Suppress the error associated with a larger display window than is sampled
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mplt.plot_free_energy(EG_distance, IG_distance, avoid_zero_count=False, ax=ax[0], kT=2.479,
                                      cmap="winter",
                                      cbar_label=None,
                                      cbar=False)
                if LINE_GRAPHS:
                    ax[1].plot(EG_distance)
                    ax[2].plot(IG_distance)


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    try:
        if not args.write_dist:
            if args.com:
                fig, ax0 = plt.subplots()
                ax0.set_ylim(0, 20)
                ax0.set_xlabel = "Timestep"
                ax0.set_ylabel = "CoM Distance ($\AA$)"
                ax = [ax0]
                if HISTOGRAMS:
                    ax1 = ax0.twiny()
                    ax1.set_xlim(0, 1)
                    ax.append(ax1)

            elif args.orientation:
                fig, ax0 = plt.subplots()
                # TODO: If I stick with orientation histograms, make the LINE_GRAPHS variable also govern these plots
                ax0.set(xlabel="Timestep", ylabel="$\\theta$ (degrees)")
                # ax0.set(xlabel="N-domain $\\theta$ (degrees)", ylabel="C-domain $\\theta$ (degrees)")
                ax = [ax0]
                if DELTA_PHI:
                    ax0 = plt.subplot(212)
                    ax0.set(xlabel="Timestep", ylabel="$\\theta$ (degrees)")
                    ax1 = plt.subplot(211, sharex=ax0)
                    ax1.set(ylabel="$\Delta$$\phi$ (degrees)")
                    # ax1.set_ylim(0, 60)
                    ax = [ax0, ax1]

            else:
                fig, ax0 = plt.subplots()
                ax = [ax0]
                if LINE_GRAPHS:
                    fig = plt.figure()
                    gs = gridspec.GridSpec(2, 2, width_ratios=[2, 1])
                    ax0 = fig.add_subplot(gs[:, 0])
                    ax1 = fig.add_subplot(gs[0, 1])
                    ax2 = fig.add_subplot(gs[1, 1])
                    ax1.set_ylim(0, 20)
                    ax1.set(ylabel="EG Distance ($\AA$)")
                    ax2.set_ylim(0, 20)
                    ax2.set(xlabel="Timestep", ylabel="IG Distance ($\AA$)")
                    fig.tight_layout()
                    ax = [ax0, ax1, ax2]
                ax0.set_xlim(7.5, 15)
                ax0.set_ylim(7, 17)
                ax0.set(xlabel="Extracellular Gate Distance ($\AA$)", ylabel="Intracellular Gate Distance ($\AA$)")

        else:
            ax = []
        for traj in args.traj_list:
            plot_trajectories(traj, args.top, args.index_list, args.name, args.stride, args.outdir,
                              args.file, args.write_dist, args.com, args.orientation, ax)
        for file in args.file:
            plot_trajectories(args.traj, args.top, args.index_list, args.name, args.stride, args.outdir,
                              file, args.write_dist, args.com, args.orientation, ax)
        if not args.write_dist:
            if args.com:
                # This is declared here so as not to break the axis with the histogram
                ax0.set_xlim(0)
            if args.orientation:
                name = args.name + '_quat'
            else:
                name = args.name
            save_figure(name, args.outdir)
            print("Wrote file: {}".format(name + '.png'))
            plt.close("all")
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
