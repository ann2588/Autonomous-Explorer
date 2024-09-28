
"""
CO2 optimizer utilities
"""
from .portaccess import *
from .liquidhandling import *
from .gashandling import *
from .electrochemistry import *
from .GCcontrolling import *

__version__ = "0.1"
__author__ = "Yi-An Lai"

__all__ = [
    'portaccess',
    'liquidhandling',
    'gashandling',
    'electrochemistry',
    'GCcontrolling'
]

def Purge_Ar_in_voir():
    change_port()
    control_gas_flow(mfm, 'open', flow_rate=30)


