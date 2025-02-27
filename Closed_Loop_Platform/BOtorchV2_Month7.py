from ax.service.ax_client import AxClient
from ax.service.utils.instantiation import ObjectiveProperties, ObjectiveThreshold
from ax.core.optimization_config import MultiObjectiveOptimizationConfig
from ax.modelbridge.generation_strategy import GenerationStrategy, GenerationStep
from ax.modelbridge.registry import Models
from ax.models.torch.botorch_modular.surrogate import Surrogate
from botorch.models.gpytorch import GPyTorchModel
from gpytorch.kernels import RBFKernel, ScaleKernel
from gpytorch.means import ConstantMean
from gpytorch.likelihoods import GaussianLikelihood
from gpytorch.models import ExactGP
from gpytorch.distributions import MultivariateNormal
from torch import Tensor
from typing import Optional
import numpy as np
import pandas as pd


# Custom GP model for multi-objective optimization
class MultiObjectiveCustomGP(ExactGP, GPyTorchModel):
    """
    Custom GP model for multi-objective optimization.
    """
    _num_outputs = 3  # Adjust this if you need a different number of outputs.

    def __init__(self, train_X, train_Y, train_Yvar: Optional[Tensor] = None):
        super().__init__(train_X, train_Y.squeeze(-1), GaussianLikelihood())
        self.mean_module = ConstantMean()
        self.covar_module = ScaleKernel(
            base_kernel=RBFKernel(ard_num_dims=train_X.shape[-1]),
        )
        self.to(train_X)  # Ensure compatibility with input dtype/device

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return MultivariateNormal(mean_x, covar_x)


# Class for managing experiments
class ExperimentManager:
    def __init__(self, generation_strategy, parameters, objectives, experiment_name="multi_objective_experiment", verbose_logging=False):
        """
        Initialize the ExperimentManager class with AxClient and setup the experiment.
        """
        self.ax_client = AxClient(generation_strategy=generation_strategy, verbose_logging=verbose_logging)
        self.parameters = parameters
        self.objectives = objectives
        self.experiment_name = experiment_name
        self.experimental_conditions = None
        self.objective_data = None
        self.metric_bulk_electrolysis = None
        self.metric_current_density = None
        self.metric_fe_co = None
        self.index_offset = 1
        self.setup_experiment()

    def setup_experiment(self):
        """
        Setup the multi-objective experiment in Ax.
        """
        self.ax_client.create_experiment(
            name=self.experiment_name,
            parameters=self.parameters,
            objectives=self.objectives,
        )

        # Access the metrics and store them as attributes
        #self.metric_bulk_electrolysis = self.ax_client.experiment.optimization_config.objective.objectives[0].metric
        self.metric_current_density = self.ax_client.experiment.optimization_config.objective.objectives[0].metric
        self.metric_fe_co = self.ax_client.experiment.optimization_config.objective.objectives[1].metric

    def load_initial_data(self, experimental_conditions_file, objective_data_file):
        """
        Load experimental conditions and objective data from files.
        """
        self.experimental_conditions = pd.read_csv(experimental_conditions_file, header=2)
        self.objective_data = pd.read_csv(objective_data_file)

    def update(self):
        """
        Fetch the next experimental condition (trial) and log it as a new trial for experimentation.
        """
        # Ensure data is loaded
        if self.experimental_conditions is None or self.objective_data is None:
            raise ValueError("Experimental conditions and objective data must be loaded before calling update.")

        # Get the next trial suggestion
        trial_index, zero_based_next_trial = self.ax_client.get_next_trial()
        one_based_next_trial = zero_based_next_trial + self.index_offset
        #print(f"Next trial (index {trial_index}): {next_trial}")

        # Log the new trial parameters
        #print(f"This is a new experimental condition for testing: EXP{next_trial}")

        # Return the next trial parameters for further experimentation
        return trial_index, one_based_next_trial
    
# Setup generation strategy
gs = GenerationStrategy(
    steps=[
        GenerationStep(
            model=Models.SOBOL,
            num_trials=5,
        ),
        GenerationStep(
            model=Models.BOTORCH_MODULAR,
            num_trials=-1,
            model_kwargs={"surrogate": Surrogate(MultiObjectiveCustomGP)},
        ),
    ]
)

# Parameters, objectives, and thresholds month 7: catalyst optimization under different CO2 condition
parameters = [
    {"name": "CuConc", "type": "choice", "values": [round(v, 2) for v in [0.2, 0.3, 0.4, 0.5]], "is_ordered": False},
    {"name": "Volt", "type": "choice", "values": [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3], "is_ordered": False},
    {"name": "Time", "type": "choice", "values": list(range(40, 500, 20)), "is_ordered": False},
    {"name": "CO2ratio", "type": "choice", "values": list(range(5, 101, 1)), "is_ordered": False},
    {"name": "IL1", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
    {"name": "IL2", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
    {"name": "IL3", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
    {"name": "IL4", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
    {"name": "IL5", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
    {"name": "blank", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
]



