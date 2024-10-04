'''
Code for analyzing the gas chromatography data
Author: Muxing Xiong
Editor: Yi-An Lai
'''

# TestTest

import os
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from pybaselines import Baseline

def find_percent_height_indices(y_data, peak_idx, percentage):
    """ Finds indices at _percentage_ height of the peak for area calculation. """
    peak_height = y_data[peak_idx]
    percent_height = peak_height * percentage
    left_idx = peak_idx

    while left_idx > 0 and y_data[left_idx] >= percent_height:
        if not np.isnan(y_data[left_idx]):
            left_idx -= 1

    right_idx = peak_idx

    while right_idx < len(y_data) - 1 and y_data[right_idx] >= percent_height:
        if not np.isnan(y_data[right_idx]):
            right_idx += 1

    if np.isnan(y_data[left_idx]):
        left_idx += 1
    if np.isnan(y_data[right_idx]):
        right_idx -= 1

    return left_idx, right_idx

#确定region1 region2的cutoff location， 是330-400秒区域里的最低点
def find_minimum_cutoff(data, time_data, start_time=330, end_time=400):
    """ Finds the minimum value in the data within a specified time range and uses a position 10 indices to the left as the cutoff. """
    valid_indices = np.where((time_data >= start_time) & (time_data <= end_time))[0]
    if len(valid_indices) == 0:
        return len(data) - 1  # Default to end if no valid index found

    min_index = valid_indices[np.argmin(data[valid_indices])]
    return max(0, min_index - 11)

#计算面积
def calculate_area(peaks_region, combined_corrected, combined_data, gas_regions, percentage):
    peak_info_list = []

    for i, peak in enumerate(peaks_region):
        left_idx, right_idx = find_percent_height_indices(combined_corrected, peak, percentage)
        area = np.trapz(combined_corrected[left_idx:right_idx+1], combined_data['Retention Time'][left_idx:right_idx+1])
        peak_time = combined_data['Retention Time'][peak]
        identified_gas = None

        for gas, (start, end) in gas_regions.items():
            if start <= peak_time <= end:
                identified_gas = gas
                break

        if identified_gas:
            peak_name = identified_gas
        else:
            peak_name = f"Unknown Peak {i + 1}"

        peak_info_list.append([peak_name, peak_time, area])

    return peak_info_list

def analyze_intensity(data, column_name, output_filename):
    """ Analyzes intensity data, performs baseline correction, and exports the results including peak areas to a CSV file. """
    gas_regions_region1 = {
        "H2 as TCD": (51, 77.4),
        "O2 as TCD": (93.42, 109.44),
        "N2 as TCD": (118.44, 172.02),
        "CH4 as FID 1": (193.2, 235.44),
        "CO as FID": (296.4, 333.36)
    }

    gas_regions_region2 = {
        "Per Gas + CO": (392.22, 414.54),
        "CH4 as FID 2": (416.88, 432),
        "CO2 as FID": (444, 472.2),
        "H2O as TCD": (574.56, 592.68)
    }

    region_cutoff = find_minimum_cutoff(data[column_name].values, data['Retention Time'].values)

    buffer = data.iloc[region_cutoff:region_cutoff+40]
    nan_array = np.full(40, np.nan)

    region1_data = data.iloc[:region_cutoff]
    region2_data = data.iloc[region_cutoff+40:]

    baseline_fitter1 = Baseline(x_data=region1_data['Retention Time'].values)
    region1_bkg, _ = baseline_fitter1.snip(region1_data[column_name].values, min_half_window=1, max_half_window=42)
    region1_corrected = region1_data[column_name] - region1_bkg

    baseline_fitter2 = Baseline(x_data=region2_data['Retention Time'].values)
    region2_bkg, _ = baseline_fitter2.snip(region2_data[column_name].values, max_half_window=25)
    region2_corrected = region2_data[column_name] - region2_bkg

    combined_data = pd.concat([region1_data, buffer])
    combined_data = pd.concat([combined_data, region2_data])
    combined_corrected = np.concatenate((region1_corrected, nan_array))
    combined_corrected = np.concatenate((combined_corrected, region2_corrected))

    # General peak detection for Region 1 and Region 2
    peaks_region1, _ = find_peaks(region1_corrected, height=0.05, width=(0.5,80), prominence=0.5)
    peaks_region2, _ = find_peaks(region2_corrected, height=3, width=(5, 40), prominence=6)
    peaks_region2_adjusted = [int(peak + region_cutoff+40) for peak in peaks_region2]

    # Calculate areas and collect peak data
    peak_info_region1 = calculate_area(peaks_region1, combined_corrected, combined_data, gas_regions_region1, 0.05)
    peak_info_region2 = calculate_area(peaks_region2_adjusted, combined_corrected, combined_data, gas_regions_region2, 0.1)

    all_peak_info = peak_info_region1 + peak_info_region2

    # Export to CSV
    peak_df = pd.DataFrame(all_peak_info, columns=['Peak Name', 'Peak Time (s)', 'Peak Area'])
    peak_df.to_csv(output_filename, index=False)
    print(f"Saved peak data to {output_filename}")

if __name__ == "__main__":
    # Specify the folder containing the ASC files
    folder_path = f'/Users/Yi-An/Documents/000_Project/044_FAARM_PA-004/Data/Gas_calibration'
    # Pending generalizing according to folder format
    asc_files = [f for f in os.listdir(folder_path) if f.endswith('.ASC')]
    print(asc_files)

    for i, file_name in enumerate(asc_files, start=1):
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, "r", encoding='utf-8') as file:
            lines = file.readlines()

        filtered_data = []
        for line in lines:
            if line.strip().startswith('IPOINT='):
                break
            if line.strip() and ',' in line:
                filtered_data.append(line.strip().split(','))

        data = pd.DataFrame(filtered_data, columns=['Intensity_1', 'Intensity_2']).astype(float)
        # Assign retention time based on index multiplied by 0.2
        data['Retention Time'] = np.arange(len(data)) * 0.2
        data['Intensity_1'] /= 1000  # Convert from uV to mV

        # Generate a unique number for the CSV filename, padded to 3 digits
        unique_number = str(i).zfill(3)
        output_filename = f"peak_data_{unique_number}.csv"

        print(f"Analyzing {file_name} and saving results to {output_filename}...")
        analyze_intensity(data, 'Intensity_1', output_filename)
