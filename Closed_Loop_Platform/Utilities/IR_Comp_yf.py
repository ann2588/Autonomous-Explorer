"""a proof of concept experiment using Ru(bpy)3 in 0.1 M R-B buffer (not yet determined)
# objects of this experiment:
Done 1. make target solutions,
Done 2. calibrate the actual concentration
Done 3. count/record the volume/concentration change, and polishing or not at different scan rates or pH
Done 4. read and record the pH
Done 5. do the CV measurement with IR correction
Done 6. calculate the kobs at a certain pH
Done 7. set a function to determine whether to remake solutions
Done 8. pH titration module
Done 9. change the stock solution and inject using two valves
Done 10. read pH, calculate volume and concentrations
Done 11. determine if a new solution needs to be made
# for further functions:
for concentrated buffer, determine how to get the middle pH
"""
import glob, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import warnings
from tqdm import tqdm
import datetime
from scipy.signal import find_peaks, savgol_filter
from .liquidhandling import stirring, plate
import Closed_Loop_Platform.pytentiostats as pstat
plt.rcParams["figure.figsize"] = (4,3)
np.errstate(divide='ignore')
warnings.simplefilter(action='ignore', category=(FutureWarning, UserWarning))

# pump is already defined in pump.py
print('Filling the pump tubing ...')
#initialize_pump()
model = 'chi760f'
path = 'C:/chi'  # Folder where the chi760e.exe is located
file_title = 'NHPester'
time_start=datetime.datetime.now()
interval=datetime.timedelta(hours=3)
#%% definition of functions

def find_CVpeaks(data:pstat.file.LoadCV, direction='anodic'):
    global p
    x = data.E[np.where(data.E == data.E[0])[0][-2]:np.where(data.E == data.E[0])[0][-1]]
    y = data.i[np.where(data.E == data.E[0])[0][-2]:np.where(data.E == data.E[0])[0][-1]]
    x_1 = x[:np.argmin(x)]
    x_2 = x[np.argmin(x):]
    filtered1 = savgol_filter(y.reshape(-1), 101, 2)
    y_2 = filtered1[np.argmin(x):]
    y_1 = filtered1[:np.argmin(x)]
    assert direction in ['anodic','cathodic'], 'Please provide valid direction: anodic or athodic'
    if direction =='anodic':
        p_a, a = find_peaks(y_2, width=20,distance=100, prominence=abs(min(y_2)-max(y_2))/50)
        plt.plot(x_2[p_a], y_2[p_a], 'x', label=sorted(x_2[p_a].tolist()))
        plt.plot(x, y)
        try:
            E_p_1 = x_2[p_a[0]]
        except IndexError:
            E_p_1 =x_2[np.argmax(y_2)]
        return E_p_1
    elif direction =='cathodic':
        background_c = (y_1[0] - y_1[-1]) / (x_1[0] - x_1[-1]) * (x_1 - x_1[0]) + y_1[0]
        p_c = find_peaks(-y_1+background_c, width=20, prominence=abs(min(y_1)-max(y_1))/200)
        #plt.plot(x_1[p_c], y_1[p_c], 'x', label=sorted(x_1[p_c].tolist()))
        #plt.plot(x, y)
        try:
            E_p_1 = x_1[p[0]]
        except:
            E_p_1 = x_1[np.argmax(y_1)]

        return E_p_1


def Peak_est_during_measurement(data:pstat.LoadCV, scan_rate, sens_cv, step=1):
    c_2_E = data.E[np.where(data.E == data.E[0])[0][-2]:np.where(data.E == data.E[0])[0][-1]]
    c_2_i = -data.i[np.where(data.E == data.E[0])[0][-2]:np.where(data.E == data.E[0])[0][-1]]
    E_c_p = c_2_E[c_2_i.argmin()]
    E_a_p = c_2_E[c_2_i.argmax()]
    delta_E = abs(E_a_p - E_c_p)
    filteredc2i = savgol_filter(c_2_i.reshape(-1), 101, 2)
    if scan_rate < 20:
        sensitive_threshold=[50, 10, 20, 20]
    else:
        sensitive_threshold=[50, 10, 15,15]
    if scan_rate > 3:
        width = 1
    else:
        width = 2
    if scan_rate >= 20:
        peaks, _ = find_peaks(c_2_i.reshape(-1),
                              prominence=max(abs(np.min(filteredc2i) - np.max(filteredc2i)) / sensitive_threshold[0], sens_cv / sensitive_threshold[1]),
                              width=width)
    else:
        peaks, _ = find_peaks(c_2_i.reshape(-1),
                              prominence=max(abs(np.min(filteredc2i) - np.max(filteredc2i)) /sensitive_threshold[2], sens_cv / sensitive_threshold[3]),
                              width=width)

    print(f'Peak separation: {delta_E}')
    print(f'peaks: {len(peaks)}')

    return delta_E, peaks, E_c_p, E_a_p






