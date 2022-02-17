import abc
import math
import random

import numpy as np
import torch

from pressure import PressureSoftBody


class BaseController(abc.ABC):

    def __init__(self, input_dim, output_dim):
        self.input_dim = input_dim
        self.output_dim = output_dim

    def __str__(self):
        return "BaseController[input={},output={}]".format(self.input_dim, self.output_dim)

    @abc.abstractmethod
    def set_params(self, params):
        pass

    @abc.abstractmethod
    def control(self, t, obs):
        pass

    @abc.abstractmethod
    def get_number_of_params(self):
        pass

    @staticmethod
    def get_number_of_params_for_controller(brain):
        if brain == "random":
            return 0
        elif brain == "phase":
            return PressureSoftBody.n_masses + 2
        elif brain == "mlp":
            return (PressureSoftBody.n_masses * 3 + 3) * (PressureSoftBody.n_masses + 1) + PressureSoftBody.n_masses + 1
        raise ValueError("Invalid controller name: {}".format(brain))

    @classmethod
    def create_controller(cls, input_dim, output_dim, brain, solution):
        if brain == "random":
            controller = RandomController(input_dim, output_dim)
        elif brain == "phase":
            controller = PhaseController(input_dim, output_dim)
        elif brain == "mlp":
            controller = MLPController(input_dim, output_dim)
        else:
            raise ValueError("Invalid controller name: {}".format(brain))
        controller.set_params(solution)
        return controller


class RandomController(BaseController):

    def __init__(self, input_dim, output_dim):
        super(RandomController, self).__init__(input_dim, output_dim)

    def __str__(self):
        return super(RandomController, self).__str__().replace("Base", "Random")

    def set_params(self, params):
        pass

    def control(self, t, obs):
        return np.random.random(self.output_dim) * 2.0 - 1.0

    def get_number_of_params(self):
        return 0


class PhaseController(BaseController):

    def __init__(self, input_dim, output_dim):
        super(PhaseController, self).__init__(input_dim, output_dim)
        self.freq = random.random()
        self.ampl = random.random()
        self.phases = []

    def set_params(self, params):
        self.freq = params[0]
        self.ampl = params[1]
        self.phases = params[2:]

    def control(self, t, obs):
        return np.sin([2 * math.pi * self.freq * t * self.phases[i] * self.ampl for i in range(self.output_dim)])

    def get_number_of_params(self):
        return self.output_dim + 2


class MLPController(BaseController):

    def __init__(self, input_dim, output_dim):
        super(MLPController, self).__init__(input_dim, output_dim)
        self.nn = torch.nn.Sequential(torch.nn.Linear(in_features=self.input_dim, out_features=self.output_dim),
                                      torch.nn.Tanh()
                                      )

    def __str__(self):
        return super(MLPController, self).__str__().replace("Base", "MLP")

    def set_params(self, params):
        state_dict = self.nn.state_dict()
        start = 0
        for key, coeffs in state_dict.items():
            num = coeffs.numel()
            state_dict[key] = torch.tensor(np.array(params[start:start + num]).reshape(state_dict[key].shape))
            start += num
        self.nn.load_state_dict(state_dict)

    def control(self, t, obs):
        return self.nn(torch.from_numpy(obs).float()).detach().numpy()

    def get_number_of_params(self):
        raise self.input_dim * self.output_dim + self.output_dim
