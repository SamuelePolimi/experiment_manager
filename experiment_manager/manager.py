from typing import List, Dict, Callable
import json, os
import numpy as np
import torch

from experiment_manager.slurm_configuration import SLURM


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

    def run_id(self, id: int, runner: Callable):
        """
        Run the job with the given id
        :param ids:
        :param runner:
        :return:
        """
        # check if the pass_filter exists
        if not os.path.exists(self._abs_path + "/pass_filter.json"):
            raise ValueError("The pass_filter.json file does not exist. Please run save_pass_filter first")
        # load the pass_filter
        with open(self._abs_path + "/pass_filter.json", 'r') as f:
            data = json.load(f)
        allowed_ids = data["jobs"]
        # check if the id is in the allowed_ids
        if id in allowed_ids:
            runner(id, self.jobs[id]["variables"], self.jobs[id]["run_config"])
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

    def get_all_ids(self):
        """
        Get all the ids of the jobs
        :return:
        """
        return list(range(len(self.jobs)))

    def set_slurm_config(self, slurm_config: SLURM):
        self.slurm_config = slurm_config

    def create_slurm_job_array_script(self, abs_python_file: str,
                                      job_name: str = None,
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

        slurm_script = self.slurm_config.get_slurm_job_array_script(abs_python_file, job_name, n_tasks)

        if verbose:
            print(slurm_script)

        with open(self._abs_path + "/slurm_script.sh", 'w') as f:
            f.write(slurm_script)

    def get_fake_runner(self):
        def runner(job_id, variables, configuration):
            # run the job
            print("Running job %d" % job_id)
            print("Variables: %s" % variables)
            print("Configuration: %s" % configuration)
            self.save_results(job_id, "configuration.json", Experiment.json_saver, configuration, override=True)
            print("Job %d done!" % job_id)

        return runner

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
