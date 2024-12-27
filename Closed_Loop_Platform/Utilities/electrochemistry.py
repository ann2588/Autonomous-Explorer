import numpy as np
import pandas as pd
import Closed_Loop_Platform.pytentiostats as pstat
global pstat, model, path
import os, time, datetime
from datetime import datetime
import matplotlib.pyplot as plt
from .liquidhandling import stirring, plate, Rinsing
from scipy.signal import savgol_filter
import seaborn as sns
import warnings
import glob
cat = str()
# %% Basic setting
message_completed = 'Experiment completed'
message_stuck = 'Unusual impedence in electrolyte, Check if the tube stuck'
script_path = 'C:\\Users\\guazh\\PycharmProjects\\CO2Platform\\Closed_Loop_Platform\\Utilities\\slack-bot.py'
default_path = "C:/Users/guazh/data"
np.errstate(divide='ignore')
warnings.simplefilter(action='ignore', category=(FutureWarning))

# CHI Setting
global model, path
model = 'chi760f'
path = 'C:/chi'

#%% Echem utilities. Data handling
def create_directory(path):
    """Create a directory if it doesn't already exist."""
    try:
        os.mkdir(path)
    except FileExistsError:
        print(f"{path} already exists.")
def generate_timestamp():
    """Generate a timestamp string."""
    datetime_str = datetime.now().isoformat(timespec='seconds')
    return datetime_str.replace(" ", "_").replace(":", "_")
def getOCP(child_filepath, time_ocp=5):
    model = 'chi760f'
    path = 'C:/chi'
    pstat.Setup(model=model, path_exe=path, folder=child_filepath)
    print('Measuring OCP')
    ocpname = f"OCP_{generate_timestamp()}"
    ocp = pstat.OCP(ttot=time_ocp, dt=0.01, fileName=ocpname, header = 'OCP', )
    time.sleep(10)
    ocp.run()
    time.sleep(5)
    ocp_data = pstat.LoadOCP(ocpname, folder=child_filepath, model=model)
    print('Finished measuring OCP\n')
    print('Waiting 15 s')
    time.sleep(15)
    print('Finished waiting\n')
    return ocp_data.E

def getRu(child_filepath, ocp_data_E):
    print('Measuring EIS at OCP and get Ru')
    Eini = np.mean(ocp_data_E)
    runame = f"EIS_{generate_timestamp()}"
    eis = pstat.EIS(Eini=Eini, fl=5e5, fh=1e6, amp=0.005, fileName=runame, header='EIS for Ru')
    time.sleep(5)
    eis.run()
    time.sleep(5)
    eis_data = pstat.LoadEIS(runame, folder=child_filepath, model='chi760e')
    Ru = eis_data.rZ[np.argmax(eis_data.iZ)]
    print('Finished measuring EIS at OCP and get Ru\n')
    print(f'Ru: {Ru}')
    print('Waiting 15 s')
    time.sleep(15)
    print('Finished waiting\n')
    return Ru

def LSV_converter_inexp(potential, current, bicarbonate=False):
    '''
    Convert LSV from Ag/AgCl to RHE scale
    '''
    evsrhe = potential + 0.205 + (6.8 if bicarbonate else 13.7) * 0.059
    currend = -current * 2 * 1000  # for 1 cm2 plate. Both side. Unit mA cm-2
    # Todo write a file exported as txt.
    return {'potential_RHE': evsrhe, 'current_density': currend}

def LSV_getoverpotential(x, y, criteria):
    '''
    input: LSV curve
    return: potential at criteria current
    '''
    smoothed_x = savgol_filter(x, window_length=5, polyorder=3, mode='nearest')
    smoothed_y = savgol_filter(y, window_length=5, polyorder=3, mode='nearest')
    #plt.plot(smoothed_x, smoothed_y)
    return np.interp(criteria, smoothed_y, smoothed_x)

def plot_cv_data(cvrhe, filepath, filename, xlim=None, ylim=None):
    """
    This function plots the CV data.
    :param cvrhe: Dictionary containing 'potential_RHE' and 'current_density'
    :param filepath: Path to save the plot
    :param filename: Name of the file to save the plot
    """
    plt.figure()
    plt.plot(cvrhe['potential_RHE'], cvrhe['current_density'])
    plt.xlabel('Potential (V vs. RHE)')
    plt.ylabel('Current Density (mA cm-2)')
    plt.title('CV')
    if xlim is not None:
        plt.xlim(xlim)
    if ylim is not None:
        plt.ylim(ylim)
    plt.savefig(os.path.join(filepath, f"{filename}.png"))
    plt.show()
def find_nearest_index(cvref_E, Ev1, threshold=0.0005):
    """
    Find the index of the element in cvref.E that is closest to Ev1 and the difference is less than threshold.
    """
    differences = np.abs(cvref_E - Ev1)
    valid_indices = np.where(differences < threshold)
    if len(valid_indices) == 0:
        raise ValueError("No valid index found with the given threshold.")
    return valid_indices
def save_cvrhe_to_txt(cvrhe, filepath, filename):
    """
    This function saves the CV data to a text file with comma-separated values.
    :param cvrhe: Tuple containing potential_RHE and current_density
    :param filepath: Path to save the text file
    :param filename: Name of the file to save the text file
    """
    txt_filename = f"{filename}vsRHE.txt"
    with open(os.path.join(filepath, txt_filename), 'w') as f:
        f.write("Potential V vs RHE, Current mA cm-2\n")
        for potential, current in zip(cvrhe['potential_RHE'], cvrhe['current_density']):
            f.write(f"{potential},{current}\n")

