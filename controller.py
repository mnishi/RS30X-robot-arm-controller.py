import sys
import os
import time
import numpy as np 
import enum 
import gevent
from gevent.queue import Queue
from gevent.event import AsyncResult
from flask import Flask, render_template
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
from RS30X.RS30X import *
from application import RS30XControllerWebSocketApplication

class Pose:
    def __init__(self, px = 0.0, py = 0.0, pz = 0.0, rx = 0.0, ry = 0.0, rz = 0.0):
        self.data = [px, py, pz, rx, ry, rz]
    def px(self):
        return self.data[0]
    def py(self):
        return self.data[1]
    def pz(self):
        return self.data[2]
    def rx(self):
        return self.data[3]
    def ry(self):
        return self.data[4]
    def rz(self):
        return self.data[5]
    def __str__(self):
        return "[%8.3f, %8.3f, %8.3f, %8.3f, %8.3f, %8.3f]" % (self.data[0],self.data[1],self.data[2],self.data[3],self.data[4],self.data[5])

class Joint:
    def __init__(self, j1 = 0.0, j2 = 0.0, j3 = 0.0, j4 = 0.0, j5 = 0.0, j6 = 0.0):
        self.data = [j1, j2, j3, j4, j5 ,j6]
    def __eq__(self, j):
        for i in range(6):
            if np.abs(self.data[i] - j.data[i]) > Kinematics.EPS:
                return False
        return True
    def __ne__(self, j):
        return not self == j
    def max_diff(self, j):
        max = 0.0
        for i in range(6):
            diff = np.abs(self.data[i] - j.data[i])
            if max < diff:
                max = diff
        return max
    def rad2deg(self):
        j = Joint()
        for i in range(6):
            j.data[i] = np.rad2deg(self.data[i])
        return j
    def deg2rad(self):
        j = Joint()
        for i in range(6):
            j.data[i] = np.deg2rad(self.data[i])
        return j
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
    def __str__(self):
        return "[%8.3f, %8.3f, %8.3f, %8.3f, %8.3f, %8.3f]" % (self.data[0],self.data[1],self.data[2],self.data[3],self.data[4],self.data[5])

