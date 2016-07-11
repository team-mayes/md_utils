# coding=utf-8

"""
Common WHAM logic.
"""
import logging
import os

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wham')

# Defaults #

DEF_TPL_DIR = os.path.join(os.getcwd(), 'tpl')
DEF_BASE_SUBMIT_TPL = "submit_wham.tpl"
DEF_LINE_SUBMIT_TPL = "submit_wham_line.tpl"
DEF_PART_LINE_SUBMIT_TPL = "submit_wham_part_line.tpl"

# Constants #

STEP_SUBMIT_FNAME = "submit_wham.{:02d}"

# Keys #

# -Meta- #

LINES_KEY = "lines"
DIR_KEY = "dir"
LOC_KEY = "loc"

# -Radial Correction- #

CORR_KEY = 'corr'
COORD_KEY = 'coord'
FREE_KEY = 'free_energy'
RAD_KEY_SEQ = [COORD_KEY, FREE_KEY, CORR_KEY]

# Exceptions #


class TemplateNotReadableError(Exception):
    pass


def read_meta(meta_file):
    """
    Reads the given meta file, returning the parsed value as a dict containing:

    * loc: A string with the original (possibly relative) location
    * dir: A string with absolute path for the directory containing the meta file.
    * lines: a list of four-element lists that represent each line in the meta file.

    :param meta_file: The meta file to parse.
    :return: The parsed contents of the meta file.
    """
    meta = {LOC_KEY: meta_file, DIR_KEY: os.path.dirname(os.path.abspath(meta_file))}
    lines = []
    with open(meta_file) as m_file:
        for m_line in m_file:
            lines.append(m_line.strip().split())
    meta[LINES_KEY] = lines
    return meta


def read_rmsd(fname):
    """
    Reads the RMSD file at the given file name.

    :param fname: The file's location.
    :return: The values in the RMSD file.
    """
    rmsd_values = []
    with open(fname) as r_file:
        row_val = None
        for r_line in r_file:
            try:
                row_val = r_line.split()[1]
                rmsd_values.append(float(row_val))
            except IndexError:
                logger.warn("RMSD Line '%s' did not have two fields", r_line)
            except TypeError:
                logger.warn("RMSD Value '%s' is not a float", row_val)
    return rmsd_values


def read_meta_rmsd(meta):
    """
    Finds and parses the RMSD files described in the given parsed meta file's contents.

    :param meta: The result of calling read_meta with a meta file location.
    :return: A dict of lists containing floats for each line in each found RMSD file
        keyed by the RMSD file name (no directory info is included in the key)
    """
    rmsd_data = {}
    for line in meta[LINES_KEY]:
        rmsd_fname = os.path.basename(line[0])
        floc = os.path.join(meta[DIR_KEY], line[0])
        rmsd_data[rmsd_fname] = read_rmsd(floc)
    return rmsd_data


def write_rmsd(data, tgt_file):
    """Writes the given RMSD data list into the given target location.

    :param data: The list of data to write.
    :param tgt_file: The target file location.
    """
    with open(tgt_file, 'w') as w_file:
        for i, rmsd_val in enumerate(data, 1):
            w_file.write("\t".join((str(i), str(rmsd_val))))
            w_file.write("\n")
    print("Wrote file: {}".format(tgt_file))


def fill_submit_wham(base_tpl, line_tpl, cur_step, use_part=False):
    """Fills the base template with one or more lines from the filled line
    template and returns the result.

    :param base_tpl: The base template to fill.  Expected to have a
        `{wham_block}` element.
    :param line_tpl: The line template to fill.  Expected to have one or
        more `{step}` elements.
    :param cur_step: The current step.
    :param use_part: Whether to add lines for each part of a split step.
    :return: The results of filling the template.
    """
    step_lines = []
    if use_part:
        for step_part in range(1, cur_step + 2):
            step_lines.append(line_tpl.format(step=cur_step,
                                              step_part=step_part))
    else:
        step_lines.append(line_tpl.format(step=cur_step))
    return base_tpl.format(wham_block=''.join(step_lines))
