'''
This version compatitble with the flow chemistry where the electrolyte connected to selection valve C channel 4
instead of only connected to voir
to use this version, Please copy this module to Utilities and replace liquid handling
'''

from .portaccess import *
from .gashandling import *
from ika.magnetic_stirrer import MagneticStirrer
from ismatec.peristaltic_pump import RegloICCFourChannel
from Closed_Loop_Platform.Hardwaretesting import MXII_valve as mxii
from Closed_Loop_Platform.Hardwaretesting.Valves import changing_port
import ismatec.errors
import time
from Closed_Loop_Platform.Communication.Logging import *

# %% Hardware Connection and Setup
global icca, iccb, swtv, valve_slva, valve_slvc
plate = MagneticStirrer(device_port=port_plate)
swtv = mxii.MX_valve(address = port_switchvalve, ports=2, name='Switching', verbose=True)
valve_slva = mxii.MX_valve(address = port_selectionvalveA, ports=6, name='SelectionA', verbose=True)
valve_slvc = mxii.MX_valve(address = port_selectionvalveC, ports=6, name='SelectionC', verbose=True)
icca = RegloICCFourChannel(device_port=port_pumpA, name = 'Icca')
iccb = RegloICCFourChannel(device_port=port_pumpB, name = 'Iccb')
cat = str()
#%%PUMP and VALVE
iccb_channel = {'waste_ano': 1, 'waste_cat': 2, 'slvc': 3, 'waste_voir': 4}
icca_channel = {'water': 1, 'electrolyte': 2, 'il': 3}
switching_position = {'loading': 1, 'injection': 2}
stock_solution_port_c = {'water': 1, 'cu': 2, 'spelec': 3, 'electrolyte': 4, 'hno3': 5, 'voir': 6}
stock_solution_port_a = {'blank': 1, 'IL1': 2, 'IL2': 3, 'IL3': 4, 'IL4': 5, 'IL5': 6}
volume = {
    '1mL': {'rpm': 33, 'second': 15},  # plating solution
    '2mL': {'rpm': 33, 'second': 30},  # Reaction volume
    '3mL': {'rpm': 50, 'second': 30},  # Reaction volume
    '4mL': {'rpm': 50, 'second': 40},  # Reaction volume
    '5mL': {'rpm': 100, 'second': 20},  # Rinsing
    '6mL': {'rpm': 100, 'second': 25},  # Rinsing
    '10mL': {'rpm': 100, 'second': 50},  # Rinsing
    '20mL' :{'rpm': 100, 'second': 100},  # Rinsing
    '26mL' :{'rpm': 100, 'second': 110},  # Rinsing
    '50mL' :{'rpm': 100, 'second': 210}  # Rinsing
}

#%% Purge
def Purge_Ar_in_voir(OPERATION:str):
    '''
    purging gas from switch valve to voir in order to degas a bit
    :param OPERATION: 'open', 'close'
    '''
    changing_port(swtv, switching_position['loading'])
    control_gas_flow(mfc_swtv, {OPERATION}, flow_rate=30)

def Purge_Ar_in_cell():
    control_co2_ar_ratio(0)

#%%  Utilities for Liquid handling
def stirring(plate=None, stirring_time=30, rpm=400):
    print(f'Stirring at {rpm} rpm for {stirring_time} s')
    plate.start_stirring()
    plate.target_stir_rate = rpm
    time.sleep(stirring_time)
    plate.stop_stirring()
    print('Finished stirring\n')
    time.sleep(5)

def assign_flowrate(volume_add):
    flow_rate = volume.get(volume_add).get('rpm')
    second = volume.get(volume_add).get('second')

    if flow_rate is None or second is None:
        print('The designated volume is not defined')
    return flow_rate, second

def flushing(pump, channel, rpm, second):
    pump.set_mode_pump_rpm(channel, rpm)
    try:
        pump.start(channel)
        print(f'\nStarting {pump.__str__()} channel {channel} at {rpm} rpm')
    except ismatec.errors.PumpError:
        pump.stop(channel)
        print(f'\n{pump.__str__()} {channel} keeps stopped because 0 rpm assigned.')
    time.sleep(second)
    pump.stop(channel)

