WHAM_BLOCK
==========

1. Have a bash script that creates a folder with input to WHAM
** Two-column space-separated text files
2. Creates a file that's an input to WHAM
3. Run WHAM

To get an error estimate, take a series of data points (each file is a series of data points)


WHAM_POST_BLOCK
===============

* Read all parts for a given dir prefix
* WHAM output file format (PMF*)
** Also accept radial correction rad_PMF
* To calculate the average and standard deviation
** read the (radial corrected) free energy for a given coordinate from each rad_PMF file for a given coordinate prefix
** output the coordiante, the average, and standard deviation (i.e. for directory 07_*, there are 8 files; the
coordinates will align for each file; read the 8 differing values for free E for that coordinate, calc the avg and st dev, and output

Out format CSV with headers:

coordinates average_free_energy standard_deviation_free_energy

File name

avg_rad_PMF.02.csv

EVBDUMP2PDB
========

* Creates lammps data files from lammps dump files, given a template lammps data file
* This cannot be done in the available programs (such as lammps2pdb) because we need to adjust for changes
  made by RAPTOR (to which molecule hosts the excess proton)

* The data file will provide some lines that are copied directly (everything above and below the "Atoms" section)
** The data file should correspond to the deprotonated state
** It is expected that all the water (and hydronium) are in a continuous section, with the oxygen atoms always
   preceding the hydrogen atoms

* The "Atoms" section of the template will be updated with coordinates from the dump file, which will be
  updated as follows:
** The x, y, z coordinates will be wrapped to be in the main box
** The protonateable residue may be protonated or not; if it is, we will converted it to the deprotonated state
   by reassigning the proton to the nearest water molecule and converting that water molecule to a hydronium
** We always want the same molecule id for the hydronium. Swap the molecule ID as needed.

* Current information hard-coded into rewritedata.cpp:
** The molecule type for water oxygen, water hydrogen, hydronium hydrogen, and hydronium oxygen
** The molecule ID for the hydronium
** The first and last atom ID for the water/hydronium section
** A specific format for the dump files

* Input into new program:
** Name of the template file
** File with list of dump file names
** The molecule type for water oxygen, water hydrogen, hydronium hydrogen, and hydronium oxygen



Questions
---------

* Did we intend to leave rad file as .txt as opposed to .csv?
