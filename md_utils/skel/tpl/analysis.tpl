#!/bin/bash
#PBS -N resubmit
#PBS -l walltime=30:00
#PBS -l nodes=1:ppn=1,pmem=1g
#PBS -A hbmayes_fluxod
#PBS -q fluxod
#PBS -V
#PBS -j oe
#PBS -m e
set -u
set -e
cd ~
files=
basename=

for file in ${files[@]}
do
    namd_scripts -p -f ${file}.log
done
python -c "from md_utils import scaling; scaling.plot_scaling('$files','$basename')"