def get_estimated_E0(E_wa, pH, redox_event=1):
    if redox_event ==1:
        if pH<=10:
            return round(E_wa-0.05*(pH-1.77),2)
        else:
            return round(E_wa - 0.05* (10- 1.77), 2)
    else:
        return min(round(E_wa-0.05*(pH-1.77),2), 1.05)


#def bubbling_N2(flow_controller,new_solution=True):

    #control_MFC(flow_controller,'open')
    #if new_solution==True:
    #    for _ in tqdm(range(600)):
    #        time.sleep(1)  #bubbling for 20 min
    #else:
    #    for _ in tqdm(range(360)):
    #        time.sleep(1)  #bubbling for 6 min
    #control_MFC(flow_controller, 'close')

def run_ocp(filepath):
    print('Measuring OCP')
    filename = f"OCP_{str(datetime.datetime.now().isoformat(timespec='seconds')).replace(' ', '_').replace(':', '_')}"
    ocp = pstat.OCP(ttot=10, dt=0.01, fileName=filename)
    ocp.run()
    ocp_data = pstat.LoadOCP(filename, folder=filepath, model=model)
    print('Finished measuring OCP')
    print('Waiting 5 s')
    time.sleep(5)
    print('Finished waiting\n')
    Eini = np.mean(ocp_data.E)  # which will be used in EIS
    return Eini


def run_eis(filepath, Eini):
    print('Measuring EIS at OCP and get Ru')
    filename=f"EIS_{str(datetime.datetime.now().isoformat(timespec='seconds')).replace(' ', '_').replace(':', '_')}"
    eis = pstat.EIS(Eini=Eini, fl=5e5, fh=1e6, amp=0.005, fileName=filename, header='EIS for Ru')
    eis.run()
    time.sleep(5)
    eis_data = pstat.LoadEIS(filename, folder=filepath, model=model)
    Ru = eis_data.rZ[np.argmax(eis_data.iZ)]  # get the Ru for IR compensation
    print(f'Finished measuring EIS at OCP and get Ru: {round(Ru,2)} Ohm\n')
    print('Waiting 5 s')
    time.sleep(5)
    print('Finished waiting\n')
    return Ru

def run_cv(E_window_a, E_window_length, scan_rate, filetitle, scan_rate_idx, Ru_test_idx, Ru_test):
     # define anything you want to include in the title
    Eini_cv = E_window_a  # V, initial potential vs Ag/AgCl
    Ev1_cv = Eini_cv  # V, first vertex potential
    Ev2_cv = Eini_cv - E_window_length  # V, second vertex potential
    Efin_cv = Eini_cv  # V, final potential
    if scan_rate <1:
        nSweeps_cv = 3
    else:
        nSweeps_cv = 6  # number of sweeps
    dE_cv = 0.001  # V, potential increment
    if scan_rate >= 500:
        sens_cv = 1e-4
    elif scan_rate >= 100:
        sens_cv = 1e-4
    elif scan_rate >= 20:
        sens_cv = 1e-5  # V/A, current sensitivity
    elif scan_rate >= 1:
        sens_cv = 1e-5
    else:
        sens_cv = 1e-6
    fileName = f"{filetitle}_{scan_rate_idx}{str(Ru_test_idx).zfill(3)}_{int(1000 * scan_rate)}mVs_{round(Ru_test)} Ohm_{str(datetime.datetime.now().isoformat(timespec='seconds')).replace(' ', '_').replace(':', '_')}"
    header = f'CVof{filetitle}_{scan_rate}Vs_{Ru_test}_Ohm'

    cv = pstat.CV(Eini=Eini_cv, Ev1=Ev1_cv, Ev2=Ev2_cv, Efin=Efin_cv, nSweeps=nSweeps_cv, dE=dE_cv, sr=scan_rate,
                  sens=sens_cv, fileName=fileName, header=header)
    stirring(plate)
    cv.ircomp(Ru=Ru_test)  # Ru get from EIS
    cv.run()

    # save_cvrhe_to_txt(cvrhe, child_filepath, fileName)
    return fileName, sens_cv


