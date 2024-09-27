from Utilities import portaccess
from ika.magnetic_stirrer import MagneticStirrer
from ismatec.peristaltic_pump import RegloICCFourChannel
from Hardwaretesting import MXII_valve as mxii, MFC
from Hardwaretesting.Valves import changing_port
#from gashandling import purgeAr
import ismatec.errors
import time
import asyncio
import time
import datetime

#%%

# %% Hardware Connection and Setup
global icca, iccb, plate
plate = MagneticStirrer(device_port=portaccess.port_plate)
#switchv = mxii.MX_valve(portaccess.port_switchvalve, ports=2, name='Switching', verbose=True)
valve_slva = mxii.MX_valve(portaccess.port_selectionvalveA, ports=6, name='SelectionA', verbose=True)
valve_slvc = mxii.MX_valve(portaccess.port_selectionvalveC, ports=6, name='SelectionC', verbose=True)
icca = RegloICCFourChannel(portaccess.port_pumpA)
iccb = RegloICCFourChannel(portaccess.port_pumpB)

#async def run_with_retry(coroutine, *args, **kwargs):
#    try:
#        await coroutine(*args, **kwargs)
#    except:
#        await coroutine(*args, **kwargs)
#def purgeAr(flowrate=50):
#    changing_port(switchv, switching_position['loading'])
#    asyncio.run(run_with_retry(MFC.n2on, flowrate))
#
#def offAr(flowrate=0):
#    asyncio.run(run_with_retry(MFC.n2off, flowrate))
#%%PUMP and VALVE
iccb_channel = {'waste_ano': 1, 'waste_cat': 2, 'slvc': 3, 'waste_voir': 4}
icca_channel = {'water': 1, 'electrolyte': 2, 'il': 3, 'waste':4}
switching_position = {'loading': 1, 'injection': 2}
stock_solution_port_c = {'water': 1, 'cu': 2, 'spelec': 3, 'regen': 4, 'hno3': 5, 'voir': 6}
stock_solution_port_a = {'blank': 1, 'IL1': 2, 'IL2': 3, 'IL3': 4, 'IL4': 5, 'IL5': 6}
volume = {
    '1mL': {'rpm': 33, 'second': 15},  # plating solution
    '2mL': {'rpm': 33, 'second': 30},  # Reaction volume
    '3mL': {'rpm': 50, 'second': 30},  # Reaction volume
    '4mL': {'rpm': 50, 'second': 40},  # Reaction volume
    '5mL': {'rpm': 100, 'second': 20},  # Rinsing
    '6mL': {'rpm': 100, 'second': 25},  # Rinsing
    '12mL' :{'rpm': 100, 'second': 50},  # Rinsing
    '50mL' :{'rpm': 100, 'second': 110}  # Rinsing
}

#%% Pump Direction setting

#%%  Utilities for Liquid handling
def stirring(plate=None, stirring_time=30, rpm=800):
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
        print(f'\nStarting {pump} {channel} channel at {rpm} rpm')
    except ismatec.errors.PumpError:
        pump.stop(channel)
        print(f'\n{pump} {channel} keeps stopped because 0 rpm assigned.')
    time.sleep(second)
    pump.stop(channel)
def select_solution_rinsing(solution_type=None, to_voir=False):
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
        if to_voir:
            channel = icca_channel.get('electrolyte')
            valve, port = None, None
        else:
            channel = iccb_channel.get('slvc')
            valve, port = valve_slvc, stock_solution_port_c.get('voir')
    elif solution_type in ['cu', 'hno3', 'regen', 'spelec']:
        channel = iccb_channel.get('slvc')
        valve, port = valve_slvc, stock_solution_port_c.get(solution_type)
    else:
        print('Solution not found')
        return None, None, None, None
    return pump, channel, valve, port
def pumping_waste_out(where:str = None, times = 40):
    if where == 'cell':
        #plate.start_stirring()
        channels = [1, 2]
        rpm = 100
        for channel in channels:
            iccb.set_mode_pump_rpm(channel, rpm)
        for channel in channels:
            iccb.start(channel)
        time.sleep(times)
        for channel in channels:
            iccb.stop(channel)

    elif where == 'voir':
        flushing(icca, 4, 100, time)
    else:
        print('Please identify which cell you want to empty')

