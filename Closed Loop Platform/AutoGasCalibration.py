#%%
from Utilities.gashandling import *
from Utilities.gasanalyzer import *

#@@ Todo: Baking method configuration
#%% Parameter setting
main_folder = '2024-09-24_lowconc' #Enter the name of your folder
gas_ratio = [0.01, 0.1, 0.2] #Enter the ratio you want to try in list

#%% GC method setting
gc = GC_Connector() #reopen the peaksimple software before running this command
data_path = f'C:\\Peak498Win10\\GCDATA\\{main_folder}' #Update your folder here
os.makedirs(data_path, exist_ok=True)
gc.update_gc_settings(data_path)

#% Load GC method and update data file saving path in GC
ctrl_file = "C:\\Peak498Win10\\GCMETHOD\\Parameter\\0819-2020_90-210C_11min.CON" # the path of your folder
gc.ctrl_file = ctrl_file
gc.load_ctrl_file() #Running error but actually successful
gc.update_gc_settings(data_path)

def start_measuring_calibration_curve(data_path = data_path):
    try:
        while gc.is_running():
            print('GC is still in post-run. Wait for another minute.')
            time.sleep(60)

        # Loop through each gas ratio
        for co2ratio in gas_ratio:

            print(f"Setting CO2/Ar ratio to {co2ratio}%")
            datapath = os.path.join(data_path, f'ratio_{co2ratio}')
            os.makedirs(datapath, exist_ok=True)
            gc.update_gc_settings(datapath)

            ## Step One: Control gas flow mixture output at certain flow rate and ratio
            # Control CO2 and Ar flow rates
            control_co2_ar_ratio(co2ratio)
            gas_key = 'N2'
            mfc_co2ar.set_flow_rate(30) ###

            ## Step two: filling the sample loop for 1.5 minutes
            time.sleep(90)
            print(f"Running experiment with CO2/Ar ratio {co2ratio}%.")
            print('Reading value:')
            print(f'Ar flow rate : {readpoint("mass_flow", mfc_ar)}')
            print(f'CO2 flow rate : {readpoint("mass_flow", mfc_co2)}')
            print(f'flow rate into GC : {readpoint("mass_flow", mfc_co2ar)}')

            ## Command GC to start run
            gc.set_running()

            ## Close the gas flow after sample injected to GC
            time.sleep(60)
            control_gas_flow(mfc_co2, operation='close')
            control_gas_flow(mfc_ar, operation='close')
            control_gas_flow(mfc_co2ar, operation='close')

            ## Waiting for one measurement
            time.sleep(720)

            ## Check if the measurement complete
            while gc.is_running():
                print('GC is still running. Wait for another minute.')
                time.sleep(60)

            #@@Todo Data analysis pending the integration script

            print(f"Experiment completed for ratio {co2ratio}%.\n")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main_folder = '2024-09-24_lowconc'  # Enter the name of your folder
    gas_ratio = [0.01, 0.1, 0.2]  # Enter the ratio you want to try in list
    #start
    start_measuring_calibration_curve(data_path = data_path)

    #%% Experiment Finished. Start baking the column
    baking_ctrl_file = "C:\\Peak498Win10\\GCMETHOD\\Parameter\\0622-2019_270C_50min_baking.CON" #The folder path of your baking method
    #@@ Todo check the setting of channel 2 temperature log file
    print('Experiment Finished. Start baking the column.')
    gc.ctrl_file = baking_ctrl_file
    gc.load_ctrl_file()
    gc.set_running()
    time.sleep(3000)
    while gc.is_running():
        print('Still baking. Wait for another minute.')
        time.sleep(60)
    script_path = "C:/Users/guazh/PycharmProjects/CO2platform/Utilities/slack-bot.py"
    os.system(f'python {script_path} -m "Baking completed. Please turn off FID manually"')
