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
    ObjectiveThreshold(metric=manager.metric_current_density, bound=0, relative=False),
    ObjectiveThreshold(metric=manager.metric_fe_co, bound=0, relative=False),
]

# Apply thresholds to the optimization config

manager.ax_client.experiment.optimization_config = MultiObjectiveOptimizationConfig(
    objective=manager.ax_client.experiment.optimization_config.objective,
    objective_thresholds=thresholds,
)
optimization_conFig = manager.ax_client.experiment.optimization_config

client = manager.ax_client
# Load your experiment if needed
exp_condition_file = "/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/experimental_conditions_cuil.csv"
objective_file = "/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/updated_objective_data_cuil.csv"
manager.load_initial_data(exp_condition_file,objective_file)
df_x = pd.read_csv(exp_condition_file, header=1)
df_x.rename(columns={"Cu": "CuConc", "Blank": "blank"}, inplace=True)
df_y = pd.read_csv(objective_file, header=0)
# Partial current density processing
# Multiply current density by the value of (average CO)/100 at the same row
#df_y['Average Current Density'] = df_y['Average Current Density'] * (df_y#['Average CO'] / 100)


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

plt.figure(figsize=(3.2, 3.2))
plt.scatter(trials_df["FE_CO"], trials_df["current_density"], color='gray', alpha=0.5, label='All Trials')

# Highlight Pareto-optimal points (red)
plt.scatter(pareto_fe_co, pareto_current_density, color='red', label='Pareto Front', marker='o')

plt.xlabel('CO Faradaic Efficiency (%)')
plt.ylabel('P. C. D. (mA/cm²)')
plt.title('Pareto Front Visualization')
plt.legend()
plt.grid(False)
plt.tight_layout()
plt.savefig("./Figure/ParetoFront_Filter_M8_CuIL_.png", dpi = 600)
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
Cuconc_values = trials_df['CuConc'].to_list()
time_values = trials_df['Time'].to_list()
volatage_values = trials_df['Volt'].to_list()
co2_values = trials_df['CO2ratio'].to_list()


#%% Plot all trials up to each step

plt.figure(figsize=(3.6, 3.6))
plt.scatter(fe_co_values, current_density_values, c=np.arange(len(fe_co_values)), cmap="viridis", alpha=0.7)
plt.xlabel('CO Faradaic Efficiency (%)')
plt.ylabel('P. C. D. (mA/cm²)')
plt.title('Optimization Trajectory Over Trials')
plt.colorbar(label="Trial Order")
plt.grid(True)
plt.tight_layout()
plt.savefig("./Figure/ParetoFront_M8_CuIL_.png", dpi = 600)
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
plt.ylabel('P. C. D. (mA/cm²)')
plt.title('Optimization Trajectory with Direction')
plt.grid(True)
plt.tight_layout()
# Save the figure
plt.savefig("./Figure/OptimizationTrajectory_Quiver_M8_CuIL_.png", dpi=600)
plt.show()


# %% Now I want to visualize the data distribution and the pareto front.
# Create subplots for each parameter mapping
fig, axes = plt.subplots(2, 2, figsize=(7.2, 7.2))
axes = axes.flatten()

# Plot with CuConc as color
sc1 = axes[0].scatter(pareto_fe_co, pareto_current_density, c=pareto_Cuconc, cmap='viridis')
#axes[0].set_title('FE_CO vs Current Density (CuConc)')
axes[0].set_xlabel('FE_CO (%)')
axes[0].set_ylabel('P. C. D. (mA/cm²)')
cbar1 = plt.colorbar(sc1, ax=axes[0], orientation='vertical', pad=0.05)
cbar1.ax.xaxis.set_label_position('top')
cbar1.set_label('Cu Conc. (M)')

# Plot with Voltage as color
sc2 = axes[1].scatter(pareto_fe_co, pareto_current_density, c=pareto_Voltage, cmap='plasma')
#axes[1].set_title('FE_CO vs Current Density (Voltage)')
axes[1].set_xlabel('CO Faradaic efficiency')
axes[1].set_ylabel('P. C. D. (mA/cm²)')
cbar2 = plt.colorbar(sc2, ax=axes[1], orientation='vertical', pad=0.05)
cbar2.ax.xaxis.set_label_position('top')
cbar2.set_label('Voltage (V)')

