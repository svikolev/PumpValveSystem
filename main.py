import serial
import io
import re
import time
import json
import logging
import atexit
import sys
import threading
import os
from PyQt5 import QtGui, QtCore,  QtWidgets

def main_ui():
    try:
        if (len(sys.argv)>1):
            main = open(sys.argv[1])
        else:
            # fp = open('mypumps1.json')
            # pc = open('simple_progs.json')
            main = open('main_config_2PV.json')
        # pump_config = json.load(fp)
        # prog_config = json.load(pc)
        main_config = json.load(main)
        # fp.close()
        # pc.close()
        main.close()
    except IOError:
        print ('config file not found')
        sys.exit(0)



    """Init pumps comp port"""
    pumpPort = main_config["PumpCOM"]
    pser = serial.Serial(baudrate=19200,timeout=0.1,port=pumpPort) # com 1 for scope comp, com 4 for bench comp
    print(pser.is_open)

    '''init pump objects'''
    pumpsdict = {}
    for p in range(main_config['NumPumps']):
        pump = main_config["Pumps"][p]
        pumpsdict[pump["address"]] = pm.Pump(pser, pump)

    """Init the labsmith objects """
    valvePort = main_config["ValveCOM"]
    eib = ls.EIB200(COM=valvePort)

    valves = []
    for v in range(main_config["NumValves"]):
        valve = main_config["Valves"][v]
        valves.append(ls.Valve(eib.ls4vm, channel=valve["ValveChannel"]))
    print(valves)

    ''' init pumpValve objects'''
    PVunits = []
    for j, (p, v) in enumerate(zip(list(pumpsdict.values()), valves)):
        PVunits.append(PumpValve(v, p, j))


    '''get simple programs'''
    #simple_prog = []
    with open("simple_progs.json", "r") as json_file:
        data = json.load(json_file)
    simple_prog = data.get("programs", [])
    #programs = {x['name']: x for x in prog_config['programs']}

    '''get json programs'''
    json_progs = []
    for filename in os.listdir(main_config['json_dir_name']):
        if filename.endswith('.json'):
            file_path = os.path.join(main_config['json_dir_name'], filename)
            file_name_without_extension = os.path.splitext(filename)[0]
            json_progs.append({'name':filename,
                               "type":"json_prog",
                               "path":file_path})

    '''combine programs'''
    combined_progs = simple_prog + json_progs
    programs = {prog['name']: prog for prog in combined_progs}

    ''' launch gui'''
    app = QtWidgets.QApplication(sys.argv)
    ex = pvc.PumpValveControl(PVunits, programs)
    ret = app.exec_()
    ex.t.cancel()
    sys.exit(ret)



if __name__ == '__main__':
    # from Pump import*
    # from PumpControl import*
    import Pump as pm
    import PumpValveControl as pvc

    import labsmith as ls
    import PumpValve
    import threading
    from PumpValve import PumpValve
    #
    # from pycromanager import Acquisition, multi_d_acquisition_events, Dataset, Core, Bridge, Studio
    # core = Core()
    # print(core)
    # core.snap_image()
    #main_test(10)
    main_ui()