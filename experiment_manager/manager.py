from __future__ import annotations
from typing import List, Dict, Callable
import json, os
import warnings

from experiment_manager.configuration import Configuration

try:
    import numpy as np
except ImportError:
    warnings.warn("Numpy is not installed. Some functionalities may not work.")
try:
    import torch
except ImportError:
    warnings.warn("Pytorch is not installed. Some functionalities may not work.")

from experiment_manager.slurm_configuration import SLURM

# TODO: write a way to make simple "fake experiments" to trace the configurations
# TODO: and, perhaps, make a way to check on completeness and correctness of automatically generated configurations


class ExperimentData:

    def __init__(self, experiment: Experiment, slurm_id: int, generate_default=False):
        self.experiment = experiment
        self.generate_default = generate_default
        if not generate_default:
            self.filtered_id = experiment.get_filtered_ids()[slurm_id]
        else:
            self.filtered_id = slurm_id
        self.job = self.experiment.jobs[self.filtered_id]
        self.variables = self.job["variables"]
        self.configuration = Configuration(self.job["run_config"], generate_default=generate_default)

    def save_results(self, filename: str, saver: Callable, results, override=False):
        if not self.generate_default:
            self.experiment.save_results(self.filtered_id, filename, saver, results, override)
        else:
            print("Save %d_%s -> %s" % (self.filtered_id, filename, results))

    def __str__(self):
        return """Experiment: %s 
        id: %d
        variables: %s
        configuration: %s""" % (self.experiment.experiment_name, self.filtered_id, self.variables, self.configuration)


