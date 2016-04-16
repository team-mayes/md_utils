# coding=utf-8

"""
Common methods for this project.
"""

from __future__ import print_function, division
# Util Methods #
import argparse
import collections
import csv
import difflib
import glob
import logging
from datetime import datetime
import re
import shutil
import errno
import fnmatch
from itertools import chain, islice

import math
import numpy as np
import os
from shutil import copy2, Error, copystat
import six
import sys
from cStringIO import StringIO
from contextlib import contextmanager
import matplotlib.pyplot as pyPlt

# logging.basicConfig(level=logging.DEBUG)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_md_utils')

# Constants #

BACKUP_TS_FMT = "_%Y-%m-%d_%H-%M-%S_%f"

# Boltzmann's Constant in kcal/mol Kelvin
BOLTZ_CONST = 0.0019872041
# Planck's Constant in kcal s / mol
PLANCK_CONST = 9.53707E-14
# Universal gas constant in kcal/mol K
R = 0.001985877534

# Tolerance based on double standard machine precision of 5 × 10−16 for float64 (decimal64)
TOL = 0.000000000000001


# Sections for reading files
SEC_TIMESTEP = 'timestep'
SEC_NUM_ATOMS = 'dump_num_atoms'
SEC_BOX_SIZE = 'dump_box_size'
SEC_ATOMS = 'atoms_section'

# Lammps-specific sections
MASSES = 'Masses'
PAIR_COEFFS = 'Pair Coeffs'
ATOMS = 'Atoms'
BOND_COEFFS = 'Bond Coeffs'
BONDS = 'Bonds'
ANGLE_COEFFS = 'Angle Coeffs'
ANGLES = 'Angles'
DIHE_COEFFS = 'Dihedral Coeffs'
DIHES = 'Dihedrals'
IMPR_COEFFS = 'Improper Coeffs'
IMPRS = 'Impropers'
LAMMPS_SECTION_NAMES = [MASSES, PAIR_COEFFS, ATOMS, BOND_COEFFS, BONDS, ANGLE_COEFFS, ANGLES,
                        DIHE_COEFFS, DIHES, IMPR_COEFFS, IMPRS]


# Exceptions #

class MdError(Exception):
    pass


class InvalidDataError(MdError):
    pass


class NotFoundError(MdError):
    pass


class ArgumentParserError(Exception):
    pass


class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)


def warning(*objs):
    """Writes a message to stderr."""
    print("WARNING: ", *objs, file=sys.stderr)


# Test utilities

## From http://schinckel.net/2013/04/15/capture-and-test-sys.stdout-sys.stderr-in-unittest.testcase/
@contextmanager
def capture_stdout(command, *args, **kwargs):
    out, sys.stdout = sys.stdout, StringIO()
    command(*args, **kwargs)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out


@contextmanager
def capture_stderr(command, *args, **kwargs):
    err, sys.stderr = sys.stderr, StringIO()
    command(*args, **kwargs)
    sys.stderr.seek(0)
    yield sys.stderr.read()
    sys.stderr = err


# Calculations #


def calc_kbt(temp_k):
    """
    Returns the given temperature in Kelvin multiplied by Boltzmann's Constant.

    :param temp_k: A temperature in Kelvin.
    :return: The given temperature in Kelvin multiplied by Boltzmann's Constant.
    """
    return BOLTZ_CONST * temp_k


def calc_k(temp, delta_gibbs):
    """
    Returns the rate coefficient calculated from Transition State Theory in inverse seconds
    @param temp: the temperature in Kelvin
    @param delta_gibbs: the change in Gibbs free energy in kcal/mol
    @return: rate coefficient in inverse sections
    """
    return BOLTZ_CONST * temp / PLANCK_CONST * math.exp(-delta_gibbs / (R * temp))


