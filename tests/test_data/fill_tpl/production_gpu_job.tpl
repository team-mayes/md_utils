#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH -t {walltime}:00:00
#SBATCH -p GPU
#SBATCH -N 1 --tasks-per-node=28
#SBATCH --mail-type=END,FAIL
#SBATCH --gres=gpu:k80:4
set echo
set -x
module load cuda
# module load namd_gpu

cd $SLURM_SUBMIT_DIR
nvidia-smi
$HOME/NAMD_Git-2018-04-18_Linux-x86_64-multicore-CUDA/namd2 +idlepoll +p $SLURM_NPROCS +pemap 0-13+14 {output_name}.inp >& {output_name}.log
