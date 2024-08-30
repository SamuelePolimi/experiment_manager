from experiment_manager.manager import Experiment, SLURM
import os

abs_folder_path = os.path.dirname(os.path.realpath(__file__))
experiment_name = "test_experiment"

slurm_config = SLURM.load(abs_folder_path + "/slurm.json")
exp = Experiment(["algorithm", "seed"], experiment_name, abs_folder_path, slurm_config)

algorithms = ["TD3", "DDPG"]
seeds = [1, 2, 3]

for alg in algorithms:
    for seed in seeds:
        # The variables define the parameters that chages from one job to the other
        variables = {"algorithm": alg, "seed": seed}
        # The configuration specifies all the parameters that define a job
        configuration = {"algorithm": alg, "seed": seed, "nn": [1, 10], "tau": 0.005}
        exp.add_job(variables, configuration)

# Save the experiment on disk
exp.save()


# Define a pass_filter
def pass_filter(variables):
    return variables["algorithm"] == "TD3"


# Get the ids of the jobs that pass the filter
allowed_ids = exp.get_ids(pass_filter)


# Save the jobs that pass the filter
exp.save_pass_filter(allowed_ids)


# Example of SLURM script generation
exp.create_slurm_job_array_script()


