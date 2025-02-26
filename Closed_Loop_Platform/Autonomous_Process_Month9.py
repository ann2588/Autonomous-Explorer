'''
# Last update: 01/25/2025
#
# Note: This is the version without human interaction in close-loop process in version 12/27. Pending update.
# Update:
Finalize the autonomous framework (yeah~)
'''

import sys, os, subprocess
from datetime import datetime
from tqdm import tqdm
from Closed_Loop_Platform.Communication import *
#%%
ask_user_restartPeakSimple()
# Start the server in a new terminal
start_server_in_new_terminal(server_script)
time.sleep(5)
open_terminal_to_view_log(r"C:\Users\guazh\data\server.log")
print("Main script is running...")

#%%
from Closed_Loop_Platform.DataProcessing import *
from Closed_Loop_Platform.BOtorchV2_Cu import *
from Closed_Loop_Platform.Utilities import *


#%% Machine Learning Agent setup
objectives = {
    "current_density": ObjectiveProperties(minimize=False),
    "FE_CO": ObjectiveProperties(minimize=False)
}

# Initialize manager
manager = ExperimentManager(generation_strategy=gs, parameters=parameters, objectives=objectives)
#%%
# Define thresholds using metric variables after experiment setup
thresholds = [
    ObjectiveThreshold(metric=manager.metric_current_density, bound=0, relative=False),
    ObjectiveThreshold(metric=manager.metric_fe_co, bound=0, relative=False),
]

# Apply thresholds to the optimization config
manager.ax_client.experiment.optimization_config = MultiObjectiveOptimizationConfig(
    objective=manager.ax_client.experiment.optimization_config.objective,
    objective_thresholds=thresholds,
)
#%%
# Load data
exp_data = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\experimental_conditions_cu.csv"
updated_data = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\updated_objective_data_cu.csv"
#%%
manager.load_initial_data(exp_data, updated_data)
#trial_index, next_experiment = manager.update()
#print("Dummy trial")
#print(f"Next experiment: EXP{next_experiment:04d}")
#print(f"Next condition: {trial_index}")
#%% Load DOE data
doepath = r"C:\Users\guazh\PycharmProjects\CO2Platform\Trial_Generation\DoE_randombatch3.csv"
exp_dicts = doeprocess(doepath)

def initialize_experiment(mainfold):
    """Initializes directories and logging for the experiment."""
    date = datetime.now().strftime('%Y-%m-%d')
    base_path = f'C:/Users/guazh/data/{mainfold}'
    create_directory(base_path)

    subfold = f'{date}-Initial'
    initial_path = f'{base_path}/{subfold}'
    create_directory(initial_path)

    global LOG
    log_folder = f'C:/Users/guazh/data/{mainfold}'
    LOG = LoggingSystem(log_folder = log_folder)
    LOG.create_master_logger()
    open_terminal_to_view_log(os.path.join(log_folder, 'master.log'))
    LOG.setup_logging_for_experiment('Initial')
    # Note: The GC has been connected when calling the server.
    SIGNAL = CheckSignalFromGC()
    #check_experiment_preconditions()

    messages = ['Start electrode regeneration', 'Finish electrode regeneration']
    for i, message in enumerate(messages):
        print(message)
        os.system(f'python {script_path} -m "{message}"')
        if i == 0:
            print()
            Rinsing('cell','water', 'hno3', volume_assigned='10mL', acidrinse=True, repetitions=1)

    LOG.restore_stdout()
    print("Experiment logs saved.")  # Prints to console

    return base_path
