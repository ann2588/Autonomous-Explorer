#%%
'''
# Last update: 12/30/2024
# Note: 
# Update:
Debugging. Update the liquid handling version with electrolyte chamber connected to
Fix the bulk electrolysis error
'''

import sys, os, subprocess
from datetime import datetime
from tqdm import tqdm
from Closed_Loop_Platform.Communication import *

ask_user_restartPeakSimple()
# Start the server in a new terminal
start_server_in_new_terminal(server_script)
time.sleep(5)
open_terminal_to_view_log(r"C:\Users\guazh\data\server.log")
print("Main script is running...")


from Closed_Loop_Platform.DataProcessing import *
from Closed_Loop_Platform.BOtorchV2 import *
from Closed_Loop_Platform.Utilities import *

# Load offline data
exp_data = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\experimental_conditions.csv"
updated_data = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\updated_objective_data.csv"
# Load DoE Data
doepath = r"C:\Users\guazh\PycharmProjects\CO2Platform\Trial_Generation\DoE_randombatch3.csv"
exp_dicts = doeprocess(doepath)
#%%

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
    check_experiment_preconditions()

    messages = ['Start electrode regeneration', 'Finish electrode regeneration']
    for i, message in enumerate(messages):
        print(message)
        os.system(f'python {script_path} -m "{message}"')
        if i == 0:
            print()
            insitu_echem_regeneration(initial_path)

    LOG.restore_stdout()
    print("Experiment logs saved.")  # Prints to console

    return base_path

def run_experiment(exp, exp_path, expn):
    """Runs individual experiment based on given parameters."""
    print(f'Running {expn}...')

    # Stage 1: Cu Catalyst Deposition
    print('Start Cu catalyst deposition')
    PlatingSolutionFormulation(exp['CuConc'])  # Formulate DOE files
    control_co2_ar_ratio(0)
    stirring(plate, 60)
    deposit_v, deposit_t = exp['Volt'], exp['Time']

    electrodeposition(exp_path, f'{expn}Deposition', deposit_v, deposit_t)
    Rinsing('cell', 'spelec', 'spelec', 1)
    print('Finish Cu catalyst deposition')

    # Stage 2: Electrolyte Preparation
    il_values = {key: exp[key] for key in ['IL1', 'IL2', 'IL3', 'IL4', 'IL5']}
    print('Preparing Electrolyte for bulk electrolysis...')
    Elelectrolyte_Formulation(il_values) #

    # Stage 3: Bulk Electrolysis
    plate.start_stirring()
    close_all_gas()

    #run_CV_HER_varyE(exp_path, sample=expn, gas=f"{exp['CO2ratio']}CO2", sr_cv=50)
    control_co2_ar_ratio(exp['CO2ratio'])
    time.sleep(180)
    print('Purging gas for 3 minutes')

    potential_windows = [-1.5]  # Pending determination

    for voltage in potential_windows:
        execute_bulk_electrolysis(exp, exp_path, expn, voltage)
    
    # Stage 4: Electrode regeneration
    messages = ['Start electrode regeneration', 'Finish electrode regeneration']
    for i, message in enumerate(messages):
        print(message)
        os.system(f'python {script_path} -m "{message}"')
        if i == 0:
            insitu_echem_regeneration(exp_path)
            print('skip')

    plate.start_stirring()
    Rinsing('cell', 'water', 'water', 1)
    Rinsing('voir', 'water', 'water', 1)

def execute_bulk_electrolysis(exp, exp_path, expn, voltage):
    """Executes bulk electrolysis for a specific voltage."""
    print(f"Running experiment with CO2/Ar ratio {exp['CO2ratio']}%.")

    read_all_gas()

    SendCommandToGC(f"Loading Control Files, subfolder: {exp_path}, filename: {expn}Elysis_{str(exp['CO2ratio'])}CO2_{voltage}")

    if wait_for_gc_signal():
        #impedence = bulk_electrolysis_beforeCP(exp_path, sample=expn, E_ed=voltage, note=f"{exp['CO2ratio']}CO2")
        SendCommandToGC("Wait 180 second and start 2 sample Injections")
        bulk_electrolysis_CP(exp_path, sample=expn, E_ed=voltage, Time_ed = 1360)

    if wait_for_gc_signal():
        print("GC is running, proceed to perform electrode regeneration.") #Assume at this moment the GC is running the second injection.
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
        time.sleep(5)
        SIGNAL = CheckSignalFromGC()
    return True

def CO2Optimizer(mainfold, doe, initialization=True):
    """Main function to orchestrate the CO2 optimization experiments."""
    if initialization:
        base_path = initialize_experiment(mainfold)
    else:
        base_path = f'C:/Users/guazh/data/{mainfold}'
        #base_path = f'/Users/Yi-An/Documents/000_Project/044_FAARM_PA-004/Data/{mainfold}'
        create_directory(base_path)
    DPAgent.master_folder = base_path
    for expn, exp in doe.items():
        # Display the fetched parameters

        LOG.setup_logging_for_experiment(expn)
        print(f"Next epxeriment: {expn}")
        print(f"Next condition: {exp}")

        subfold = f"{datetime.now().strftime('%Y-%m-%d')}-{expn}"
        exp_path = f"{base_path}/{subfold}"
        create_directory(exp_path)

        print("------Data Collection Start------")
        run_experiment(exp, exp_path, expn)
        print("------Data Collection Finished---")

        DPAgent.exp_num = int(expn[3:])  # Extract the number from the EXPXXXX format and convert to integer
        print(f"Experiment number: EXP{expn}")
        print(f"Condition for EXP{expn}: {exp}")
        bulk_electrolysis_potential, current_density, FECO = DPAgent.encode(exp) # Data processing

        # Print the results of the completed trial
        print(f"EXP{expn} completed with:")
        print(f"  bulk_electrolysis_potential: {bulk_electrolysis_potential} V")
        print(f"  current_density: {current_density:.2e} A")
        print(f"  FE_CO: {FECO:.2f} %")
        print("------------------------------------------------")
        LOG.restore_stdout()
        print("Experiment logs saved.")  # Prints to console
        print(f'Exp{expn}completed')

        #Check if GC finished yet
        SendCommandToGC("Is GC still running?")
        if wait_for_gc_signal():
            print("GC finished measurement. Proceed to next experiment.")


    # Final rinsing
    Rinsing('cell', 'water', 'water', 3)

    print('Experiment completed')

    os.system(f'python {script_path} -m "{message_completed}"')

# Example Usage
if __name__ == "__main__":
    #
    main_folder = 'DoE_3t3'
    DPAgent = DataProcessing()
    CO2Optimizer(main_folder, exp_dicts, initialization=True)
