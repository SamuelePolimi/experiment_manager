from experiment_manager import SLURM
import os

abs_folder_path = os.path.dirname(os.path.realpath(__file__))

slurm = {
    "n_gpus": 1,
    "n_cpus": 1,
    "memory": "1000",
    "time": "00:01:00",
    "pre_script": ["module load python/3.10", "module load Anaconda3/2023.03/python-3.11.0-numpy-conda-2023.03", "conda activate experiment_manager"],
    "post_script": ["conda deactivate experiment_manager", "module unload Anaconda3/2023.03/python-3.11.0-numpy-conda-2023.03", "module unload python/3.10"],
    "job_runner": "python ../fake_runner.py"
}

slurm_config = SLURM(**slurm)
slurm_config.save(abs_folder_path + "/slurm.json")