#%%
def run_experiment(exp, exp_path, expn):
    """Runs individual experiment based on given parameters."""
    print(f'Running {expn}...')

    # Stage 1: Cu Catalyst Deposition
    print('Start Cu catalyst deposition')
    PlatingSolutionFormulation(exp['CuConc'])  # Formulate DOE files
    control_co2_ar_ratio(0, flowrate=1)
    stirring(plate, 60)
    deposit_v, deposit_t = exp['Volt'], exp['Time']

    electrodeposition(exp_path, f'{expn}', deposit_v, deposit_t)
    control_co2_ar_ratio(0, flowrate=1)
    Rinsing('cell', 'spelec', 'water', 1)
    print('Finish Cu catalyst deposition')
    os.system(f'python {script_path} -m "{"Finish Cu catalyst deposition"}"')

    # Stage 2: Electrolyte Preparation
    #il_values = {key: exp[key] for key in ['IL1', 'IL2', 'IL3', 'IL4', 'IL5']}
    #print('Preparing Electrolyte for bulk electrolysis...')
    #Elelectrolyte_Formulation(il_values) #
    control_co2_ar_ratio(0, flowrate=1)
    Rinsing('cell', 'electrolyte', 'electrolyte', 1, from_voir=False)
    os.system(f'python {script_path} -m "{"Finish Electrolyte Formulation"}"')

    # Stage 3: Bulk Electrolysis
    plate.start_stirring()
    close_all_gas()

    #run_CV_HER_varyE(exp_path, sample=expn, gas=f"{exp['CO2ratio']}CO2", sr_cv=50)
    control_co2_ar_ratio(exp['CO2ratio'], flowrate=10)
    time.sleep(180) # Necessary. DO NOT CHANGE
    print('Purging gas for 3 minutes')

    voltage = -2.0

    SendCommandToGC("Is GC still running?")
    time.sleep(5)
    if wait_for_gc_signal():
        print("GC finished measurement. Proceed to next experiment.")
    execute_bulk_electrolysis(exp, exp_path, expn, voltage)

    # Stage 4: Electrode regeneration
    messages = ['Start electrode regeneration', 'Finish electrode regeneration']
    for i, message in enumerate(messages):
        print(message)
        os.system(f'python {script_path} -m "{message}"')
        if i == 0:
            close_all_gas()
            Rinsing('cell','water', 'hno3', volume_assigned='10mL', acidrinse=True, repetitions=1)
            print('skip')

    #plate.start_stirring()
    #Rinsing('cell', 'water', 'water', 1)
    #Rinsing('voir', 'water', 'water', 1)


def execute_bulk_electrolysis(exp, exp_path, expn, voltage):
    """Executes bulk electrolysis for a specific voltage."""
    print(f"Running experiment with CO2/Ar ratio {exp['CO2ratio']}%.")

    read_all_gas()
    svoltage = str(voltage).replace('.', 'p')
    SendCommandToGC(f"Loading Control Files, subfolder: {exp_path}, filename: {expn}_{int(exp['CO2ratio'])}CO2_{svoltage}")

    if wait_for_gc_signal():
        SendCommandToGC("Wait 360 second and start 1 sample Injections")
        plate.start_stirring()
        bulk_electrolysis_CP(exp_path, sample=expn, E_ed=voltage, note=f"{int(exp['CO2ratio'])}CO2_{svoltage}", Time_ed = 400)

    if wait_for_gc_signal(timeout = 600):
        print("GC is running, proceed to next action.") #Assume at this moment the GC is running the second injection.
    else:
        print("Hey, GC is not running!!!")
        os.system(f'python {script_path} -m "GC is not running, check it out."')


def wait_for_gc_signal(timeout=300):
    """Waits for GC signal with a timeout."""
    start_time = time.time()
    SIGNAL = CheckSignalFromGC()
    while not SIGNAL:
        if time.time() - start_time > timeout:
            logging.error("Timeout: GC did not respond within the timeout period.")
            os.system(f'python {script_path} -m "Timeout: GC did not respond in time."')
            return False
        time.sleep(10)
        SIGNAL = CheckSignalFromGC()
    return True

