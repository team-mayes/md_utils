#!/bin/bash
#SBATCH --constraint=ib
#SBATCH --job-name=wham
#SBATCH --output=wham.out
#SBATCH --error=wham.err
#SBATCH --time=04:00:00
#SBATCH --partition=westmere
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16
#SBATCH --exclusive
#SBATCH --mail-type=ALL
#SBATCH --mail-user=hmayes@hmayes.com

{wham_block}
