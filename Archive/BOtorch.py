'''
BOtorch framework for multi-objective optimization

Author: Muxin Xiong
'''

from ax.models.torch.botorch_modular.model import BoTorchModel
from ax.models.torch.botorch_modular.surrogate import Surrogate
from ax.modelbridge.generation_strategy import GenerationStrategy, GenerationStep
from ax.modelbridge.registry import Models
from gpytorch.kernels import RBFKernel, ScaleKernel
from gpytorch.means import ConstantMean
from gpytorch.likelihoods import GaussianLikelihood
from botorch.models.gpytorch import GPyTorchModel
from torch import Tensor
import torch
from gpytorch.distributions import MultivariateNormal
from gpytorch.models import ExactGP
from typing import Optional

# Custom GP model for two objectives
class MultiObjectiveCustomGP(ExactGP, GPyTorchModel):
    _num_outputs = 2  # Set for two objectives

    def __init__(self, train_X, train_Y, train_Yvar: Optional[Tensor] = None):
        super().__init__(train_X, train_Y.squeeze(-1), GaussianLikelihood())
        self.mean_module = ConstantMean()
        self.covar_module = ScaleKernel(
            base_kernel=RBFKernel(ard_num_dims=train_X.shape[-1]),
        )
        self.to(train_X)  # Ensure we're on the right device/dtype

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return MultivariateNormal(mean_x, covar_x)

# Generation strategy for multi-objective GP
gs = GenerationStrategy(
    steps=[
        GenerationStep(
            model=Models.SOBOL,  # Sobol sampling initialization
            num_trials=5,  # Number of random trials before optimization
        ),
        GenerationStep(
            model=Models.BOTORCH_MODULAR,
            num_trials=-1,  # Continue optimizing indefinitely
            model_kwargs={
                "surrogate": Surrogate(MultiObjectiveCustomGP),
            },
        ),
    ]
)

from ax.service.ax_client import AxClient
from ax.service.utils.instantiation import ObjectiveProperties, ObjectiveThreshold
from ax.core.optimization_config import MultiObjectiveOptimizationConfig
from ax.core.objective import MultiObjective, Objective
import pandas as pd

# Load the initial experimental data from the CSV file
initial_data = pd.read_csv('initial_experimental_data.csv')

# Initialize the AxClient with your custom generation strategy from earlier
ax_client = AxClient(generation_strategy=gs)

# Setup the multi-objective experiment
ax_client.create_experiment(
    name="multi_objective_experiment",
    parameters=[
        {"name": "x1", "type": "range", "bounds": [-5.0, 10.0]},
        {"name": "x2", "type": "range", "bounds": [0.0, 15.0]},
    ],
    objectives={
        "objective_1": ObjectiveProperties(minimize=False),  # Maximize objective 1
        "objective_2": ObjectiveProperties(minimize=True),  # Minimize objective 2
    },
)

# After the experiment is created, now we define the thresholds
# Access the objectives (assuming objectives are in a list)
metric_objective_1 = ax_client.experiment.optimization_config.objective.objectives[0].metric
metric_objective_2 = ax_client.experiment.optimization_config.objective.objectives[1].metric

# Define the objective thresholds
objective_thresholds = [
    ObjectiveThreshold(metric=metric_objective_1, bound=0, relative=False),  # Threshold for Objective 1
    ObjectiveThreshold(metric=metric_objective_2, bound=1, relative=False)  # Threshold for Objective 2
]

# Apply the thresholds to the experiment's optimization config
ax_client.experiment.optimization_config = MultiObjectiveOptimizationConfig(
    objective=ax_client.experiment.optimization_config.objective,
    objective_thresholds=objective_thresholds
)