def xyz_distance(fir, sec):
    """
    Calculates the Euclidean distance between the two given
    coordinates (expected format is numbers as [x,y,z]).

    TODO: Consider adding numpy optimization if lib is present.

    :param fir: The first XYZ coordinate.
    :param sec: The second XYZ coordinate.
    :returns:  float -- The Euclidean distance between the given points.
    :raises: KeyError
    """
    return math.sqrt((fir[0] - sec[0]) ** 2 + (fir[1] - sec[1]) ** 2 + (fir[2] - sec[2]) ** 2)


def pbc_dist(a, b, box):
    # TODO: make a test that ensures the distance calculated is <= sqrt(sqrt((a/2)^2+(b/2)^2) + (c/2)^2))
    return np.linalg.norm(pbc_vector_diff(a, b, box))


def pbc_vector_diff(a, b, box):
    # TODO: test pbc
    vec = a - b
    return vec - box * np.asarray(map(round, vec / box))


# def dot_product(v1, v2):
#   return sum((a*b) for a, b in zip(v1, v2))
#
# def length(v):
#   return math.sqrt(dot_product(v, v))
#
# def angle(v1, v2):
#   return math.acos(dot_product(v1, v2) / (length(v1) * length(v2)))

def pbc_angle(p0, p1, p2, box):
    #
    print(p0, p1, p2, box)
    pass


# noinspection PyUnresolvedReferences
def pbc_dihedral(p0, p1, p2, p3, box):
    """
    From:
    http://stackoverflow.com/questions/20305272/
      dihedral-torsion-angle-from-four-points-in-cartesian-coordinates-in-python
    Khouli formula
    1 sqrt, 1 cross product
    @param p0: xyz coordinates of point 0, etc.
    @param p1:
    @param p2:
    @param p3:
    @param box: periodic box lengths
    @return: dihedral angle in degrees
    """
    b0 = -1.0 * (pbc_vector_diff(p1, p0, box))
    b1 = pbc_vector_diff(p2, p1, box)
    b2 = pbc_vector_diff(p3, p2, box)

    # normalize b1 so that it does not influence magnitude of vector
    # rejections that come next
    b1 /= np.linalg.norm(b1)

    # vector rejections
    # v = projection of b0 onto plane perpendicular to b1
    #   = b0 minus component that aligns with b1
    # w = projection of b2 onto plane perpendicular to b1
    #   = b2 minus component that aligns with b1
    v = b0 - np.dot(b0, b1) * b1
    w = b2 - np.dot(b2, b1) * b1

    # angle between v and w in a plane is the torsion angle
    # v and w may not be normalized but that's fine since tan is y/x
    x = np.dot(v, w)
    y = np.dot(np.cross(b1, v), w)
    return np.degrees(np.arctan2(y, x))


# Other #

def chunk(seq, chunk_size, process=iter):
    """Yields items from an iterator in iterable chunks.
    From https://gist.github.com/ksamuel/1275417

    :param seq: The sequence to chunk.
    :param chunk_size: The size of the returned chunks.
    :param process: The function to use for creating the iterator.  Useful for iterating over different
    data structures.
    :return: Chunks of the given size from the given sequence.
    """
    it = iter(seq)
    while True:
        yield process(chain([six.next(it)], islice(it, chunk_size - 1)))


# I/O #

def make_dir(tgt_dir):
    """
    Creates the given directory and its parent directories if it
    does not already exist.

    Keyword arguments:
    tgt_dir -- The directory to create

    """
    if not os.path.exists(tgt_dir):
        os.makedirs(tgt_dir)
    elif not os.path.isdir(tgt_dir):
        raise NotFoundError("Resource %s exists and is not a dir" %
                            tgt_dir)


def file_to_str(fname):
    """
    Reads and returns the contents of the given file.

    :param fname: The location of the file to read.
    :return: The contents of the given file.
    :raises: IOError if the file can't be opened for reading.
    """
    with open(fname) as f:
        return f.read()


def str_to_file(str_val, fname, mode='w'):
    """
    Writes the string to the given file.

    :param str_val: The string to write.
    :param fname: The location of the file to write.
    """
    with open(fname, mode) as f:
        f.write(str_val)