def Rinsing(where:str = None, rinsing_solution:str=None, target_solution=None, repetitions=3, acidrinse=False, volume_assigned = '12mL'):
    '''
    :param where: assign 'voir' or 'cell'
    :param rinsing_solution: 'electrolyte, 'il', 'water', 'cu', 'hno3', 'regen', 'spelec'
    :param target_solution: 'electrolyte, 'il', 'water', 'cu', 'hno3', 'regen', 'spelec'
    :param repetitions: 3
    :param acidrinse: True to immerse for 10 minutes
    :return:
    '''
    to_voir = True if where == 'voir' else False #%% default would be rinsing the cell unless specified.
    def add_solution(solution_type, volume_add, to_voirs = to_voir):
        plate.start_stirring()
        pump, channel, valve, port = select_solution_rinsing(solution_type, to_voir=to_voirs)
        changing_port(valve, port)
        flow_rate, second = assign_flowrate(volume_add)
        flushing(pump, channel, flow_rate, second)
    def run_solution(solution, volume = volume_assigned):
        for _ in range(repetitions):
            plate.start_stirring()
            add_solution(solution, volume_add = volume , to_voirs = to_voir)  # pump control
            pumping_waste_out(where)  # pump control
            print(_ + 1, ' rinsed by ', solution)
        print('Cell rinsed by ', solution, ' completed')
    pumping_waste_out(where)  # Initial waste_out() call
    run_solution(rinsing_solution, volume = volume_assigned)
    if target_solution != None:
        run_solution(target_solution, volume = volume_assigned)
        print('Cell rinsing completed')
        add_solution(target_solution, volume_add = volume_assigned)  # pump control
        print(target_solution, ' added to cell')
    else:
        add_solution('water', volume_add = volume_assigned)
        print('Cell rinsing completed')
    if acidrinse == True:
        stirring(plate, 600)
        print('Acid rinsing completed')
def titration(element, number_of_drops, pump, valve, valve_port, pump_channel):  # to be optimized to use acid/base as little as possible

    print(valve, valve_port)
    changing_port(valve, valve_port)
    #changing_port(switchv, switching_position['loading'])
    purgeAr()

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
        changing_port(switchv, switching_position['injection'])
        print(f'Injecting {element}')
        pump.start(pump_channel)
        time.sleep(3)
        changing_port(switchv, switching_position['loading'])
        time.sleep(1)
        pump.stop(pump_channel)
def select_solution_IL(element= None):
    if element in ['IL1', 'IL2', 'IL3', 'IL4', 'IL5','Blank']:
        valve = valve_slva
        valve_port = stock_solution_port_a[element]
        pump = icca  # to remove the quote
        pump_channel = icca_channel['slva']
    else:
        raise ValueError("Element not recognized")  # Do sth else to add blank solution
    return valve, valve_port, pump, pump_channel
def titration_rinsing(valve, valve_port,pump, pump_channel):
    changing_port(valve, valve_port)
    changing_port(switchv, switching_position['loading'])
    pump.set_mode_pump_rpm(pump_channel, 100)  # check the input value
    pump.start(pump_channel)
    time.sleep(15)
    pump.stop(pump_channel)

#%% Utilitis for Plating Solution Making, pending to be optimize for varying potential
'''
#Pass one of the following samples to test the plating solution module
titrationmoduletestsample = {'IL1': 1, 'IL2': 1, 'IL3': 1, 'IL4': 1, 'IL5': 1, 'Blank': 0}
#rinsingvalvesample = {'blanka':5, 'blankb':5}

def test_make_solution_module(sample):
    
    This function run every channel in making solution module for 1 droplet
    please run this function and check in person to see if every channel is working
    
    for element, partition in sample.items():
        if element in ['V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'S', 'Se', 'P', 'blank']:
            if partition == 0.0:
                continue
            else:
                valve, valve_port, pump, pump_channel = select_solution_IL(element=element)
                plate.start_stirring()
                print(
                    f'Adding {element} for {int(partition)} times with {valve} at port {valve_port}, {pump} running at channel {pump_channel}')
                titration(element, int(partition), pump, valve, valve_port, pump_channel)
                if valve == valve_slva:
                    print(f'Rinsing titration channel by blank solution from {valve_slva}')
                    titration_rinsing(valve_slva, stock_solution_channels_a['blank'], icca,
                                      pump_channel=icca_channel['slva'])
                else:
                    continue
        else:
            continue
    print('make_solution_test finished')
def make_plating_solution(sample:dict):
    global valve
    cell_rinsing('water', 'spelec', 3)
    pumping_waste_out()
    add_solution('spelec', '4mL') #@@ Require customization
    add_solution('spelec', '1mL') #@@ Require customization
    print('1 mL spelec added to cell')
    for element, partition in sample.items():
        if element in ['IL1', 'IL2', 'IL3', 'IL4', 'IL5','Blank']:
            if partition == 0.0:
                continue
            else:
                valve, valve_port, pump, pump_channel = select_solution_IL(element=element)
                plate.start_stirring()
                print(
                    f'Adding {element} for {int(partition)} times with {valve} at port {valve_port}, {pump} running at channel {pump_channel}')
                titration(element, int(partition), pump, valve, valve_port, pump_channel)
                if valve == valve_slva:
                    print(f'Rinsing titration channel by blank solution from {valve_slva}')
                    titration_rinsing(valve_slva, stock_solution_channels_a['blank'], icca, pump_channel=icca_channel['slva'])
                #elif valve == valve_slvb:
                #    print(f'Rinsing titration channel by blank solution from {valve_slvb}')
                #    titration_rinsing(valve_slvb, stock_solution_channels_b['blank'], icca, pump_channel=icca_channel['slvb'])
                else:
                    continue
        else:
            continue
    #add_solution('spelec', '2mL')  # pump control
    print('spelec added to cell to 5 mL total volume')
'''