class Kinematics:
    EKinErr = enum.Enum("EKinErr", "none out_of_range")
    EPS = 0.1 ** 12

    def __init__(self, la = 30.0, lb = 0.0, lc = 40.0, ld = 0.0, le = 0.0, lf  = 30.0, lg = 30.0, joint_limit = 150.0):
        self.la = la
        self.lb = lb
        self.lc = lc
        self.ld = ld
        self.le = le
        self.lf = lf
        self.lg = lg
        self.joint_limit_deg = joint_limit + Kinematics.EPS
        self.joint_limit_rad = np.deg2rad(joint_limit) + Kinematics.EPS
    
    def __get_t03_(self, j):
        s23 = np.sin(j.j2() + j.j3())
        c23 = np.cos(j.j2() + j.j3())
        lbd = self.lb - self.ld

        s1 = np.sin(j.j1())
        s2 = np.sin(j.j2())
        c1 = np.cos(j.j1())
        c2 = np.cos(j.j2())

        lcc2plec23mlfs23 = self.lc * c2 + self.le * c23 - self.lf * s23
        px = c1 * lcc2plec23mlfs23 - lbd * s1        
        py = s1 * lcc2plec23mlfs23 + lbd * c1        
        pz = -(self.lc * s2)-(self.le * s23)-(self.lf * c23)
        t03_ = np.matrix([ 
                [ c1*c23,  s1, -c1*s23,  px ],
                [ s1*c23, -c1, -s1*s23,  py ],
                [   -s23, 0.0,    -c23,  pz ],
                [    0.0, 0.0,     0.0, 1.0 ]])
        return t03_

    @classmethod
    def get_rx(cls, x):
        sx = np.sin(x)
        cx = np.cos(x)
        rx = np.matrix([
                [ 1.0, 0.0, 0.0, 0.0 ],
                [ 0.0,  cx, -sx, 0.0 ],
                [ 0.0,  sx,  cx, 0.0 ],
                [ 0.0, 0.0, 0.0, 1.0 ]])
        return rx
 
    @classmethod
    def get_ry(cls, y):
        sy = np.sin(y)
        cy = np.cos(y)
        ry = np.matrix([
                [  cy, 0.0,  sy, 0.0 ],
                [ 0.0, 1.0, 0.0, 0.0 ],
                [ -sy, 0.0,  cy, 0.0 ],
                [ 0.0, 0.0, 0.0, 1.0 ]])
        return ry

    @classmethod
    def get_rz(cls, z):
        sz = np.sin(z)
        cz = np.cos(z)
        rz = np.matrix([
                [  cz, -sz, 0.0, 0.0 ], 
                [  sz,  cz, 0.0, 0.0 ],
                [ 0.0, 0.0, 1.0, 0.0 ],
                [ 0.0, 0.0, 0.0, 1.0 ]])
        return rz

    def __get_t36_(self, j):
        tmp = np.dot(Kinematics.get_rz(j.j4()), Kinematics.get_ry(j.j5()))
        t36_ = np.dot(tmp, Kinematics.get_rz(j.j6()))
        return t36_
   
    def __get_t6h(self):
        t6h = np.matrix([
                [  1.0, 0.0, 0.0,     0.0 ],
                [  0.0, 1.0, 0.0,     0.0 ],
                [  0.0, 0.0, 1.0, self.lg ],
                [  0.0, 0.0, 0.0,     1.0 ]])
        return t6h
        
    def forward(self, j):
        t03_ = self.__get_t03_(j.deg2rad())
        j_ = j.deg2rad()
        j_.data[4] = -j_.data[4]
        t36_ = self.__get_t36_(j_)
        t06 = np.dot(t03_, t36_)
        la = np.matrix([
                [  0.0, 0.0, 0.0,     0.0 ],
                [  0.0, 0.0, 0.0,     0.0 ],
                [  0.0, 0.0, 0.0, self.la ],
                [  0.0, 0.0, 0.0,     0.0 ]])
        tb6 = t06 + la
        t6h = self.__get_t6h()
        tbh = np.dot(tb6, t6h)
        Logger.log(Logger.ELogLevel.TRACE, "t03_=\n%s", t03_)
        Logger.log(Logger.ELogLevel.TRACE, "t36_=\n%s", t36_)
        Logger.log(Logger.ELogLevel.TRACE, "t06 =\n%s", t06)
        Logger.log(Logger.ELogLevel.TRACE, "tb6 =\n%s", tb6)
        Logger.log(Logger.ELogLevel.TRACE, "t6h =\n%s", t6h)
        Logger.log(Logger.ELogLevel.TRACE, "tbh =\n%s", tbh)
        return Kinematics.mat2pose(tbh)

    @classmethod
    def mat2pose(cls, mat):
        pose = Pose(mat[(0,3)], mat[(1,3)], mat[(2,3)])
        cy = np.sqrt(mat[(2,1)]**2.0 + mat[(2,2)]**2.0)
        if cy < Kinematics.EPS:
            pose.data[3] = 0.0
            if mat[(2,0)] < 0.0:
                pose.data[4] = 90.0
                pose.data[5] = np.rad2deg(np.arctan2(mat[(0,1)], mat[(1,1)]))
            else:
                pose.data[4] = -90.0
                pose.data[5] = -np.rad2deg(np.arctan2(mat[(0,1)], mat[(1,1)]))
        else:
            pose.data[3] = np.rad2deg(np.arctan2(mat[(2,1)], mat[(2,2)]))
            pose.data[4] = np.rad2deg(np.arctan2(-mat[(2,0)], cy))
            pose.data[5] = np.rad2deg(np.arctan2(mat[(1,0)], mat[(0,0)]))
        return pose

    @classmethod
    def pose2mat(cls, p):
        cx = np.cos(np.deg2rad(p.rx()))
        cy = np.cos(np.deg2rad(p.ry()))
        cz = np.cos(np.deg2rad(p.rz()))
        sx = np.sin(np.deg2rad(p.rx()))
        sy = np.sin(np.deg2rad(p.ry()))
        sz = np.sin(np.deg2rad(p.rz()))
        r11 = cz * cy
        r21 = sz * cy
        r31 = -sy
        r12 = -sz*cx + cz*sy*sx
        r22 = cz*cx + sz*sy*sx
        r32 = cy*sx
        r13 = sz*sx + cz*sy*cx
        r23 = -cz*sx + sz*sy*cx
        r33 = cy*cx
        mat = np.matrix([
            [ r11, r12, r13, p.px()],
            [ r21, r22, r23, p.py()],
            [ r31, r32, r33, p.pz()],
            [  0,  0,  0, 1    ]])
        return mat

    def inverse(self, pose, joint = Joint()):
        sol = []
        j1 = []

        tbh = Kinematics.pose2mat(pose)
        t6h = self.__get_t6h()
        inv_t6h = np.linalg.inv(t6h)
        tb6 = np.dot(tbh, inv_t6h)
        la = np.matrix([
                [  0.0, 0.0, 0.0,     0.0 ],
                [  0.0, 0.0, 0.0,     0.0 ],
                [  0.0, 0.0, 0.0, self.la ],
                [  0.0, 0.0, 0.0,     0.0 ]])
        t06 = tb6 - la
        p = Kinematics.mat2pose(t06)

        Logger.log(Logger.ELogLevel.TRACE, "t06 =\n%s", t06)
        Logger.log(Logger.ELogLevel.TRACE, "tb6 =\n%s", tb6)
        Logger.log(Logger.ELogLevel.TRACE, "t6h =\n%s", t6h)
        Logger.log(Logger.ELogLevel.TRACE, "tbh =\n%s", tbh)

        lbd = self.lb - self.ld
        px2ppy2 = p.px() ** 2.0 + p.py() ** 2.0
        sqr_px2ppy2 = np.sqrt(px2ppy2)
        a = lbd / sqr_px2ppy2

        if np.abs(a) > 1.0:
            return Kinematics.EKinErr.out_of_range, None
    
        if px2ppy2 < Kinematics.EPS:
            if self.lb != self.ld:
                return Kinematics.EKinErr.out_of_range, None
            else:
                j1.append(0.0)
        else:
            j1.append(Kinematics.nomalize_rad(np.arctan2(p.py(), p.px()) - np.arctan2(a,  np.sqrt(1.0 - a ** 2.0))))
            j1.append(Kinematics.nomalize_rad(np.arctan2(p.py(), p.px()) - np.arctan2(a, -np.sqrt(1.0 - a ** 2.0))))
    
        px2ppy2ppz2 = px2ppy2 + p.pz() ** 2.0

        if px2ppy2ppz2 < Kinematics.EPS:
            return Kinematics.EKinErr.out_of_range, None
        sol123 = []
        for i in range(len(j1)):
            if np.abs(j1[i]) <= self.joint_limit_rad:
                err, tmp = self.__inverse23(p, j1[i])
                if err is Kinematics.EKinErr.none:
                    sol123.extend(tmp)

        Logger.log(Logger.ELogLevel.TRACE, "sol123 = %s", np.rad2deg(sol123)) 

        if len(sol123) == 0:
            return Kinematics.EKinErr.out_of_range, None
        for i in range(len(sol123)):
            err, sol456 = self.__inverse456(t06, Joint(sol123[i][0], sol123[i][1], sol123[i][2]))
            if err is Kinematics.EKinErr.none:    
                sol.extend(sol456)

        if len(sol) == 0:
            return Kinematics.EKinErr.out_of_range, None
        elif len(sol) == 1:
            return Kinematics.EKinErr.none, sol[0]

        Logger.log(Logger.ELogLevel.TRACE, "joint = %s", joint) 
        Logger.log(Logger.ELogLevel.TRACE, "sol[0] = %s", sol[0]) 
        max_diff = sol[0].max_diff(joint)
        max_diff_id = 0
        for i in range(1,len(sol)):
            Logger.log(Logger.ELogLevel.TRACE, "sol[%d] = %s", i, sol[i]) 
            diff = sol[i].max_diff(joint)
            if max_diff > diff:
                max_diff = diff
                max_diff_id = i
    
        return Kinematics.EKinErr.none, sol[max_diff_id]
    
    @classmethod
    def nomalize_rad(cls, rad):
        rad = rad + np.pi
        rad = rad % (2.0 * np.pi)
        if rad < 0.0:
            rad = rad + np.pi
        else:
            rad = rad - np.pi
        return rad

    def __inverse456(self, t06, j):
        sol = []
        j4 = []
        t03_ = self.__get_t03_(j)
        t36_ = np.dot(np.linalg.inv(t03_), t06)
        ax = t36_[(0,2)]
        ay = t36_[(1,2)]
        az = t36_[(2,2)]
        ax2pay2 = (ax**2.0 + ay**2.0)
        
        if ax2pay2 < Kinematics.EPS:
            j4.append(0.0)
        else:
            j4.append(Kinematics.nomalize_rad(np.arctan(ay/ax)))
            j4.append(Kinematics.nomalize_rad(np.arctan(ay/ax) + np.pi))
 
        Logger.log(Logger.ELogLevel.TRACE, "j4 = %s", np.rad2deg(j4)) 

        for i in range(len(j4)):
            if np.abs(j4[i]) <= self.joint_limit_rad:
                j5 = None
                j6 = None
                if ax2pay2 > Kinematics.EPS:
                    j5, j6 = self.__inverse56(t36_, j4[i])
                else:
                    j5, j6 = self.__inverse56(t36_, j4[i])
                    j5 = Kinematics.nomalize_rad(np.pi / 2.0 * ( 1.0 - az))

                if np.abs(j5) <= self.joint_limit_rad and np.abs(j6) <= self.joint_limit_rad:
                    sol.append(Joint(j.j1(),j.j2(),j.j3(),j4[i],-j5,j6).rad2deg())

        if len(sol) == 0:
            return Kinematics.EKinErr.out_of_range, None

        return Kinematics.EKinErr.none, sol

    def __inverse56(self, t36_, j4):
        ax = t36_[(0,2)]
        ay = t36_[(1,2)]
        az = t36_[(2,2)]
        sx = t36_[(0,1)]
        sy = t36_[(1,1)]
        nx = t36_[(0,0)]
        ny = t36_[(1,0)]
        c4 = np.cos(j4)
        s4 = np.sin(j4)

        s = np.arctan2(ax*c4 + ay*s4, az)
        j5 = s
        j6 = np.arctan2(-nx*s4 + ny*c4, -sx*s4 + sy*c4)
        return (Kinematics.nomalize_rad(j5), Kinematics.nomalize_rad(j6))
 
    def __inverse23(self, p, j1):
        ret = []
        z = []

        s1 = np.sin(j1)
        c1 = np.cos(j1)

        b = p.px() * c1 + p.py() * s1
        e = np.arctan2(self.lf * p.pz() - b * self.le, self.le * p.pz() + b * self.lf)
        cu = self.lc**2.0 - b**2.0 - p.pz()**2.0 - self.le**2.0 - self.lf**2.0
        cl = 2.0 * np.sqrt((self.le * p.pz() + b * self.lf)**2.0 + (self.lf * p.pz() - b * self.le)**2.0)
        c = cu / cl

        if np.abs(c) > 1.0:
            return Kinematics.EKinErr.out_of_range, None

        z.append(np.arctan2(c,  np.sqrt(1.0 - c**2.0)) - e)
        z.append(np.arctan2(c, -np.sqrt(1.0 - c**2.0)) - e)

        for i in range(len(z)):
            j2, j3 = self.__inverseZ(p, b, z[i])
            if np.abs(j2) <= self.joint_limit_rad and np.abs(j3) <= self.joint_limit_rad:
                ret.append([j1,j2,j3])
                Logger.log(Logger.ELogLevel.TRACE, "inverse kinematics solution j123, j1 = %-8.3f, j2 = %-8.3f, j3 = %-8.3f" % (np.rad2deg(j1), np.rad2deg(j2), np.rad2deg(j3)))
        if len(ret) == 0:
            return Kinematics.EKinErr.out_of_range, None

        return Kinematics.EKinErr.none, ret

    def __inverseZ(self, p, b, z):
        sz = np.sin(z)
        cz = np.cos(z)
        j2 = np.arctan2(-p.pz() - self.le*sz - self.lf*cz, b - self.le * cz + self.lf * sz)
        j3 = z - j2
        return (Kinematics.nomalize_rad(j2), Kinematics.nomalize_rad(j3))