def select_solution_rinsing(solution_type=None, to_voir=False, from_voir=False):
    # Default values for pump and channel based on `to_voir` flag
    if to_voir:
        pump = icca
    else:
        pump = iccb

    if solution_type == 'water':
        if to_voir:
            channel = icca_channel.get('water')
            valve, port = None, None
        else:
            channel = iccb_channel.get('slvc')
            valve, port = valve_slvc, stock_solution_port_c.get('water')
    elif solution_type == 'electrolyte':
        if to_voir and from_voir == False:
            channel = icca_channel.get('electrolyte')
            valve, port = None, None
        elif to_voir == False and from_voir:
            channel = iccb_channel.get('slvc')
            valve, port = valve_slvc, stock_solution_port_c.get('voir')
        else:
            channel = iccb_channel.get('slvc')
            valve, port = valve_slvc, stock_solution_port_c.get('electrolyte')

    elif solution_type in ['cu', 'hno3', 'regen', 'spelec']:
        channel = iccb_channel.get('slvc')
        valve, port = valve_slvc, stock_solution_port_c.get(solution_type)
    else:
        print('Solution not found')
        return None, None, None, None
    return pump, channel, valve, port
#%%
def pumping_waste_out(where:str = None, times = 100):
    if times != 100:
        print('Removing liquid to dilute the bulk concentration...')
    else:
        print(f'Pumping waste out from {where}...')

    if where == 'cell':
        plate.start_stirring()
        channels = [1, 2]
        rpm = 100
        for channel in channels:
            iccb.set_mode_pump_rpm(channel, rpm)
        for channel in channels:
            iccb.start(channel)
            print(f'Starting {iccb} channel {channel} at {rpm} rpm')
        print(f'{times} seconds.')
        time.sleep(times)
        for channel in channels:
            iccb.stop(channel)

    elif where == 'voir':
        flushing(iccb, 4, 100, second = times)

    elif where == 'both':
        channels = [1, 2, 4]
        rpm = 100
        times = 100
        for channel in channels:
            iccb.set_mode_pump_rpm(channel, rpm)
        for channel in channels:
            iccb.start(channel)
            print(f'Starting {iccb} channel {channel} at {rpm} rpm')
        print(f'{times} seconds.')
        time.sleep(times)
        for channel in channels:
            iccb.stop(channel)


    else:
        print('Please identify which cell you want to empty')



def add_solution(solution_type, volume_add = None, seconds = None, to_voirs = False, from_voirs = False):
    plate.start_stirring()
    pump, channel, valve, port = select_solution_rinsing(solution_type, to_voir = to_voirs, from_voir = from_voirs  )

    if valve is None and port is None and to_voirs is True: # Electrolyte and water into voir from pump a
        print(f'{solution_type} {pump} {channel} {valve} {port}')
        print(f'{solution_type} flow into voir. No valve involved.')
    else:
        print(f'{solution_type} {pump} {channel} {valve} {port}')
        changing_port(valve, port)

    ## Scenerio for plating solution formulation
    if seconds != None and volume_add == None:
        flow_rate = 100 #rpm
        second = seconds
        flushing(pump, channel, flow_rate, second)

    ## For normal Add solution
    else:
        flow_rate, second = assign_flowrate(volume_add)
        flushing(pump, channel, flow_rate, second)

