#from Hardwaretesting.MXII_valve import MX_valve as mxii

#valve_switch = mxii.MX_valve('COM7', ports=2, name='Switching', verbose=True)
#valve_select = mxii.MX_valve('COM4', ports=6, name='Selection', verbose=True)
#valve_switch.change_port(1)# need to open the software and make sure it is on BCD level for switch valve

def changing_port(valve=None, target_port=1):
    valve.change_port(target_port)

#if __name__ == '__main__':
#    changing_port(valve_select, 2)
#    valve_select.get_port()