class Controller:
    EMsgKey = enum.Enum("EMsgKey", "msg_type target callback")
    EConType = enum.Enum("EConType", "move_ptp torque home")
    EStatKey = enum.Enum("EStatKey", "pose joint busy")

    @classmethod
    def tenth_deg(cls, deg):
        return int(round(deg * 10.0, 0))

    def __init__(self, controll_period = 20.0, max_speed = 240.0 / 1000.0, loglv = Logger.ELogLevel.DEBUG):
        Logger.level = loglv 
        self.max_speed = max_speed # deg per msec
        self.controll_period = controll_period # msec
        self.status = {}
        self.status[Controller.EStatKey.pose] = Pose() 
        self.status[Controller.EStatKey.joint] = Joint() 
        self.status[Controller.EStatKey.busy] = False 
        self.controller = RS30XController()
        self.kinematics = Kinematics()
        self.queue = Queue()
        self.notifier = None
        gevent.spawn(self.__handle_massage)

    def __handle_massage(self):
        msg = None
        while True:
            msg = self.queue.get()
            Logger.log(Logger.ELogLevel.TRACE, "new message, msg = %s", msg)
            
            if msg is None:
                pass
            elif msg[Controller.EMsgKey.msg_type] is Controller.EConType.torque:
                target = msg[Controller.EMsgKey.target]
                Logger.log(Logger.ELogLevel.INFO_, "torque, target = %d", target)
                for id in range(6):
                    if target is True:
                        self.controller.torqueOn(id)
                    else:
                        self.controller.torqueOff(id)
                self.__callback(msg) 

            elif msg[Controller.EMsgKey.msg_type] is Controller.EConType.home:
                self.status[Controller.EStatKey.busy] = True
                home_position = [0.0, -45.0, 0.0, 0.0, 45.0, 0.0]
                for id in range(6):
                    self.controller.move(id, home_position[id], 300)
                    self.status[Controller.EStatKey.joint].data[id] = home_position[id]
                gevent.sleep(3)
                self.status[Controller.EStatKey.busy] = False
                self.__update_pose()
                self.__callback(msg) 

            elif msg[Controller.EMsgKey.msg_type] is Controller.EConType.move_ptp:
                Logger.log(Logger.ELogLevel.INFO_, "move_ptp, start")
                self.status[Controller.EStatKey.busy] = True
                trajectory = []
                target = msg[Controller.EMsgKey.target]
                current = self.status[Controller.EStatKey.joint]

                if isinstance(target, Pose):
                    Logger.log(Logger.ELogLevel.INFO_,"move_ptp, target_pose = %s", target)
                    err, target = self.kinematics.inverse(target, current)
                    if err is not Kinematics.EKinErr.none:
                        Logger.log(Logger.ELogLevel.ERROR, "inverse kinematics error = %s", err.name)
                        self.__callback(msg, err)
                        continue

                Logger.log(Logger.ELogLevel.INFO_,"move_ptp, target_joint = %s", target)
                for id in range(6): 
                    trajectory.append(
                            Trajectory.interporate_poly5d(
                                current.data[id], 
                                target.data[id], 
                                self.controll_period, 
                                self.max_speed))
                
                periods = 0 
                for id in range(6): 
                    if periods < len(trajectory[id]):
                        periods = len(trajectory[id])

                interval = self.controll_period / 1000.0
                
                for period in range(periods):
                    Logger.log(Logger.ELogLevel.TRACE, "period = %d", period)
                    params = []
                    
                    for id in range(6):
                        if len(trajectory[id]) > period:
                            param = RS30XParameter(id, Controller.tenth_deg(trajectory[id][period]), int(self.controll_period))
                            params.append(param)
                            if period > 0:
                                self.status[Controller.EStatKey.joint].data[id] = trajectory[id][period - 1]
                    self.controller.move(params)
                    self.__update_pose(not self.status[Controller.EStatKey.busy])
                    gevent.sleep(interval)

                for id in range(6):
                    self.status[Controller.EStatKey.joint].data[id] = target.data[id]

                self.status[Controller.EStatKey.busy] = False 
                self.__update_pose(not self.status[Controller.EStatKey.busy])
                self.__callback(msg) 
                Logger.log(Logger.ELogLevel.INFO_, "move_ptp, end")
            
            else:
                Logger.log(Logger.ELogLevel.ERROR, "invalid message type, msg = %s", msg)
            
            gevent.sleep(0)
    
    def __update_pose(self, report = True):
        self.status[Controller.EStatKey.pose] = self.kinematics.forward(self.status[Controller.EStatKey.joint])
        if self.notifier is not None:
            self.notifier()
        if report is True: 
            Logger.log(Logger.ELogLevel.INFO_, "update_pose, joint = %s", self.status[Controller.EStatKey.joint])
            Logger.log(Logger.ELogLevel.INFO_, "update_pose, pose = %s", self.status[Controller.EStatKey.pose])
            if Logger.level.value >= Logger.ELogLevel.DEBUG.value:
                err, sol = self.kinematics.inverse(self.status[Controller.EStatKey.pose], self.status[Controller.EStatKey.joint])
                if err is Kinematics.EKinErr.none:
                    if sol != self.status[Controller.EStatKey.joint]:
                        Logger.log(Logger.ELogLevel.ERROR, "inverse kinematics solution does not correspond, result = %s", sol)
                else:
                    Logger.log(Logger.ELogLevel.ERROR, "inverse kinematics error = %s", err.name)

    def __callback(self, msg, value = None):
        if msg[Controller.EMsgKey.callback] is not None:
            msg[Controller.EMsgKey.callback].set(value)
    
    def __send_message_wait_reply(self, message):
        self.queue.put(message)
        Logger.log(Logger.ELogLevel.TRACE, "message send, msg = %s", message)
        message[Controller.EMsgKey.callback].get()
        Logger.log(Logger.ELogLevel.TRACE, "message replied, msg = %s", message)

    def move_ptp(self, target):
        callback = AsyncResult()
        message = {
                Controller.EMsgKey.msg_type: Controller.EConType.move_ptp, 
                Controller.EMsgKey.target: target,
                Controller.EMsgKey.callback: callback
                }
        gevent.spawn(self.__send_message_wait_reply, message)

    def torque(self, target = True):
        callback = AsyncResult()
        message = {
                Controller.EMsgKey.msg_type: Controller.EConType.torque, 
                Controller.EMsgKey.target: target,
                Controller.EMsgKey.callback: callback
                }
        gevent.spawn(self.__send_message_wait_reply, message)

    def home(self):
        callback = AsyncResult()
        message = {
                Controller.EMsgKey.msg_type: Controller.EConType.home, 
                Controller.EMsgKey.callback: callback
                }
        gevent.spawn(self.__send_message_wait_reply, message)

    def set_notifier(self, notifier):
        self.notifier = notifier

