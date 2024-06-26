
from uProcess_x64 import CEIB, C4VM
import time

class EIB200:
    def __init__(self,COM):
        """EIB200 is the labsmith interface device where the usb and power is connected,
        init with the com port on computer,
        can have up to 4 manifold devices,
        here only using 1 4vm02 device"""
        self.COM = COM
        self.eib = CEIB()
        self.eib.InitConnection(COM)
        self.dev_list = self.eib.CmdCreateDeviceList()
        self.ls4vm = self.dev_list[0]
class Valve:
    def __init__(self,ls4vm, channel,lock = None):
        """Valve object is connected to the labsmith 4VM02 manifold on channels 1-4,
        Init using the 4VM02 obj in eib200,the channel on the 4vmo2,and optional a lock obj for the valve com port"""
        self.ls4vm = ls4vm
        self.channel = channel
        self.lock = lock
        self.current_port = None
        self.moveToPort(1)
        print(f'called init valve {channel}')

    def moveToPort(self,port):
        """Sends command called 'CmdSelect' to ls4VM02 with the channel of the valve
        and the port that it should move to,
        if there is a lock on the valve com, wait to acquire,then send the command,
        the command for checking if the valve is moving is passing in the output of
        GetValveStatus (the port its on, exept when finished says 0)
        to IsMoving which returns boolean"""
        # port_ref = [5,6,7,8,1,2,3,4]
        # if self.channel == 1:
        #     port = port_ref[port-1]

        print("valve # {}, moving from {} to port {}".format(self.channel,self.current_port,port))

        if self.current_port is None or self.current_port != port:
            if self.lock is not None:
                self.lock.acquire()
            _ = self.ls4vm.CmdSelect(self.channel, port)
            print('valv_rot wait')
            #port_delta = port - self.current_port
            if self.current_port is None:
                time.sleep(8)
            elif self.current_port < port:
                time.sleep(int(port - self.current_port)+0.5)
            else:
                time.sleep(int(8- (self.current_port - port))+0.5)

            if self.lock is not None:
                self.lock.release()
                #print(moving, C4VM.GetSelection(s))
            print("moved to port{}".format(port))
            self.setPort(port)
        #
        # print("labsmith valve obj, moving to port {}".format(port))
        # moving = True
        # while moving:
        #     if self.lock is not None:
        #         self.lock.acquire()
        #     _ = self.ls4vm.CmdSelect(self.channel, port)
        #     s = self.ls4vm.GetValveStatus(self.channel)
        #     if self.lock is not None:
        #         self.lock.release()
        #     moving = C4VM.IsMoving(s)
        #     #print(moving, C4VM.GetSelection(s))
        # print("moved to port{}".format(port))
        # self.setPort(port)

    def getStatus(self):
        """asks the valve what port its on. this one doesnt use the lock because
        it's intended to pe used only in terminal"""
        return self.ls4vm.GetValveStatus(self.channel)

    def setLock(self,lock):
        """adds a lock object to the valve, typicaly passed in from pumpValveControl"""
        self.lock = lock

    def setPort(self,port):
        "sets the memory of the object to know what port its on, does not send any commands"
        self.current_port = port