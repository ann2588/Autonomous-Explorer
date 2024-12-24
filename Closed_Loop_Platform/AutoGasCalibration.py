#%%
from Utilities.gashandling import *
from Utilities.gasanalyzer import *

#%%
import sys, glob
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Closed_Loop_Platform.DataProcessing.gc_dataprocessing import * 

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

#%%
def DataProcessing(path = str):
    '''
    After the measurement finished. Access the folder. Perform Peak integration.
    Access the peak area. Perform linear regression to get slope and intercelp.
    Record the result in calibration file under DataProcessing folder. For every calibration file. Note the date.
    Step:
    1. Go to folder
    2. Process all the file.
    3. Come back to master folder.
    4. Access the FID and TCD under different subfolder. Record the conc. and area value.
    5. save in a csv file.
    6. Perform linear regression for conc. vs area H2 and area CO.
    7. Save the slope and intercept and r square in different csv file.
    '''
    os.chdir(data_path)
    folders = [folder for folder in os.listdir() if folder != ".DS_Store" and not folder.endswith('.png') and not folder.endswith('.csv')]
    for folder in folders:
        process_asc_files(folder)
        os.chdir(data_path)
    data = []
    for folder in folders: 
        os.chdir(folder)
        files = glob.glob(f"peak_data*")
        peak_areas = {
            'H2 as TCD': 0,
            'CO as FID': 0
        }

        for file in files:
            if "TCD" in file:
                continue  # Skip H2 as TCD
            elif "FID" in file:
                peak_name = 'CO as FID'
            else:
                continue

            test_df = pd.read_csv(file)
            peak_areas[peak_name] = test_df.loc[test_df['Peak Name'] == peak_name, 'Peak Area'].iloc[0]
        concentration = float(str(folder))
        data.append([concentration, peak_areas.get('H2 as TCD', 0), peak_areas['CO as FID']])  # Default to 0 if 'H2 as TCD' not found
        os.chdir('..')

    df = pd.DataFrame(data, columns=['Concentration', 'Peak Area H2', 'Peak Area CO'])
    df['Concentration'] = df['Concentration'] * 0.1 *10000  # Convert from % to ppm
    df = df.sort_values(by='Concentration')

    from scipy.stats import linregress
    import matplotlib.pyplot as plt
    from datetime import datetime

    # Perform linear regression for high concentration (from 20)
    high_conc_df = df[df['Concentration'] >= 20]
    slope_high, intercept_high, r_value_high, p_value_high, std_err_high = linregress(high_conc_df['Concentration'], high_conc_df['Peak Area CO'])
    print(f"High Concentration Slope: {slope_high}, Intercept: {intercept_high}, R^2: {r_value_low**2:.2f}")

    # Plot the result for high concentration
    plt.figure(figsize=(3.6, 3.6))
    plt.scatter(high_conc_df['Concentration'], high_conc_df['Peak Area CO'])
    plt.plot(high_conc_df['Concentration'], intercept_high + slope_high*high_conc_df['Concentration'], 'r')
    plt.xlabel('Concentration (ppm)')
    plt.ylabel('Peak Area CO')
    plt.text(0.05, 0.95, f"Slope: {slope_high:.2f}\nIntercept: {intercept_high:.2f}\nR^2: {r_value_low**2:.2f}", transform=plt.gca().transAxes, fontsize=10, ha='left', va='top')
    plt.title('Linear Regression of Peak Area CO over Concentration (High)')
    plt.savefig('LR_high.png', dpi = 600)
    plt.show()

    # Perform linear regression for low concentration (below 20)
    low_conc_df = df[df['Concentration'] < 20]
    slope_low, intercept_low, r_value_low, p_value_low, std_err_low = linregress(low_conc_df['Concentration'], low_conc_df['Peak Area CO'])
    print(f"Low Concentration Slope: {slope_low}, Intercept: {intercept_low}, R^2: {r_value_low**2:.2f}")

    # Plot the result for low concentration
    plt.figure(figsize=(3.6, 3.6))
    plt.scatter(low_conc_df['Concentration'], low_conc_df['Peak Area CO'])
    plt.plot(low_conc_df['Concentration'], intercept_low + slope_low*low_conc_df['Concentration'], 'r')
    plt.xlabel('Concentration (ppm)')
    plt.ylabel('Peak Area CO')
    plt.text(0.05, 0.95, f"Slope: {slope_high:.2f}\nIntercept: {intercept_high:.2f}\nR^2: {r_value_low**2:.2f}", transform=plt.gca().transAxes, fontsize=10, ha='left', va='top')
    plt.title('Linear Regression of Peak Area CO over Concentration (Low)')
    plt.savefig('LR_low.png', dpi = 600)
    plt.show()

    # Store the slope and intercept for both high and low concentrations in another CSV
    calibration_data = pd.DataFrame({
        'High Concentration Slope': [slope_high],
        'High Concentration Intercept': [intercept_high],
        'Low Concentration Slope': [slope_low],
        'Low Concentration Intercept': [intercept_low]
    })
    datetime_str = datetime.now().strftime('%Y-%m-%d')
    calibration_filename = f"GC calibration - {datetime_str}.csv"
    calibration_data.insert(0, "Compound", "CO")
    calibration_data.to_csv(calibration_filename, index=False)
    print(f"Calibration data saved to {calibration_filename}")
    cali_file_path = "/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/DataProcessing"
    calibration_data.to_csv(os.path.join(cali_file_path, calibration_filename), index = False)
    
    
    
    
#%%
if __name__ == "__main__":
    main_folder = '2024-09-24_lowconc'  # Enter the name of your folder
    gas_ratio = [0.01, 0.1, 0.2]  # Enter the ratio you want to try in list
    #start
    start_measuring_calibration_curve(data_path = data_path)

    #% Experiment Finished. Start baking the column
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
    script_path = "/Closed_Loop_Platform/Utilities/slack-bot.py"
    os.system(f'python {script_path} -m "Baking completed. Please turn off FID manually"')