# Plot with Time as color
sc3 = axes[2].scatter(pareto_fe_co, pareto_current_density, c=Pareto_time, cmap='coolwarm')
#axes[2].set_title('FE_CO vs Current Density (Time)')
axes[2].set_xlabel('FE_CO (%)')
axes[2].set_ylabel('P. C. D. (mA/cm²)')
cbar3 = plt.colorbar(sc3, ax=axes[2], orientation='vertical', pad=0.05)
cbar3.ax.xaxis.set_label_position('top')
cbar3.set_label('Time (s)')

# Plot with Time as color
sc4 = axes[3].scatter(pareto_fe_co, pareto_current_density, c=pareto_co2, cmap='inferno')
#axes[3].set_title('FE_CO vs Current Density (Time)')
axes[3].set_xlabel('FE_CO (%)')
axes[3].set_ylabel('P. C. D. (mA/cm²)')
cbar4 = plt.colorbar(sc4, ax=axes[3], orientation='vertical', pad=0.05)
cbar4.ax.xaxis.set_label_position('top')
cbar4.set_label('CO2 %')


# Adjust layout for better visibility
plt.tight_layout()
plt.show()
# %%




#%% All

trial_indices = trials_df.index.to_list()
fe_co_values = trials_df["FE_CO"].to_list()
current_density_values = trials_df["current_density"].to_list()
Cuconc_values = trials_df['CuConc'].to_list()
time_values = trials_df['Time'].to_list()
volatage_values = trials_df['Volt'].to_list()
co2_values = trials_df['CO2ratio'].to_list()


# %% I want to visualize the data distribution and the pareto front.
# Create subplots for each parameter mapping
fig, axes = plt.subplots(2, 2, figsize=(7.2, 7.2))
axes = axes.flatten()

# Plot with CuConc as color
sc1 = axes[0].scatter(fe_co_values, current_density_values, c=Cuconc_values, cmap='viridis')
#axes[0].set_title('FE_CO vs Current Density (CuConc)')
axes[0].set_xlabel('CO Faradaic efficiency (%)')
axes[0].set_ylabel('P. C. D. (mA/cm²)')
cbar1 = plt.colorbar(sc1, ax=axes[0], orientation='vertical', pad=0.05)
cbar1.ax.xaxis.set_label_position('top')
cbar1.set_label('Cu Conc. (M)')

# Plot with Voltage as color
sc2 = axes[1].scatter(fe_co_values, current_density_values, c=volatage_values, cmap='plasma')
#axes[1].set_title('FE_CO vs Current Density (Voltage)')
axes[1].set_xlabel('CO Faradaic efficiency')
axes[1].set_ylabel('P. C. D. (mA/cm²)')
cbar2 = plt.colorbar(sc2, ax=axes[1], orientation='vertical', pad=0.05)
cbar2.ax.xaxis.set_label_position('top')
cbar2.set_label('Voltage (V)')

# Plot with Time as color
sc3 = axes[2].scatter(fe_co_values, current_density_values, c=time_values, cmap='coolwarm')
#axes[2].set_title('FE_CO vs Current Density (Time)')
axes[2].set_xlabel('CO Faradaic efficiency (%)')
axes[2].set_ylabel('P. C. D. (mA/cm²)')
cbar3 = plt.colorbar(sc3, ax=axes[2], orientation='vertical', pad=0.05)
cbar3.ax.xaxis.set_label_position('top')
cbar3.set_label('Time (s)')

# Plot with CO2 as color
sc4 = axes[3].scatter(fe_co_values, current_density_values, c=co2_values, cmap='inferno')
#axes[3].set_title('FE_CO vs Current Density (CO2)')
axes[3].set_xlabel('CO Faradaic efficiency (%)')
axes[3].set_ylabel('P. C. D. (mA/cm²)')
cbar4 = plt.colorbar(sc4, ax=axes[3], orientation='vertical', pad=0.05)
cbar4.ax.xaxis.set_label_position('top')
cbar4.set_label(r'CO$_2$ (%)')


# Adjust layout for better visibility
plt.tight_layout()
plt.savefig("./Figure/ParetoFront_M8_CuIL_ParameterMappings.png", dpi=600)
plt.show()


