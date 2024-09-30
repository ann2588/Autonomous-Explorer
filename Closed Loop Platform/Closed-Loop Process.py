from Utilities.liquidhandling import *
from Utilities.gashandling import *
from Utilities.electrochemistry import *
from Utilities.gasanalyzer import *
from DoEFormatting import *
# Last update: 09/27/2024
# Note: The closed-loop process still requires testing



#%% Macro script
def CO2Optimizer(mainfold: str, doe:exp_dicts, initialization:True):

    date = datetime.now().strftime('%Y-%m-%d')
    base_path = f'C:/Users/guazh/data/{mainfold}'
    create_directory(base_path)


    #Stage 0: Initialization
    if initialization == True:
        cat = 'Initial'
        subfold = f'{date}-{cat}'
        initial_path = f'{base_path}/{subfold}'
        create_directory(initial_path)
        insitu_echem_regeneration(initial_path)
        Rinsing('cell','water', 'electrolyte', 3)
        control_co2_ar_ratio(0) #Purge Ar into Cell to degas
        time.sleep(60)
        run_CV_HER_varyE(initial_path, sample=cat, gas='ArKOH', sr_cv=50)

    for expn, exp in doe.items():
        print(f'Running {expn}...')

        cat = expn
        subfold = f'{date}-{cat}'
        exp_path = f'{base_path}/{subfold}'
        create_directory(exp_path)

        # Stage 1: Cu film deposition
        PlatingSolutionFormulation(exp['CuConc']) #@todo formulate doe files
        control_co2_ar_ratio(0)
        stirring(plate, 60)
        deposit_v, deposit_t = exp['Volt'], exp['Time'] ### Use previous notation
        electrodeposition(exp_path, f'{cat}Deposition', deposit_v, deposit_t)
        Rinsing('cell','spelec', 'spelec', 2)

        # Stage 2: Electrolyte formulation with
        il_values = {key: exp[key] for key in ['IL1', 'IL2', 'IL3', 'IL4', 'IL5']}
        Elelectrolyte_Formulation(il_values)

        # Stage 3: Echem characterization & Bulk electrolysis
        plate.start_stirring()
        time.sleep(180)
        Rinsing('cell', 'water', 'electrolyte', 1)
        close_all_gas()
        run_CV_HER_varyE(exp_path, sample=cat, gas=f"{exp['CO2ratio']}CO2", sr_cv=50)
        control_co2_ar_ratio(exp['CO2ratio'])
        potential_windows = [-1.0, -1.4, -1.6, -1.8, -2.0] # Pending determining numbers of potential windows
        for voltage in potential_windows:
            bulk_electrolysis(exp_path, sample=cat, E_ed = voltage, note=f"{exp['CO2ratio']}CO2")
            ''' 
            #@@ Pending using client/server format for hardware communication when electrolysis/sample injection
            # Current challenge: Cannot run other command while the echem tech is running due to subprocess format.
            # os.execvp() vs sub processing
            '''

        close_all_gas()
        Rinsing('cell','electrolyte', 'electrolyte', 1)

        # Stage 4-1: GC data processing


        # Stage 4-2: Electrode Regeneration
        insitu_echem_regeneration(exp_path)
        Rinsing('cell', 'water', 'electrolyte', 3)
        plate.start_stirring()
        time.sleep(60)
        LSV_HER(exp_path, 'RegeneratedGCE', criteria_current=10)
        Rinsing('voir', 'water', 'water', 3)
        os.system(f'python {script_path} -m "{cat} completed"')

    # Final rinsing
    Rinsing('cell', 'water', 'water', 3)

    # Completion script
    os.system(f'python {script_path} -m "{message_completed}"')


#%%%
if __name__ == '__main__':
   main_folder = 'Your Filename'
   CO2Optimizer(main_folder, exp_dicts, Initialization = True)
