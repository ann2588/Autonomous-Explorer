#%%
import numpy as np
import pandas as pd
import sys, os
from ax.core.trial import Trial
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Closed_Loop_Platform.BOtorchV2_Month7 import *
# Add the parent directory to the system path

# Assuming you have an instance of AxClient
# Machine Learning Agent setup


#%% Machine Learning Agent setup
objectives = {
    #"bulk_electrolysis_potential": ObjectiveProperties(minimize=True),
    "current_density": ObjectiveProperties(minimize=False),
    "FE_CO": ObjectiveProperties(minimize=False)
}
manager = ExperimentManager(generation_strategy=gs, parameters=parameters, objectives=objectives)

# Define thresholds using metric variables after experiment setup
thresholds = [
    #ObjectiveThreshold(metric=manager.metric_bulk_electrolysis, bound=-2.2, relative=False),
    ObjectiveThreshold(metric=manager.metric_current_density, bound=20, relative=False),
    ObjectiveThreshold(metric=manager.metric_fe_co, bound=10, relative=False),
]

# Apply thresholds to the optimization config

manager.ax_client.experiment.optimization_config = MultiObjectiveOptimizationConfig(
    objective=manager.ax_client.experiment.optimization_config.objective,
    objective_thresholds=thresholds,
)
optimization_conFig = manager.ax_client.experiment.optimization_config

client = manager.ax_client
# Load your experiment if needed
exp_condition_file = "/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/experimental_conditions_cu.csv"
objective_file = "/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/updated_objective_data_cu.csv"
manager.load_initial_data(exp_condition_file,objective_file)
df_x = pd.read_csv(exp_condition_file, header=0)
df_x.rename(columns={"Cu": "CuConc", "Blank": "blank"}, inplace=True)
df_y = pd.read_csv(objective_file, header=0)

df_x_dict = df_x.iloc[:, 1:].to_dict(orient='list')
df_y_dict = df_y.iloc[:, 3:].to_dict(orient='list')


#%%

for i in range(len(df_x)):
    # Prepare trial parameters
    trial_parameters = {key: df_x_dict[key][i] for key in df_x_dict.keys()}
    
    # Attach the trial to the client
    trial_params, trial_index = client.attach_trial(parameters=trial_parameters)

    # Complete the trial by providing evaluation results from df_y_dict
    client.complete_trial(trial_index, raw_data={
        #"bulk_electrolysis_potential": (-2.2, 0.0),  # mean, SEM (standard error)
        "current_density": (df_y_dict["Average Current Density"][i], 0.0),
        "FE_CO": (df_y_dict["Average CO"][i], 0.0),
    })

    print(f"Trial {trial_index} completed with parameters: {trial_params}")

    #hypervolume = client.get_hypervolume(optimization_config=optimization_conFig)
    #print(f"Hypervolume: {hypervolume}")

trials = client.get_trials_data_frame()
print(trials)


#%% retrieve pareto front and visualize
pareto_optimal_solutions = client.get_pareto_optimal_parameters()

pareto_fe_co = []
pareto_current_density = []
pareto_Cuconc = []
pareto_Voltage = []
Pareto_time = []
pareto_co2=[]

for trial_index, (parameters, outcomes) in pareto_optimal_solutions.items():
    pareto_fe_co.append(outcomes[0]['FE_CO'])  # Get the mean value of FE_CO
    pareto_current_density.append(outcomes[0]['current_density'])  # Get the mean value of current density
    pareto_Cuconc.append(parameters['CuConc']),
    pareto_Voltage.append(parameters['Volt'])  # Get the mean value of Voltage
    Pareto_time.append(parameters['Time'])  # Get the mean value of Time
    pareto_co2.append(parameters['CO2ratio'])  # Get the mean value of Time

print("Pareto FE_CO values:", pareto_fe_co)
print("Pareto Current Density values:", pareto_current_density)# %%
import matplotlib.pyplot as plt

# Scatter all trials (for reference)
trials_df = client.get_trials_data_frame()

plt.figure(figsize=(3.6, 3.6))
plt.scatter(trials_df["FE_CO"], trials_df["current_density"], color='gray', alpha=0.5, label='All Trials')

# Highlight Pareto-optimal points (red)
plt.scatter(pareto_fe_co, pareto_current_density, color='red', label='Pareto Front', marker='o')

plt.xlabel('CO Faradaic Efficiency (%)')
plt.ylabel('Current Density (mA)')
plt.title('Pareto Front Visualization')
plt.legend()
plt.grid(False)
plt.tight_layout()
plt.savefig("./Figure/ParetoFront_Filter.png", dpi = 600)
plt.show()
# %% Trajectory

import numpy as np

import matplotlib.pyplot as plt

# Get the trial data from the experiment
trials_df = client.get_trials_data_frame()

# Ensure the DataFrame contains the required columns
if "FE_CO" not in trials_df.columns or "current_density" not in trials_df.columns:
    raise ValueError("FE_CO or current_density data is missing in the trials data.")

# Sort by trial index to maintain order
trials_df.sort_index(inplace=True)

