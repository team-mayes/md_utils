from __future__ import print_function
import numpy as np
import os
import pyemma.plots as mplt
import argparse
import matplotlib.pyplot as plt
from matplotlib import gridspec
from scipy.stats import gaussian_kde
import sys
import warnings
from md_utils.md_common import IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, InvalidDataError, warning

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
DELTA_PHI = False

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError

DEF_NAME = 'PCA'
DEF_QUAT_FILE = "orientation.log"
ROTATION_AXIS = np.array([0.9647, 0.2503, 0.0815])  # Referenced Unbiased opening rotation axis

plt.rcParams.update({'font.size': 12})


def save_figure(name, out_dir=None):
    # change these if desired
    if out_dir is None:
        fig_dir = './'
    else:
        fig_dir = out_dir
    plt.savefig(fig_dir + '/' + name, bbox_inches='tight')


def read_com(log_file):
    print("Reading data from log file: {}.".format(log_file))
    com_list = []
    with open(log_file, "rt") as fin:
        for row in fin:
            s_data = row.split(sep=',')
            if not s_data[0][0] == '#':
                com_list.append(s_data)
    return np.concatenate([np.array(i, float) for i in com_list])


def plot_com(data, ax, label=None):
    ax[0].plot(data[0], label=label)
    if HISTOGRAMS:
        dummy = np.linspace(min(data[0]), max(data[0]), data[0].size)
        density = gaussian_kde(data[0])
        density.covariance_factor = lambda: .25
        density._compute_covariance()
        ydummy = density(dummy)
        ax[1].plot(ydummy, dummy, antialiased=True, linewidth=2)
        ax[1].fill_between(ydummy, dummy, alpha=.5, zorder=5, antialiased=True)


def read_orient(log_file):
    q1_6_angles = []
    q7_12_angles = []
    delta1_6_angles = []
    delta7_12_angles = []

    with open(log_file, "rt") as fin:
        for line in fin:
            if line != '\n' and line[0] != '#':
                s_line = line.split()
                q1_6, q7_12 = 2 * 180 * np.arccos(float(s_line[2])) / np.pi, 2 * 180 * np.arccos(
                    float(s_line[11])) / np.pi
                q1_6_angles.append(q1_6), q7_12_angles.append(q7_12)

    return [q1_6_angles, q7_12_angles, delta1_6_angles, delta7_12_angles]


def plot_orient(data, ax, label=None):
    # ax[0].plot(q1_6_angles, label='N (static)-domain')
    # ax[0].plot(q7_12_angles, label='C (mobile)-domain')
    # ax[0].legend()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mplt.plot_free_energy(data[0], data[1], avoid_zero_count=False, ax=ax[0], kT=2.479,
                              cmap="winter",
                              cbar_label=None,
                              cbar=False)
    if DELTA_PHI:
        ax[1].plot(data[2], label='N (static)-domain')
        ax[1].plot(data[3], label='C (mobile)-domain')
        ax[1].axhline(y=150, linestyle='--')
        ax[1].axhline(y=30, linestyle='--')
        ax[1].legend()


def read_eg_ig(log_file):
    eg_list = []
    ig_list = []
    with open(log_file, "rt") as fin:
        for line in fin:
            if line != '\n' and line[0] != '#':
                s_line = line.split()
                eg_list.append(s_line[1]), ig_list.append(s_line[2])
    eg_distance = np.array(eg_list, float)
    ig_distance = np.array(ig_list, float)
    return [eg_distance, ig_distance]


def plot_eg_ig(data, ax, label=None):
    # Suppress the error associated with a larger display window than is sampled
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mplt.plot_free_energy(data[0], data[1], avoid_zero_count=False, ax=ax[0], kT=2.479,
                              cmap="winter",
                              cbar_label=None,
                              cbar=False)
        if LINE_GRAPHS:
            ax[1].plot(data[0])
            ax[2].plot(data[1])


def parse_cmdline(argv=None):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(
        description='Plot trajectory files projected onto gating or orientation dimensions')
    parser.add_argument("-n", "--name", help="Name for the saved plot. "
                                             "Default name is the input file name with _com or _2D "
                                             "depending on whether a 1 or 2D plot is generated",
                        default=None)
    parser.add_argument("--outdir", help="Directory to save the figure to, default is current directory.",
                        default=None)
    parser.add_argument("file", metavar='file', type=str, help="Text files containing logged distances to plot.",
                        nargs='+')
    parser.add_argument("-c", "--com", help="Flag to switch to a 1D CoM plot instead of a 2D PCA plot.",
                        action='store_true', default=False)
    parser.add_argument("-o", "--orientation",
                        help="Flag to switch to plot quaternion orientations of 2 or more protein domains. "
                             "If no file is provided (-f), will use default of {}".format(DEF_QUAT_FILE),
                        action='store_true', default=False)

    args = None
    try:
        args = parser.parse_args(argv)
        for file in args.file:
            if not os.path.isfile(file):
                raise InvalidDataError("Could not find file {}".format(file))
        if args.orientation and args.com:
            raise InvalidDataError(
                "Cannot flag both for 1D CoM plot (-c) and quaternion orientation (-o).")
        elif args.orientation and bool(args.file) is False:
            args.file.append(DEF_QUAT_FILE)
        # If a log file is read in, trajectory information is not required
        if args.name is None:
            args.name = os.path.splitext(args.file[0])[0].split('/')[-1]
        elif os.path.splitext(args.name)[1] != '':
            print("Removing extension")
            args.name = args.name.split(".")[:-1][0]
        # Check for stride error
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


def proc_trajectories(args, log_file=None, ax=None, read_func=None, plot_func=None):
    # TODO: have plot_trajectories accept a "read_data" function rather than having to shoehorn it in
    if log_file:
        print("Reading data from log file: {}.".format(log_file))
        data = read_func(log_file)

    plot_func(data, ax, log_file)


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    # TODO: Figure out if I should move this to the parse_cmdline function
    try:
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
            # ax0.set(xlabel="Timestep", ylabel="$\\theta$ (degrees)")
            ax0.set(xlabel="N-domain $\\theta$ (degrees)", ylabel="C-domain $\\theta$ (degrees)", xlim=(0, 20),
                    ylim=(0, 20))
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

        if args.com:
            read_func = read_com
            plot_func = plot_com

        elif args.orientation:
            read_func = read_orient
            plot_func = plot_orient

        else:
            read_func = read_eg_ig
            plot_func = plot_eg_ig

        for file in args.file:
            proc_trajectories(args, file, ax, read_func=read_func, plot_func=plot_func)
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