#%% Echem utilities. Potentiostat
def run_ca(time=120, Hz=1, sensitivity=1e-3):
    caname = f"CA_{generate_timestamp()}"
    caheader = 'CA'
    ca = pstat.CA(Estep=1, Ehigh=1, Elow=-1.5, dt=0.1, ttot=1 / Hz, sens=sensitivity, fileName=caname, header=caheader, tstep=time + 1)
    ca.run()
    return caname

def LSV_HER(mainpath, sample, note='LSVinKOH', criteria_current=10):
    '''
    This function do LSV scan automatically and extend potential until the max reach 10mA cm-2 #Todo
    :param mainpath: The path to store the data
    :param sample: Your Sample name
    :param note: This LSV typically run in KOH
    :param criteria_current: current density in positive value (deal with negative value)
    :return: Overpotential in negative value
    '''
    filename = sample
    main_filepath = mainpath
    create_directory(main_filepath)

    datetime_str = generate_timestamp()
    adding = f'{sample}-{datetime_str}-{note}'

    child_filepath = os.path.join(main_filepath, adding)
    create_directory(child_filepath)

    #model = 'chi760f'
    #path = 'C:/chi'
    pstat.Setup(model=model, path_exe=path, folder=child_filepath)

    # N2 Purging at 20 sccm for 30 mins
    print('Start purging N2 for 30 mins')
    #asyncio.run(MFC.n2on())
    #time.sleep(1800)
    #asyncio.run(MFC.n2off())
    print('Stop purging')


    stirring(plate, 30)
    time.sleep(30)

    ocp_data_E = getOCP(child_filepath)
    Ru = getRu(child_filepath, ocp_data_E)

    # LSV measurement
    # plate.start_stirring()
    Efin_LSV = -1.7
    sr_lsv = 0.050
    max_current = 0
    plt.figure()
    plt.xlim(0, -1.6)
    plt.ylim(0, -15.0)
    plt.xlabel('E (V vs. RHE)')
    plt.ylabel('Current Density (mA cm-2)')
    eta = 0

    while max_current <= criteria_current and Efin_LSV >= -3.0:
        print(f'Measuring LSV at {sr_lsv} V/s')
        fileName = filename + '_LSV_{:.0f}mVs_Efin_{:.0f}mV'.format(sr_lsv * 1000, Efin_LSV * 1000)
        header = 'LSV ran at {:.0f} mVs with Efin at {:.0f}mV'.format(sr_lsv * 1000, Efin_LSV * 1000)
        lsv = pstat.LSV(Eini=-0.6, Efin=Efin_LSV, sr=sr_lsv, dE=0.001, sens=1e-4, fileName=fileName,
                        header=header)  # E to be customized
        lsv.ircomp(Ru=Ru)  # Ru get from EIS
        time.sleep(5)
        lsv.run()
        time.sleep(5)
        # plate.stop_stirring()
        data = pstat.LoadLSV(fileName, folder=child_filepath, model=model)
        lsvrhe = LSV_converter_inexp(data.E, data.i, phosphate=True)
        max_current = max(-lsvrhe['current_density'])
        print(lsvrhe['potential_RHE'])
        plt.plot(lsvrhe['potential_RHE'], lsvrhe['current_density'])
        plt.xlabel('E (V vs. RHE)')
        plt.ylabel('Current Density (mA cm-2)')
        # plt.legend(title=f'{sample}')
        print('Finished measuring LSV')
        # stirring
        stirring(plate, stirring_time=30)
        print('Waiting 15 s')
        time.sleep(15)
        print('Finished waiting\n')
        if max_current > criteria_current:
            smoothed_x = savgol_filter(np.asarray(lsvrhe['potential_RHE']), window_length=5, polyorder=3,
                                       mode='nearest')
            smoothed_y = savgol_filter(np.asarray(lsvrhe['current_density']), window_length=5, polyorder=3,
                                       mode='nearest')
            # Debug statements to check the shapes and contents of the arrays
            print(f"Shape of smoothed_x: {smoothed_x.shape}")
            print(f"Shape of smoothed_y: {smoothed_y.shape}")

            # Ensure the arrays are 1-dimensional
            if smoothed_x.ndim > 1:
                smoothed_x = smoothed_x.flatten()
            if smoothed_y.ndim > 1:
                smoothed_y = smoothed_y.flatten()
            plt.plot(smoothed_x, smoothed_y)
            eta = np.interp(-criteria_current, smoothed_y, smoothed_x)
            print(eta)
            # Store eta here
            plt.legend(title=f'{sample}')
            plt.savefig(child_filepath + '/' + fileName + '.png')
            plt.show()
            break
        else:
            Efin_LSV -= 0.2
            print(
                f'Maximum current density = {max_current}  < {criteria_current} mA. extend the potential window to {Efin_LSV}')
    plt.show()
    return eta


