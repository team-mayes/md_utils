# coding=utf-8
import os
from collections import OrderedDict

from md_utils.md_common import InvalidDataError, warning

# Constants #

MISSING_ATOMS_MSG = "Could not find lines for atoms ({}) in timestep {} in file: {}"
TSTEP_LINE = 'ITEM: TIMESTEP'
ATOMS_LINE = 'ITEM: ATOMS'


# Logic #

def find_atom_data(lammps_f, atom_ids):
    """Searches and returns the given file location for atom data for the given IDs.

    :param lammps_f: The LAMMPS data file to search.
    :param atom_ids: The set of atom IDs to collect.
    :return: A nested dict of the atoms found keyed first by time step, then by atom ID.
    :raises: InvalidDataError If the file is missing atom data or is otherwise malformed.
    """
    tstep_atoms = OrderedDict()
    atom_count = len(atom_ids)

    with open(lammps_f) as lfh:
        file_name = os.path.basename(lammps_f)
        tstep_id = None
        tstep_val = "(no value)"
        for line in lfh:
            if line.startswith(TSTEP_LINE):
                try:
                    tstep_val = next(lfh).strip()
                    tstep_id = int(tstep_val)
                # Todo: remove if never used
                except ValueError as e:
                    raise InvalidDataError(
                        "Invalid timestep value {}: {}".format(tstep_val, e))
            elif tstep_id is not None:
                atom_lines = find_atom_lines(lfh, atom_ids, tstep_id, file_name)
                if len(atom_lines) != atom_count:
                    try:
                        missing_atoms_err(atom_ids, atom_lines, tstep_id, file_name)
                    except InvalidDataError as e:
                        warning(e)
                        warning("Skipping timestep and continuing.")
                else:
                    tstep_atoms[tstep_id] = atom_lines
                    tstep_id = None
    return tstep_atoms


def find_atom_lines(lfh, atom_ids, tstep_id, file_name):
    """Collects the atom data for the given IDs, returning a dict keyed by atom
    ID with the atom value formatted as a six-element list containing:

    * Molecule ID (int)
    * Atom type (int)
    * Charge (float)
    * X (float)
    * Y (float)
    * Z (float)

    :param lfh: A file handle for a LAMMPS file.
    :param atom_ids: The set of atom IDs to collect.
    :param tstep_id: The ID for the current time step.
    :param file_name: the file name (basename) for the lammps file (for error printing)
    :return: A dict of atom lines keyed by atom ID (int).
    :raises: InvalidDataError If the time step section is missing atom data or
        is otherwise malformed.
    """
    found_atoms = {}
    atom_count = len(atom_ids)
    for line in lfh:
        if line.startswith(ATOMS_LINE):
            for aline in lfh:
                s_line = aline.split()
                if len(s_line) == 7 and int(s_line[0]) in atom_ids:
                    # noinspection PyTypeChecker
                    p_line = list(map(int, s_line[:3])) + list(map(float, s_line[-4:]))
                    found_atoms[p_line[0]] = p_line[1:]
                    if len(found_atoms) == atom_count:
                        return found_atoms
                elif aline.startswith(TSTEP_LINE):
                    missing_atoms_err(atom_ids, found_atoms, tstep_id, file_name)
    return found_atoms

# Exception Creators #


def missing_atoms_err(atom_ids, found_atoms, tstep_id, file_name):
    """Creates and raises an exception when the function is unable to find atom
    data for all of the requested IDs.

    :param atom_ids: The atoms that were requested.
    :param found_atoms: The collection of atoms found.
    :param tstep_id: The time step ID where the atom data was missing.
    :param file_name: the file name with the time step ID where atom was missing.
    :raises: InvalidDataError Describing the missing atom data.
    """
    missing = map(str, atom_ids.difference(found_atoms.keys()))
    raise InvalidDataError(MISSING_ATOMS_MSG.format(",".join(missing),
                                                    tstep_id, file_name))
