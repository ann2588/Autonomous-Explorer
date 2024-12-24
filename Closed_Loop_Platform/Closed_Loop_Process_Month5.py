#%%
import sys
import os
from datetime import datetime
# Add the parent directory of Closed_Loop_Platform to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from Closed_Loop_Platform.Communication import *
from Closed_Loop_Platform.DataProcessing import *
from Closed_Loop_Platform.BOtorchV2 import *
#from Closed_Loop_Platform.Utilities import *



'''
# Last update: 12/23/2024
# Note: The closed-loop process still requires testing
# Update:


'''

#%% Machine Learning Agent setup
objectives = {
    "bulk_electrolysis_potential": ObjectiveProperties(minimize=True),
    "current_density": ObjectiveProperties(minimize=False),
    "FE_CO": ObjectiveProperties(minimize=False),
}

# Initialize manager
manager = ExperimentManager(generation_strategy=gs, parameters=parameters, objectives=objectives)

# Define thresholds using metric variables after experiment setup
thresholds = [
    ObjectiveThreshold(metric=manager.metric_bulk_electrolysis, bound=-1.0, relative=False),
    ObjectiveThreshold(metric=manager.metric_current_density, bound=20.0, relative=False),
    ObjectiveThreshold(metric=manager.metric_fe_co, bound=0.9, relative=False),
]

# Apply thresholds to the optimization config
manager.ax_client.experiment.optimization_config = MultiObjectiveOptimizationConfig(
    objective=manager.ax_client.experiment.optimization_config.objective,
    objective_thresholds=thresholds,
)

# Load data
manager.load_initial_data("experimental_conditions.csv", "updated_objective_data.csv")


#%%
doepath = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\DoERandomBatch10.csv"
exp_dicts = doeprocess(doepath)


def initialize_experiment(mainfold):
    """Initializes directories and logging for the experiment."""
    date = datetime.now().strftime('%Y-%m-%d')
    base_path = f'C:/Users/guazh/data/{mainfold}'
    create_directory(base_path)

    subfold = f'{date}-Initial'
    initial_path = f'{base_path}/{subfold}'
    create_directory(initial_path)

    log_folder = f'C:/Users/guazh/data/{mainfold}'
    create_master_logger(log_folder)
    setup_logging_for_experiment('Initial')

    SendCommandToGC(f"Connect to GC, mainfolder: {mainfold}")
    time.sleep(30)

    SIGNAL = CheckSignalFromGC()
    # Ask human to check if the current platform is connected to the server (Y/N?)

    print('Start electrode initialization')
    insitu_echem_regeneration(initial_path) #Todo Change this protocol
    print('Finish electrode initialization')
    #control_co2_ar_ratio(0)  # Purge Ar into Cell to degas
    #print('Check electrode Activity')
    #run_CV_HER_varyE(initial_path, sample='Initial', gas='ArKOH', sr_cv=50)

    return base_path

def run_experiment(exp, exp_path, expn):
    """Runs individual experiment based on given parameters."""
    setup_logging_for_experiment(expn)
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
    #Elelectrolyte_Formulation(il_values)

    # Stage 3: Bulk Electrolysis
    plate.start_stirring()
    Rinsing('cell', 'water', 'electrolyte', 1, volume_assigned='50mL')
    close_all_gas()

    #run_CV_HER_varyE(exp_path, sample=expn, gas=f"{exp['CO2ratio']}CO2", sr_cv=50)
    control_co2_ar_ratio(exp['CO2ratio'])

    potential_windows = [-1.6]  # Pending determination

    for voltage in potential_windows:
        execute_bulk_electrolysis(exp, exp_path, expn, voltage)

    print('Start electrode regeneration')
    insitu_echem_regeneration(exp_path)
    print('Finish electrode regeneration')

    Rinsing('cell', 'water', 'water', 1)
    plate.start_stirring()
    time.sleep(60)
    Rinsing('voir', 'water', 'water', 1)

    print('Experiment completed')


def execute_bulk_electrolysis(exp, exp_path, expn, voltage):
    """Executes bulk electrolysis for a specific voltage."""
    print(f"Running experiment with CO2/Ar ratio {exp['CO2ratio']}%.")

    print('Reading values:')
    print(f'Ar flow rate: {readpoint("mass_flow", mfc_ar)}')
    print(f'CO2 flow rate: {readpoint("mass_flow", mfc_co2)}')
    print(f'Total flow into GC: {readpoint("mass_flow", mfc_co2ar)}')

    SendCommandToGC(f"Loading Control Files, subfolder: {exp_path}, filename: {expn}_{exp['CO2ratio']}CO2_{voltage}")

    if wait_for_gc_signal():
        #impedence = bulk_electrolysis_beforeCP(exp_path, sample=expn, E_ed=voltage, note=f"{exp['CO2ratio']}CO2")
        SendCommandToGC("Wait 180 second and start sample Injection")
        bulk_electrolysis_CP(exp_path, sample=expn, RU=10, E_ed=voltage, note=f"{exp['CO2ratio']}CO2")
        time.sleep(300)

    if wait_for_gc_signal():
        print("GC is running, waiting 7 minutes...")
        time.sleep(560)
    else:
        print("Hey, GC is not running!!!")
        os.system(f'python {script_path} -m "GC is not running, check it out."')

    SendCommandToGC("Is GC still running?")
    if wait_for_gc_signal():
        print("GC finished measurement. Proceed to next experiment.")


def wait_for_gc_signal(timeout=300):
    """Waits for GC signal with a timeout."""
    start_time = time.time()
    SIGNAL = CheckSignalFromGC()
    while not SIGNAL:
        if time.time() - start_time > timeout:
            logging.error("Timeout: GC did not respond within the timeout period.")
            os.system(f'python {script_path} -m "Timeout: GC did not respond in time."')
            return False
        time.sleep(60)
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
        next_experiment = manager.update() #suggest next experiment
        # Display the fetched parameters
        print(f"Next trial fetched: {next_experiment}")

        subfold = f"{datetime.now().strftime('%Y-%m-%d')}-{expn}"
        exp_path = f"{base_path}/{subfold}"
        create_directory(exp_path)
        #run_experiment(exp, exp_path, expn)

        print(expn)
        print(exp)
        DPAgent.exp_num = int(expn[3:])  # Extract the number from the EXPXXXX format and convert to integer
        print(DPAgent.exp_num)
        bulk_electrolysis_potential, current_density, FECO = DPAgent.encode(exp) # Data processing
        manager.ax_client.complete_trial(
            trial_index=int(expn[3:]),  # Use the iteration index as the trial index
            raw_data={
                "bulk_electrolysis_potential": (bulk_electrolysis_potential, None),  # Provide the value and its variance (None here)
                "current_density": (current_density, None), 
                "FE_CO": (FECO, None)
            }
        ) 


    # Final rinsing
    Rinsing('cell', 'water', 'water', 3)

    print('Experiment completed')
    os.system(f'python {script_path} -m "{message_completed}"')


# Example Usage
main_folder = 'TestRunForDataStructure_Structure3'
DPAgent = DataProcessing()
CO2Optimizer(main_folder, exp_dicts, initialization=False)