def LSV_Regeneration(mainpath, sample, note='LSVinHCO3', Efin_LSV=-2.1, current_criteria=5):
    ''' #Todo merge it with the LSV_HER(), there are basically the same with different parameters
    This function run LSV scan automatically and extend potential until the current reach current_criteria mA cm-2 #Todo
    :param mainpath: The path to store the data
    :param sample: Your Sample name
    :param note: This LSV typically run in Phosphate buffer
    :param criteria_current: current density in positive value (deal with negative value)
    :return: Onsetpotential V vs. RHE in negative value
    '''
    filename = sample
    main_filepath = mainpath
    create_directory(main_filepath)

    datetime_str = generate_timestamp()
    adding = f'{sample}-{datetime_str}-{note}'

    child_filepath = os.path.join(main_filepath, adding)
    create_directory(child_filepath)

    model = 'chi760f'
    path = 'C:/chi'
    pstat.Setup(model=model, path_exe=path, folder=child_filepath)

    stirring(plate, 30)
    time.sleep(30)

    ocp_data_E = getOCP(child_filepath)
    Ru = getRu(child_filepath, ocp_data_E)

    # LSV measurement
    # plate.start_stirring()
    # Efin_LSV = -2.1
    sr_lsv = 0.050
    max_current = 0
    plt.figure()
    plt.xlim(0, -1.75)
    plt.ylim(0, -5.0)
    plt.xlabel('E (V vs. RHE)')
    plt.ylabel('Current Density (mA cm-2)')
    onset = 0
    while max_current <= current_criteria and Efin_LSV >= -2.5:
        print(f'Measuring LSV at {sr_lsv} V/s')
        fileName = filename + '_LSV_{:.0f}mVs_Efin_{:.0f}mV'.format(sr_lsv * 1000, Efin_LSV * 1000)
        header = 'LSV ran at {:.0f} mVs with Efin at {:.0f}mV'.format(sr_lsv * 1000, Efin_LSV * 1000)
        lsv = pstat.LSV(Eini=-0.6, Efin=Efin_LSV, sr=sr_lsv, dE=0.001, sens=1e-4, fileName=fileName,
                        header=header)  # E to be customized
        lsv.ircomp(Ru=Ru)  # Ru get from EIS
        time.sleep(5)
        lsv.run()
        time.sleep(5)
        # plate.stop_stirring()
        data = pstat.LoadLSV(fileName, folder=child_filepath, model=model)
        lsvrhe = LSV_converter_inexp(data.E, data.i, phosphate=True)
        max_current = max(-lsvrhe['current_density'])
        print(lsvrhe['potential_RHE'])
        plt.plot(lsvrhe['potential_RHE'], lsvrhe['current_density'])
        plt.xlabel('E (V vs. RHE)')
        plt.ylabel('Current Density (mA cm-2)')
        plt.xlim(0,-1.6)
        # plt.legend(title=f'{sample}')
        print('Finished measuring LSV')
        # stirring



        if max_current > current_criteria:
            smoothed_x = savgol_filter(np.asarray(lsvrhe['potential_RHE']), window_length=5, polyorder=3, mode='nearest')
            smoothed_y = savgol_filter(np.asarray(lsvrhe['current_density']), window_length=5, polyorder=3, mode='nearest')
            # Debug statements to check the shapes and contents of the arrays
            print(f"Shape of smoothed_x: {smoothed_x.shape}")
            print(f"Shape of smoothed_y: {smoothed_y.shape}")

            # Ensure the arrays are 1-dimensional
            if smoothed_x.ndim > 1:
                smoothed_x = smoothed_x.flatten()
            if smoothed_y.ndim > 1:
                smoothed_y = smoothed_y.flatten()
            plt.plot(smoothed_x, smoothed_y)
            onset =  np.interp(-current_criteria, smoothed_y, smoothed_x)
            #onset = LSV_getoverpotential(lsvrhe['potential_RHE'], lsvrhe['current_density'], -current_criteria)
            plt.legend()
            plt.savefig(child_filepath + '/' + fileName + '.png')
            plt.show()
        else:
            Efin_LSV -= 0.2
            print(
                f'Maximum current density = {max_current}  < {current_criteria} mA. extend the potential window to {Efin_LSV}')
        stirring(plate, stirring_time=30)
    plt.show()

    # onset = onset-0.205-7.6*0.059 #convert V vs. RHE back to V vs. Ag/AgCl scale
    return onset  # in RHE scale

