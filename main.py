import logging

import numpy as np
import yaml

from controllers import BaseController
from listener import FileListener
from simulation import simulation, parallel_solve
from utils import set_seed, create_solver, random_solution


def parse_config():
    with open("config.yaml", "r") as yaml_file:
        cfg = yaml.load(yaml_file, Loader=yaml.FullLoader)
    return cfg


if __name__ == "__main__":
    config = parse_config()
    set_seed(config["seed"])
    config["n_params"] = BaseController.get_number_of_params_for_controller(config)
    file_name = ".".join([config["solver"], str(config["seed"]), config["task"].split("-")[0], config["brain"]])
    if config["mode"] == "random":
        print("fitness: {}".format(simulation(config, random_solution(config), render=True)))
    elif config["mode"].startswith("opt"):
        listener = FileListener(file_name, ["iteration", "elapsed.sec", "evaluations", "best.fitness"])
        solver = create_solver(config)
        if not config["mode"].endswith("parallel"):
            config["np"] = 1
        best = parallel_solve(solver, config["evaluations"] // solver.popsize, config, listener)
        logging.warning("fitness score at this local optimum: {}".format(best[1]))
    elif config["mode"] == "best":
        best = np.load(FileListener.get_best_file_name(file_name))
        print("fitness: {}".format(simulation(config, best, render=True)))
    else:
        raise ValueError("Invalid mode: {}".format(config["mode"]))