#%% ternary plot, with quiver
import matplotlib.pyplot as plt
import ternary
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from ternary.helpers import project_point

# Prepare and normalize data with specific ranges:
data = df_x[['CuConc', 'Volt', 'Time']]

# Define custom normalization ranges
ranges = {
    'CuConc': (0.2, 0.5),    # 0.2 to 0.5
    'Volt': (-1.0, -0.3),    # -0.3 to -1.0
    'Time': (40, 500)        # 40 to 500
}

# Custom normalization function
data_normalized = pd.DataFrame()
for col in data.columns:
    min_val, max_val = ranges[col]
    data_normalized[col] = (data[col] - min_val) / (max_val - min_val)

# Convert to percentages and ensure the sum equals 100
data_final = data_normalized.div(data_normalized.sum(axis=1), axis=0) * 100
points = list(zip(data_final["CuConc"], data_final["Volt"], data_final["Time"]))

# Normalize CO Faradaic Efficiency for color mapping
co_values = df_y['Average CO']
norm = mcolors.Normalize(vmin=min(co_values), vmax=max(co_values))
colors = cm.plasma(norm(co_values))  # Convert CO values to RGBA colors


# Define custom formatter functions for each axis.
def cuconc_formatter(tick):
    min_CuConc, max_CuConc = 0.2, 0.5
    orig = tick/100 * (max_CuConc - min_CuConc) + min_CuConc
    return f"{orig:.2f}"

def volt_formatter(tick):
    min_Volt, max_Volt = -1.0, -0.3
    orig = tick/100 * (max_Volt - min_Volt) + min_Volt
    return f"{orig:.2f}"

def time_formatter(tick):
    min_Time, max_Time = 40, 500
    orig = tick/100 * (max_Time - min_Time) + min_Time
    return f"{orig:.0f}"

# Create dictionaries mapping tick values to formatted strings.
tick_values = np.arange(0, 101, 10)
tick_labels_cuconc = {tick: cuconc_formatter(tick) for tick in tick_values}
tick_labels_volt   = {tick: volt_formatter(tick) for tick in tick_values}
tick_labels_time   = {tick: time_formatter(tick) for tick in tick_values}

# Create ternary plot with scale=100
fig, tax = ternary.figure(scale=100)


# (Optional) Remove Matplotlib axis
tax.clear_matplotlib_ticks()
tax.get_axes().axis('off')
# Note: Not calling tax.get_axes().axis('off') so we can see our custom tick labels.

# Plot formatting: boundary, gridlines, title, and axis labels (using original scale descriptions)
tax.boundary(linewidth=1.0)
tax.gridlines(multiple=10, color="gray", alpha=0.3)
tax.set_title("Parameter Space Distribution", fontsize=12, y=1.0)
tax.left_axis_label("Voltage (original scale)", fontsize=10 , offset=0.15)
tax.right_axis_label("Time (original scale)", fontsize=10, offset=0.15)
tax.bottom_axis_label("Cu Conc. (original scale)", fontsize=10, offset=0.05)

# Get the underlying Matplotlib axes for manual annotation.
ax = tax.get_axes()

# Manually annotate tick labels along each edge.
# We'll use tick values from 0 to 100 in steps of 10.
tick_vals = np.arange(0, 101, 10)

# For bottom axis (corresponding to Cu Conc.):
# The bottom edge runs from (100, 0, 0) to (0, 0, 100) in ternary coordinates.
for t in tick_vals:
    # Linear interpolation along the bottom edge: point = (t, 0, 100-t)
    point_b = (t, 0, 100 - t)
    cart_b = project_point(point_b)
    label_b = cuconc_formatter(t)
    # Adjust y offset as needed (here, subtract a small amount)
    ax.text(cart_b[0], cart_b[1] - 5, label_b,
            horizontalalignment='center', fontsize=8, color='black')

# For left axis (corresponding to Voltage):
# The left edge runs from (0, 100, 0) to (0, 0, 100).
for t in tick_vals:
    point_l = (0, t, 100 - t)
    cart_l = project_point(point_l)
    label_l = volt_formatter(t)
    # Adjust x offset as needed (here, subtract a small amount)
    ax.text(cart_l[0] - 5, cart_l[1], label_l,
            horizontalalignment='center', fontsize=8, color='black')