def LSV_fixrange(mainpath:str, sample:str, note='LSVinHCO3', Efin_LSV=-2.3):
    '''
    This function do LSV scan automatically within fix potential range [-0.9, -2.3]
    :param mainpath: The path to store the data
    :param sample: Your Sample name
    :param note: This LSV typically run in KOH
    :return: The maximum current density
    '''
    filename = sample
    main_filepath = mainpath
    create_directory(main_filepath)

    datetime_str = generate_timestamp()
    adding = f'{sample}-{datetime_str}-{note}'

    child_filepath = os.path.join(main_filepath, adding)
    create_directory(child_filepath)

    model = 'chi760e'
    path = 'C:/chi'
    pstat.Setup(model=model, path_exe=path, folder=child_filepath)

    stirring(plate, 30)
    time.sleep(30)

    ocp_data_E = getOCP(child_filepath)
    Ru = getRu(child_filepath, ocp_data_E)

    # LSV measurement
    # plate.start_stirring()
    # Efin_LSV = -2.1
    sr_lsv = 0.050
    max_current = 0
    plt.figure()
    plt.xlim(0, -2.0)
    plt.ylim(0, -5.0)
    plt.xlabel('E (V vs. RHE)')
    plt.ylabel('Current Density (mA cm-2)')
    print(f'Measuring LSV at {sr_lsv} V/s')
    fileName = filename + '_LSV_{:.0f}mVs_Efin_{:.0f}mV'.format(sr_lsv * 1000, Efin_LSV * 1000)
    header = 'LSV ran at {:.0f} mVs with Efin at {:.0f}mV'.format(sr_lsv * 1000, Efin_LSV * 1000)
    lsv = pstat.LSV(Eini=-0.6, Efin=Efin_LSV, sr=sr_lsv, dE=0.001, sens=1e-4, fileName=fileName,
                    header=header)  # E to be customized
    lsv.ircomp(Ru=Ru)  # Ru get from EIS
    time.sleep(5)
    lsv.run()
    time.sleep(5)
    plate.stop_stirring()
    data = pstat.LoadLSV(fileName, folder=child_filepath, model=model)
    lsvrhe = LSV_converter_inexp(data.E, data.i, phosphate=True)
    #ndata_E, ndata_i = LSV_converter_inexp(data.E, data.i, phosphate=True)
    smoothed_x = savgol_filter(np.asarray(lsvrhe['potential_RHE']), window_length=5, polyorder=3, mode='nearest')
    smoothed_y = savgol_filter(np.asarray(lsvrhe['current_density']), window_length=5, polyorder=3, mode='nearest')
    # Debug statements to check the shapes and contents of the arrays
    print(f"Shape of smoothed_x: {smoothed_x.shape}")
    print(f"Shape of smoothed_y: {smoothed_y.shape}")

    # Ensure the arrays are 1-dimensional
    if smoothed_x.ndim > 1:
        smoothed_x = smoothed_x.flatten()
    if smoothed_y.ndim > 1:
        smoothed_y = smoothed_y.flatten()
    plt.plot(smoothed_x, smoothed_y)
    onsetP = np.interp(-5, smoothed_y, smoothed_x)
    #onsetP = LSV_getoverpotential(ndata_E, ndata_i[:, 0], -5)
    plt.plot(lsvrhe['potential_RHE'], lsvrhe['current_density'])
    print('Finished measuring LSV')
    # stirring
    stirring(plate, stirring_time=30)
    print('Waiting 15 s')
    time.sleep(15)
    print('Finished waiting\n')
    plt.legend()
    plt.savefig(child_filepath + '/' + fileName + '.png')
    plt.show()
    return onsetP


def electrodeposition(mainpath, sample, E_ed, Time_ed, note='Deposition'):
    '''
    This function perform electrodeposition with designated potential and time
    :param mainpath: The dic you want to store your data
    :param sample: Sample name
    :param E_ed: Potential for electrodeposition in negative value
    :param Time_ed: Deposition time in second
    :param note:
    :return: #Todo Return integrated C
    '''
    # CHI Settings

    filename = sample
    main_filepath = mainpath
    create_directory(main_filepath)

    datetime_str = generate_timestamp()
    adding = f'{sample}-{datetime_str}-{note}'

    child_filepath = os.path.join(main_filepath, adding)
    create_directory(child_filepath)

    model = 'chi760f'
    path = 'C:/chi'
    pstat.Setup(model=model, path_exe=path, folder=child_filepath)

    stirring(plate, 30)
    time.sleep(30)

    ocp_data_E = getOCP(child_filepath)
    Ru = getRu(child_filepath, ocp_data_E)

    # deposition start
    print('Electrodeposition started.')
    plate.start_stirring()
    time.sleep(15)
    fileName = sample + '_it_Edep_{:.0f}mV'.format(E_ed * 100)
    header = 'Electrodeposition at potential = {:.1f}mV'.format(E_ed)
    itcurve = pstat.i(Eini=E_ed, dt=0.1, ttot=Time_ed, sens=1e-3, fileName=fileName, header=header)  # Todo
    itcurve.ircomp(Ru=Ru)  # Ru get from EIS
    itcurve.run()
    time.sleep(5)
    plate.stop_stirring()
    itcurve_data = pstat.LoadITCURVE(fileName=fileName, folder=child_filepath, model=model)
    plt.figure()
    plt.plot(itcurve_data.t, -itcurve_data.i / 0.0706858 * 1000)
    plt.xlabel('$Time$ / s')
    plt.ylabel('Current density (mA cm-2)')
    plt.legend(title=f'E = {E_ed}')
    plt.savefig(child_filepath + '/' + 'ITCURVE' + '.png')
    plt.show()
    print('Finished electrodeposition\n')
    print('Waiting 15 s')
    time.sleep(15)
    print('Finished waiting\n')
    # charge = np.trapz(itcurve_data.i[:,0],itcurve_data.t)


