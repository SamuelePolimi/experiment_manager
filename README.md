# Experiment Manager
_Configure and run python experiments and SLURM scripts_

## Installation

## Creation of an experiment
`experiment_manager` is a python package that allows to create and manage experiments. An experiment is a collection of jobs that are run with different parameters. The package allows to save the experiment on disk and to generate SLURM scripts to run the jobs on a cluster.
We suggest to create a folder where you want to manage all your experiment. Such folder is referred in the code as `abs_folder_path`.
Each experiment (i.e., group of jobs), has a name `experiment_name`, which will coincide with a subfolder in `abs_folder_path`.

To create an experiment, you can simply create an instance of the `Experiment` class.

```python
from experiment_manager import Experiment

import os

abs_folder_path = os.path.dirname(os.path.realpath(__file__))
experiment_name = "test_experiment"
exp = Experiment(["algorithm", "seed"], experiment_name, abs_folder_path)
```

The variable names in the list `["algorithm", "seed"]` are the names of the variables that will change from one job to the other.

To allow for high flexibility, jobs can be added "manually", i.e.,

```python
algorithms = ["TD3", "DDPG"]
seeds = [1, 2, 3]

for alg in algorithms:
    for seed in seeds:
        # The variables define the parameters that chages from one job to the other
        variables = {"algorithm": alg, "seed": seed}
        # The configuration specifies all the parameters that define a job
        configuration = {"algorithm": alg, "seed": seed, "nn": [1, 10], "tau": 0.005}
        exp.add_job(variables, configuration)
```

At this point, the experiment is ready to be saved on disk.

```python
exp.save()
```

However, it is not possible yet to run experiments, because we need to decide which jobs to run.
This is done by a `pass_filter` function, which takes as input the variables of a job and returns a boolean value, i.e., and saving the pass filter.

```python
def pass_filter(variables):
    return variables["algorithm"] == "TD3"

allowed_ids = exp.get_ids(pass_filter)
exp.save_pass_filter(allowed_ids)
```

Notice that `get_ids` can also be used to retrieve results, and in general to perform.

Here is a complete example.


```python
from experiment_manager import Experiment

import os

abs_folder_path = os.path.dirname(os.path.realpath(__file__))
experiment_name = "test_experiment"
exp = Experiment(["algorithm", "seed"], experiment_name, abs_folder_path)

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

# Define a pass_filter (to selef which jobs to run).
def pass_filter(variables):
    return variables["algorithm"] == "TD3"


# Get the ids of the jobs that pass the filter
allowed_ids = exp.get_ids(pass_filter)


# Save the jobs that pass the filter
exp.save_pass_filter(allowed_ids)
```

## Defining a SLURM script
The first thing to do is to define the SLURM configuration. That can be done manually, i.e.,

```python
from experiment_manager import SLURM

slurm = {
    "n_gpus": 1,
    "n_cpus": 1,
    "memory": "1000",
    "time": "10:00:00",
    "post_script": ["module load python/3.8", "module load conda"],
    "pre_script": ["conda deactivate idrl", "module unload conda", "module unload python/3.8"],
    "python_runner": "runner.py"
}

slurm_config = SLURM(**slurm)
```

or by loading it from file

```python
slurm_config = SLURM.load("slurm_config.json")
```

Then the SLURM configuration needs to be added to the experiment.

```python
exp.set_slurm_config(slurm_config)
exp.save()
```

At this point, we can create the SLURM scripts to run the jobs on the cluster.

```python
exp.generate_slurm_script("python_script", # python runner program (see later)
                          "job_name", # name of the job
                          10, # number of jobs to run -- if not specified, it will be inferred from the number of jobs that pass the filter
                          )
```

The `generate_slurm_script` method generates a SLURM script that runs the python script `python_script.py` on the cluster. The script is generated in the folder `abs_folder_path/experiment_name/slurm_scripts.sh`.

## The python runner

The python runner defined above (i.e., python_script) should be a python script that takes as input
three parameters: --job_id, --experiment_path, --experiment_name. The script should load the job with the given job_id and run the job.

```python
import argparse
from experiment_manager import Experiment

def runner(job_id, variables, configuration):
    # Run the job... Insert here the code to run the job
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", type=int)
    parser.add_argument("--experiment-path", type=str)
    parser.add_argument("--experiment-name", type=str)
    args = parser.parse_args()
    
    exp = Experiment.load(args.experiment_name, args.experiment_path)
    exp.run_id(args.job_id, runner)
```

To test that everything works correctly, one can use the `fake_runner` function, which simply prints the job_id, variables, and configuration of the job.

```python
import argparse
from experiment_manager import Experiment

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", type=int)
    parser.add_argument("--experiment-path", type=str)
    parser.add_argument("--experiment-name", type=str)
    args = parser.parse_args()
    
    exp = Experiment.load(args.experiment_name, args.experiment_path)
    exp.run_id(args.job_id, exp.fake_runner)
```

Instead, to test jobs, one can use the random_filter, which randomly selects jobs to run.

```python
ids = exp.get_random_ids(10)
exp.save_pass_filter(ids)
```