def np_float_array_from_file(data_file):
    """
    Adds to the basic np.loadtxt by performing data checks.
    @param data_file: file expected to have space-separated values, with the same number of entries per line
    @return: a numpy array or InvalidDataError if np.loadtxt was unsuccessful
    """
    try:
        dim_vectors = np.loadtxt(data_file, dtype=np.float64)
    except ValueError:
        with open(data_file) as d:
            first_line = None
            for line in d:
                line = line.strip()
                try:
                    f_line = [float(x) for x in line.split()]
                except ValueError:
                    raise InvalidDataError("Could not convert the following line to floats: {}".format(line))
                if first_line is None:
                    first_line = f_line
                else:
                    if len(f_line) != len(first_line):
                        raise InvalidDataError("File could not be read as an array of floats: {}\n  Expected "
                                               "space-separated values with an equal number of columns per row.\n  "
                                               "However, found {} values on the first line ({})\n  "
                                               "           and {} values on the later line ({})"
                                               "".format(data_file,
                                                         len(first_line), first_line,
                                                         len(f_line), f_line))
        raise InvalidDataError("File could not be read as an array of floats: {}\n Expected space-separated values "
                               "with an equal number of columns per row.".format(data_file))
    if len(dim_vectors.shape) == 1:
        raise InvalidDataError("File contains a vector, not an array of floats: {}\n".format(data_file))

    return dim_vectors


def create_backup_filename(orig):
    base, ext = os.path.splitext(orig)
    now = datetime.now()
    return "".join((base, now.strftime(BACKUP_TS_FMT), ext))


def find_backup_filenames(orig):
    base, ext = os.path.splitext(orig)
    found = glob.glob(base + "*" + ext)
    try:
        found.remove(orig)
    except ValueError:
        # Original not present; ignore.
        pass
    return found


def silent_remove(filename):
    """
    Removes the target file name, catching and ignoring errors that indicate that the
    file does not exist.

    :param filename: The file to remove.
    """
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


# TODO: Use this instead of duplicate logic in project.
def allow_write(f_loc, overwrite=False):
    """
    Returns whether to allow writing to the given location.

    :param f_loc: The location to check.
    :param overwrite: Whether to allow overwriting an existing location.
    :return: Whether to allow writing to the given location.
    """
    if os.path.exists(f_loc) and not overwrite:
        logger.warn("Not overwriting existing location '%s'", f_loc)
        return False
    return True


def move_existing_file(f_loc):
    """
    Renames an existing file using a timestamp based on the move time.

    :param f_loc: The location to check.
    """
    if os.path.exists(f_loc):
        shutil.move(f_loc, create_backup_filename(f_loc))


def create_out_fname(src_file, prefix='', suffix='', base_dir=None, ext=None):
    """Creates an outfile name for the given source file.

    :param src_file: The file to process.
    :param suffix: The file prefix to add, if specified.
    :param suffix: The file suffix to append, if specified.
    :param base_dir: The base directory to use; defaults to `src_file`'s directory.
    :param ext: The extension to use instead of the source file's extension;
        defaults to the `scr_file`'s extension.
    :return: The output file name.
    """

    if base_dir is None:
        base_dir = os.path.dirname(src_file)

    file_name = os.path.basename(src_file)
    base_name = os.path.splitext(file_name)[0]

    if ext is None:
        ext = os.path.splitext(file_name)[1]

    return os.path.abspath(os.path.join(base_dir, prefix + base_name + suffix + ext))


def find_files_by_dir(tgt_dir, pat):
    """Recursively searches the target directory tree for files matching the given pattern.
    The results are returned as a dict with a list of found files keyed by the absolute
    directory name.
    :param tgt_dir: The target base directory.
    :param pat: The file pattern to search for.
    :return: A dict where absolute directory names are keys for lists of found file names
        that match the given pattern.
    """
    match_dirs = {}
    for root, dirs, files in os.walk(tgt_dir):
        matches = [match for match in files if fnmatch.fnmatch(match, pat)]
        if matches:
            match_dirs[os.path.abspath(root)] = matches
    return match_dirs


