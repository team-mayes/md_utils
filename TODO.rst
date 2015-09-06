WHAM_BLOCK
==========

1. Have a bash script that creates a folder with input to WHAM
** Two-column space-separated text files
2. Creates a file that's an input to WHAM
3. Run WHAM

To get an error estimate, take a series of data points (each file is a series of data points)

TODO
----

Make a new set of files to send to WHAM.
* Average pairs of numbers in the second column (last odd is thrown out)
** Repeat pair average n cycles (user-definable) each in a separate file
** Create folders and meta file with the two-digit number
** Use template to create an aggregated submit script
* Replace first column with a new sequence
* New input file for WHAM

Submit Script
-------------

wham 1.00 6.00 50 0.0001 310.0 0 meta.$i PMF.$i > wham.$i.txt
