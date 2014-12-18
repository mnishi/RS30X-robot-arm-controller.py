import sys
import os
import time
import numpy as np 
import enum 
import gevent
from gevent.queue import Queue
from gevent.event import AsyncResult
from RS30X.RS30X import *

class Pose:
    def __init__(self, px = 0.0, py = 0.0, pz = 0.0, ox = 0.0, oy = 0.0, oz = 0.0):
        self.data = [px, py, pz, ox, oy, oz]
    def px(self):
        return self.data[0]
    def py(self):
        return self.data[1]
    def pz(self):
        return self.data[2]
    def ox(self):
        return self.data[3]
    def oy(self):
        return self.data[4]
    def oz(self):
        return self.data[5]

class Joint:
    def __init__(self, j1 = 0.0, j2 = 0.0, j3 = 0.0, j4 = 0.0, j5 = 0.0, j6 = 0.0):
        self.data = [j1, j2, j3, j4, j5 ,j6]
    def j1(self):
        return self.data[0]
    def j2(self):
        return self.data[1]
    def j3(self):
        return self.data[2]
    def j4(self):
        return self.data[3]
    def j5(self):
        return self.data[4]
    def j6(self):
        return self.data[5]

class Kinematics:
    def __init__(self, la = 30.0, lb = 1.0, lc = 30.0, ld = 1.0, le = 1.0, lf  = 30.0, lg = 1.0):
        self.la = la
        self.lb = lb
        self.lc = lc
        self.ld = ld
        self.le = le
        self.lf = lf
        self.lg = lg

    def forward(self, j):
        s23 = np.sin(np.pi/180.0*j.j2() + j.j3())
        c23 = np.cos(np.pi/180.0*j.j2() + j.j3())
        lbd = self.lb - self.ld
        s1 = np.sin(np.pi/180.0*j.j1())
        s2 = np.sin(np.pi/180.0*j.j2())
        s4 = np.sin(np.pi/180.0*j.j4())
        s5 = np.sin(np.pi/180.0*-j.j5())
        s6 = np.sin(np.pi/180.0*j.j6())
        c1 = np.cos(np.pi/180.0*j.j1())
        c2 = np.sin(np.pi/180.0*j.j2())
        c4 = np.cos(np.pi/180.0*j.j4())
        c5 = np.cos(np.pi/180.0*-j.j5())
        c6 = np.cos(np.pi/180.0*j.j6())
        lcc2plec23mlfs23 = self.lc * c2 + self.le * c23 - self.lf * s23
        px = c1 * lcc2plec23mlfs23 - lbd * s1        
        py = s1 * lcc2plec23mlfs23 + lbd * s1        
        pz = -(self.lc * s2)-(self.le * s23)-(self.lf * c23)
        t03 = np.matrix([ 
                [c1*c23, s1, -c1*s23, px],
                [s1*c23,-c1, -s1*s23, py],
                [  -s23,  0,    -c23, pz],
                [     0,  0,       0,  1]])
        rx = np.matrix([
                [  0,  0,  0,  0],
                [  0, c4,-s4,  0],
                [  0, s4, c4,  0],
                [  0,  0,  0,  1]])
        ry = np.matrix([
                [ c5,  0, s5,  0],
                [  0,  1,  0,  0],
                [-s5,  0, c5,  0],
                [  0,  0,  0,  1]])
        rz = np.matrix([
                [ c6,-s6,  0,  0],
                [ s6, c6,  0,  0],
                [  0,  0,  1,  0],
                [  0,  0,  0,  1]])
        tmp = np.dot(rx,ry)
        t36 = np.dot(tmp,rz)
        t06 = np.dot(t03, t36)
        tb6 = t06
        tb6[(2,3)] = tb6[(2,3)] + self.la
        t6h = np.matrix([
                [  1,  0,  0,       0],
                [  0,  1,  0,       0],
                [  0,  0,  1, self.lg],
                [  0,  0,  0,       1]])
        tbh = np.dot(tb6, t6h)
        Logger.log(Logger.ELogLevel.TRACE, "0T3 =\n%s", t03)
        Logger.log(Logger.ELogLevel.TRACE, "3T6 =\n%s", t36)
        Logger.log(Logger.ELogLevel.TRACE, "BT6 =\n%s", tb6)
        Logger.log(Logger.ELogLevel.TRACE, "6TH =\n%s", t6h)
        Logger.log(Logger.ELogLevel.TRACE, "BTH =\n%s", tbh)
        pose = Pose(tbh[(0,3)], tbh[(1,3)], tbh[(2,3)])
        if np.abs(tbh[(0,2)]) != 1.0:
            pose.data[3] = np.arctan2(tbh[(2,1)], tbh[(2,2)]) * 180.0 / np.pi
            pose.data[4] = np.arcsin(-tbh[(2,0)]) * 180.0 / np.pi
            pose.data[5] = np.arctan2(tbh[(1,0)], tbh[(0,0)]) * 180.0 / np.pi
        else:
            pose.data[3] = 0.0
            pose.data[4] = np.arcsin(-tbh[(2,0)]) * 180.0 / np.pi
            pose.data[5] = np.arctan2(tbh[(0,1)], tbh[(1,1)]) * 180.0 / np.pi
        return pose 
 