# For right axis (corresponding to Time):
# The right edge runs from (100, 0, 0) to (0, 100, 0).
for t in tick_vals:
    point_r = (t, 100 - t, 0)
    cart_r = project_point(point_r)
    label_r = time_formatter(t)
    # Adjust y offset as needed (here, add a small amount)
    ax.text(cart_r[0]+5, cart_r[1], label_r,
            horizontalalignment='center', fontsize=8, color='black')

# Optionally, add arrow annotations to indicate the direction of increasing values.
# For bottom axis (Cu Conc.): arrow from (90,10,0) to (100,0,0)
#ax.annotate("", xy=project_point((100, 0, 0)), xytext=project_point((90, 10, 0)),
#            arrowprops=dict(arrowstyle="->", color="black", lw=2))
# For right axis (Time): arrow from (10,90,0) to (0,100,0)
#ax.annotate("", xy=project_point((0, 100, 0)), xytext=project_point((10, 90, 0)),
#            arrowprops=dict(arrowstyle="->", color="black", lw=2))
# For left axis (Voltage): arrow from (0,10,90) to (0,0,100)
#ax.annotate("", xy=project_point((0, 0, 100)), xytext=project_point((0, 10, 90)),
#            arrowprops=dict(arrowstyle="->", color="black", lw=2))

# Plot data points with manually assigned colors
ax = tax.get_axes()

# Plot points and draw arrows between consecutive points
for i, (point, color) in enumerate(zip(points, colors)):
    if i < len(points) - 1:
        # Convert ternary coordinates to Cartesian coordinates
        p1 = project_point(point)
        p2 = project_point(points[i + 1])
        # Compute vector in Cartesian space
        vector = np.array(p2) - np.array(p1)
        # Draw arrow using Matplotlib's quiver with lower zorder
        ax.quiver(p1[0], p1[1], vector[0], vector[1],
                  color='gray', width=0.005,  # Thinner, gray arrow
                  angles='xy', scale_units='xy', scale=1, zorder=1)
    # Plot scatter points with a higher zorder so they appear above the arrows
    tax.scatter([point], marker='o', color=color, alpha=0.6, s=80, zorder=10)

# Create a colorbar manually using ScalarMappable
sm = cm.ScalarMappable(cmap="plasma", norm=norm)
sm.set_array([])  # Necessary for the colorbar
cbar = plt.colorbar(sm, ax=ax, orientation="vertical", pad=0.1)
cbar.set_label('CO Faradaic Efficiency (%)', fontsize=10)

plt.tight_layout()
plt.savefig("./Figure/Ternery_IL_quiver_CuIL.png")
tax.show()

#%% ternary plot, without quiver
import matplotlib.pyplot as plt
import ternary
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from ternary.helpers import project_point

# Prepare and normalize data with specific ranges:
data = df_x[['CuConc', 'Volt', 'Time']]

# Define custom normalization ranges
ranges = {
    'CuConc': (0.2, 0.5),    # 0.2 to 0.5
    'Volt': (-1.0, -0.3),    # -0.3 to -1.0
    'Time': (40, 500)        # 40 to 500
}

# Custom normalization function
data_normalized = pd.DataFrame()
for col in data.columns:
    min_val, max_val = ranges[col]
    data_normalized[col] = (data[col] - min_val) / (max_val - min_val)

# Convert to percentages and ensure the sum equals 100
data_final = data_normalized.div(data_normalized.sum(axis=1), axis=0) * 100
points = list(zip(data_final["CuConc"], data_final["Volt"], data_final["Time"]))

# Normalize CO Faradaic Efficiency for color mapping
co_values = df_y['Average CO']
norm = mcolors.Normalize(vmin=min(co_values), vmax=max(co_values))
colors = cm.plasma(norm(co_values))  # Convert CO values to RGBA colors

# Get original min and max for each variable (for tick conversion)
min_CuConc, max_CuConc = df_x['CuConc'].min(), df_x['CuConc'].max()
min_Volt,   max_Volt   = df_x['Volt'].min(),   df_x['Volt'].max()
min_Time,   max_Time   = df_x['Time'].min(),   df_x['Time'].max()

