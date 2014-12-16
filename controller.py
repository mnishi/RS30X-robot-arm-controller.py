import sys
import os
import time
from numpy import * 
import enum 
import gevent
from gevent.queue import Queue
from gevent.event import AsyncResult
from RS30X.RS30X import *

class Pose:
    def __init__(self, px = 0.0, py = 0.0, pz = 0.0, ox = 0.0, oy = 0.0, oz = 0.0):
        self.data = [px, py, pz, ox, oy, oz]

class Joint:
    def __init__(self, j1 = 0.0, j2 = 0.0, j3 = 0.0, j4 = 0.0, j5 = 0.0, j6 = 0.0):
        self.data = [j1, j2, j3, j4, j5 ,j6]

class Controller:
    EMsgKey = enum.Enum("EMsgKey", "type target callback")
    EConType = enum.Enum("EConType", "move_ptp torque")
    EStatKey = enum.Enum("EStatKey", "pose")

    @classmethod
    def tenth_deg(cls, deg):
        return int(round(deg * 10.0, 0))

    def __init__(self, controll_period = 20.0, max_speed = 240.0 / 1000.0):
        self.max_speed = max_speed # deg per msec
        self.controll_period = controll_period # msec
        self.status = {}
        self.status[Controller.EStatKey.pose] = Joint() 
        self.controller = RS30XController()
        self.queue = Queue()
        gevent.spawn(self.__hundle_massage)

    def __hundle_massage(self):
        msg = None
        while True:
            msg = self.queue.get()
            Logger.log(Logger.ELogLevel.TRACE, "new message, msg = %s", msg)
            
            if msg is None:
                pass
            elif msg[Controller.EMsgKey.type] is Controller.EConType.torque:
                target = msg[Controller.EMsgKey.target]
                Logger.log(Logger.ELogLevel.TRACE, "target = %d", target)
                for id in range(6):
                    if target is True:
                        self.controller.torqueOn(id)
                    else:
                        self.controller.torqueOff(id)
                if msg[Controller.EMsgKey.callback] is not None:
                    msg[Controller.EMsgKey.callback].set()

            elif msg[Controller.EMsgKey.type] is Controller.EConType.move_ptp:
                Logger.log(Logger.ELogLevel.TRACE, "move_ptp start")
                trajectory = []     
                for i in range(6): 
                    trajectory.append(Trajectory.interporate_5poly(self.status[Controller.EStatKey.pose].data[i], msg[Controller.EMsgKey.target].data[i], self.controll_period, self.max_speed))
                periods = len(trajectory[0]) 
                
                for period in range(periods):
                    Logger.log(Logger.ELogLevel.TRACE, "period = %d", period)
                    params = []
                    interval = self.controll_period / 500.0

                    for id in range(6):
                        if period < (periods - 1):
                            param = RS30XParameter(id, Controller.tenth_deg(trajectory[i][period + 1]), int(self.controll_period * 2))
                            params.append(param)
                            interval = self.controll_period / 1000.0
                        else:
                            param = RS30XParameter(id, Controller.tenth_deg(trajectory[i][period]), int(self.controll_period))
                            params.append(param)
                    self.controller.move(params)
                    gevent.sleep(interval)

                for i in range(6):
                    self.status[Controller.EStatKey.pose].data[i] = msg[Controller.EMsgKey.target].data[i]

                if msg[Controller.EMsgKey.callback] is not None:
                    msg[Controller.EMsgKey.callback].set()
            else:
                Logger.log(Logger.ELogLevel.ERROR, "invalid message type, msg = %s", msg)
            
            gevent.sleep(0)
    
    def __receive_message(self, message):
        message[Controller.EMsgKey.callback].get()

    def __send_message_wait_reply(self, message):
        self.queue.put(message)
        Logger.log(Logger.ELogLevel.TRACE, "message send, msg = %s", message)
        gevent.spawn(self.__receive_message, message).join()
        Logger.log(Logger.ELogLevel.TRACE, "message replied, msg = %s", message)

    def move_ptp(self, joint):
        callback = AsyncResult()
        message = {
                Controller.EMsgKey.type: Controller.EConType.move_ptp, 
                Controller.EMsgKey.target: joint,
                Controller.EMsgKey.callback: callback
                }
        self.__send_message_wait_reply(message)

    def torque(self, target = True):
        callback = AsyncResult()
        message = {
                Controller.EMsgKey.type: Controller.EConType.torque, 
                Controller.EMsgKey.target: target,
                Controller.EMsgKey.callback: callback
                }
        self.__send_message_wait_reply(message)


class Trajectory:
    @classmethod
    def get_last_period(cls, src, dest, controll_period, max_speed):
        return int( math.ceil( abs ( ( 15.0 * ( dest - src ) / ( 8.0 * max_speed ) ) / controll_period ) ) )

    @classmethod
    def interporate_5poly(cls, src_, dest_, controll_period_, max_speed_):
        trajectory = []
        src = float(src_)
        dest = float(dest_)
        controll_period = float(controll_period_)
        max_speed = float(max_speed_)
        last_period = cls.get_last_period(src, dest, controll_period, max_speed)
        Logger.log(Logger.ELogLevel.TRACE, "interporate_5poly start, src = %f, dest = %f, last_period = %d", src, dest, last_period)
        
        for i in range(1, last_period + 1, 1):
            pos = cls.resolve_5poly(src, dest, i, last_period)
            trajectory.append(pos)
            Logger.log(Logger.ELogLevel.TRACE, "period = %d, pos = %f", i, pos)

        return trajectory

    @classmethod
    def resolve_5poly(cls, src, dest, period_, last_period_):
        period = float(period_)
        last_period = float(last_period_)
        return src + ( dest - src ) * ( ( period / last_period ) ** 3.0 ) * ( 10.0 - 15.0 * period / last_period + 6.0 * ( ( period / last_period ) ** 2.0 ) )

#
# main code
#
if __name__ == '__main__':
    Logger.log(Logger.ELogLevel.INFO_, "main start")
    c = Controller()
    c.torque(True)
    time.sleep(1)
    c.move_ptp(Joint(30.0, 30.0, 30.0, 30.0, 30.0, 30.0))
    c.move_ptp(Joint(-60.0, -60.0, -60.0, -60.0, -60.0, -60.0))
    c.move_ptp(Joint(90.0, 90.0, 90.0, 90.0, 90.0, 90.0))
    c.move_ptp(Joint(-120.0, -120.0, -120.0, -120.0, -120.0, -120.0))
    c.move_ptp(Joint(150.0, 150.0, 150.0, 150.0, 150.0, 150.0))
    c.move_ptp(Joint(-120.0, -120.0, -120.0, -120.0, -120.0, -120.0))
    c.move_ptp(Joint(90.0, 90.0, 90.0, 90.0, 90.0, 90.0))
    c.move_ptp(Joint(-60.0, -60.0, -60.0, -60.0, -60.0, -60.0))
    c.move_ptp(Joint(30.0, 30.0, 30.0, 30.0, 30.0, 30.0))
    c.torque(False)