# Extract objective values
trial_indices = trials_df.index.to_list()
fe_co_values = trials_df["FE_CO"].to_list()
current_density_values = trials_df["current_density"].to_list()


#%% Plot all trials up to each step

plt.figure(figsize=(3.6, 3.6))
plt.scatter(fe_co_values, current_density_values, c=np.arange(len(fe_co_values)), cmap="viridis", alpha=0.7)
plt.xlabel('CO Faradaic Efficiency (%)')
plt.ylabel('Current Density (mA)')
plt.title('Optimization Trajectory Over Trials')
plt.colorbar(label="Trial Order")
plt.grid(True)
plt.tight_layout()
plt.savefig("./Figure/ParetoFront.png", dpi = 600)
plt.show()

# %% Trajectory

import numpy as np
import matplotlib.pyplot as plt

# Convert the trial data to NumPy arrays
fe_co_values = np.array(fe_co_values)
current_density_values = np.array(current_density_values)

# Calculate the differences to show directionality
delta_fe_co = np.diff(fe_co_values)
delta_current_density = np.diff(current_density_values)

# Start and end points for arrows (excluding last point)
start_fe_co = fe_co_values[:-1]
start_current_density = current_density_values[:-1]

# Plot the scatter points
plt.figure(figsize=(3.6, 3.6))
plt.scatter(fe_co_values, current_density_values, c=np.arange(len(fe_co_values)), cmap="viridis", alpha=0.7)
plt.colorbar(label="Trial Order")

# Add quiver arrows to indicate progress direction
plt.quiver(
    start_fe_co, start_current_density,  # Starting points of arrows
    delta_fe_co, delta_current_density,  # Differences (arrow direction)
    angles='xy', scale_units='xy', scale=1, 
    color="black", alpha=0.5, 
    width=0.005,  # Controls the thickness of the shaft
    headwidth=10,   # Increase this to make the arrowhead wider
    headlength=10,  # Increase this to make the arrowhead longer
    headaxislength=5  # Adjust arrowhead axis length for proportionality
)

# Labels and styling
plt.xlabel('CO Faradaic Efficiency (%)')
plt.ylabel('Current Density (mA)')
plt.title('Optimization Trajectory with Direction')
plt.grid(True)
plt.tight_layout()
# Save the figure
plt.savefig("./Figure/OptimizationTrajectory_Quiver.png", dpi=600)
plt.show()



# %% Now I want to visualize the data distribution and the pareto front.
# Create subplots for each parameter mapping
fig, axes = plt.subplots(2, 2, figsize=(7.2, 7.2))
axes = axes.flatten()

# Plot with CuConc as color
sc1 = axes[0].scatter(pareto_fe_co, pareto_current_density, c=pareto_Cuconc, cmap='viridis')
#axes[0].set_title('FE_CO vs Current Density (CuConc)')
axes[0].set_xlabel('CO Faradaic efficiency (%)')
axes[0].set_ylabel('Current Density (mA/cm²)')
cbar1 = plt.colorbar(sc1, ax=axes[0], orientation='vertical', pad=0.05)
cbar1.ax.xaxis.set_label_position('top')
cbar1.set_label('Cu Conc. (M)')

# Plot with Voltage as color
sc2 = axes[1].scatter(pareto_fe_co, pareto_current_density, c=pareto_Voltage, cmap='plasma')
#axes[1].set_title('FE_CO vs Current Density (Voltage)')
axes[1].set_xlabel('CO Faradaic efficiency (%)')
axes[1].set_ylabel('Current Density (mA/cm²)')
cbar2 = plt.colorbar(sc2, ax=axes[1], orientation='vertical', pad=0.05)
cbar2.ax.xaxis.set_label_position('top')
cbar2.set_label('Voltage (V)')

# Plot with Time as color
sc3 = axes[2].scatter(pareto_fe_co, pareto_current_density, c=Pareto_time, cmap='coolwarm')
#axes[2].set_title('FE_CO vs Current Density (Time)')
axes[2].set_xlabel('CO Faradaic efficiency (%)')
axes[2].set_ylabel('Current Density (mA/cm²)')
cbar3 = plt.colorbar(sc3, ax=axes[2], orientation='vertical', pad=0.05)
cbar3.ax.xaxis.set_label_position('top')
cbar3.set_label('Time (s)')

# Plot with Time as color
sc4 = axes[3].scatter(pareto_fe_co, pareto_current_density, c=pareto_co2, cmap='inferno')
#axes[3].set_title('FE_CO vs Current Density (Time)')
axes[3].set_xlabel('CO Faradaic efficiency (%)')
axes[3].set_ylabel('Current Density (mA/cm²)')
cbar4 = plt.colorbar(sc4, ax=axes[3], orientation='vertical', pad=0.05)
cbar4.ax.xaxis.set_label_position('top')
cbar4.set_label(r'CO$_2$ (%)')


# Adjust layout for better visibility
plt.tight_layout()
plt.savefig("./Figure/ParetoFront_ParameterMappings.png", dpi=600)
plt.show()
# %%
