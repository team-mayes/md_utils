============
MD Utilities
============

.. image:: https://img.shields.io/travis/team-mayes/md_utils.svg
        :target: https://travis-ci.org/team-mayes/md_utils

.. image:: https://img.shields.io/pypi/v/md_utils.svg
        :target: https://pypi.python.org/pypi/md_utils

.. image:: https://codecov.io/gh/team-mayes/md_utils/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/team-mayes/md_utils/branch/master

Utility scripts for MD data

* Free software: BSD license
* Documentation: https://md_utils.readthedocs.org.


Package organization
--------------------

This packaging process is based on https://jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/

Scripts added to the package aim have at least 90% test coverage.


Installation
------------

1. Make sure python is installed. Python 2.7 is recommended. The package is meant to be python 3 compatible,
   but primarily tested with Python 2.7. There are many ways to install python.
   For example, see http://conda.pydata.org/miniconda.html

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
--------------------------------

align_on_col
  For combining data from multiple files based on a common column name, such as "timestep". If a timestep (or other
  specified column value) does not appear in all files, it will be ignored. Options demonstrated in the test files
  include aligning multiple sets of files to produce one output file that notes the "run" name (set of aligned files;
  either a common part of the name of the aligned files or a the set number).

fes_combo
  Combines multiple FES output files into a single file so that the first
  column's value is sequential.  Files with higher starting index numbers
  are favored.

filter_col
  Produces a file in which only rows are reproduced that pass filtering criteria set in the configuration file. The
  config file allows specifying max and/or min values for any column heading (with a "max_vals" and/or "max_vals"
  section in the config file). Additionally, a "bin_settings" section
  allows the user to specify a column name on which to bin data. The user should provide a list of integers:
  initial_bin_value, final_bin_value, num_bins, and (optionally) a max number of rows per bin.

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
---------------------

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
-----------------------------

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

lammps_proc
  From lammps dump file(s), finds key distance, such as the hydroxyl OH distance on the protonatable residue
  (when protonated). This script assumes we care about one protonatable residue in a simulation with a PBC.
  The options include:
  * calc_hydroxyl_props_flag: calculate distance between the closest transferable proton to each of the protonatable residue oxygen atoms.
  * calc_hij_da_gauss_flag: prints the calculated h_ij per Nelson et al. 2014 (http://pubs.acs.org/doi/abs/10.1021/ct500250f)
    equation 7.
  * calc_hij_arg_flag: prints the calculated h_ij per Maupin et al. 2006 (http://pubs.acs.org/doi/pdf/10.1021/jp053596r) equations 4-8.

pdb_edit
  Creates a new version of a pdb file applying options such as renumbering molecules.
  * use the option "add_element_types = true" to fill in the column of element types (VMD dropped them for the protein section; CP2K wants them)
      * by default, it will check all atoms. You can specify a range on which to perform this action with
        'first_atom_add_element' and 'last_atom_add_element'
      * it will only add the element type if it is in the internal atom_type/element dictionary (a warning will show if
        a type is not in the dictionary). Otherwise, it will leave those columns as they originally were.
      * by default, it loads a dictionary I made based on charmm atom types (charmm_atom_type,element; one per line).
        The user can specify a different dictionary file with "atom_type_element_dict_file"
  * if the user specifies a 'first_wat_atom' and 'last_wat_atom', the program will check that the atoms are printed in the order OH2, H1, H2
      * when using this option, if the first protein atom is not 1 (numbering begins at 1, like in a PDB, not 0, like
        VMD index), use the option "last_prot_atom = " to indicate the first protein atom num
      * this options requires inputting the last protein atom id (add "last_prot_atom = X" to the configuration file,
        where X is the integer (decimal) atom number)
  * by default, the output pdb name of a pdb file called 'struct.pdb' will be 'struct_new.pdb'. You can specify a new
    name with the keyword 'new_pdb_name'
  * by default, the output directory will be the same as that for the input pdb. This can be changed with the 'output_directory' keyword
  * the program will renumber atoms starting from 1 (using hex for atom numbers greater than 99999), using a dictionary
    to change order if a csv dictionary of "old,new" indexes is specified with 'atom_reorder_old_new_file'
  * the program will renumber molecules starting from 1 if 'mol_renum_flag = True' is included in the configuration file.
    Molecules may also be renumbered with by specifying a csv dictionary of "old,new" indexes with 'mol_renum_old_new_file'

psf_edit
  Currently only has limited functionality:
  * Can be used to renumber residues/molecules starting from 1 using "mol_renum_flag = True" (no reordering of atoms)
  * can map old molecule numbers to new ones by specifying a mapping dictionary with "mol_renum_old_new_file" (no reordering of atoms)
  * Mapping of old atom numbers to new ones is not fully implemented.
  * there is no option to reorder the psf
  * the current most useful part of psf_edit is to help prepare files for CP2K, by specifying residue IDs that will be
    included in a qm region, i.e. "resids_qmmm_ca_cb_link = 1,5"
    * note: to do so, it uses a default dictionary that can map between CHARMM atom types and elements, and between
      CHARMM atom types and MM_KIND radii (radii for water and hydronium from http://pubs.acs.org/doi/abs/10.1021/ct6001169;
      all other radii from http://xlink.rsc.org/?DOI=b801115j). If a mapping is needed that is not in the default dictionaries,
      the program will print a warning and exit. Users may supply their own dictionaries with the
      "atom_type_element_dict_file" and "atom_type_radius_dict_file"
    * it assumes that all residues will be broken between the CA and CB atoms (if they exist), with all backbone atoms
      outside the QM region (types [CA, C, O, NT, HNT, CAT, HT1, HT2, HT3, HA, CAY, HY1, HY2, HY3, CY, OY, N, HN]);
      a different exclude list can be specified with 'exclude_atom_types_from_QM'
    * it will output an "amino_id.dat" file that lists the atom ids (numbering from 1) for each element in the QM
      region from the non-excluded residue/molecule atoms. It will also print a link section noting the break between
      the CA and CB atoms, and capping with H
    * it will output an "mm_kinds.dat" file that notes the radius for each atom type found in the psf
      (see above to specify the dictionary to use)
    * it will print a "vmd_protein_atoms.dat" file that lists the indices (atom_num - 1) of each atom in the QM region
      (useful for a VMD script that is part of converting RAPTOR output to VMD input)


For RAPTOR or EVBFit/RMDFit:
----------------------------

convert_cp2k_forces
  cp2k force output files

evb_get_info
  collects selected data form evb output files such as the number of states, the maximum ci^2 value for a protonated
  state, and the max ci^2 value for a deprotonated state

fitevb_setup
  provided a allowable ranges of parameters and results of a previous fitting step, creates a new fitevb input file

process_cv_file
  converts plumed cv output to evb cv output style