class Trajectory:
    @classmethod
    def get_last_period(cls, src, dest, controll_period, max_speed):
        return int( np.ceil( np.abs ( ( 15.0 * ( dest - src ) / ( 8.0 * max_speed ) ) / controll_period ) ) )

    @classmethod
    def interporate_poly5d(cls, src_, dest_, controll_period_, max_speed_):
        trajectory = []
        src = float(src_)
        dest = float(dest_)
        controll_period = float(controll_period_)
        max_speed = float(max_speed_)
        last_period = cls.get_last_period(src, dest, controll_period, max_speed)
        Logger.log(Logger.ELogLevel.INFO_, "interporate_poly5d start, src = %f, dest = %f, last_period = %d", src, dest, last_period)
        
        for i in range(1, last_period + 1, 1):
            pos = cls.resolve_poly5d(src, dest, i, last_period)
            trajectory.append(pos)
            Logger.log(Logger.ELogLevel.TRACE, "period = %d, pos = %f", i, pos)

        return trajectory

    @classmethod
    def resolve_poly5d(cls, src, dest, period_, last_period_):
        period = float(period_)
        last_period = float(last_period_)
        return src + ( dest - src ) * ( ( period / last_period ) ** 3.0 ) * ( 10.0 - 15.0 * period / last_period + 6.0 * ( ( period / last_period ) ** 2.0 ) )

#
# main code
#
if __name__ == '__main__':
    Logger.log(Logger.ELogLevel.INFO_, "main start")

    address = '0.0.0.0'
    port = 8000

    if len(sys.argv) > 1:
        address = sys.argv[1]

    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    controller = Controller()
    controller.torque(True)
    controller.home()

    RS30XControllerWebSocketApplication.set_controller(controller)

    flask_app = Flask(__name__)
    #flask_app.debug = True
    
    @flask_app.route("/")
    def index():
       return render_template('index.html')

    server = WebSocketServer(
            (address, port),
            Resource({
                '/'  : flask_app,
                '/ws': RS30XControllerWebSocketApplication
                }),
            debug=False
            )
    server.serve_forever()
    
