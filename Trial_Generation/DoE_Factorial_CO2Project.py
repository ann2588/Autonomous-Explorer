# Required for Dragonfly (note: ignore Fortran warning)
import numpy as np
from argparse import Namespace
from dragonfly import load_config
from dragonfly.exd import domains
from dragonfly.exd.experiment_caller import CPFunctionCaller, CPMultiFunctionCaller
from dragonfly.opt.gp_bandit import CPGPBandit
from dragonfly.opt.multiobjective_gp_bandit import CPMultiObjectiveGPBandit
from dragonfly.exd.worker_manager import SyntheticWorkerManager

# Utilities
import pandas as pd
import math
import csv
import matplotlib.pyplot as plt # for plotting


#def experiment(x, objective='single'):

# Change a method to apply constrain
# maybe 12 is too large for B.O.

#Relaxed ratio Constraints. Keep the step as 5

MAX = 51
MIN = 51-MAX

variables_C = [
    {'name': "Cu (Conti)", 'type': 'discrete_numeric', 'items': list(np.arange(0.2, 0.6, 0.1))},
    {'name': "Volt", 'type': 'discrete_numeric', 'items': list(np.arange(-1.0, -0.1, 0.1))},
    {'name': "Time", 'type': 'discrete_numeric', 'items': list(range(30, 180, 10))},
    {'name': "CO2ratio", 'type': 'discrete_numeric', 'items': list(range(0, 101, 5))}
] + [
    {'name': element, 'type': 'discrete_numeric', 'items': list(range(0, MAX,5))}
    for element in ["IL1", "IL2", "IL3", "IL4", "IL5", "Blank"]
]

constraints_C = [
    {"name": "max", "constraint": f'IL1 + IL2 + IL3 + IL4 + IL5 + Blank < {MAX}'}
]

config_params = {'domain':variables_C, 'domain_constraints': constraints_C}
config = load_config(config_params)

num_init = 20
number_total = 100
batch_size = 20

options = Namespace(
    build_new_model_every = batch_size,           # set to batch size
    init_capital = num_init-1,                    # number of initialization experiments (-1 is included since Dragonfly generates n+1 expts)
    gpb_hp_tune_criterion = 'ml-post_sampling',   # Criterion for tuning GP hyperparameters. Options: 'ml-post_sampling' (algorithm default), 'ml', 'post_sampling'.
    )

func_caller = CPFunctionCaller(None, config.domain, domain_orderings=config.domain_orderings)
opt = CPGPBandit(func_caller, 'default', ask_tell_mode=True, options=options)

opt.initialise()
init_expts = opt.ask(num_init)

print(init_expts)
c_nbubr_list = np.array(init_expts)
print(c_nbubr_list)

filename = 'DoE_randombatch20'
columns = ["CuConc", "Volt", "Time", "CO2ratio", "IL1", "IL2", "IL3", "IL4", "IL5", "Blank"]
df_combinations = pd.DataFrame(init_expts, columns=columns)
# Save the DataFrame to a CSV file
csv_file_path = f'/Users/Yi-An/Documents/000_Project/044_FAARM_PA-004/Code/{filename}.csv'
df_combinations.to_csv(csv_file_path, index=False)