def copytree(src, dst, symlinks=False, ignore=None):
    """This is a copy of the standard Python shutil.copytree, but it
    allows for an existing destination directory.

    Recursively copy a directory tree using copy2().

    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    :param src: The source directory.
    :param dst: The destination directory.
    :param symlinks: Whether to follow symbolic links.
    :param ignore: A callable for items to ignore at a given level.
    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)

    errors = []
    for name in names:
        if name in ignored_names:
            continue
        src_name = os.path.join(src, name)
        dst_name = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(src_name):
                link_to = os.readlink(src_name)
                os.symlink(link_to, dst_name)
            elif os.path.isdir(src_name):
                copytree(src_name, dst_name, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy2(src_name, dst_name)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((src_name, dst_name, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        # can't copy file access times on Windows
        if why.winerror is None:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error(errors)


# CSV #

def read_csv_header(src_file):
    """Returns a list containing the values from the first row of the given CSV
    file or None if the file is empty.

    :param src_file: The CSV file to read.
    :return: The first row or None if empty.
    """
    with open(src_file) as csv_file:
        for row in csv.reader(csv_file):
            return list(row)


def convert_dict_line(all_conv, data_conv, line):
    s_dict = {}
    for s_key, s_val in line.items():
        if data_conv and s_key in data_conv:
            try:
                s_dict[s_key] = data_conv[s_key](s_val)
            except ValueError as e:
                logger.debug("Could not convert value "
                             "'%s' from column '%s': '%s'.  Leaving as str",
                             s_val, s_key, e)
                s_dict[s_key] = s_val
        elif all_conv:
            try:
                s_dict[s_key] = all_conv(s_val)
            except ValueError as e:
                logger.debug("Could not convert value "
                             "'%s' from column '%s': '%s'.  Leaving as str",
                             s_val, s_key, e)
                s_dict[s_key] = s_val
        else:
            s_dict[s_key] = s_val
    return s_dict


def read_csv(src_file, data_conv=None, all_conv=None):
    """
    Reads the given CSV (comma-separated with a first-line header row) and returns a list of
    dicts where each dict contains a row's data keyed by the header row.

    :param src_file: The CSV to read.
    :param data_conv: A map of header keys to conversion functions.  Note that values
        that throw a TypeError from an attempted conversion are left as strings in the result.
    :param all_conv: A function to apply to all values in the CSV.  A specified data_conv value
        takes precedence.
    :return: A list of dicts containing the file's data.
    """
    result = []
    with open(src_file) as csv_file:
        for line in csv.DictReader(csv_file):
            result.append(convert_dict_line(all_conv, data_conv, line))
    return result


def read_csv_to_dict(src_file, col_name, data_conv=None, all_conv=None):
    """
    Reads the given CSV (comma-separated with a first-line header row) and returns a
    dict of dicts indexed on the given col_name. Each dict contains a row's data keyed by the header row.

    :param src_file: The CSV to read.
    :param col_name: the name of the column to index on
    :param data_conv: A map of header keys to conversion functions.  Note that values
        that throw a TypeError from an attempted conversion are left as strings in the result.
    :param all_conv: A function to apply to all values in the CSV.  A specified data_conv value
        takes precedence.
    :return: A list of dicts containing the file's data.
    """
    result = {}
    with open(src_file) as csv_file:
        for line in csv.DictReader(csv_file):
            val = convert_dict_line(all_conv, data_conv, line)
            if col_name in val:
                col_val = val[col_name]
                if col_val in result:
                    warning("Duplicate values found for {}. Value for key will be overwritten.".format(col_val))
                result[col_val] = convert_dict_line(all_conv, data_conv, line)
            else:
                raise InvalidDataError("Could not find value for {} in file {} on line {}."
                                       "".format(col_name, src_file, line))
    return result


def write_csv(data, out_fname, fieldnames, extrasaction="raise", mode='w'):
    """
    Writes the given data to the given file location.

    :param data: The data to write (list of dicts).
    :param out_fname: The name of the file to write to.
    :param fieldnames: The sequence of field names to use for the header.
    :param extrasaction: What to do when there are extra keys.  Acceptable
        values are "raise" or "ignore".
    """
    with open(out_fname, mode) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, extrasaction=extrasaction)
        if mode == 'w':
            writer.writeheader()
        writer.writerows(data)


# Other input/output files

def save_fig(name, base_dir=None):
    pyPlt.savefig(base_dir + name, bbox_inches='tight')


def read_int_dict(d_file, one_to_one=True):
    """
    If an dictionary file is given, read it and return the dict[old]=new.
    Checks that all keys are unique.
    If one_to_one=True, checks that there 1:1 mapping of keys and values.
    @param d_file: the files with csv of old_id,new_id
    @return: int_dict
    """
    int_dict = {}
    # If d_file is None, return the empty dictionary, as no dictionary file was specified
    if d_file is not None:
        with open(d_file) as csv_file:
            reader = csv.reader(csv_file)
            key_count = 0
            for row in reader:
                if len(row) == 0:
                    continue
                if len(row) == 2:
                    int_dict[int(row[0])] = int(row[1])
                    key_count += 1
                else:
                    warning('Expected exactly two comma-separated values per row in file {}. '
                            'Skipping row containing: {}.'.format(d_file, row))
        if key_count == len(int_dict):
            if one_to_one:
                for key in int_dict:
                    if not (key in int_dict.values()):
                        raise InvalidDataError('Did not find a 1:1 mapping of key,val ids in {}'.format(d_file))
        else:
            raise InvalidDataError('A non-unique key value (first column) found in file: {}\n'.format(d_file))
    return int_dict


def list_to_file(list_to_print, fname, list_format=None, delimiter=' ', mode='w'):
    """
    Writes the list of sequences to the given file in the specified format for a PDB.

    @param list_to_print: A list of lines to print. The list may be a list of lists, list of strings, or a mixture.
    @param fname: The location of the file to write.
    @param list_format: Specified formatting for the line if the line is  list.
    @param delimiter: If no format is given and the list contains lists, the delimiter will join items in the list.
    @param mode: write by default; can be changed to allow appending to file.
    """
    with open(fname, mode) as w_file:
        for line in list_to_print:
            if isinstance(line, six.string_types):
                w_file.write(line + '\n')
            elif isinstance(line, collections.Iterable):
                if list_format is None:
                    w_file.write(delimiter.join(map(str, line)) + "\n")
                else:
                    w_file.write(list_format.format(*line) + '\n')


# Conversions #

def to_int_list(raw_val):
    return_vals = []
    for val in raw_val.split(','):
        return_vals.append(int(val.strip()))
    return return_vals


def str_to_bool(s):
    """
    Basic converter for Python boolean values written as a str.
    :param s: The value to convert.
    :return: The boolean value of the given string.
    :raises: ValueError if the string value cannot be converted.
    """
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError("Cannot covert {} to a bool".format(s))


def fmt_row_data(raw_data, fmt_str):
    """ Formats the values in the dicts in the given list of raw data using
    the given format string.

    :param raw_data: The list of dicts to format.
    :param fmt_str: The format string to use when formatting.
    :return: The formatted list of dicts.
    """
    fmt_rows = []
    for row in raw_data:
        fmt_row = {}
        for key, raw_val in row.items():
            fmt_row[key] = fmt_str.format(raw_val)
        fmt_rows.append(fmt_row)
    return fmt_rows


def conv_raw_val(param, def_val):
    """
    Converts the given parameter into the given type (default returns the raw value).  Returns the default value
    if the param is None.
    :param param: The value to convert.
    :param def_val: The value that determines the type to target.
    :return: The converted parameter value.
    """
    if param is None:
        return def_val
    if isinstance(def_val, bool):
        if param in ['T', 't', 'true', 'TRUE', 'True']:
            return True
        else:
            return False
    if isinstance(def_val, int):
        return int(param)
    if isinstance(def_val, long):
        return long(param)
    if isinstance(def_val, float):
        return float(param)
    if isinstance(def_val, list):
        return to_int_list(param)
    return param


def process_cfg(raw_cfg, def_cfg_vals=None, req_keys=None):
    """
    Converts the given raw configuration, filling in defaults and converting the specified value (if any) to the
    default value's type.
    :param raw_cfg: The configuration map.
    :return: The processed configuration.
    """
    proc_cfg = {}
    for key in raw_cfg:
        if not (key in def_cfg_vals or key in req_keys):
            raise InvalidDataError("Unexpected key '{}' in configuration ('ini') file.".format(key))
    key = None
    try:
        for key, def_val in def_cfg_vals.items():
            proc_cfg[key] = conv_raw_val(raw_cfg.get(key), def_val)
        for key, type_func in req_keys.items():
            proc_cfg[key] = type_func(raw_cfg[key])
    except KeyError as e:
        raise KeyError('Missing config val for key {}'.format(key, e))
    except Exception as e:
        raise InvalidDataError('Problem with config vals on key {}: {}'.format(key, e))

    return proc_cfg


# Comparisons #

def conv_num(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def diff_lines(floc1, floc2):
    """
    Determine all lines in a file are equal.
    If not, test if the line is a csv that has floats and the difference is due to machine precision.
    If not, return all lines with differences.
    @param floc1: file location 1
    @param floc2: file location 1
    @return: a list of the lines with differences
    """
    diff_lines_list = []
    diff_plus_lines = []
    diff_neg_lines = []
    close_enough = False
    with open(floc1) as file1:
        with open(floc2) as file2:
            diff = difflib.ndiff(file1.read().splitlines(), file2.read().splitlines())
    for line in diff:
        if line.startswith('-') or line.startswith('+'):
            diff_lines_list.append(line)
            # line may be space or comma-separated. First, remove difflib's two-charatcter code,
            #   then split on comma, then clean up white space (and split on white-space, just in case)
            #   then convert to number
            s_line = [conv_num(x.strip()) for x in line[2:].split(',')]
            if line.startswith('-'):
                diff_plus_lines.append(s_line)
            elif line.startswith('+'):
                diff_neg_lines.append(s_line)

    if len(diff_plus_lines) == len(diff_neg_lines):
        # if the same number of lines, there is a chance that the difference is only due to difference in
        # floating point precision. Check each value of the line, split on whitespace or comma
        close_enough = True
        for line_plus, line_neg in zip(diff_plus_lines, diff_neg_lines):
            for item_plus, item_neg in zip(line_plus, line_neg):
                if isinstance(item_plus, float) and isinstance(item_neg, float):
                    if abs(item_plus - item_plus) < TOL:
                        close_enough = close_enough and True
                else:
                    if item_plus != item_neg:
                        close_enough = False

    if not close_enough:
        return diff_lines_list
    else:
        return []


# Data Structures #

def unique_list(a_list):
    """ Creates an ordered list from a list of tuples or other hashable items.
    From https://code.activestate.com/recipes/576694/#c6
    """
    m_map = {}
    o_set = []
    for item in a_list:
        if item not in m_map:
            m_map[item] = 1
            o_set.append(item)
    return o_set


# Processing LAMMPS files #

def find_dump_section_state(line, sec_timestep=SEC_TIMESTEP, sec_num_atoms=SEC_NUM_ATOMS, sec_box_size=SEC_BOX_SIZE,
                            sec_atoms=SEC_ATOMS):
    atoms_pat = re.compile(r"^ITEM: ATOMS id mol type q x y z.*")
    if line == 'ITEM: TIMESTEP':
        return sec_timestep
    elif line == 'ITEM: NUMBER OF ATOMS':
        return sec_num_atoms
    elif line == 'ITEM: BOX BOUNDS pp pp pp':
        return sec_box_size
    elif atoms_pat.match(line):
        return sec_atoms

