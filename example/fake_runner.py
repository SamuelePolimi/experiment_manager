import argparse
from experiment_manager import Experiment

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", type=int)
    parser.add_argument("--experiment-path", type=str)
    parser.add_argument("--experiment-name", type=str)
    args = parser.parse_args()

    exp = Experiment.load(args.experiment_path, args.experiment_name)
    exp.run_id(args.job_id, exp.get_fake_runner())