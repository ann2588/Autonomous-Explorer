'''
# Last update: 03/17/2025, DDL: 03/26/2025
#
# Note:
# Update:
# Todo:
# X Power Intermittance Optimization Script #Currently conduct catalysis, and wait under open circuit for 15 minute, then do the catalysis again with product characterization (Pending testing)
# X Make sure GC Column Baking Column every 10 trials (Pending Testing)
# X Pull out the Constraint setting. Modify them in the script
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
from Closed_Loop_Platform.BOtorchV2_Month7 import *
from Closed_Loop_Platform.Utilities import *


#%% Machine Learning Agent setup. Modify your constraint and objective according to your need
objectives = {
    "current_density": ObjectiveProperties(minimize=False),
    "FE_CO": ObjectiveProperties(minimize=False)
}

parameters = [
    {"name": "CuConc", "type": "choice", "values": [round(v, 2) for v in [0.2, 0.3, 0.4, 0.5]], "is_ordered": False},
    {"name": "Volt", "type": "choice", "values": [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3], "is_ordered": False},
    {"name": "Time", "type": "choice", "values": list(range(40, 500, 1)), "is_ordered": False},
    {"name": "CO2ratio", "type": "choice", "values": list(range(100, 101, 1)), "is_ordered": False},
    {"name": "IL1", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
    {"name": "IL2", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
    {"name": "IL3", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
    {"name": "IL4", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
    {"name": "IL5", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
    {"name": "blank", "type": "choice", "values": list(range(0, 20, 1)), "is_ordered": False},
]

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
#%
# Load data
exp_data = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\experimental_conditions_cuil.csv"
updated_data = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\updated_objective_data_cuil.csv"
#%%
manager.load_initial_data(exp_data, updated_data)
'''
trial_index, next_experiment = manager.update()
print("Dummy trial")
print(f"Next experiment: EXP{next_experiment:04d}")
print(f"Next condition: {trial_index}")
exp = trial_index
'''
#% Load DOE data
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
def check_gc_status():
    """
    Function to check if the GC is still running.
    Continues checking every minute until 'finished' is received.
    Use this command when the execution of next action need the confirmation that GC is not running
    """
    while True:
        time.sleep(5)  # Wait for server response
        SendCommandToGC("Is GC still running?")
        time.sleep(5)  # Wait for server response

        T, res= wait_for_gc_signal()  # Store response
        print(res)
        if not T:
            print("No response from GC. Retrying...")
            continue  # Retry if no response

        if "finished" in str(res).lower():
            print("GC finished measurement. Proceeding to the next experiment.")
            break  # Exit the loop and proceed

        elif "still" in str(res).lower():
            print("GC is still running. Waiting another 3 minute before rechecking...")
            time.sleep(180)  # Wait for another minute before checking again
        else:
            print(f"Unexpected response from GC: {res}. Retrying...")
#%%
def run_experiment(exp, exp_path, expn, trialamount):
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
    close_all_gas()
    il_values = {key: exp[key] for key in ['IL1', 'IL2', 'IL3', 'IL4', 'IL5']}
    print('Preparing Electrolyte for bulk electrolysis...')
    Elelectrolyte_Formulation(il_values) #
    control_co2_ar_ratio(0, flowrate=1)
    #Rinsing('cell', 'electrolyte', 'electrolyte', 1, from_voir=False)
    os.system(f'python {script_path} -m "{"Finish Electrolyte Formulation"}"')

    # Stage 3: Bulk Electrolysis
    plate.start_stirring()
    close_all_gas()

    #run_CV_HER_varyE(exp_path, sample=expn, gas=f"{exp['CO2ratio']}CO2", sr_cv=50)
    control_co2_ar_ratio(exp['CO2ratio'], flowrate=5)
    time.sleep(180) # Necessary. DO NOT CHANGE
    print('Purging gas for 3 minutes')

    voltage = -2.0
    svoltage = str(voltage).replace('.', 'p')

    # Preactivate the catalyst, ocp for 15 minute
    bulk_electrolysis_CP(exp_path, sample=expn, E_ed=voltage, note=f"Pre_{int(exp['CO2ratio'])}CO2_{svoltage}", Time_ed = 400)
    close_all_gas()
    time.sleep(900) # Simulating

    #The real catalysis
    control_co2_ar_ratio(exp['CO2ratio'], flowrate=5)
    time.sleep(180) # Necessary. DO NOT CHANGE
    print('Purging gas for 3 minutes')
    time.sleep(2)
    check_gc_status()
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

    # Bake the column every 10 trials
    if trialamount % 10 == 0 and trialamount != 0:
        print(f'{trialamount} trials reached. GC start baking')
        time.sleep(5)
        check_gc_status()
        print("GC finished measurement. Proceed to next action.")
        SendCommandToGC("Baking")
        os.system(f'python {script_path} -m "10th trial reached. GC start to bake column"')
    else:
        print(f'{trialamount} trials reached. No need for baking yet.')

    #plate.start_stirring()
    #Rinsing('cell', 'water', 'water', 1)
    #Rinsing('voir', 'water', 'water', 1)

#%%
def execute_bulk_electrolysis(exp, exp_path, expn, voltage):
    """Executes bulk electrolysis for a specific voltage."""
    print(f"Running experiment with CO2/Ar ratio {exp['CO2ratio']}%.")

    read_all_gas()
    svoltage = str(voltage).replace('.', 'p')
    SendCommandToGC(f"Loading Control Files, subfolder: {exp_path}, filename: {expn}_{int(exp['CO2ratio'])}CO2_{svoltage}")
    time.sleep(5)
    T3, _ = CheckSignalFromGC()
    T3 = True

    if "unavailable" in _:
        time.sleep(5)
        SendCommandToGC(f"Loading Control Files, subfolder: {exp_path}, filename: {expn}_{int(exp['CO2ratio'])}CO2_{svoltage}")
        T3, _ = wait_for_gc_signal()
        T3 = True

    if T3:
        time.sleep(5)
        SendCommandToGC("Wait 360 second and start 1 sample Injections")
        time.sleep(5)
        plate.start_stirring()
        bulk_electrolysis_CP(exp_path, sample=expn, E_ed=voltage, note=f"{int(exp['CO2ratio'])}CO2_{svoltage}", Time_ed = 400)
    T2, _ = wait_for_gc_signal(timeout = 600)
    if T2:
        print("GC is running, proceed to next action.") #Assume at this moment the GC is running the second injection.
    else:
        print("Hey, GC is not running!!!")
        os.system(f'python {script_path} -m "GC is not running, check it out."')
#%%
def wait_for_gc_signal(timeout=300):
    """Waits for GC signal with a timeout."""
    start_time = time.time()
    T, SIGNAL = CheckSignalFromGC()
    if "unavailable" in SIGNAL:
        SendCommandToGC("Is GC still running?")
        T, SIGNAL = CheckSignalFromGC()

    while not T:
        if time.time() - start_time > timeout:
            logging.error("Timeout: GC did not respond within the timeout period.")
            SIGNAL = "Timeout"
            os.system(f'python {script_path} -m "Timeout: GC did not respond in time."')
            return False, SIGNAL

        time.sleep(10)
        T, SIGNAL = CheckSignalFromGC()
    return T, SIGNAL

#%%
def CO2Optimizer(mainfold:str, num_trials:int, initialization=True):

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
        time.sleep(2)


        DPAgent.master_folder = base_path

    for i in range(num_trials):

        global trial_index, next_experiment, exp, expn, exp_path, bulk_electrolysis_potential, current_density, FECO
        trial_index, next_experiment = manager.update() #suggest next experiment
        exp = trial_index
        expn = f'EXP{next_experiment:04d}'
        LOG.setup_logging_for_experiment(expn)
        # Display the fetched parameters
        time.sleep(5)
        check_gc_status()
        print(f"Next experiment: EXP{next_experiment:04d}")
        print(f"Next condition: {trial_index}")
        subfold = f'{expn}'
        exp_path = f"{base_path}/{subfold}"
        print(exp_path)
        create_directory(exp_path)
        DPAgent.master_folder = base_path

        print("------Data Collection Start------")
        run_experiment(exp, exp_path, expn, i)
        print("------Data Collection Finished---")

        #%
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
    main_folder = 'Month9_Run13_2p0V_power' # Check why no flow into GC. check if the tube flow into GC stuck. Check the quick connection.
    DPAgent = DataProcessing()
    CO2Optimizer(main_folder, num_trials = 10, initialization=False)