#%%
def CO2Optimizer(mainfold, initialization=True):
    """Main function to orchestrate the CO2 optimization experiments."""
    if initialization:
        global base_path
        base_path = initialize_experiment(mainfold)
        print()
    else:
        base_path = f'C:/Users/guazh/data/{mainfold}'
        # base_path = f'/Users/Yi-An/Documents/000_Project/044_FAARM_PA-004/Data/{mainfold}'
        create_directory(base_path)
        global LOG
        log_folder = f'C:/Users/guazh/data/{mainfold}'
        LOG = LoggingSystem(log_folder=log_folder)
        LOG.create_master_logger()
        open_terminal_to_view_log(os.path.join(log_folder, 'master.log'))
        # Note: The GC has been connected when calling the server.
        SIGNAL = CheckSignalFromGC()
        #check_experiment_preconditions()

        DPAgent.master_folder = base_path

    for i in range(5):
        global trial_index, next_experiment, exp, expn, exp_path, bulk_electrolysis_potential, current_density, FECO
        trial_index, next_experiment = manager.update() #suggest next experiment
        exp = trial_index
        expn = f'EXP{next_experiment:04d}'
        LOG.setup_logging_for_experiment(expn)
        # Display the fetched parameters
        print(f"Next experiment: EXP{next_experiment:04d}")
        print(f"Next condition: {trial_index}")
        subfold = f'{expn}'
        exp_path = f"{base_path}/{subfold}"
        print(exp_path)
        create_directory(exp_path)
        DPAgent.master_folder = base_path

        print("------Data Collection Start------")
        run_experiment(exp, exp_path, expn)
        print("------Data Collection Finished---")
        print(f"Experiment number: {expn}")
        print(f"Experiment for {expn}: {trial_index}")
        DPAgent.exp_num = int(expn[3:])

        bulk_electrolysis_potential, current_density, FECO = DPAgent.encode(trial_index) # Data processing
        manager.ax_client.complete_trial(
            trial_index=DPAgent.exp_num-1,  # Use the iteration index as the trial index, zero based
            raw_data={
                # Provide the value and its variance (None here)
                "current_density": (current_density*FECO/100, None),
                "FE_CO": (FECO, None)
            }
        )
        # Print the results of the completed trial
        result_summary = (
            f"{expn} completed with:\n  bulk_electrolysis_potential: {bulk_electrolysis_potential} V vs Ag/AgCl\n  partial_current_density: {current_density*FECO/100:.1f} mA\n  FE_CO: {FECO:.1f} %"
        )
        result_summary2 = (
            f"{expn} completed with:  bulk_electrolysis_potential: {bulk_electrolysis_potential} V vs Ag/AgCl;  partialcurrent_density: {current_density*FECO/100:.1f} mA;  FE_CO: {FECO:.1f} %"
        )

        print(result_summary)
        print("------------------------------------------------")

        os.system(f'python {script_path} -m "{expn} completed. result:{result_summary2}"')

    # Final rinsing
    Rinsing('cell', 'water', 'water', 3)

    print('Experiment completed')
    os.system(f'python {script_path} -m "{message_completed}"')


# Example Usage
#%%
if __name__ == "__main__":
    #%%
    main_folder = 'Month9_Run17_Cu_2p0V' # Check why no flow into GC. check if the tube flow into GC stuck. Check the quick connection.
    DPAgent = DataProcessing()

    #%%
    time.sleep(1200)
    CO2Optimizer(main_folder, initialization=False)

    # to extract the data stored in manager
    # Get completed trial data
    experiment = manager.ax_client.experiment
    trials = experiment.trials
    # Collect data
    records = []
    for trial_index, trial in trials.items():
        if trial.status.is_completed:
            params = trial.arm.parameters
            results = trial.fetch_data().df
            for _, row in results.iterrows():
                record = {"trial_index": trial_index, **params, **row.to_dict()}
                records.append(record)

    # Create a DataFrame
    results_df = pd.DataFrame(records)
    print(results_df)