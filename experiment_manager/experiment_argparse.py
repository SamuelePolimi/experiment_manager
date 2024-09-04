import argparse
from experiment_manager.manager import Experiment, ExperimentData

# TODO: perhaps this should be a launcher


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", type=int)
    parser.add_argument("--experiment-path", type=str)
    parser.add_argument("--experiment-name", type=str)
    args = parser.parse_args()
    return args


def get_experiment_data():
    args = get_arguments()
    expperiment = Experiment.load(args.experiment_path, args.experiment_name)
    experiment_data = ExperimentData(expperiment, args.job_id)
    return experiment_data

