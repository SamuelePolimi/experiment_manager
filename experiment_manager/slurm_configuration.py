from typing import List, Dict, Callable
import json, os


class SLURM:

    def __init__(self, pre_script: List[str],
                       post_script: List[str],
                       n_gpus: int,
                       n_cpus: int,
                       mem: str,
                       time: str,
                       python_runner: str):

        self.pre_script = pre_script
        self.post_script = post_script
        self.n_gpus = n_gpus
        self.n_cpus = n_cpus
        self.mem = mem
        self.time = time
        self.python_runner = python_runner

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

    def get_slurm_job_array_script(self, abs_python_file: str,
                                        job_name: str = None,
                                        n_tasks: int = None):
            """ Create a slurm job array script for the experiment
            :param abs_python_file: the absolute path of the python file to run
            :param job_name: the name of the job
            :param n_tasks: the number of tasks to run
            :param verbose: print the script to the console
            """
            script = "#!/bin/bash\n"
            script += "#SBATCH --job-name=%s\n" % job_name
            script += "#SBATCH --output=%s.out\n" % job_name
            script += "#SBATCH --error=%s.err\n" % job_name
            script += "#SBATCH --ntasks=%d\n" % n_tasks
            script += "#SBATCH --cpus-per-task=%d\n" % self.n_cpus
            script += "#SBATCH --gpus-per-task=%d\n" % self.n_gpus
            script += "#SBATCH --mem=%s\n" % self.mem
            script += "#SBATCH --time=%s\n" % self.time
            script += "#SBATCH --array=0-%d\n" % (n_tasks-1)
            script += "\n"

            for line in self.pre_script:
                script += line + "\n"

            script += "\n"
            script += "python -m " + self.python_runner + "--job-id $SLURM_ARRAY_TASK_ID" \
                      + "--experiment-path " + abs_python_file \
                    + "--experiment-name " + job_name + "\n"

            for line in self.post_script:
                script += line + "\n"







