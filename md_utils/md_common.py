# coding=utf-8

"""
Common methods for this project.
"""

from __future__ import print_function, division
# Util Methods #
import argparse
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
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_md_utils')

# Constants #

BACKUP_TS_FMT = "_%Y-%m-%d_%H-%M-%S_%f"

# Boltzmann's Constant in kcal/mol Kelvin
BOLTZ_CONST = 0.0019872041

# Sections for reading files
SEC_TIMESTEP = 'timestep'
SEC_NUM_ATOMS = 'dump_num_atoms'
SEC_BOX_SIZE = 'dump_box_size'
SEC_ATOMS = 'atoms_section'

# Exceptions #

class MdError(Exception): pass


class InvalidDataError(MdError): pass


class NotFoundError(MdError): pass


class ArgumentParserError(Exception): pass

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


def diff_lines(floc1, floc2):
    difflines = []
    with open(floc1, 'r') as file1:
        with open(floc2, 'r') as file2:
            diff = difflib.ndiff(file1.read().splitlines(), file2.read().splitlines())
            for line in diff:
                if line.startswith('-'):
                    logger.debug(line)
                    difflines.append(line)
                elif line.startswith('+'):
                    logger.debug(line)
                    pass
    return difflines

# Calculations #


def calc_kbt(temp_k):
    """
    Returns the given temperature in Kelvin multiplied by Boltzmann's Constant.

    :param temp_k: A temperature in Kelvin.
    :return: The given temperature in Kelvin multiplied by Boltzmann's Constant.
    """
    return BOLTZ_CONST * temp_k


def xyz_distance(fir, sec):
    """
    Calculates the Euclidean distance between the two given
    coordinates (expected format is numbers as [x,y,z]).

    TODO: Consider adding numpy optimization if lib is present.

    :param fir: The first XYZ coordinate.
    :type name: list.
    :param sec: The second XYZ coordinate.
    :type state: list.
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


# def dotproduct(v1, v2):
#   return sum((a*b) for a, b in zip(v1, v2))
#
# def length(v):
#   return math.sqrt(dotproduct(v, v))
#
# def angle(v1, v2):
#   return math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))

def pbc_angle(p0, p1, p2, box):
    pass

def pbc_dihedral(p0, p1, p2, p3, box):
    """
    From http://stackoverflow.com/questions/20305272/dihedral-torsion-angle-from-four-points-in-cartesian-coordinates-in-python
    khouli formula
    1 sqrt, 1 cross product
    @param p0: xyz coordinates of point 0, etc.
    @param p1:
    @param p2:
    @param p3:
    @param box: periodic box lengths
    @return: dihedral angle in degrees
    """
    b0 = -1.0*(pbc_vector_diff(p1, p0, box))
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
    v = b0 - np.dot(b0, b1)*b1
    w = b2 - np.dot(b2, b1)*b1

    # angle between v and w in a plane is the torsion angle
    # v and w may not be normalized but that's fine since tan is y/x
    x = np.dot(v, w)
    y = np.dot(np.cross(b1, v), w)
    return np.degrees(np.arctan2(y, x))


# Other #


def swarn(*objs):
    """Writes a warning message to a target (stderr by default).
    :param objs: The elements of the message to write.
    """
    print("WARNING:", *objs, file=sys.stderr)


def swerr(*objs):
    """Writes an error message to a target (stderr by default).
    :param objs: The elements of the message to write.
    """
    print("ERROR:", *objs, file=sys.stderr)


def chunk(seq, chunksize, process=iter):
    """Yields items from an iterator in iterable chunks.
    From https://gist.github.com/ksamuel/1275417

    :param seq: The sequence to chunk.
    :param chunksize: The size of the returned chunks.
    :param process: The function to use for creating the iterator.  Useful for iterating over different
    data structures.
    :return: Chunks of the given size from the given sequence.
    """
    it = iter(seq)
    while True:
        yield process(chain([six.next(it)], islice(it, chunksize - 1)))


# I/O #

def cmakedir(tgt_dir):
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
    with open(fname) as myfile:
        return myfile.read()


def str_to_file(str_val, fname, mode='w'):
    """
    Writes the string to the given file.

    :param str_val: The string to write.
    :param fname: The location of the file to write.
    """
    with open(fname, mode) as myfile:
        myfile.write(str_val)


def list_to_file(list_val, fname, mode='w'):
    """
    Writes the list to the given file.

    :param list_val: The list to write.
    :param fname: The location of the file to write.
    """
    with open(fname, mode) as myfile:
        for line in list_val:
            myfile.write(line + "\n")


def seq_list_to_file(list_val, fname, mode='w', header=None, delimiter=','):
    """
    Writes the list of sequences to the given file.

    :param list_val: The list of sequences to write.
    :param fname: The location of the file to write.
    """
    with open(fname, mode) as myfile:
        if header:
            myfile.write(delimiter.join(header) + "\n")
        for line in list_val:
            myfile.write(delimiter.join(map(str,line)) + "\n")


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
def allow_write(floc, overwrite=False):
    """
    Returns whether to allow writing to the given location.

    :param floc: The location to check.
    :param overwrite: Whether to allow overwriting an exisiting location.
    :return: Whether to allow writing to the given location.
    """
    if os.path.exists(floc) and not overwrite:
        logger.warn("Not overwriting existing location '%s'", floc)
        return False
    return True


def move_existing_file(floc):
    """
    Renames an existing file using a timestamp based on the move time.

    :param floc: The location to check.
    """
    if os.path.exists(floc):
        shutil.move(floc, create_backup_filename(floc))


def create_prefix_out_fname(src_file, prefix, base_dir=None, ext=None):
    """Creates an outfile name for the given source file.

    :param src_file: The file to process.
    :param prefix: The file prefix to prepend.
    :param base_dir: The base directory to use; defaults to `src_file`'s directory.
    :param ext: The extension to use instead of the source file's extension;
        defaults to the `sec_file`'s extension.
    :return: The output file name.
    """
    if base_dir is None:
        base_dir = os.path.dirname(src_file)

    if ext is None:
        tgt_file = src_file
    else:
        tgt_file = os.path.splitext(src_file)[0] + ext

    return os.path.abspath(
        os.path.join(base_dir, prefix + os.path.basename(tgt_file)))


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

    base_name = os.path.splitext(src_file)[0]

    if ext is None:
        ext = os.path.splitext(src_file)[1]

    return os.path.abspath(os.path.join(base_dir, prefix + base_name + suffix + ext ))


def find_files_by_dir(tgt_dir, pat):
    """Recursively searches the target directory tree for files matching the given pattern.
    The results are returned as a dict with a list of found files keyed by the absolute
    directory name.
    :param tgt_dir: The target base directory.
    :param pat: The file pattern to search for.
    :return: A dict where absolute directory names are keys for lists of found file names
        that match the given pattern.
    """
    matchdirs = {}
    for root, dirs, files in os.walk(tgt_dir):
        matches = [match for match in files if fnmatch.fnmatch(match, pat)]
        if matches:
            matchdirs[os.path.abspath(root)] = matches
    return matchdirs


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
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
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
    with open(src_file) as csvfile:
        for row in csv.reader(csvfile):
            return list(row)


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
    with open(src_file) as csvfile:
        for sline in csv.DictReader(csvfile):
            sdict = {}
            for skey, sval in sline.items():
                if data_conv and skey in data_conv:
                    try:
                        sdict[skey] = data_conv[skey](sval)
                    except ValueError as e:
                        logger.debug("Could not convert value "
                                     "'%s' from column '%s': '%s'.  Leaving as str",
                                     sval, skey, e)
                        sdict[skey] = sval
                elif all_conv:
                    try:
                        sdict[skey] = all_conv(sval)
                    except ValueError as e:
                        logger.debug("Could not convert value "
                                     "'%s' from column '%s': '%s'.  Leaving as str",
                                     sval, skey, e)
                        sdict[skey] = sval
                else:
                    sdict[skey] = sval
            result.append(sdict)
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
    with open(out_fname, mode) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames, extrasaction=extrasaction)
        if mode == 'w':
            writer.writeheader()
        writer.writerows(data)


# Other input/output files

def save_fig(name, base_dir=None):
    plt.savefig(base_dir + name, bbox_inches='tight')


def read_int_dict(d_file):
    """
    If an dictionary file is given, read it and return the dict[old]=new.
    Checks that there 1:1 mapping of keys and values and that all keys are unique.
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
                    key_count +=1
                else:
                    warning('Expected exactly two comma-separated values per row in file {}. '
                            'Skipping row containing: {}.'.format(d_file, row))
        if key_count == len(int_dict):
            for key in int_dict:
                if not (key in int_dict.values()):
                    raise InvalidDataError('Did not find a 1:1 mapping of old,new atom ids in {}'.format(d_file))
        else:
            raise InvalidDataError('An old atom id appeared more than once in the file: {}\n'.format(d_file))
    return int_dict


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
    try:
        for key, def_val in def_cfg_vals.items():
            proc_cfg[key] = conv_raw_val(raw_cfg.get(key), def_val)
    except Exception as e:
        logger.error('Problem with default config vals on key %s: %s', key, e)
    for key, type_func in req_keys.items():
        proc_cfg[key] = type_func(raw_cfg[key])

    return proc_cfg