class Experiment:
    """
    Class to manage experiments
    """

    def __init__(self, variables: List[str], experiment_name: str, abs_path: str = None, slurm_config: SLURM = None):
        self.variables = variables
        self.jobs = []
        self.experiment_name = experiment_name
        if abs_path is not None:
            self._abs_path = abs_path + "/" + experiment_name
        else:
            raise ValueError("Please provide an absolute path to save the experiment.")
        self.slurm_config = slurm_config

    def add_job(self, variables: Dict, run_config: Dict):
        """
        Add a job to the experiment
        :param variables:
        :param run_config:
        :return:
        """
        # check that the job does not exist
        for job in self.jobs:
            if job["variables"] == variables:
                raise ValueError("The job already exists.")
        self.jobs.append({"variables": variables,
                          "run_config": run_config})

    def save(self, verbose=True):
        """
        Save an experiment to a json file
        :param filename:
        :return:
        """
        # If the folder does not exists, create it
        if not os.path.exists(self._abs_path):
            os.makedirs(self._abs_path)
        # Save the experiment to a json file
        with open(self._abs_path + "/config.json", 'w') as f:
            json.dump({"variables": self.variables, "jobs": self.jobs}, f)
        # if the slurm_config exists, save it
        if self.slurm_config is not None:
            self.slurm_config.save(self._abs_path + "/slurm_config.json")
        if verbose:
            print("Experiment saved in %s" % self._abs_path)

    @staticmethod
    def load(abs_folder: str, experiment_name: str):
        """
        Load an experiment from a folder experiment
        :param abs_folder:
        :return:
        """

        with open(abs_folder + "/" + experiment_name + "/config.json", 'r') as f:
            data = json.load(f)
        slurm_config = None
        # check if the slurm_config exists
        if os.path.exists(abs_folder + "/" + experiment_name + "/slurm_config.json"):
            slurm_config = SLURM.load(abs_folder + "/" + experiment_name + "/slurm_config.json")
        exp = Experiment(data["variables"], experiment_name, abs_folder, slurm_config)
        exp.jobs = data["jobs"]
        return exp

    def get_ids(self, filter: Callable):
        """
        Get the ids of the jobs that pass the filter
        :param filter:
        :return:
        """
        # Get the ids of the jobs that pass the filter
        return [i for i, job in enumerate(self.jobs) if filter(job["variables"])]

    def get_random_ids(self, n_jobs: int):
        """
        Get the ids of the jobs that pass the filter
        :param filter:
        :return:
        """

        return np.random.choice(range(len(self.jobs)), n_jobs, replace=False).tolist()

    def save_pass_filter(self, allowed_ids: List[int]):
        """
        Save the jobs that pass the filter
        :param allowed_ids:
        :return:
        """
        # Save the jobs that pass the filter
        with open(self._abs_path + "/pass_filter.json", 'w') as f:
            json.dump({"jobs": allowed_ids}, f)

    def get_filtered_ids(self):
        # check if the pass_filter exists
        if not os.path.exists(self._abs_path + "/pass_filter.json"):
            raise ValueError("The pass_filter.json file does not exist in %s. Please run save_pass_filter first" %
                             self._abs_path)
        # load the pass_filter
        with open(self._abs_path + "/pass_filter.json", 'r') as f:
            data = json.load(f)
        allowed_ids = data["jobs"]
        return allowed_ids

    def run_id(self, id: int, runner: Callable[[ExperimentData], None]):
        """
        Run the job with the given id
        :param ids:
        :param runner:
        :return:
        """
        allowed_ids = self.get_filtered_ids()
        # check if the id is in the allowed_ids
        if id in allowed_ids:
            experiment_data = ExperimentData(self, id)
            runner(experiment_data)
        else:
            raise ValueError("The id is not in the list of allowed ids.")

    def save_results(self, id: int, filename: str, saver: Callable, results, override=False):
        """
        Save the results of the jobs on file
        :param ids:
        :param results:
        :return:
        """
        # if the file already exists, raise an error
        if not override and os.path.exists(self._abs_path + "/%d_%s" % (id, filename)):
            raise ValueError("The file already exists. Please use override=True to overwrite it.")
        else:
            saver(self._abs_path + "/%d_%s" % (id, filename), results)

    def get_results(self, id: int, filename: str, loader: Callable):
        """
        Load the results of the jobs from file
        :param ids:
        :param results:
        :return:
        """
        return loader(self._abs_path + "/%d_%s" % (id, filename))

    def get_all_ids(self):
        """
        Get all the ids of the jobs
        :return:
        """
        return list(range(len(self.jobs)))

    def are_all_results_present(self, filename: str):
        """
        Check if all the results are present
        :param filename:
        :return:
        """
        return all([os.path.exists(self._abs_path + "/%d_%s" % (id, filename)) for id in self.get_filtered_ids()])

    def set_slurm_config(self, slurm_config: SLURM):
        self.slurm_config = slurm_config

    def create_slurm_job_array_script(self, job_name: str = None,
                                      n_tasks: int = None,
                                      verbose=True):
        """ Create a slurm job array script for the experiment
        :param abs_python_file: absolute path to the python file
        :param job_name: name of the job
        :param n_tasks: number of tasks. If not provided, it will be the number of jobs in the pass_filter.json
        """
        # check if the slurm_config exists
        if self.slurm_config is None:
            raise ValueError("The slurm_config is not defined.")

        if n_tasks is None:
            with open(self._abs_path + "/pass_filter.json", 'r') as f:
                data = json.load(f)
            n_tasks = len(data["jobs"])

        if job_name is None:
            job_name = self.experiment_name

        slurm_script = self.slurm_config.get_slurm_job_array_script(self._abs_path, job_name, n_tasks)

        if verbose:
            print(slurm_script)

        with open(self._abs_path + "/slurm_script.sh", 'w') as f:
            f.write(slurm_script)

    def get_fake_runner(self):
        def runner(experiment_data: ExperimentData):
            # run the job
            print(experiment_data)
            experiment_data.save_results("results.json", Experiment.json_saver, experiment_data.configuration)

        return runner

    # Savers

    @staticmethod
    def json_saver(filename, data):
        with open(filename, 'w') as f:
            json.dump(data, f)

    @staticmethod
    def numpy_saver(filename, data):
        np.save(filename, data)

    @staticmethod
    def torch_saver(filename, data):
        torch.save(data, filename)

    # Loaders

    @staticmethod
    def json_loader(filename):
        with open(filename, 'r') as f:
            return json.load(f)

    @staticmethod
    def numpy_loader(filename):
        return np.load(filename)

    @staticmethod
    def torch_loader(filename):
        return torch.load(filename)
