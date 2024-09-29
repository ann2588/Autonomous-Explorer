from ismatec.peristaltic_pump import RegloICCFourChannel, ChannelStatus
import ismatec.errors
import time
import numpy as np
#port_pump = 'COM8'
global icc2
global icc1
#icc = RegloICCFourChannel('COM5')
icc.set_counter_clockwise(1)
icc.set_mode_pump_rpm(1, 100)
