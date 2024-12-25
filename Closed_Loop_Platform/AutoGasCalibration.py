#%%
from Closed_Loop_Platform.Utilities.gashandling import *
#from Closed_Loop_Platform.Communication.gasanalyzer import *


#%%
import sys, glob, os
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Closed_Loop_Platform.DataProcessing.gc_dataprocessing import * 

#@@ Todo: Baking method configuration
#%% Parameter setting
main_folder = '2024-12-24_wholerange2'  # Enter the name of your folder
gas_ratio = [100, 90, 80, 60, 40, 20, 10, 1, 0.5, 0.2, 0.05, 0.01] #Enter the ratio you want to try in list

#%% GC method setting
gc = GC_Connector() #reopen the peaksimple software before running this command
data_path = f'C:/Users/guazh/data/{main_folder}'  # Update your folder here
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
            datapath = os.path.join(data_path, f'{co2ratio}')
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
    folders = [folder for folder in os.listdir() if folder != ".DS_Store" and folder != "Archive" and not folder.endswith('.png') and not folder.endswith('.csv')]
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
                peak_name = 'H2 as TCD'
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
    df = df.sort_values(by='Concentration')

    from scipy.stats import linregress
    import matplotlib.pyplot as plt
    from datetime import datetime

    # Perform linear regression for the whole concentration range for both H2 and CO
    slope_H2, intercept_H2, r_value_H2, p_value_H2, std_err_H2 = linregress(df['Concentration'], df['Peak Area H2'])
    slope_CO, intercept_CO, r_value_CO, p_value_CO, std_err_CO = linregress(df['Concentration'], df['Peak Area CO'])
    print(f"Slope H2: {slope_H2}, Intercept H2: {intercept_H2}, R^2 H2: {r_value_H2**2:.2f}")
    print(f"Slope CO: {slope_CO}, Intercept CO: {intercept_CO}, R^2 CO: {r_value_CO**2:.2f}")

    # Plot the result for the whole concentration range for both H2 and CO
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(3.6, 7.2))
    ax1.scatter(df['Concentration'], df['Peak Area H2'], label='H2')
    ax1.scatter(df['Concentration'], df['Peak Area CO'], label='CO')
    ax1.plot(df['Concentration'], intercept_H2 + slope_H2*df['Concentration'], 'r', label='H2 Regression')
    ax1.set_xlabel('Concentration (ppm)')
    ax1.set_ylabel('Peak Area')
    ax1.legend()
    ax1.text(0.05, 0.95, f"H2 Slope: {slope_H2:.2f}\nH2 Intercept: {intercept_H2:.2f}\nH2 R^2: {r_value_H2**2:.2f}\nCO Slope: {slope_CO:.2f}\nCO Intercept: {intercept_CO:.2f}\nCO R^2: {r_value_CO**2:.2f}", transform=ax1.transAxes, fontsize=10, ha='left', va='top')
    ax1.set_title('Linear Regression of CO over Concentration (Whole Range)')

    ax2.plot(df['Concentration'], intercept_CO + slope_CO*df['Concentration'], 'b', label='CO Regression')
    ax2.set_xlabel('Concentration (ppm)')
    ax2.set_ylabel('Peak Area')
    ax2.legend()
    ax2.text(0.05, 0.95, f"CO Slope: {slope_CO:.2f}\nCO Intercept: {intercept_CO:.2f}\nCO R^2: {r_value_CO**2:.2f}", transform=ax2.transAxes, fontsize=10, ha='left', va='top')
    ax2.set_title('Linear Regression of H2 over Concentration (Whole Range)')
    plt.savefig('LR_whole_range.png', dpi = 600)
    plt.show()

    # Store the slope and intercept for the whole concentration range in another CSV for both H2 and CO
    calibration_data = pd.DataFrame({
        'Slope H2': [slope_H2],
        'Intercept H2': [intercept_H2],
        'Slope CO': [slope_CO],
        'Intercept CO': [intercept_CO]
    })
    datetime_str = datetime.now().strftime('%Y-%m-%d')
    calibration_filename = f"GC calibration - {datetime_str}.csv"
    calibration_data.insert(0, "Compound", ["H2", "CO"])
    calibration_data.to_csv(calibration_filename, index=False)
    print(f"Calibration data saved to {calibration_filename}")
    cali_file_path = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\DataProcessing"
    calibration_data.to_csv(os.path.join(cali_file_path, calibration_filename), index = False)
    
    
    
    
#%%
if __name__ == "__main__":
    main_folder = '2024-12-24_wholerange2'  # Enter the name of your folder
    data_path = f'C:/Users/guazh/data/{main_folder}'  # Update your folder here
    gas_ratio = [100, 90, 80, 60, 40, 20, 10, 1, 0.5, 0.2, 0.05, 0.01] #Enter the ratio you want to try in list
    #start_measuring_calibration_curve(data_path = data_path)

    #% Experiment Finished. Start baking the column
    #baking_ctrl_file = "C:\\Peak498Win10\\GCMETHOD\\Parameter\\0622-2019_270C_50min_baking.CON" #The folder path of your baking method
    #print('Experiment Finished. Start baking the column.')
    #gc.ctrl_file = baking_ctrl_file
    #gc.load_ctrl_file()
    #gc.set_running()
    #time.sleep(3000)
    #while gc.is_running():
    #    print('Still baking. Wait for another minute.')
    #    time.sleep(60)
    DataProcessing(data_path)
    script_path = "/Closed_Loop_Platform/Utilities/slack-bot.py"
    os.system(f'python {script_path} -m "Baking completed. Please turn off FID manually"')
