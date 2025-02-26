#%%
from Closed_Loop_Platform.DataProcessing.DoEFormatting import *
from Closed_Loop_Platform.Communication.Client import *
from Archive.liquidhandling import *
from Closed_Loop_Platform.Utilities.electrochemistry import *


# Last update: 12/12/2024
# Note: The closed-loop process still requires testing
# Test stage
# 1: Dry run with print() to make sure the framework is alright Done
# 2: Test run with GC and gas line to ensure the communication, before start set up the gas line first.
# The expected result would be the CO2 ratio change
# 3: Test run with liquid for one closed loop process
# Todo 1: for regeneration protocol, use acid rinse only
# Todo 2: Use glassy carbon rod as counter first.
# Todo 3: Check the gas analyzer code run in server console first.
# For Demo: Ensure the camera is running (On Friday)

#%%
doepath = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\DoERandomBatch10.csv" #Todo Change the input format
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

    #print('Start electrode initialization')
    #insitu_echem_regeneration(initial_path) #Todo Change this protocol
    #Rinsing('water', 'hno3', acidrinse=True, repetitions=1)
    #print('Finish electrode initialization')
    #Rinsing('cell', 'water', 'electrolyte', 3)
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
    #PlatingSolutionFormulation(exp['CuConc'])  # Formulate DOE files
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

    potential_windows = [-1.5]  # Pending determination

    for voltage in potential_windows:
        execute_bulk_electrolysis(exp, exp_path, expn, voltage)

    print('Start electrode regeneration')
    #insitu_echem_regeneration(exp_path)
    #Rinsing('cell', 'water', 'HNO3', 1, acidrinse=True)
    print('Finish electrode regeneration')

    #Rinsing('cell', 'water', 'electrolyte', 3)
    plate.start_stirring()
    time.sleep(60)
    #LSV_HER(exp_path, 'RegeneratedGCE', criteria_current=10)
    #Rinsing('voir', 'water', 'water', 3)

    print('Experiment completed')


def execute_bulk_electrolysis(exp, exp_path, expn, voltage):
    """Executes bulk electrolysis for a specific voltage."""
    print(f"Running experiment with CO2/Ar ratio {exp['CO2ratio']}%.")

    print('Reading values:')
    print(f'Ar flow rate: {readpoint("mass_flow", mfc_ar)}')
    print(f'CO2 flow rate: {readpoint("mass_flow", mfc_co2)}')
    print(f'Total flow into GC: {readpoint("mass_flow", mfc_co2ar)}')

    SendCommandToGC(f"Loading Control Files, subfolder: {exp_path}, filename: {expn}_{voltage}")

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

    for expn, exp in doe.items():
        subfold = f"{datetime.now().strftime('%Y-%m-%d')}-{expn}"
        exp_path = f"{base_path}/{subfold}"
        create_directory(exp_path)
        run_experiment(exp, exp_path, expn)

    # Final rinsing
    #Rinsing('cell', 'water', 'water', 3)

    print('Experiment completed')
    os.system(f'python {script_path} -m "{message_completed}"')


# Example Usage
main_folder = 'DryRun_withDeposition'
CO2Optimizer(main_folder, exp_dicts, initialization=True)