# Define custom formatter functions for each axis.
def cuconc_formatter(tick):
    min_CuConc, max_CuConc = 0.2, 0.5
    orig = tick/100 * (max_CuConc - min_CuConc) + min_CuConc
    return f"{orig:.2f}"

def volt_formatter(tick):
    min_Volt, max_Volt = -1.0, -0.3
    orig = tick/100 * (max_Volt - min_Volt) + min_Volt
    return f"{orig:.2f}"

def time_formatter(tick):
    min_Time, max_Time = 40, 500
    orig = tick/100 * (max_Time - min_Time) + min_Time
    return f"{orig:.0f}"

# Create dictionaries mapping tick values to formatted strings.
tick_values = np.arange(0, 101, 10)
tick_labels_cuconc = {tick: cuconc_formatter(tick) for tick in tick_values}
tick_labels_volt   = {tick: volt_formatter(tick) for tick in tick_values}
tick_labels_time   = {tick: time_formatter(tick) for tick in tick_values}



# Create ternary plot with scale=100
fig, tax = ternary.figure(scale=100)


# (Optional) Remove Matplotlib axis
tax.clear_matplotlib_ticks()
tax.get_axes().axis('off')
# Note: Not calling tax.get_axes().axis('off') so we can see our custom tick labels.

# Plot formatting: boundary, gridlines, title, and axis labels (using original scale descriptions)
tax.boundary(linewidth=1.0)
tax.gridlines(multiple=10, color="gray", alpha=0.5)
tax.set_title("Parameter Space Distribution", fontsize=12, y=1)
tax.left_axis_label("Voltage (original scale)", fontsize=10 , offset=0.15)
tax.right_axis_label("Time (original scale)", fontsize=10, offset=0.15)
tax.bottom_axis_label("Cu Conc. (original scale)", fontsize=10, offset=0.05)

# Get the underlying Matplotlib axes for manual annotation.
ax = tax.get_axes()

# Manually annotate tick labels along each edge.
# We'll use tick values from 0 to 100 in steps of 10.
tick_vals = np.arange(0, 101, 10)

# For bottom axis (corresponding to Cu Conc.):
# The bottom edge runs from (100, 0, 0) to (0, 0, 100) in ternary coordinates.
for t in tick_vals:
    # Linear interpolation along the bottom edge: point = (t, 0, 100-t)
    point_b = (t, 0, 100 - t)
    cart_b = project_point(point_b)
    label_b = cuconc_formatter(t)
    # Adjust y offset as needed (here, subtract a small amount)
    ax.text(cart_b[0], cart_b[1] - 5, label_b,
            horizontalalignment='center', fontsize=8, color='black')

# For left axis (corresponding to Voltage):
# The left edge runs from (0, 100, 0) to (0, 0, 100).
for t in tick_vals:
    point_l = (0, t, 100 - t)
    cart_l = project_point(point_l)
    label_l = volt_formatter(t)
    # Adjust x offset as needed (here, subtract a small amount)
    ax.text(cart_l[0] - 5, cart_l[1], label_l,
            horizontalalignment='center', fontsize=8, color='black')

# For right axis (corresponding to Time):
# The right edge runs from (100, 0, 0) to (0, 100, 0).
for t in tick_vals:
    point_r = (t, 100 - t, 0)
    cart_r = project_point(point_r)
    label_r = time_formatter(t)
    # Adjust y offset as needed (here, add a small amount)
    ax.text(cart_r[0]+5, cart_r[1], label_r,
            horizontalalignment='center', fontsize=8, color='black')

# Plot data points with manually assigned colors
ax = tax.get_axes()

# Plot points and draw arrows between consecutive points
# Plot data points with manually assigned colors
for point, color in zip(points, colors):
    tax.scatter([point], marker='o', color=color, alpha=0.6, s=80)

# Create a colorbar manually using ScalarMappable
sm = cm.ScalarMappable(cmap="plasma", norm=norm)
sm.set_array([])  # Necessary for the colorbar
cbar = plt.colorbar(sm, ax=ax, orientation="vertical", pad=0.1)
cbar.set_label('CO Faradaic Efficiency (%)', fontsize=10)

plt.tight_layout()
plt.savefig("./Figure/Ternery_CuIL.png", dpi = 600)
tax.show()
# %%
