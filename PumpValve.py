import threading
import time


class PumpValve:
    def __init__(self,valve,pump,pvADR):
        """pump valve object is a pump and valve pair where the syringe is connected to the fixed port on the AV801
        init with a valve object, pump object, and address for the unit"""
        self.valve = valve
        self.pump = pump
        self.pvADR = pvADR
        self.current_port = 1
        #self.valve.moveToPort(1)
        #self.moveToPort(1)
        print('initialized valve at port 1')
        self.running_seq = False
        self.seq_dict = None
        self.current_phase = "not running seq"
        self.phaseTargetDispense = 0
        self.size = 10  # default 10 ml
        print(f'called init pv {pvADR}')

    def set_size(self,size):
        self.size = size
        self.pump.set_size(size)

    def get_pump_obj(self):
        return self.pump

    def moveToPort(self,port):
        cp = self.current_port
        """Moves valve to the port passed in, helper method for RunAtPort"""
        if self.pump.getStatus() != 'halted':
            self.pump.stop()
        self.valve.moveToPort(port)
        # if port != cp:
        #     def get_next(p):
        #         if p ==8:
        #             return 1
        #         else:
        #             return p+1
        #     steps = port - cp
        #     if steps < 0:
        #         steps = 8 + steps
        #     for ii in range(steps):
        #         self.valve.moveToPort(get_next(cp+ii))
        #         time.sleep(1.5)
        self.current_port = port

    def runPumpPhase(self,rat,vol,direction):
        """sends a single phase program to the pump, helper method for RunAtPort"""
        self.pump.singlePhaseProgram(rat,vol,direction)
        print('code from pumpvalve to pump')

    def RunAtPort(self,port,rat,vol,direction):
        """moves valve to the input port and sends a single phase program to pump"""
        self.current_phase = {'p':port,'r':rat,'v':vol,'d':direction}
        self.moveToPort(port)
        self.phaseTargetDispense = float(self.pump.getDispensed(units = False))+vol
        self.runPumpPhase(rat,vol,direction)

    def RunAtPort_prog_phase(self,step_dict):
        """moves valve to the input port and sends a single phase program to pump"""
        self.current_phase = {'s_num':step_dict['step_num'],'p':step_dict['p'],'r':step_dict['r'],'v':step_dict['v'],
                              'd':step_dict['d'],'dur':step_dict['expect_duration'], 'info':step_dict['status']}
        self.moveToPort(step_dict['p'])
        self.phaseTargetDispense = float(self.pump.getDispensed(units = False))+step_dict['v']
        self.runPumpPhase(step_dict['r'],step_dict['v'],step_dict['d'])

    def runSequence(self, seq_dict, entry_params = None):#port = None, dir = None, vol = None, rat = None):
        """Runs program for the pump valve unit,
        Takes in the program dictionary,
        launches a new thread that sends a sequence of RunAtPort commands
        and sleeps for the expected pump run time in between"""
        self.seq_dict = seq_dict
        self.running_seq = True

        def runSeq(_self,seq_dictionary,entry_params):#,thread_kill):# port = None, dir = None, vol = None, rat = None):
            for loop in range(seq_dictionary["Loops"]):
                print("starting loop {}".format(loop))
                print(seq_dictionary)
                for phase in seq_dictionary["Phases"]:
                    print("Current Phase:", phase)
                    # if the prog dict has -1 or 'entry', use the entered parameters passed this this function an entry params dict

                    # old way thats now commented had dict phases that was somehow being reused:
                    # if first run is with infuse then next run will also have infused because "entry" will be overwriten
                    # could also use a copy dictionary
                    if phase["port"] == -1:
                        p = int(entry_params["port"])
                    else: p = phase["port"]
                    if phase["rate"] == -1:
                        r = int(entry_params["rate"])
                    else: r = phase["rate"]
                    if phase["vol"] == -1:
                        v = int(entry_params["vol"])
                    else: v = phase["vol"]
                    if phase["dir"] == "Entry":
                        d = entry_params["dir"]
                    else: d = phase["dir"]
                    _self.RunAtPort(p, r, v, d)
                    expect_time = int(int(v) / (int(r) / 60))+4 +8
                    _self.thread_kill.wait(timeout = expect_time)
                    if _self.thread_kill.is_set():
                        print("killing thread inner")
                        break
                    pump_Running = True
                    while pump_Running:
                        status = _self.pump.getStatus()
                        if status == 'halted':
                            pump_Running = False
                if _self.thread_kill.is_set():
                    print("killing thread outter")
                    break
            _self.running_seq = False
            _self.thread_kill.clear()
            _self.current_phase = "no seq"
            print("finished sequence")
        self.thread_kill = threading.Event()
        self.k = threading.Thread(target=runSeq, args=(self,seq_dict,entry_params))
        self.k.start()