# Iterate over the initial data and manually complete each trial
for index, row in initial_data.iterrows():
    # Check the format of the parameters before passing them to Ax
    parameters = {
        "x1": row["x1"],
        "x2": row["x2"]
    }
    print(f"Attaching trial with parameters: {parameters}")

    # Attach the trial and capture its trial index
    trial_index = ax_client.attach_trial(parameters=parameters)

    # If attach_trial returns a tuple, ensure trial_index is properly extracted
    if isinstance(trial_index, tuple):
        trial_index = trial_index[1]

    # Prepare the raw_data
    raw_data = {
        "objective_1": (row["objective_1"], None),  # Objective 1 result and no standard error
        "objective_2": (row["objective_2"], None)  # Objective 2 result and no standard error
    }
    print(f"Completing trial {trial_index} with data: {raw_data}")

    # Complete the trial with the observed objectives
    ax_client.complete_trial(
        trial_index=trial_index,
        raw_data=raw_data
    )

#%% Training Machine with Preliminary Result
# List of objective results for 10 trials
new_objective_1_list = [0.5, 0.6, 0.7, 0.55, 0.65, 0.58, 0.62, 0.68, 0.7, 0.75]  # Replace these with actual or simulated values
new_objective_2_list = [0.3, 0.4, 0.35, 0.33, 0.37, 0.32, 0.36, 0.39, 0.31, 0.34]  # Replace these with actual or simulated values

# Run for 10 trials
for i in range(10):
    # Ask for the next suggested trial (Ax will suggest new x1, x2 values)
    next_trial, trial_index = ax_client.get_next_trial()

    # next_trial is the parameters dictionary, so access them directly
    print(f"Next trial suggested: x1 = {next_trial['x1']}, x2 = {next_trial['x2']}")

    # Get the objective results for the current trial from the lists
    new_objective_1 = new_objective_1_list[i]
    new_objective_2 = new_objective_2_list[i]

    # Complete the trial with the observed results
    ax_client.complete_trial(
        trial_index=trial_index,  # Use the trial index returned from get_next_trial
        raw_data={"objective_1": new_objective_1, "objective_2": new_objective_2}
    )
    print(f"Trial {i+1} completed with objective_1: {new_objective_1}, objective_2: {new_objective_2}")

ax_client.get_trials_data_frame()

#%% Deal with Pareto front
# Retrieve Pareto-optimal trial indices
pareto_optimal_trials = ax_client.get_pareto_optimal_parameters()

# Print the Pareto-optimal solutions
print("Pareto-optimal solutions:")
for i, trial_index in enumerate(pareto_optimal_trials):
    # Retrieve the parameters for the current trial index
    trial = ax_client.experiment.trials[trial_index]
    parameters = trial.arm.parameters
    values = trial.fetch_data().df

    # Print the parameters and the corresponding objective values
    print(f"Pareto-optimal solution {i+1}:")
    print(f"Parameters: {parameters}")
    print(f"Objective 1: {values['mean'][0]}, Objective 2: {values['mean'][1]}")

#%% Setting the prior knowledge if any

from ax.plot.pareto_frontier import plot_pareto_frontier
from ax.plot.pareto_utils import compute_posterior_pareto_frontier
from ax.utils.notebook.plotting import render
from ax.metrics.noisy_function import NoisyFunctionMetric
import torch
import numpy as np

# Define Metric for Objective 1
class Objective1Metric(NoisyFunctionMetric):
    def f(self, x: np.ndarray) -> float:
        # This is a placeholder function. Replace with your actual evaluation logic for Objective 1.
        return float(x[0])  # Modify according to your problem.

# Define Metric for Objective 2
class Objective2Metric(NoisyFunctionMetric):
    def f(self, x: np.ndarray) -> float:
        # This is a placeholder function. Replace with your actual evaluation logic for Objective 2.
        return float(x[1])  # Modify according to your problem.

# Instantiate the metrics with no noise (noise_sd=0.0)
metric_objective_1 = Objective1Metric("objective_1", ["x1", "x2"], noise_sd=0.0, lower_is_better=False)  # Maximize
metric_objective_2 = Objective2Metric("objective_2", ["x1", "x2"], noise_sd=0.0, lower_is_better=True)   # Minimize