def insitu_echem_regeneration_HER(mainpath: str):
    '''
    This function perform electrode regeneration by following procedure
    1. Rinsing Cell with water and 50 mM phosphate buffer
    2. Record LSV in Phosphate buffer as criteria for Pre-Regeneration with 5 mA as current criteria
    3. Rinse cell with 1 M HNO3 and stir for 10 mins
    4. Change solvent to phosphate and run ACV for 180 s at 1 hz, +1V, -1.5V
    5. Record LSV in Phosphate buffer as criteria for Post-Regeneration with 1 mA as current criteria
    6. If onsetpotential at 5 mA difference < 0.01 V, current converged. If not, go back to step 5.
    7. If the onset potential @ 5 mA cm-2 < criteria -1.5 V vs. RHE. If not, current converged but potential not reach criteria, go back to Step3 again.
    8. If  rinse_times > 3, the catalyst cannot be removed by regeneration protocol. Error report. and (Supposedly) break function.
    NOTE: NOT INCLUDE LSV IN KOH
    The criteria should correspond to the criteria of onset potential @ 10 mA cm -2 < -1.0 V vs. RHE
    :param mainpath: your dictionary
    :return: None
    :Todo:
    '''
    model = 'chi760f'
    path = 'C:/chi'  # Folder where the chi760e.exe is located #Todo
    pstat.Setup(model=model, path_exe=path, folder=mainpath)
    Rinsing('water', 'phosphate', 1)
    LSV_Regeneration(mainpath, f'Pre-Regen', current_criteria=2, Efin_LSV=-1.9)
    print('Electrode Regeneration start...')
    rinse_times = 1
    onset_array = []
    while rinse_times <= 3:
        Rinsing('water', 'hno3', acidrinse=True, repetitions=1)
        Rinsing('water', 'regen', 1)
        run_ca(180)
        i = 1
        # Set the onset potential at 10 mA because the potential curve can growth really fast before any generation
        onset = LSV_Regeneration(mainpath, f'{rinse_times}acid_{i}ac', current_criteria=2)  # set criteria for onset potential
        onset_array.append(onset)  # Ag/AgCl scale
        print('onset_array: ', onset_array)
        bkg_array = []
        bkg = 0
        Converged = True
        while Converged:
            i += 1
            run_ca(180)
            bkg = LSV_fixrange(mainpath, f'{rinse_times}acid_{i}ac', Efin_LSV=-2.3)
            # RUN LSV FOR SINGLE LINE IN RANGE FROM INIAL TO ONSET POTENTIAL AND RETURN THE MAX CURRENT
            bkg_array.append(bkg)
            print('bkg_array: ', bkg_array)
            if i > 8:
                print('Error: Current didn\'t converge. Check the status of electrode or rinsed by acid again')
                break
            if len(bkg_array) >= 2:
                if abs((bkg_array[-1] - bkg_array[-2])) <= 0.01:
                    Converged = False
                    print('Current difference: ', (bkg_array[-1] - bkg_array[-2]))
                    print('Current decay converged. Check the Onset potential again')
                else:
                    print('Current difference: ', (bkg_array[-1] - bkg_array[-2]))
                    print('Current is still decaying. Run another AC again')
            else:
                continue

        post_onset = LSV_Regeneration(mainpath, f'Post-Regen{rinse_times}', Efin_LSV=-2.3, current_criteria=2)
        onset_array.append(post_onset)  # in RHE
        print('Onset array : ', onset_array)  # write it into CSV
        e_criteria = -1.5  # V vs RHE at 5 mA cm^2, should correspond to -1.0 at 10 mA cm^2 in KOH
        if post_onset <= e_criteria or post_onset == 0:  # both in RHE
            print(
                f'Onset potential at 1 mA is {post_onset} V vs Ag/AgCl. reaching minimum. Electrode Regeneration completed')
            break
        elif post_onset == 0:
            print('Onset potential cannot reach 1 mA at -2.5 V vs Ag/AgCl. Electrode inert enough. Electrode Regeneration completed')

        else: #post_onset >= e_criteria
            rinse_times += 1
            print(f'Onset potential {post_onset} didnt reach minimum. Rinsed by acid again')
            if rinse_times == 3:
                print(f'Error: Catalyst cannot be removed by regeneration protocol. Please check the electrode')
    # cell_rinsing('water','koh', 1)
    # eta = LSV_HER(mainpath, 'RegeneratedGCEinKOH', criteria_current = 5)
    # print(eta)
    # if eta < -1.5:
    #    print(f'Onset potential {eta} V vs. RHE lower than criteria -1.6 V vs RHE in KOH. Please check the electrode')


def insitu_echem_regeneration(mainpath: str):
    '''
    This function performs electrode regeneration by following procedure:
    1. Rinsing Cell with water and electrolyte
    2. Recording LSV in electrolyte under N2 as criteria for Pre-Regeneration with 5 mA as current criteria
    3. Rinsing cell with 5 M HNO3 and stirring for 20 minutes
    4. Changing solvent to electrolyte and recording LSV again to check the criteria after 1 acid rinse
    5. If the onset potential at 5 mA difference < 0.01 V, current has converged. If not, repeat step 3
    6. If the onset potential @ 5 mA cm-2 < criteria -1.5 V vs. RHE, the catalyst has been removed. If not, current has converged but potential not reached criteria, repeat step 3 again.
    7. If rinse_times > 3, the catalyst cannot be removed by regeneration protocol. Error report. and (Supposedly) break function.
    '''

    Rinsing('cell', 'water', 'electrolyte', 3, volume_assigned='50mL')
    LSV_Regeneration(mainpath, f'Pre-Regen', current_criteria=2, Efin_LSV=-1.9)
    print('Electrode Regeneration start...')
    rinse_times = 1
    onset_array = []
    while rinse_times <= 5:
        Rinsing('cell','water', 'hno3', acidrinse=True, repetitions=1)
        Rinsing('cell', 'water', 'electrolyte', 1)
        onset = LSV_Regeneration(mainpath, f'{rinse_times}acid', current_criteria=2)
        onset_array.append(onset)
        print('onset_array: ', onset_array)
        bkg_array = []
        Converged = True
        while Converged:
            bkg = LSV_fixrange(mainpath, f'{rinse_times}acid', Efin_LSV=-2.3)
            bkg_array.append(bkg)
            print('bkg_array: ', bkg_array)
            if len(bkg_array) >= 2 and abs((bkg_array[-1] - bkg_array[-2])) <= 0.01:
                Converged = False
                print('Current difference: ', (bkg_array[-1] - bkg_array[-2]))
                print('Current decay converged. Check the Onset potential again')
            elif rinse_times > 3:
                print('Error: Current didn\'t converge. Check the status of electrode or rinsed by acid again')
                break
        post_onset = LSV_Regeneration(mainpath, f'Post-Regen{rinse_times}', Efin_LSV=-2.3, current_criteria=2)
        onset_array.append(post_onset)
        print('Onset array : ', onset_array)
        e_criteria = -1.5
        if post_onset <= e_criteria or post_onset == 0:
            print(f'Onset potential at 1 mA is {post_onset} V vs Ag/AgCl. reaching minimum. Electrode Regeneration completed')
            break
        elif post_onset == 0:
            print('Onset potential cannot reach 1 mA at -2.5 V vs Ag/AgCl. Electrode inert enough. Electrode Regeneration completed')
        else:
            rinse_times += 1
            print(f'Onset potential {post_onset} didnt reach minimum. Rinsed by acid again')
            if rinse_times == 3:
                print(f'Error: Catalyst cannot be removed by regeneration protocol. Please check the electrode')




