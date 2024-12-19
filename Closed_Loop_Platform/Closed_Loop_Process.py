#%%
from Closed_Loop_Platform.Communication.Logging import *
from Closed_Loop_Platform.Utilities.DoEFormatting import *
from Closed_Loop_Platform.Communication.Client import *
from Closed_Loop_Platform.Utilities.gashandling import *
from Closed_Loop_Platform.Utilities.liquidhandling import *
from Closed_Loop_Platform.Utilities.electrochemistry import *

# Last update: 12/12/2024
# Note: The closed-loop process still requires testing
# Test stage
# 1: Dry run with print() to make sure the framework is alright
# 2: Test run with instruments to check one close loop, skip the initialization first. And skip ionic liquid.
# Purpose: to get correct data structure for at least 3 close loop
#%%
doepath = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\DoERandomBatch10.csv" #Todo Change the input format
exp_dicts = doeprocess(doepath)

#%% Macro script
def CO2Optimizer(mainfold: str, doe:exp_dicts, initialization:True):

    date = datetime.now().strftime('%Y-%m-%d')
    base_path = f'C:/Users/guazh/data/{mainfold}'
    create_directory(base_path)
    #log_folder = mainfold
    log_folder = r'/Users/Yi-An/Documents/000_Project/044_FAARM_PA-004/Data/Logfile'
    create_master_logger(log_folder)
    SendCommandToGC(f"Connect to GC, mainfolder: {mainfold}")
    CheckSignalFromGC()

    ###
    # Ask human to check if the current platform is connected to the server (Y/N?)
    ###
    while True:
        user_confirmation = input("Is the server connected to GC? (Y/N): ").strip().upper()
        if user_confirmation == 'Y':
            print("Proceeding with the experiment...")
            logging.info("User confirmed GC connection.")
            break
        elif user_confirmation == 'N':
            print("Please connect the server to the GC and confirm when ready.")
            logging.warning("User indicated GC is not connected. Waiting for confirmation...")
            time.sleep(10)  # Wait for user to take action
        else:
            print("Invalid input. Please enter 'Y' or 'N'.")

    #Stage 0: Initialization
    if initialization == True:
        cat = 'Initial'
        subfold = f'{date}-{cat}'
        initial_path = f'{base_path}/{subfold}'
        create_directory(initial_path)
        setup_logging_for_experiment(f'{cat}')
        print('Start electrode initialization')
        insitu_echem_regeneration(initial_path)
        print('Finish electrode initialization')
        Rinsing('cell','water', 'electrolyte', 3)
        control_co2_ar_ratio(0) #Purge Ar into Cell to degas
        time.sleep(60)
        print('Check electrode Activity')
        run_CV_HER_varyE(initial_path, sample=cat, gas='ArKOH', sr_cv=50)

    for expn, exp in doe.items():
        cat = expn
        setup_logging_for_experiment(f'{cat}')
        print(f'Running {expn}...')
        subfold = f'{date}-{cat}'
        exp_path = f'{base_path}/{subfold}'
        create_directory(exp_path)


        # Stage 1: Cu film deposition
        print('Start Cu catalyst deposition')
        PlatingSolutionFormulation(exp['CuConc']) #@todo formulate doe files
        control_co2_ar_ratio(0)
        stirring(plate, 60)
        deposit_v, deposit_t = exp['Volt'], exp['Time'] ### Use previous notation
        electrodeposition(exp_path, f'{cat}Deposition', deposit_v, deposit_t)
        Rinsing('cell','spelec', 'spelec', 2)
        print('Finish Cu catalyst deposition')

        # Stage 2: Electrolyte formulation with
        il_values = {key: exp[key] for key in ['IL1', 'IL2', 'IL3', 'IL4', 'IL5']}
        print('Preparing Electrolyte for bulk electrolysis...')
        Elelectrolyte_Formulation(il_values)

        # Stage 3: Echem characterization & Bulk electrolysis
        plate.start_stirring()
        time.sleep(180)
        Rinsing('cell', 'water', 'electrolyte', 1)
        close_all_gas()
        #run_CV_HER_varyE(exp_path, sample=cat, gas=f"{exp['CO2ratio']}CO2", sr_cv=50)
        control_co2_ar_ratio(exp['CO2ratio'])
        potential_windows = [-1.0, -1.4, -1.6, -1.8, -2.0] # Pending determining numbers of potential windows
        for voltage in potential_windows:
            for step in range(1):

                #Seperate the process of electrolysis and GC instead of putting in one
                print(f"Running experiment with CO2/Ar ratio {exp['CO2ratio']}%.")
                print('Reading value:')
                print(f'Ar flow rate : {readpoint("mass_flow", mfc_ar)}')
                print(f'CO2 flow rate : {readpoint("mass_flow", mfc_co2)}')
                print(f'flow rate into GC : {readpoint("mass_flow", mfc_co2ar)}')

                SendCommandToGC(f"Loading Control Files, subfolder: {exp_path}, filename: {expn}_{exp['CO2ratio']}CO2_{voltage}_step{step+1}")
                # Remember to change the command Read by GC
                bulk_electrolysis(exp_path, sample=cat, E_ed = voltage, note=f"{exp['CO2ratio']}CO2_step{step+1}")
                SIGNAL = CheckSignalFromGC()

                if SIGNAL:
                    impedence = bulk_electrolysis_beforeCP(exp_path, sample=cat, E_ed = voltage, note=f"{exp['CO2ratio']}CO2_step{step+1}")
                    SendCommandToGC("Wait 180 second and start sample Injection")
                    bulk_electrolysis_CP(exp_path, sample=cat, RU = impedence,  E_ed = voltage, note=f"{exp['CO2ratio']}CO2_step{step+1}")

                SIGNAL = CheckSignalFromGC()
                if SIGNAL:
                    print(f"GC is running, waiting 7 minutes...")
                    time.sleep(560)
                else:
                    print(f"Hey GC is not running!!!")
                    os.system(f'python {script_path} -m "GC is not running, check it out."')

                SendCommandToGC("Is GC still running?")
                # Add timeout for signal check
                start_time = time.time()
                timeout = 300  # Timeout after 5 minutes (300 seconds)
                while not SIGNAL:
                    SIGNAL = CheckSignalFromGC()
                    if time.time() - start_time > timeout:
                        print("Timeout: GC did not respond in time.")
                        logging.error("GC did not respond within the timeout period.")
                        # Take appropriate action after timeout (e.g., skip this step, alert user, etc.)
                        os.system(f'python {script_path} -m "Timeout: GC did not respond in time."')
                        break  # Exit the loop if GC signal wasn't received within timeout

        close_all_gas()
        Rinsing('cell','electrolyte', 'electrolyte', 1)

        # Stage 4-1: Electrode Regeneration

        print('Start electrode regeneration')
        #insitu_echem_regeneration(exp_path)
        print('Finish electrode regeneration')

        Rinsing('cell', 'water', 'electrolyte', 3)
        plate.start_stirring()
        time.sleep(60)

        LSV_HER(exp_path, 'RegeneratedGCE', criteria_current=10)
        Rinsing('voir', 'water', 'water', 3)

        print('Experiment completed')

        #Stage 4-2: Data processing

        os.system(f'python {script_path} -m "{cat} completed"')

    # Final rinsing
    Rinsing('cell', 'water', 'water', 3)

    # Completion script
    print('Experiment completed')
    os.system(f'python {script_path} -m "{message_completed}"')


#%%%
if __name__ == '__main__':
   main_folder = 'CloseLooptestForDataStructure'
   CO2Optimizer(main_folder, exp_dicts, Initialization = False)