# Now let's fetch the data for the experiment
data = ax_client.experiment.fetch_data()

# Compute the posterior Pareto frontier for the multi-objective case
frontier = compute_posterior_pareto_frontier(
    experiment=ax_client.experiment,
    data=data,
    primary_objective=metric_objective_1,  # Primary objective
    secondary_objective=metric_objective_2,  # Secondary objective
    absolute_metrics=["objective_1", "objective_2"],  # The two objectives
    num_points=50  # Number of points to plot on the Pareto frontier
)

# Render the Pareto frontier plot with confidence intervals
render(plot_pareto_frontier(frontier, CI_level=0.90))

#%% Deal with Pareto Front, take 10 s per plot
from ax.plot.pareto_frontier import plot_pareto_frontier
from ax.plot.pareto_utils import compute_posterior_pareto_frontier
from ax.utils.notebook.plotting import render
from ax.metrics.noisy_function import NoisyFunctionMetric
import torch
import numpy as np
import matplotlib.pyplot as plt

# Define Metric for Objective 1 (Maximize)
class Objective1Metric(NoisyFunctionMetric):
    def f(self, x: np.ndarray) -> float:
        # Replace this with your actual logic for calculating objective 1
        return float(x[0])

# Define Metric for Objective 2 (Minimize)
class Objective2Metric(NoisyFunctionMetric):
    def f(self, x: np.ndarray) -> float:
        # Replace this with your actual logic for calculating objective 2
        return float(x[1])

# Instantiate the metrics with the correct lower_is_better settings
metric_objective_1 = Objective1Metric(name="objective_1", param_names=["x1", "x2"], noise_sd=0.0, lower_is_better=False)  # Maximize
metric_objective_2 = Objective2Metric(name="objective_2", param_names=["x1", "x2"], noise_sd=0.0, lower_is_better=True)   # Minimize

# Fetch data from the experiment
data = ax_client.experiment.fetch_data()

# Compute the posterior Pareto frontier
frontier = compute_posterior_pareto_frontier(
    experiment=ax_client.experiment,
    data=data,
    primary_objective=metric_objective_1,
    secondary_objective=metric_objective_2,
    absolute_metrics=["objective_1", "objective_2"],
    num_points=50  # Number of points to sample along the Pareto frontier
)

# Plot the computed Pareto frontier
pareto_plot = plot_pareto_frontier(frontier, CI_level=0.90)
render(pareto_plot)

# Now, plot the exact Pareto-optimal solutions on top of the frontier plot
pareto_solutions = ax_client.get_pareto_optimal_parameters()

# Extract the Pareto-optimal parameters and objective values
pareto_x = []
pareto_y = []
for trial_index in pareto_solutions:
    trial = ax_client.experiment.trials[trial_index]
    values = trial.fetch_data().df

    # Assuming 'mean' column has the objective values
    pareto_x.append(values['mean'][0])  # Objective 1
    pareto_y.append(values['mean'][1])  # Objective 2

# Overlay the actual Pareto-optimal solutions as scatter points using matplotlib
plt.scatter(pareto_x, pareto_y, color='red', label='Pareto-Optimal Solutions')
plt.xlabel('Objective 1')
plt.ylabel('Objective 2')
plt.legend()
plt.show()

#%% Extracting the hypervolume improvement parameters
from ax.modelbridge.modelbridge_utils import observed_hypervolume
from ax.modelbridge.registry import Models

# Initialize variables for tracking hypervolume
hv_list = []

# Run the optimization loop for the number of trials
for i, trial in enumerate(ax_client.experiment.trials.values()):
    try:
        # Compute the hypervolume after each iteration
        observed_hv = observed_hypervolume(modelbridge=ax_client.generation_strategy.model)
        hv_list.append(observed_hv)
        print(f"Iteration {i+1}: Hypervolume = {observed_hv}")
    except Exception as e:
        print(f"Failed to compute hypervolume in iteration {i+1}: {e}")
        hv_list.append(None)  # Append None if failed to compute hypervolume

