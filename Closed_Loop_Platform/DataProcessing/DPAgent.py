import os
import sys
import glob
import pandas as pd
import matplotlib.pyplot as plt
import warnings
# Dynamically add the project root to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Closed_Loop_Platform.DataProcessing.gc_dataprocessing import process_asc_files

warnings.filterwarnings("ignore", category=DeprecationWarning)

Master_folder = r"/Users/Yi-An/Documents/000_Project/044_FAARM_PA-004/Data/DryRun_withDeposition"
Calibration_file = r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\DataProcessing\GC calibration - 2024-12-24.csv"
class DataProcessing:

    def __init__(self, master_folder=Master_folder, calibration_file = Calibration_file):
        self.master_folder = master_folder
        self.calibration_file = calibration_file
        self.exp_num = 1  # Experiment number to be used in file path construction
        self.database = pd.DataFrame(columns=["ExpID", "CuConc", "DepositionVoltage", "Deposition time", "CO2ratio", "IL1", "IL2", "IL3", "IL4", "IL5", "blank", "catalysis potential", "Catalysis Current", "FECO", "FEH2"])
        # Assigning calibration parameters
        if not self.calibration_file:
            raise ValueError("No calibration file found.")
        df_cali = pd.read_csv(self.calibration_file)  # Assuming the first file in the list is the correct one
        products = ['CO', 'H2']
        for product in products:
            slope, intercept = df_cali.loc[df_cali['Product'] == product, ['Slope', 'Intercept']].iloc[0]
            setattr(self, f"slope_{product}", slope)
            setattr(self, f"intercept_{product}", intercept)
        

    def gtdata(self):
        os.chdir(self.master_folder)

    def fdtitle(self, string, filename):
        """
        Find the line number where a specific string is first found in a file.
        :param string: The string to search for in the file.
        :param filename: The name of the file to search in.
        :return: The line number where the string is found, or None if not found.
        """
        flag = 0
        index = 0
        with open(filename, "r") as file1:  # Use a context manager to ensure the file is properly closed
            # Loop through the file line by line
            for line in file1:
                index += 1
                # checking string is present in line or not
                if string in line:
                    flag = 1
                    break
            # checking condition for string found or not
        if flag == 0:
            print('String', string, 'Not Found')
        else:
            return index

    def extract_catalysis_current(self):
        """
        Extract and plot the catalysis current over time for a given experiment.
        """
        self.gtdata()
        dirs = [d for d in glob.glob(f"*EXP{self.exp_num:04d}*") if not d.endswith('.log')]  # Find directories matching the experiment number and exclude those ending with .log
        os.chdir(dirs[0] if dirs else None)  # Change to the first matching directory if found
        dirs = glob.glob(f"*CO2*")  # Find directories related to CO2 and step 1
        dir = [d for d in dirs if "GC" not in d]  # Filter out directories containing "GC"
        os.chdir(dir[0] if dir else None)  # Change to the first matching directory if found
        file = glob.glob(f"*_it_Elysis_*.txt")  # Find the file containing the catalysis current data
        skiprow = self.fdtitle("Time/sec, Current/A", file[0])  # Find the line number where the data starts
        titles = ['Time second', 'Current A']  # Column titles for the DataFrame
        itcurve = pd.read_csv(file[0], skiprows=skiprow-1, header=0, names=titles)  # Read the data into a DataFrame

        def plotxy():
            """
            Plot the catalysis current over time.
            """
            plt.figure(figsize=(3.6, 3.6))  # Set the figure size
            plt.plot(itcurve['Time second'], itcurve['Current A'], marker='o', linestyle='-', color='b')  # Plot the data
            plt.title('Catalysis Current Over Time')  # Set the title
            plt.xlabel('Time (seconds)')  # Set the x-axis label
            plt.ylabel('Current (A)')  # Set the y-axis label
            plt.grid(True)  # Show the grid
            plt.savefig(os.path.join(os.getcwd(), f'{dir[0]}.png'), dpi=600)  # Save the plot
            plt.show()  # Show the plot

        plotxy()
        last_30_seconds = itcurve[itcurve['Time second'] >= itcurve['Time second'].max() - 30]
        average_current = last_30_seconds['Current A'].mean()  # Calculate the average current for the last 30 seconds
        #print(f'Average Current: {average_current} A')  # Print the average current
        return average_current  # Return the average current

    def extract_faradaic_efficienty(self, current):
        """
        Extract signal from gas chromotography and calculate the corresponding faradaic efficiency
        """
        self.gtdata()
        dirs = [d for d in glob.glob(f"*EXP{self.exp_num:04d}*") if not d.endswith('.log')]  # Find directories matching the experiment number and exclude those ending with .log
        os.chdir(dirs[0] if dirs else None)  # Change to the first matching directory if found
        dir = glob.glob(f"GC*")  # Find directories related to CO2 and step 1
        
        process_asc_files(dir[0]) # this will generate 2 csv file with integral area of every peak
        os.chdir(dir[0])
        files = glob.glob(f"peak_data*")
        area_CO = 0
        area_H2 = 0
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

            try:
                test_df = pd.read_csv(file)
                peak_area = test_df.loc[test_df['Peak Name'] == peak_name, 'Peak Area'].iloc[0]
                peak_areas[peak_name] = peak_area
            except IndexError:
                print(f"No peak found for {peak_name}. Assuming 0 concentration.")
                peak_areas[peak_name] = 0

        conc_H2 = peak_areas['H2 as TCD'] and (peak_areas['H2 as TCD'] - self.intercept_H2) / self.slope_H2 or 0  # ppm
        conc_CO = peak_areas['CO as FID'] and (peak_areas['CO as FID'] - self.intercept_CO) / self.slope_CO or 0  # ppm
        print(f'  Area H2: {peak_areas["H2 as TCD"]}; Area CO: {peak_areas["CO as FID"]}')
        #print(f'Concentration H2: {conc_H2}; Concentration CO: {conc_CO}.')

        # Convert concentration from ppm to molarity (mol/L)
        # Assuming the gas density is approximately 1.225 kg/m^3 for air at room temperature
        # and using the molar mass of CO (28.01 g/mol) and H2 (2.02 g/mol)
        molarity_CO = conc_CO * 1e-6  # Convert ppm to mol/L
        molarity_H2 = conc_H2 * 1e-6  # Convert ppm to mol/L

        FECO = molarity_CO * (1 / 22.414) * 2 * 96485 / (abs(current) * 60)  # Adjusted for molarity
        FEH2 = molarity_H2 * (1 / 22.414) * 2 * 96485 / (abs(current) * 60)  # Adjusted for molarity

        return FECO, FEH2

    def display_result(self):
        current = self.extract_catalysis_current()
        FECO, FEH2 = self.extract_faradaic_efficienty(current)

        # now I got the output data, current, FECO, FEH2. I want to build a table with input and output data as follow:
        # f"*EXP{self.exp_num:04d}*", CuConc, DepositionVoltage, Deposition time,  CO2ratio, IL1, IL2, IL3, IL4, IL5, blamk, catalysis potential, Catalysis Current density, FECO, FEH2, 

        print(f"  Average Current: {current:.2e} A")
        print(f"  Faradaic Efficiency CO: {FECO:.2f}")
        print(f"  Faradaic Efficiency H2: {FEH2:.2f}")
        output = [current, FECO, FEH2]
        return current, FECO, FEH2
    
    def encode(self, x):
        id = f"EXP{self.exp_num:04d}"
        current, FECO, FEH2 = self.display_result()
        
        new_row_data = {
            'ExpID': id, 
            'CuConc': x['CuConc'], 
            'DepositionVoltage': x['Volt'], 
            'Deposition time': x['Time'], 
            'CO2ratio': x['CO2ratio'], 
            'IL1': x['IL1'], 
            'IL2': x['IL2'], 
            'IL3': x['IL3'], 
            'IL4': x['IL4'], 
            'IL5': x['IL5'], 
            'blank': x['blank'], 
            'catalysis potential': -1.6, 
            'Catalysis Current': current, 
            'FECO': FECO, 
            'FEH2': FEH2
        }

        bulk_electrolysis_potential = -1.6

        if self.database.empty:
            self.database = pd.DataFrame([new_row_data])
        else:
            if id not in self.database['ExpID'].values:
                self.database = pd.concat([self.database, pd.DataFrame([new_row_data])], ignore_index=False)
            else:
                self.database.loc[self.database['ExpID'] == id, list(new_row_data.keys())] = list(new_row_data.values())
        
        self.database.to_csv(os.path.join(self.master_folder,'experiment_data.csv'), index=False)

        return bulk_electrolysis_potential, current, FECO

'''
DataAgent = DataProcessing(Master_folder, Calibration_file)

# for batch processing
for i in range(1,3):
    DataAgent.exp_num = i
    print(i)
    DataAgent.display_result()
'''