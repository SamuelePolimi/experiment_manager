import argparse

from experiment_manager.manager import Experiment


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", type=int)
    parser.add_argument("--experiment-name", type=str)
    parser.add_argument("--abs-folder", type=str)
    args = parser.parse_args()

    # load the experiment
    exp = Experiment.load(args.abs_folder, args.experiment_name)
    # run the job
    exp.run_id(args.job_id, exp.get_fake_runner())