def run_CV_HER_lowE(mainpath, sample, Note, sr_cv=50):
    """
    Run a CV experiment and save the results.

    Parameters:
    - mainpath: The main directory path for saving results.
    - sample: Sample name as a string.
    - Note: Note to add to the directory name.
    - sr_cv: Scan rate for CV, default is 50.
    """
    main_filepath = mainpath
    create_directory(main_filepath)

    datetime_str = generate_timestamp()
    adding = f'{sample}-{datetime_str}-{Note}'
    child_filepath = os.path.join(main_filepath, adding)
    create_directory(child_filepath)

    #model = 'chi760e'
    #path = 'C:/chi'  # Path to the chi760e.exe
    pstat.Setup(model=model, path_exe=path, folder=child_filepath)
    filename = sample

    # Stirring the plate for 30 seconds
    time.sleep(30)

    ocp_data_E = getOCP(child_filepath)
    Ru = getRu(child_filepath, ocp_data_E)
    ocp_data_E = np.mean(ocp_data_E)
    print(ocp_data_E)

    Eini, Ev1, Ev2, Efin = -1.00, -1.4, -1.00, -1.00
    stirring(plate, 60)
    fileName = f'{filename}_CV_{sr_cv / 1000:.0f}mVs'
    cvheader = f'CV ran at {sr_cv / 1000:.0f} mVs'
    sr_cv /= 1000

    cv = pstat.CV(
        Eini=Eini, Ev1=Ev1, Ev2=Ev2, Efin=Efin, nSweeps=10, dE=0.001, sr=sr_cv,
        sens=1E-3, fileName=fileName, header=cvheader, qt=60
    )

    cv.ircomp(Ru=Ru)
    time.sleep(5)
    cv.run()
    time.sleep(5)

    data = pstat.LoadCV(fileName, folder=child_filepath, model=model)
    plot_cv_data(data, child_filepath, fileName)

    print(f'Finished measuring CV at {sr_cv * 1000:.0f} mV/s')
    plate.stop_stirring()
    time.sleep(15)

    return cv
def run_CV_HER_varyE(mainpath, sample, gas, sr_cv=50):
    """
    Run a CV experiment and save the results.

    Parameters:
    - mainpath: The main directory path for saving results.
    - sample: Sample name as a string.
    - sr_cv: Scan rate for CV, default is 50.
    """
    main_filepath = mainpath
    create_directory(main_filepath)

    datetime_str = generate_timestamp()
    adding = f'{sample}-{datetime_str}-{gas}'
    child_filepath = os.path.join(main_filepath, adding)
    create_directory(child_filepath)

    #model = 'chi760e'
    #path = 'C:/chi'  # Path to the chi760e.exe
    pstat.Setup(model=model, path_exe=path, folder=child_filepath)
    filename = sample

    # Stirring the plate for 30 seconds
    time.sleep(30)
    sr_cv = 50
    ocp_data_E = getOCP(child_filepath)
    Ru = getRu(child_filepath, ocp_data_E)
    if gas == 'H2KOH' and Ru > 3:
        Ru_temp = getRu(child_filepath, ocp_data_E)
        if Ru_temp > 6:
            os.system(f'python {script_path} -m "{message_stuck}"')
            breakpoint()
        else: Ru = Ru_temp
    ocp_data_E = np.mean(ocp_data_E)
    print(f'OCP: {ocp_data_E}')

    Eini, Ev1, Ev2, Efin = -1.00, -1.4, -1.00, -1.00
    while Ev1 >= -3.0:
        #stirring(plate, 60)
        fileName = f'{filename}_CV_{sr_cv:.0f}mVs_Efin_{Ev1*1000:.0f}mV'
        cvheader = f'CV ran at {sr_cv:.0f} mVs'
        cv = pstat.CV(
            Eini=Eini, Ev1=Ev1, Ev2=Ev2, Efin=Efin, nSweeps=6, dE=0.001, sr=sr_cv/1000,
            sens=1E-3, fileName=fileName, header=cvheader, qt=60
        )
        cv.ircomp(Ru=Ru)
        time.sleep(5)
        cv.run()
        time.sleep(5)

        cvref = pstat.LoadCV(fileName, folder=child_filepath, model=model)
        cvrhe = LSV_converter_inexp(cvref.E, cvref.i[:,0])
        plot_cv_data(cvrhe, child_filepath, fileName)
        save_cvrhe_to_txt(cvrhe, child_filepath, fileName)
        current_threshold = 7.07E-4 # current density 10 mA cm-2
        nearest_index = find_nearest_index(cvref.E, Ev1,0.0005)  # Find the index of the nearest x-value
        y_at_Ev1 = cvref.i[nearest_index, 0]  # Get the y-value at the nearest x-value

        # Check if y value is below the threshold
        if y_at_Ev1[0][-1] < 7.07E-5:
            Ev1 -= 0.2
        elif y_at_Ev1[0][-1] > 3.5E-3:
            sr_cv = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]
            for sr in sr_cv:

                fileName = f'{filename}_CV_sr_{sr:.0f}mVs_Efin_{Ev1 * 1000:.0f}mV'
                cvheader = f'CV ran at {sr:.0f} mVs'
                cv2 = pstat.CV(
                    Eini=Eini, Ev1=Ev1, Ev2=Ev2, Efin=Efin, nSweeps=2, dE=0.001, sr=sr / 1000,
                    sens=1E-2, fileName=fileName, header=cvheader, qt=2
                )
                cv2.ircomp(Ru=Ru)
                time.sleep(5)
                cv2.run()
                time.sleep(5)

                cvref = pstat.LoadCV(fileName, folder=child_filepath, model=model)
                cvrhe = LSV_converter_inexp(cvref.E, cvref.i[:, 0])
                plot_cv_data(cvrhe, child_filepath, fileName)
                save_cvrhe_to_txt(cvrhe, child_filepath, fileName)
            break
        else:
            Ev1 -= 0.1

        print(f'Finished measuring CV at {sr_cv} mV/s with Efin at {Ev1 * 1000:.0f} V')
        plate.stop_stirring()
        time.sleep(15)
    # This line didnt work, the plot should be processed later after the experiment
    files = glob.glob('*mVvsRHE*')
    sns.set_palette("flare", 8)
    for file in files:
        df = pd.read_csv(file)
        plt.plot(df['Potential V vs RHE'], df[' Current mA cm-2'])
    plt.xlabel('Potential (V vs RHE)')
    plt.ylabel('Current Density (mA cm-2)')
    plt.savefig(os.path.join(child_filepath, f"{filename}.png"))
    plt.show()

    return cv

    #indices = find_nearest_index(cvref.E, min_potential value, 0.0005)
    #for idx in indices:
    #    plt.plot(cvref.E[idx], cvref[])