def run_ca(time=30, Hz=1, sensitivity=1e-5):

    caname = f"CA_{str(datetime.datetime.now().isoformat(timespec='seconds')).replace(' ', '_').replace(':', '_')}"
    caheader = f'CA'
    ca = pstat.CA(Estep=1, Ehigh=1, Elow=-1.5, dt=0.1, ttot=1/Hz, sens=sensitivity, fileName=caname, header=caheader, tstep=time+1)
    ca.run()
    return caname

def read_ca_peak_i(filepath, filename, sensitivity=None, threshold=None):
    ca_data = pstat.LoadCA(filename, folder=filepath, model=model)
    peak_curs,_ = find_peaks(ca_data.i.reshape(-1))
    peak_currents = ca_data.i[peak_curs].reshape(-1)
    if sensitivity !=None:
        return abs(np.diff(peak_currents)[-1]) < sensitivity/ 100
    if threshold != None:
        return abs(peak_currents[-1]) < threshold


def cv_at_one_pH(c_Os, c_buffer, pH, Realv, assigned_rates=None,new_solution=False, Ru_assigned=None, pos_feedback=True, Eini_assigned=None, E_window_len=0.7, main_filepath='.'):
    # pH = 6.84
    global recording_ir
    if assigned_rates==None:
        assigned_rates=[1, 1.5, 3,6,10,40]
    #records_total.loc[len(records_total.index), ['Volume','Complex_mM','Buffer_M','pH']] = [Realv, c_Os, c_buffer, pH]
    # write pH into the child_folder name
    sub_file_path = f'{main_filepath}/pH_{pH:.2f}_Os_{round(c_Os,3)}mM_Buffer_{round(c_buffer, 3)}M_{round(Realv,2)}ml-new_{new_solution}'
    try:
        os.mkdir(sub_file_path)
    except:
        print(sub_file_path + ' already exists.')

    scan_rates =  assigned_rates # can be defined
    Ru_optimal = []
    Ru_opt_index = []
    polishing_any=[]

    if Ru_assigned == None:
        print('Generating the test sequence of Ru based on the EIS result.')
        stirring(plate)
        # OCP
        pstat.Setup(model=model, path_exe=path, folder=sub_file_path)
        Eini = run_ocp(sub_file_path)
        # EIS measurement
        Ru = run_eis(sub_file_path, Eini)
        Ru_list = np.arange(5, 40, 10) * Ru
        # Ru_list = np.append(Ru*10,Ru_list)
        Ru_list = np.append(Ru * 1.5, Ru_list)
        Ru_list = np.append(Ru, Ru_list)
    else:
        if pos_feedback == True:
            print('Generating the test sequence of Ru based on the prior knowledge of the Ru')
            Ru_list = sorted([Ru_assigned*0.8, Ru_assigned * 0.9, Ru_assigned, Ru_assigned * 1.1, Ru_assigned * 1.2])
        else:
            Ru_list = [Ru_assigned]
    for k in range(len(scan_rates)):
        scan_rate = scan_rates[k]
        adding = f'{scan_rate}_V'
        child_filepath = os.path.join(sub_file_path, adding) + '/'
        try:
            os.mkdir(child_filepath)
        except:
            print(child_filepath + ' already exists.')
        pstat.Setup(model=model, path_exe=path, folder=child_filepath)
        # CV in loops
        print('Parameters for this experiment: \n')
        print(f'Scan rates: {scan_rate}  in (V/s)')

        # CV measurement
        if pos_feedback==True:
            print('IR correction based on positive feedback')
            tables = pd.DataFrame(columns=['Ru', 'E_c_p', 'E_a_p', 'deltaE', 'Oscillation', 'Step'])
            # step one
            plt.figure(figsize=(4, 3))
            peak_sep = []
            plt.clf()
            for j in range(len(Ru_list)):
                step = 1
                osci = 0
                print(f'Measuring CV at {scan_rate} V/s with compensated Ru = {Ru_list[j]}_Ohm')
                fileName, sens_cv=run_cv(Eini_assigned, E_window_len, scan_rate, file_title,k,j,Ru_list[j])
                data = pstat.LoadCV(fileName, folder=child_filepath, model=model)
                plt.plot(data.E, data.i[:, 0])
                plt.title(f'CV at scan rate {scan_rate} V/s and Ru {Ru_list[j]} Ohm')
                plt.xlabel('E vs. Ag/AgCl')
                plt.ylabel('Current A')
                plt.savefig(os.path.join(child_filepath,f'{fileName}.png'))
                plt.show()
                delta_E, peaks, E_c_p, E_a_p = Peak_est_during_measurement(data, scan_rate, sens_cv)
                peak_sep = np.append(peak_sep, delta_E)
                print('Finished measuring CV')
                print('Waiting 5 s')
                time.sleep(5)
                print('Finished waiting\n')
                # stirring
                # stirring(plate, stirring_time=30)
                if len(peaks) > 30 or np.max(data.i) >= 10*sens_cv:
                    print(f'Oscillation happens! Should zoom in the Ru range to find a optimal compensate value')
                    print(len(peaks))
                    osci = 1
                    tables.loc[len(tables.index)] = [Ru_list[j]] + [E_c_p] + [E_a_p] + [abs(E_c_p-E_a_p)] + [osci] + [step]
                    break
                tables.loc[len(tables.index)] = [Ru_list[j]] + [E_c_p] + [E_a_p] + [abs(E_c_p-E_a_p)] + [osci] + [step]
            if j >0:
                starting = Ru_list[j-1]
                ending = Ru_list[j]
                next_Ru = (starting + ending) / 2
            else:
                next_Ru = Ru_list[0]
            #step two
            for i in range(j+1, 100):
                # THE NEXT Ru to be measured
                old_Ru = next_Ru
                print(f'Measuring CV at {scan_rate} V/s with compensated Ru = {next_Ru}_Ohm')
                fileName, sens_cv = run_cv(Eini_assigned, E_window_len, scan_rate, file_title, k, i, next_Ru)
                data = pstat.LoadCV(fileName, folder=child_filepath, model=model)
                plt.plot(data.E, data.i[:, 0])
                plt.title(f'CV at scan rate {scan_rate} V/s and Ru {next_Ru} Ohm')
                plt.xlabel('E vs. Ag/AgCl')
                plt.ylabel('Current A')
                plt.savefig(os.path.join(child_filepath, f'{fileName}.png'))
                plt.show()
                delta_E, peaks,E_c_p, E_a_p=Peak_est_during_measurement(data,scan_rate, sens_cv)
                peak_sep = np.append(peak_sep, delta_E)
                print('Finished measuring CV')
                print('Waiting 5 s')
                time.sleep(5)
                print('Finished waiting\n')
                # stirring
                # stirring(plate, stirring_time=30)
                if len(peaks) > 15:
                    print(f'Oscillation happens! Should zoom in the Ru range to find a optimal compensate value')
                    oscillation = 1
                    ending = next_Ru
                else:
                    oscillation = 0
                    starting = next_Ru
                tables.loc[len(tables.index)] = [old_Ru] + [E_c_p] + [E_a_p] + [abs(E_c_p - E_a_p)] + [oscillation] + [step]
                try:
                    next_Ru = (ending+starting) / 2
                except:
                    next_Ru = ending
                print(f"Next Ru to try:{round(next_Ru, 3)}Ohm")
                if (np.sum(tables.Oscillation[j:]) >=1)&(np.abs(tables['Ru'].iloc[-2] - tables['Ru'].iloc[-1]) <= max(1, Ru/100)) | (i > j + 6):
                    break
            try: print(f"The optimal Ru for IR compensation is: {tables[tables.Oscillation==0]['Ru'].iloc[-1]}")
            except: print(f"The optimal Ru for IR compensation is: {tables['Ru'].iloc[-1]}")
            try:
                Ru_optimal = np.append(Ru_optimal,tables[tables.Oscillation==0]['Ru'].iloc[-1])
                Ru_opt_index = np.append(Ru_opt_index, tables[tables.Oscillation == 0].index[-1])
            except:
                Ru_optimal = np.append(Ru_optimal, tables['Ru'].iloc[-1])
                Ru_opt_index = np.append(Ru_opt_index, tables.index[-1])
            print(f'Quality Control:\nMeasuring CV at {scan_rate} V/s with compensated Ru = {Ru}_Ohm')
            fileName, sens_cv = run_cv(Eini_assigned, E_window_len, scan_rate, file_title, k, i+1, Ru)
            #fileName_orig = glob.glob(f'{file_title}_{k}{str(0).zfill(3)}_{int(1000 * scan_rate)}mVs_{round(Ru)} Ohm*.txt')[0][:-4]
            fileName_orig = glob.glob(f"{child_filepath}/{file_title}_{k}{str(0).zfill(3)}_{int(1000 * scan_rate)}mVs_{round(Ru)} Ohm*.txt")[0].split('\\')[-1][:-4]
            data = pstat.LoadCV(fileName, folder=child_filepath, model=model)
            p_1 = find_CVpeaks(data)
            data_orig=pstat.LoadCV(fileName_orig, folder=child_filepath, model=model)
            p_2 = find_CVpeaks(data_orig)
            diff = abs(p_1-p_2)
            delta_E, peaks, E_c_p, E_a_p=Peak_est_during_measurement(data,scan_rate, sens_cv, 1)
            print(f'Peak separation: {delta_E}')
            peak_sep = np.append(peak_sep, delta_E)
            print('Finished measuring CV')
            print('Waiting 5 s')
            time.sleep(5)
            print(f'Quality control: The difference between two peak separation is: {diff}')
            polishing=False
            time2 = datetime.datetime.now()
            elapsed_time = time2 - time_start
            #time_acucmulation= elapsed_time >=interval and elapsed_time.total_seconds()%interval.total_seconds()<60*60
            if diff > 5 / 1000:# or time_acucmulation:
                try:
                    # Raise an error manually
                    raise Exception('Repolishing or reactivating is needed.')
                except Exception as e:
                    # Print the error message and pause the script, for the robotic arms
                    print(e)
                    message = f'You need to polish the electrode! pH: {pH}, scan rate: {scan_rate} V/s'
                    os.system(f'python slack-bot.py -m "{message}"')
                    polishing = True
                    #insitu_echem_activation(filepath=sub_file_path)
                    #input("Press enter to continue: ")
                    #de = int(1000 * abs(peak_sep[0] - peak_sep[-1]))
                    #caname = f'CA_{scan_rate}_Vs_{de}mV'
                    #caheader = f'CAof{filename}_{scan_rate}Vs'
                    #ca = pstat.CA(Estep=0.6, Ehigh=0.6, Elow=0.61, ttot=20, sens=1e-3, fileName=caname, header=caheader, tstep=1)
                    #ca.run()
            polishing_any.append(polishing)
            tables.to_csv(f"{child_filepath}/Sum_polishing_{polishing}.csv", index=True)

        else:
            print('For slow scan rate, use intrinsic IR compensation')
            Ru_for_test=Ru_list[0]
            Ru_optimal = np.append(Ru_optimal, Ru_for_test)
            Ru_opt_index = np.append(Ru_opt_index, 0)
            print(f'Measuring CV at {scan_rate} V/s with compensated Ru = {Ru_for_test}_Ohm')
            #fileName, sens_cv = run_cv(Eini_assigned, E_window_len, scan_rate, file_title, k, 0, Ru_for_test)
            fileName, sens_cv = run_cv(Eini_assigned, E_window_len, scan_rate, file_title, k, 0, Ru_for_test)
            data = pstat.LoadCV(fileName, folder=child_filepath, model=model)
            delta_E, peaks,E_c_p, E_a_p =Peak_est_during_measurement(data,scan_rate, sens_cv)
            print('Finished measuring CV')
            print('Waiting 5 s')
            time.sleep(5)
            print('Finished waiting\n')
            print('Not applicable to slow scans')
    if pos_feedback==True:
        recording_ir = pd.DataFrame({'Scan rates': scan_rates, 'Ru_comp': Ru_optimal, 'Ru_idx': Ru_opt_index})
        recording_ir.to_csv(f'{sub_file_path}/Records_of_optimal_Ru.csv', index=False)

        return recording_ir, sub_file_path, polishing_any
    if pos_feedback==False:
        return pd.DataFrame({'Scan rates': scan_rates, 'Ru_comp': Ru_for_test * np.ones(len(scan_rates)),
                                     'Ru_idx': 0}), sub_file_path, polishing_any
                # one function including post-analysis of the collected data and return the kobs value

#%%
'''
file_path = 'C:/Users/guazh/data/20240529_NHPEster' # the path where you want to save the test data
pstat.Setup(model=model, path_exe=path, folder=file_path)
E_ocp=run_ocp(file_path) # run OCP to get the open circuit potential
Ru=run_eis(file_path, E_ocp) # run EIS at E=E_ocp, to estimate Ru

#  technical params for CV
c_redox = 1 # unit mM
c_electrolyte = 0.1 # unit M
pH = 2 # pH of the solution, can be served as a label/name
volume = 2 # unit ml
E_window_a = -1.0 #V
E_window_length = 0.8 #V
scan_rates = [1, 10, 20, 100, 200, 500, 800, 1500] #V/s
filetitle = 'decaFeCp2' # filename

_, subfile, polishings = cv_at_one_pH(round(c_redox, 2), round(c_electrolyte, 3), round(pH, 2), round(volume, 2),
                                              new_solution=True, assigned_rates=scan_rates, Ru_assigned=None,
                                              pos_feedback=True, Eini_assigned=E_window_a,
                                              E_window_len=E_window_length, main_filepath=file_path)
'''