def Rinsing(where:str = None, rinsing_solution:str=None, target_solution=None, repetitions=3, acidrinse=False, volume_assigned = '20mL', from_voir = False):
    '''
    :param where: assign 'voir' or 'cell'
    :param rinsing_solution: 'electrolyte, 'il', 'water', 'cu', 'hno3', 'regen', 'spelec'
    :param target_solution: 'electrolyte, 'il', 'water', 'cu', 'hno3', 'regen', 'spelec'
    :param repetitions: 3
    :param acidrinse: True to immerse for 10 minutes
    :return:
    '''
    to_voir = True if where == 'voir' else False #%% default would be rinsing the cell unless specified.

    def run_solution(solution, volume = volume_assigned, to_voirs = to_voir, from_voirs = from_voir):
        for _ in range(repetitions):
            plate.start_stirring()
            mfc_co2ar.set_flow_rate(7)
            add_solution(solution, volume_add = volume , to_voirs = to_voirs, from_voirs = from_voirs)  # pump control
            mfc_co2ar.set_flow_rate(0)
            mfc_co2.set_flow_rate(7)
            pumping_waste_out(where)  # pump control
            mfc_co2.set_flow_rate(0)
            print(f'{ _ + 1} rinsed by {solution}. ')
        print(f'{where} rinsed by {solution} completed')

    if target_solution == 'electrolyte' and from_voir == True:
        mfc_co2.set_flow_rate(7)
        pumping_waste_out(where)
        mfc_co2.set_flow_rate(0)
    else:
        mfc_co2.set_flow_rate(7)
        pumping_waste_out('both')
        mfc_co2.set_flow_rate(0)

    run_solution(rinsing_solution, volume=volume_assigned, to_voirs=to_voir, from_voirs=from_voir)

    # The case when adding prepared electrolyte from voir
    if target_solution == 'electrolyte' and from_voir == True and to_voir == False:
        mfc_co2ar.set_flow_rate(7)
        add_solution(target_solution, volume_add=volume_assigned, to_voirs = to_voir,from_voirs=from_voir)  # pump control
        mfc_co2ar.set_flow_rate(0)
        print(f'{target_solution} added to {where}')

    elif target_solution == 'None': # If not target_solution not assigned, add water in defult
        mfc_co2ar.set_flow_rate(7)
        add_solution('water', volume_add=volume_assigned, to_voirs=to_voir, from_voirs=from_voir)
        mfc_co2ar.set_flow_rate(0)
        print(f'{where} rinsed by water completed')

    else: #Normal
        run_solution(target_solution, volume=volume_assigned, to_voirs=to_voir, from_voirs=from_voir)
        mfc_co2ar.set_flow_rate(7)
        add_solution(target_solution, volume_add=volume_assigned, to_voirs=to_voir, from_voirs=from_voir)
        mfc_co2ar.set_flow_rate(0)
        print(f'{where} rinsed by {target_solution} completed')

    if acidrinse == True:
        stirring(plate = plate, stirring_time=1200)
        print('Acid rinsing completed')

def titration(element, number_of_drops, pump, valve, valve_port, pump_channel):  # to be optimized to use acid/base as little as possible

    print(f'{valve}, {valve_port}')
    changing_port(valve, valve_port)
    control_gas_flow(mfc_swtv, 'open', flow_rate=30)
    # load mode initial filling
    pump.set_mode_pump_rpm(pump_channel, 100)  # check the input value
    pump.start(pump_channel)
    time.sleep(10)
    pump.stop(pump_channel)
    # 5s per titration
    # number of drops acts as input passed into pH_titration
    # start stirring here ( estimate a time )
    # optimize the work flow and time to make it time efficient
    for i in range(number_of_drops):
        plate.start_stirring()
        pump.set_mode_pump_rpm(pump_channel, 20)
        pump.start(pump_channel)  # initial filling of each tube
        time.sleep(3)
        changing_port(swtv, switching_position['injection'])
        print(f'Injecting {element}')
        pump.start(pump_channel)
        time.sleep(3)
        changing_port(swtv, switching_position['loading'])
        time.sleep(1)
        pump.stop(pump_channel)

def select_solution_IL(element= None):
    if element in ['IL1', 'IL2', 'IL3', 'IL4', 'IL5','Blank']:
        valve = valve_slva
        valve_port = stock_solution_port_a[element]
        pump = icca  # to remove the quote
        pump_channel = icca_channel['il']
    else:
        raise ValueError("Element not recognized")  # Do sth else to add blank solution
    return valve, valve_port, pump, pump_channel

def titration_channel_rinsing(valve, valve_port,pump, pump_channel):
    changing_port(valve, valve_port)
    changing_port(swtv, switching_position['loading'])
    pump.set_mode_pump_rpm(pump_channel, 100)  # check the input value
    pump.start(pump_channel)
    time.sleep(15)
    pump.stop(pump_channel)