def run_CV_varysr(mainpath, sample, sr_cv, Rus = None):
    """
    Run a CV experiment and save the results.

    Parameters:
    - mainpath: The main directory path for saving results.
    - sample: Sample name as a string.
    - sr_cv: Scan rate for CV, default is 50.
    """

    main_filepath = mainpath
    create_directory(main_filepath)

    datetime_str = generate_timestamp()
    adding = f'{sample}-{datetime_str}'
    child_filepath = os.path.join(main_filepath, adding)
    create_directory(child_filepath)

    model = 'chi760f'
    path = 'C:/chi'  # Path to the chi760e.exe
    pstat.Setup(model=model, path_exe=path, folder=child_filepath)
    filename = sample

    # Stirring the plate for 30 seconds
    stirring(plate)
    time.sleep(30)
    ocp_data_E = getOCP(child_filepath)
    Ru = getRu(child_filepath, ocp_data_E)


    Eini, Ev1, Ev2, Efin = -0.0, -2.2, -0.0, -0.0
    #sr_cv = [1500, 800, 500, 200, 100, 20, 10, 1]
    #Rus = [20000000000000, 15000000000000, 10000000000000, 9000000000000, 3000000000, 980]
    #Rus = [750, 750, 750, 750, 750, 750, 750]

    for scan_rate, Ru in zip(sr_cv, Rus) :
        if scan_rate < 1:
            nSweeps_cv = 3
        else:
            nSweeps_cv = 6  # number of sweeps
        dE_cv = 0.001  # V, potential increment
        if scan_rate >= 70:
            sens_cv = 1e-4
        elif scan_rate >= 10:
            sens_cv = 1e-5
        elif scan_rate >= 1:
            sens_cv = 1e-5  # V/A, current sensitivity
        elif scan_rate <= 0.05:
            sens_cv = 1e-6
        else:
            sens_cv = 1e-6

        fileName = f'{filename}_CV_sr_{scan_rate:.0f}mVs_Efin_{Ev1 * 1000:.0f}mV'
        cvheader = f'CV ran at {scan_rate:.0f} mVs'
        cv2 = pstat.CV(
            Eini=Eini, Ev1=Ev1, Ev2=Ev2, Efin=Efin, nSweeps=nSweeps_cv, dE=0.001, sr=scan_rate,
            sens=sens_cv, fileName=fileName, header=cvheader, qt=2
        )
        cv2.ircomp(Ru=Ru)
        time.sleep(5)
        cv2.run()
        time.sleep(5)

        cvref = pstat.LoadCV(fileName, folder=child_filepath, model=model)
        #cvrhe = LSV_converter_inexp(cvref.E, cvref.i[:, 0])

        plt.figure(figsize=(4, 3))
        plt.plot(cvref.E, cvref.i[:, 0])
        # plt.xlim((-2.4,0.2))
        # plt.ylim((-2e-5,5e-5))
        plt.xlabel('Potential/V (vs Ag/AgCl)')
        plt.ylabel('Current/A')
        plt.title(f"{fileName}.png")
        plt.tight_layout()
        plt.savefig(os.path.join(child_filepath, f"{fileName}.png"))
        plt.show()
        #plot_cv_data(cvrhe, child_filepath, fileName)
        #save_cvrhe_to_txt(cvrhe, child_filepath, fileName)

        print(f'Finished measuring CV at {sr_cv} mV/s with Efin at {Ev1 * 1000:.0f} V')
        plate.stop_stirring()
        time.sleep(15)

