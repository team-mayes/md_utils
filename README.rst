============
MD Utilities
============

.. image:: https://img.shields.io/travis/cmayes/md_utils.svg
        :target: https://travis-ci.org/cmayes/md_utils

.. image:: https://img.shields.io/pypi/v/md_utils.svg
        :target: https://pypi.python.org/pypi/md_utils

.. image:: https://coveralls.io/repos/cmayes/md_utils/badge.svg?branch=master&service=github
        :target: https://coveralls.io/github/cmayes/md_utils?branch=master

Utility scripts for MD data

* Free software: BSD license
* Documentation: https://md_utils.readthedocs.org.


Package organization
--------------------

This packaging process is based on https://jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/

Scripts added to the package aim have at least 90% test coverage.


Installation instructions
-------

1. Clone the git repository or update to the latest version (git pull)
2. From the fit repository folder, run ''python setup.py sdist"
3. Run "pip install dist/md_utils-XXX.tar.gz --user" or 
"pip install --upgrade dist/md_utils-XXX.tar.gz --user", where XXX is the current 
version (the *.tar.gz that you created in the previous step)
(see https://pip.pypa.io/en/stable/installing/ if you don't have pip installed)
4. To allow the scripts to be found anywhere on your computer using your terminal screen,
making sure the following path is in your .bashrc or .bash_profile paths: $HOME/.local/bin


Example use:

Update a configuration file like one found in the folder
https://github.com/team-mayes/md_utils/tree/master/tests/test_data/data_edit
(FYI, config files end with "ini" and there are a variety here, meant
to work or fail, to test functionality).

To see if it works, try running with the help option. All scripts in this package
have such an option, which will briefly tell you about the code:
"data_edit -h"

To only have the program print interactions "owned" by atom numbers 1
and 2 in a data file called "my_file.data", make a file called (for example) 
"print_owned_atoms.ini", with
the following text:
    [main]
    data_file = my_file.data
    print_interactions_owned_by_atoms = 1,2

This assumes that my_file.data is in the same file as the
configuration file. You can have as many atom numbers as you wish;
just separate them by commas.

Now, run:
'data_edit -c print_owned_atoms.ini"


Scripts for combining/processing output:
-------

align_on_col
  For combining data from multiple files based on a common timestep. All other data will be ignored or, if in logging
  mode, printed to a log file.

fes_combo
  Combines multiple FES output files into a single file so that the first
  column's value is sequential.  Files with higher starting index numbers
  are favored.

filter_col_data
  Produces a file in which only rows are reproduced that pass filtering criteria set in the configuration file. The
  config file allows specifying max and/or min values for any column heading

path_bin
  Creates a summary VMD XYZ file (and separate log file) that averages a
  set of coordinates (one set of XYZ coordinates per line) from an input file.

pdb_edit
  Creates a new version of a pdb file applying options such as renumbering molecules.

per_col_stats
  Given a file with columns of data, returns the min, max, avg, and std dev per column. Optionally, it can return
  the maximum value from each column plus a "buffer" length (useful for preparing CP2K input for FitEVB).

press_dups
  Compresses lines in a given CSV based on duplicate values in a specified
  column (RMSD by default)  Compressed lines have their values averaged.


Scripts for PMF calculations:
-------

md_init
  Initializes a location for running md utilities. Specifically, it makes template files for creating wham input.

wham_split
  Breaks wham input into increasingly smaller blocks (divide initial data set
  by 2, then 3, 4...) and creates wham input (meta) files and submit scripts.

wham_rad
  Calculates the radially-corrected free energy values from WHAM output.

calc_pka
  From the wham_rad output, calculates the pKa.


Scripts for Processing LAMMPS output:
-------

data_edit
  offers a range of options to: 
  * produce a new, edited data file (such as renumbering interactions types)
    ** see example scripts in tests/test_data/data_edit: data_reorder.ini, data_retype.ini, data_sort.ini
  * output selected data (i.e. interactions involving or owned by a particular atom number)
    ** see example scripts in tests/test_data/data_edit: data_print_impt_atoms.ini, data_print_own_atoms.ini
  * compare two data files and output only "meaningful" differences (ignore formatting differences, order of bonds, angles, dihedrals, atom XYZ coords, notes...)
    ** see example script tests/test_data/data_edit/data_compare.ini

dump_edit
  available options include renumbering atoms or molecules and producing a new file with a subset of timesteps

lammps_dist
  Calculates the distances between a given set of atom pairs for each
  time step in a given LAMMPS dump file

lammps_proc_data
  From lammps dump file(s), finds key distance, such as the hydroxyl OH distance on the protonatable residue
  (when protonated). This script assumes we care about one protonatable residue in a simulation with a PBC.


Scripts for RAPTOR or EVBFit/RMDFit:
-------

convert_cp2k_forces
  cp2k force output files

evb_get_info
  collects selected data form evb output files such as the number of states, the maximum ci^2 value for a protonated
  state, and the max ci^2 value for a deprotonated state

fitevb_setup
  provided a allowable ranges of parameters and results of a previous fitting step, creates a new fitevb input file

process_cv_file
  converts plumed cv output to evb cv output style

