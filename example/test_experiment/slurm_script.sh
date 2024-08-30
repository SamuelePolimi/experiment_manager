#!/bin/bash
#SBATCH --job-name=test_experiment
#SBATCH --output=test_experiment.out
#SBATCH --error=test_experiment.err
#SBATCH --n_tasks=3
#SBATCH --cpus-per-task=1
#SBATCH --gpus-per-task=1
#SBATCH --mem=1000
#SBATCH --time=00:01:00
#SBATCH --array=0-2

module load python/3.10
module load conda
conda activate experiment_manager

python ../fake_runner.py--job-id $SLURM_ARRAY_TASK_ID--experiment-path /home/c7031412/Projects/experiment_manager/example/test_experiment--experiment-name test_experiment
conda deactivate experiment_manager
module unload conda
module unload python/3.10
