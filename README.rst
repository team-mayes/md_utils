= ===========
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


Installation
-------

1. Make sure python is installed. Python 2.7 is recommended. The package is meant to be python 3 compatible, 
   but expentensively tested only on Python 2.7. There are many ways to install it. For example, see http://conda.pydata.org/miniconda.html
2. From the base folder where you would like the set of files (a new folder will be created, by default called md_utils):
   ::
      git clone https://github.com/team-mayes/md_utils.git
3. From the git repository folder

   a. see https://pip.pypa.io/en/stable/installing/ to install if you don't have pip installed
   b. run:
      ::
         pip install md_utils --user 
   c. alternately (the * below will change based on current version; this is created in the first step):
      ::
         python setup.py sdist
         pip install dist/md_utils-*.tar.gz --user  
4. To allow the scripts to be found anywhere on your computer using your terminal screen, 
   making sure the following path is in your .bashrc or .bash_profile path, and remember to source that file 
   after an update:
   ::
      $HOME/.local/bin

Upgrade
-------

From the location of your cloned git repository, make sure you have the latest files, then use pip to update:
::
   git pull
   pip install --upgrade  md_utils --user 

Example
-------

1. Update a configuration file like one found in the folder 
   https://github.com/team-mayes/md_utils/tree/master/tests/test_data/data_edit
   (FYI, config files end with "ini" and there are a variety here, meant
   to work or fail, to test functionality).
2. To see if the installation worked, try running with the help option. All scripts in 
   this package have such an option, which will briefly tell you about the code::
       data_edit -h

3. To only have the program print interactions "owned" by atom numbers 1
   and 2 in a data file called "my_file.data", make a file called (for example) 
   "print_owned_atoms.ini", with
   the following text::
       [main]
       data_file = my_file.data
       print_interactions_owned_by_atoms = 1,2
   
   This assumes that my_file.data is in the same file as the
   configuration file. You can have as many atom numbers as you wish;
   just separate them by commas.

4. Give it a try!
   Run::
       data_edit -c print_owned_atoms.ini


When the whole git repository is cloned, there will many example input files in the tests/test_data folder.


-------
Scripts
-------

For combining/processing output:
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

per_col_stats
  Given a file with columns of data, returns the min, max, avg, and std dev per column. Optionally, it can return
  the maximum value from each column plus a "buffer" length (useful for preparing CP2K input for FitEVB).

press_dups
  Compresses lines in a given CSV based on duplicate values in a specified
  column (RMSD by default)  Compressed lines have their values averaged.


For PMF calculations:
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


For processing LAMMPS output:
-------

data_edit
  offers a range of options to: 
  
  * produce a new, edited data file (such as renumbering interactions types)

      see example scripts in tests/test_data/data_edit: data_reorder.ini, data_retype.ini, data_sort.ini

  * output selected data (i.e. interactions involving or owned by a particular atom number)

      see example scripts in tests/test_data/data_edit: data_print_impt_atoms.ini, data_print_own_atoms.ini

  * compare two data files and output only "meaningful" differences (ignore formatting differences, 
    order of bonds, angles, dihedrals, atom XYZ coords, notes...)

      see example script tests/test_data/data_edit/data_compare.ini

data2pdb
  * produces a pdb file with the coordinates from a data file, and everything else as in the pdb file

      see example scripts in tests/test_data/data2odb: data2pdb.ini, data2pdb_glu_dict.ini ...

  * specify a pdb template file with 'pdb_tpl_file'
  * specify a single data file with 'data_file'
  * specify a file that lists any number of data file names with 'data_list_file'
  * specify an output directory with 'output_directory'
  * make a dictionary by lining up the rows of the data and pdb files with 'make_dictionary_flag = True'
  * use a dictionary to check alignment (proper ordering) of data file with 'use_atom_dict_flag = True'

dump_edit
  available options include renumbering atoms or molecules and producing a new file with a subset of timesteps

lammps_dist
  Calculates the distances between a given set of atom pairs for each
  time step in a given LAMMPS dump file

lammps_proc_data
  From lammps dump file(s), finds key distance, such as the hydroxyl OH distance on the protonatable residue
  (when protonated). This script assumes we care about one protonatable residue in a simulation with a PBC.

pdb_edit
  Creates a new version of a pdb file applying options such as renumbering molecules.
  * use the option "add_element_types = true" to fill in the column of element types (VMD dropped them for the protein section; CP2K wants them)
      * by default, it will check all atoms. You can specify a range on which to perform this action with 'first_atom_add_element' and 'last_atom_add_element'
      * it will only add the element type if it is in the internal atom_type/element dictionary (a warning will show if a type is not in the dictionary). Otherwise, it will leave those columns as they originally were.
  * if the user specifies a 'first_wat_atom' and 'last_wat_atom', the program will check that the atoms are printed in the order OH2, H1, H2
      * when using this option, if the first protein atom is not 1 (numbering begins at 1, like in a PDB, not 0, like VMD index), use the option "last_prot_atom = " to indicate the first protein atom num
      * this options requires inputing the last protein atom id (add "last_prot_atom = X" to the configuration file, where X is the integer (decimal) atom number)
  * by default, the output pdb name of a pdb file called 'struct.pdb' will be 'struct_new.pdb'. You can specify a new name with the keyword 'new_pdb_name'
  * by default, the output directory will be the same as that for the input pdb. This can be changed with the 'output_directory' keyword
  * the program will renumber atoms starting from 1 (using hex for atom numbers greater than 99999), using a dictionary to change order if a csv dictionary of "old,new" indexes is specified with 'atom_reorder_old_new_file'
  * the program will renumber molecules starting from 1 if 'mol_renum_flag = True' is included in the configuration file. Molecules may also be renumbered with by specifying a csv dictionary of "old,new" indexes with 'mol_renum_old_new_file'


For RAPTOR or EVBFit/RMDFit:
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