def bulk_electrolysis(mainpath, sample, E_ed, Time_ed = 300, note='Electrolysis'):
    '''
    This function perform electrodeposition with designated potential and time
    :param mainpath: The dic you want to store your data
    :param sample: Sample name
    :param E_ed: Potential for electrodeposition in negative value
    :param Time_ed: Deposition time in second
    :param note:
    :return: #Todo Return integrated C
    '''
    # CHI Settings

    filename = sample
    main_filepath = mainpath
    create_directory(main_filepath)

    datetime_str = generate_timestamp()
    adding = f'{sample}-{datetime_str}-{note}'

    child_filepath = os.path.join(main_filepath, adding)
    create_directory(child_filepath)

    model = 'chi760f'
    path = 'C:/chi'  # Path to the chi760e.exe
    pstat.Setup(model=model, path_exe=path, folder=child_filepath)
    filename = sample

    # Stirring the plate for 30 seconds
    time.sleep(30)
    ocp_data_E = getOCP(child_filepath)
    Ru = getRu(child_filepath, ocp_data_E)

    # deposition start
    print('Bulk electrolysis started.')
    plate.start_stirring()
    time.sleep(15)
    fileName = sample + '_it_Elysis_{:.0f}mV'.format(E_ed * 100) + note
    header = 'Bulk electrolysis at potential = {:.1f}mV'.format(E_ed)
    itcurve = pstat.i(Eini=E_ed, dt=0.1, ttot=Time_ed, folder = child_filepath, sens=1e-3, fileName=fileName, header=header, path_exe=path)  # Todo
    itcurve.ircomp(Ru=Ru)  # Ru get from EIS
    time.sleep(5)
    itcurve.run()
    time.sleep(5)
    plate.stop_stirring()
    itcurve_data = pstat.LoadITCURVE(fileName=fileName, folder=child_filepath, model=model)
    plt.figure()
    plt.plot(itcurve_data.t, -itcurve_data.i / 0.0706858 * 1000)
    plt.xlabel('$Time$ / s')
    plt.ylabel('Current density (mA cm-2)')
    plt.legend(title=f'E = {E_ed}')
    plt.savefig(child_filepath + '/' + 'ITCURVE' + '.png')
    plt.show()
    print('Finished Bulk electrolysis\n')
    print('Waiting 15 s')
    time.sleep(15)
    print('Finished waiting\n')
    # charge = np.trapz(itcurve_data.i[:,0],itcurve_data.t)

def bulk_electrolysis_beforeCP(mainpath, sample, E_ed, Time_ed = 300, note='Electrolysis'):
    '''
    This function perform electrodeposition with designated potential and time
    :param mainpath: The dic you want to store your data
    :param sample: Sample name
    :param E_ed: Potential for electrodeposition in negative value
    :param Time_ed: Deposition time in second
    :param note:
    :return: #Todo Return integrated C
    '''
    # CHI Settings

    filename = sample
    main_filepath = mainpath
    create_directory(main_filepath)

    datetime_str = generate_timestamp()
    adding = f'{sample}-{datetime_str}-{note}'

    child_filepath = os.path.join(main_filepath, adding)
    create_directory(child_filepath)

    pstat.Setup(model=model, path_exe=path, folder=child_filepath)

    stirring(plate, 30)
    time.sleep(30)

    ocp_data_E = getOCP(child_filepath)
    global Ru
    Ru = getRu(child_filepath, ocp_data_E)

    return Ru

def bulk_electrolysis_CP(mainpath, sample, RU , E_ed, Time_ed = 960, note='Electrolysis'):
    '''
    This function perform electrodeposition with designated potential and time
    :param mainpath: The dic you want to store your data
    :param sample: Sample name
    :param E_ed: Potential for electrodeposition in negative value
    :param Time_ed: Deposition time in second
    :param note:
    :return: #Todo Return integrated C
    '''
    # CHI Settings


    filename = sample
    main_filepath = mainpath
    create_directory(main_filepath)

    datetime_str = generate_timestamp()
    adding = f'{sample}-{datetime_str}-{note}'

    child_filepath = os.path.join(main_filepath, adding)
    create_directory(child_filepath)

    model = 'chi760f'
    path = 'C:/chi'  # Path to the chi760e.exe
    pstat.Setup(model=model, path_exe=path, folder=child_filepath)

    # deposition start
    print('Bulk electrolysis started.')
    plate.start_stirring()
    time.sleep(15)
    fileName = sample + '_it_Elysis_{:.0f}mV'.format(E_ed * 100) + note
    header = 'Bulk electrolysis at potential = {:.1f}mV'.format(E_ed)
    itcurve = pstat.i(Eini=E_ed, dt=0.1, ttot=Time_ed, sens=1e-3, fileName=fileName, header=header)  # Todo
    itcurve.ircomp(Ru=RU)  # Ru get from EIS
    itcurve.run()
    time.sleep(5)
    plate.stop_stirring()
    itcurve_data = pstat.LoadITCURVE(fileName=fileName, folder=child_filepath, model=model)
    plt.figure()
    plt.plot(itcurve_data.t, -itcurve_data.i / 0.0706858 * 1000)
    plt.xlabel('$Time$ / s')
    plt.ylabel('Current density (mA cm-2)')
    plt.legend(title=f'E = {E_ed}')
    plt.savefig(child_filepath + '/' + 'ITCURVE' + '.png')
    plt.show()
    print('Finished Bulk electrolysis\n')
    print('Waiting 15 s')
    time.sleep(15)
    print('Finished waiting\n')
    # charge = np.trapz(itcurve_data.i[:,0],itcurve_data.t)