class Controller:
    EMsgKey = enum.Enum("EMsgKey", "type target callback")
    EConType = enum.Enum("EConType", "move_ptp torque home")
    EStatKey = enum.Enum("EStatKey", "pose joint")

    @classmethod
    def tenth_deg(cls, deg):
        return int(round(deg * 10.0, 0))

    def __init__(self, controll_period = 20.0, max_speed = 240.0 / 1000.0):
        self.max_speed = max_speed # deg per msec
        self.controll_period = controll_period # msec
        self.status = {}
        self.status[Controller.EStatKey.pose] = Pose() 
        self.status[Controller.EStatKey.joint] = Joint() 
        self.controller = RS30XController()
        self.kinematics = Kinematics()
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
                Logger.log(Logger.ELogLevel.INFO_, "target = %d", target)
                for id in range(6):
                    if target is True:
                        self.controller.torqueOn(id)
                    else:
                        self.controller.torqueOff(id)
                self.__callback(msg) 

            elif msg[Controller.EMsgKey.type] is Controller.EConType.home:
                home_position = [0.0, 0.0, 90.0, 0.0, 0.0, 0.0]
                for id in range(6):
                    self.controller.move(id, home_position[id], 300)
                    self.status[Controller.EStatKey.joint].data[id] = home_position[id]
                gevent.sleep(3)
                self.__update_pose()
                self.__callback(msg) 

            elif msg[Controller.EMsgKey.type] is Controller.EConType.move_ptp:
                Logger.log(Logger.ELogLevel.INFO_, "move_ptp start")
                trajectory = []     
                for i in range(6): 
                    trajectory.append(Trajectory.interporate_5poly(self.status[Controller.EStatKey.joint].data[i], msg[Controller.EMsgKey.target].data[i], self.controll_period, self.max_speed))
                periods = len(trajectory[0]) 
                interval = self.controll_period / 1000.0
                
                for period in range(periods):
                    Logger.log(Logger.ELogLevel.TRACE, "period = %d", period)
                    params = []

                    for id in range(6):
                        param = RS30XParameter(id, Controller.tenth_deg(trajectory[i][period]), int(self.controll_period))
                        params.append(param)
                    self.controller.move(params)
                    gevent.sleep(interval)

                for i in range(6):
                    self.status[Controller.EStatKey.joint].data[i] = msg[Controller.EMsgKey.target].data[i]
                self.__update_pose()
                self.__callback(msg) 
                Logger.log(Logger.ELogLevel.INFO_, "move_ptp end")
            else:
                Logger.log(Logger.ELogLevel.ERROR, "invalid message type, msg = %s", msg)
            
            gevent.sleep(0)
    
    def __update_pose(self):
        self.status[Controller.EStatKey.pose] = self.kinematics.forward(self.status[Controller.EStatKey.joint])
        Logger.log(Logger.ELogLevel.INFO_, "joint = %s, pose = %s", self.status[Controller.EStatKey.joint].data, self.status[Controller.EStatKey.pose].data)

    def __callback(self, msg):
        if msg[Controller.EMsgKey.callback] is not None:
            msg[Controller.EMsgKey.callback].set()
    
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

    def home(self):
        callback = AsyncResult()
        message = {
                Controller.EMsgKey.type: Controller.EConType.home, 
                Controller.EMsgKey.callback: callback
                }
        self.__send_message_wait_reply(message)

class Trajectory:
    @classmethod
    def get_last_period(cls, src, dest, controll_period, max_speed):
        return int( np.ceil( np.abs ( ( 15.0 * ( dest - src ) / ( 8.0 * max_speed ) ) / controll_period ) ) )

    @classmethod
    def interporate_5poly(cls, src_, dest_, controll_period_, max_speed_):
        trajectory = []
        src = float(src_)
        dest = float(dest_)
        controll_period = float(controll_period_)
        max_speed = float(max_speed_)
        last_period = cls.get_last_period(src, dest, controll_period, max_speed)
        Logger.log(Logger.ELogLevel.INFO_, "interporate_5poly start, src = %f, dest = %f, last_period = %d", src, dest, last_period)
        
        for i in range(1, last_period + 1, 1):
            pos = cls.resolve_5poly(src, dest, i, last_period)
            trajectory.append(pos)
            Logger.log(Logger.ELogLevel.DEBUG, "period = %d, pos = %f", i, pos)

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
    c.home()
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
