from typing import List, Dict, Callable
import json, os


class SLURM:

    def __init__(self, pre_script: List[str],
                 post_script: List[str],
                 n_gpus: int,
                 n_cpus: int,
                 memory: str,
                 time: str,
                 job_runner: str):

        self.pre_script = pre_script
        self.post_script = post_script
        self.n_gpus = n_gpus
        self.n_cpus = n_cpus
        self.memory = memory
        self.time = time
        self.job_runner = job_runner

    def save(self, filename: str):
        with open(filename, 'w') as f:
            f.write(json.dumps(self.__dict__))

    @staticmethod
    def load(filename: str):
        # check if the file exists
        if not os.path.exists(filename):
            raise ValueError("The file does not exist.")
        with open(filename, 'r') as f:
            data = json.load(f)
            return SLURM(**data)

    def get_slurm_job_array_script(self, abs_experiment_path: str,
                                   job_name: str = None,
                                   n_tasks: int = None):
        """ Create a slurm job array script for the experiment
        :param abs_experiment_path: the absolute path of the python file to run
        :param job_name: the name of the job
        :param n_tasks: the number of tasks to run
        :param verbose: print the script to the console
        """
        script = "#!/bin/bash\n"
        script += "#SBATCH --job-name=%s\n" % job_name
        script += "#SBATCH --ntasks=1\n"
        script += "#SBATCH --output=%s.out\n" % (abs_experiment_path + "_%A_%a")
        script += "#SBATCH --error=%s.err\n" % (abs_experiment_path + "_%A_%a")
        script += "#SBATCH --cpus-per-task=%d\n" % self.n_cpus
        script += "#SBATCH --gpus-per-task=%d\n" % self.n_gpus
        script += "#SBATCH --mem=%s\n" % self.memory
        script += "#SBATCH --time=%s\n" % self.time
        script += "#SBATCH --array=0-%d\n" % (n_tasks-1)
        script += "\n"

        for line in self.pre_script:
            script += line + "\n"

        script += "\n"
        script += self.job_runner + " --job-id $SLURM_ARRAY_TASK_ID" \
                  + " --experiment-path " + abs_experiment_path \
                  + " --experiment-name " + job_name + "\n"

        for line in self.post_script:
            script += line + "\n"

        return script







