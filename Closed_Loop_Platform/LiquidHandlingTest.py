from Closed_Loop_Platform.Utilities import *

Rinsing('cell', 'water', 'electrolyte',1, volume_assigned='20mL')

#%%Done
#Rinsing('cell', 'water', 'electrolyte',1, volume_assigned='20mL', from_voir=True)
#%%
titrationmoduletestsample = {'IL1': 0, 'IL2': 1, 'IL3': 1, 'IL4': 1, 'IL5': 1, 'Blank': 0}
test_titration_module(titrationmoduletestsample)

#%% Done
ILModuleTestSample = {'IL1': 10, 'IL2': 27, 'IL3': 18, 'IL4': 2, 'IL5': 5, 'Blank': 3}
Elelectrolyte_Formulation(ILModuleTestSample)

#%%

PlatingSolutionFormulation(0.2)

#%%
main_folder = 'RegenerationTest'
def initialize_experiment(mainfold):
    """Initializes directories and logging for the experiment."""
    date = datetime.now().strftime('%Y-%m-%d')
    base_path = f'C:/Users/guazh/data/{mainfold}'
    create_directory(base_path)

    subfold = f'{date}-Initial'
    initial_path = f'{base_path}/{subfold}'
    create_directory(initial_path)

    '''
    log_folder = f'C:/Users/guazh/data/{mainfold}'
    create_master_logger(log_folder)
    setup_logging_for_experiment('Initial')

    SendCommandToGC(f"Connect to GC, mainfolder: {mainfold}")
    time.sleep(30)

    SIGNAL = CheckSignalFromGC()
    # Ask human to check if the current platform is connected to the server (Y/N?)
    '''

    print('Start electrode initialization')
    insitu_echem_regeneration(initial_path) #Todo Change this protocol
    print('Finish electrode initialization')
    #control_co2_ar_ratio(0)  # Purge Ar into Cell to degas
    #print('Check electrode Activity')
    #run_CV_HER_varyE(initial_path, sample='Initial', gas='ArKOH', sr_cv=50)

    return base_path