def to_int_list(raw_val):
    return_vals = []
    for val in raw_val.split(','):
        return_vals.append(int(val.strip()))
    return return_vals


# Comparisons #

def diff_lines(floc1, floc2):
    difflines = []
    with open(floc1) as file1:
        with open(floc2) as file2:
            diff = difflib.ndiff(file1.read().splitlines(), file2.read().splitlines())
            for line in diff:
                if line.startswith('-'):
                    logger.debug(line)
                    difflines.append(line)
                elif line.startswith('+'):
                    logger.debug(line)
                    pass
    return difflines


# Data Structures #

def unique_list(alist):
    """ Creates an ordered list from a list of tuples or other hashable items.
    From https://code.activestate.com/recipes/576694/#c6
    """
    mmap = {}
    oset = []
    for item in alist:
        if item not in mmap:
            mmap[item] = 1
            oset.append(item)
    return oset


# Processing LAMMPS files #

def find_dump_section_state(line, sec_timestep=SEC_TIMESTEP, sec_num_atoms=SEC_NUM_ATOMS, sec_box_size=SEC_BOX_SIZE, sec_atoms=SEC_ATOMS):
    atoms_pat = re.compile(r"^ITEM: ATOMS id mol type q x y z.*")
    if line == 'ITEM: TIMESTEP':
        return sec_timestep
    elif line == 'ITEM: NUMBER OF ATOMS':
        return sec_num_atoms
    elif line == 'ITEM: BOX BOUNDS pp pp pp':
        return sec_box_size
    elif atoms_pat.match(line):
        return sec_atoms

