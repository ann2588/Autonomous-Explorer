from random import sample

import Utilities
from Utilities.liquidhandling import *
from Utilities.gashandling import *
from Utilities.electrochemistry import *
from Utilities.gasanalyzer import *
# Last update: 09/27/2024
# Note: The closed-loop process still requires testing

#%% Macro script
def CO2Optimizer(mainfold: str, doe:dict, initialization:True):

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
        control_co2_ar_ratio(0)
        time.sleep(60)
        run_CV_HER_varyE(initial_path, sample=cat, gas='ArKOH', sr_cv=50)
        control_co2_ar_ratio(0)

    for expn, exp in doe.items():
        print(f'Running {expn}...')

        cat = expn
        subfold = f'{date}-{cat}'
        exp_path = f'{base_path}/{subfold}'
        create_directory(exp_path)

        # Stage 1: Cu film deposition
        PlatingSolutionFormulation(doe.items) #@todo
        control_co2_ar_ratio(0)
        stirring(plate, 60)
        deposit_v, deposit_t = exp['Volt'], exp['Time'] ### Use previous notation
        electrodeposition(exp_path, f'{cat}Deposition', deposit_v, deposit_t)
        Rinsing('cell','spelec', 'spelec', 2)

        # Stage 3: Electrolysis
        Elelectrolyte_Formulation(sample=exp)
        plate.start_stirring()
        time.sleep(180)
        Rinsing('cell', 'water', 'electrolyte', 1)
        close_all_gas()
        run_CV_HER_varyE(exp_path, sample=cat, gas=f'{CO2ratio}CO2', sr_cv=50)
        control_co2_ar_ratio({CO2ratio})
        bulk_electrolysis(exp_path, sample=cat, gas=f'{CO2ratio}CO2', E_ed = electrolysis_v)
        # gc.update_gc_settings(
        # Usually Regeneration takes 2.5 hours.
        # after run GC. Running Regeneration.
        # Can we make regeneration another module?
        # os.execvp() vs sub processing


        #@@ GC controlling command
        #offCO2Ar()
        Rinsing('cell','electrolyte', 'electrolyte', 1)

        # Stage 4: electrode Regeneration
        insitu_echem_regeneration(exp_path)
        Rinsing('cell','water', 'electrolyte', 3)
        plate.start_stirring()
        time.sleep(60)
        LSV_HER(exp_path, 'RegeneratedGCE', criteria_current=10)
        Rinsing('voir', 'water', 'water', 3)
        os.system(f'python {script_path} -m "{cat} completed"')




    # Final rinsing
    Rinsing('cell', 'water', 'water', 3)

    # Completion script
    os.system(f'python {script_path} -m "{message_completed}"')

'''
#%%%
doepath="C:\\Users\\guazh\\data\\Batch\\20240802_batch\\20240802_batch_500.csv"
doedicts = doeprocess(doepath)
doedicts_0903 = dict(list(doedicts.items())[251:])

#CO2Optimizer('20240813_batch_89_500', doedicts_0813, initialization = False)
#CO2Optimizer('20240903_batch_252_500', doedicts_0903, initialization = True)
'''