#%% Utilitis for electrolyte formulation, pending to be optimize for varying potential

def test_titration_module(sample):
    '''
    This function run every channel in making solution module for 1 equivilent
    please run this command and check in person to see if every channel is working properly
    Status: Pending test run
    '''
    for element, partition in sample.items():
        if element in ['IL1', 'IL2', 'IL3', 'IL4', 'IL5', 'Blank']:
            if partition == 0.0:
                continue
            else:
                valve, valve_port, pump, pump_channel = select_solution_IL(element=element)
                plate.start_stirring()
                print(
                    f'Adding {element} for {int(partition)} times with {valve.__str__()} at port {valve_port}, {pump.__str__()} running at channel {pump_channel}')
                titration(element, int(partition), pump, valve, valve_port, pump_channel)
        else:
            continue
    print('Titration Test module test completed')

#please run below command and check in person to see if every channel is working properly
titrationmoduletestsample = {'IL1': 1, 'IL2': 1, 'IL3': 1, 'IL4': 1, 'IL5': 1, 'Blank': 0}
#test_titration_module(titrationmoduletestsample)

#Electrolyte formulation

def Elelectrolyte_Formulation(sample:dict):
    '''
    Formulating the electrolyte with ionic liquid. Prepared in solution vior
    Status: Pending test run
    '''
    Rinsing('voir', 'water', 'electrolyte', 1, volume_assigned='20mL')
    print('50 mL electrolyte added to reservoir')
    
    for element, partition in sample.items():
        if element in ['IL1', 'IL2', 'IL3', 'IL4', 'IL5','blank']:
            if partition == 0.0:
                continue
            else:
                valve, valve_port, pump, pump_channel = select_solution_IL(element=element)
                print(
                    f'Adding {element} for {int(partition)} times with {valve.__str__()} at port {valve_port}, {pump.__str__()} running at channel {pump_channel}')
                titration(element, int(partition), pump, valve, valve_port, pump_channel)
                titration_channel_rinsing(valve, stock_solution_port_a['blank'], pump, pump_channel=icca_channel['il'])
        else:
            continue
    
    time.sleep(30) #Stir for 30 sec
    print('Electrolyte formulated in reservoir')
    Rinsing('cell', 'water', 'electrolyte', 2, volume_assigned='20mL', from_voir=True)
    print('Electrolyte in voir transferred to cell.')

def PlatingSolutionFormulation(sample:dict):
    '''
    Formulates the electrolyte with copper sulfate and supporting electrolyte for plating solution.
    Status: Pending test run
    :param sample: Concentration of the plating solution (0.1 to 0.5 M)
    :return: None
    '''
    # Add 50 mL of plating solution to the cell
    close_all_gas()
    start_time = time.time()
    Rinsing('cell', 'spelec', 'cu', 1, volume_assigned='20mL')
    end_time = time.time()
    print(f'20 mL 0.5 M plating solution added to cell in {end_time - start_time:.2f} seconds')

    # Dilute the plating solution if necessary
    if sample != 0.5:
        print(f'Diluting the plating solution from 0.5 M to {sample} M')
        plate.start_stirring()
        # Calculate the time required to pump out waste for dilution
        dilution_time = int(100 * (0.5 - sample) / 0.5)
        start_time = time.time()
        pumping_waste_out('cell', times = dilution_time)
        end_time = time.time()
        print(f'Pumping waste out for dilution in {end_time - start_time:.2f} seconds')
        # Add the required amount of solution for dilution
        start_time = time.time()
        add_solution('spelec', volume_add = None, seconds=dilution_time)
        end_time = time.time()
        print(f'Adding solution for dilution in {end_time - start_time:.2f} seconds')
        # Stir the solution after dilution
        start_time = time.time()
        stirring(plate=plate, stirring_time=10)
        end_time = time.time()
        print(f'Stirring solution after dilution in {end_time - start_time:.2f} seconds')
        print(f'{sample} M plating solution prepared in cell.')

def StopAllPump():
    for i in range(1, 5):
        icca.stop(i)
        iccb.stop(i)
    print('All the channel are stopped')