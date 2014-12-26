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
    EKinErr = enum.Enum("EKinErr", "none out_of_range no_solution")
    
    def __init__(self, la = 30.0, lb = 0.0, lc = 40.0, ld = 0.0, le = 0.0, lf  = 30.0, lg = 30.0, joint_limit = 150.0):
        self.la = la
        self.lb = lb
        self.lc = lc
        self.ld = ld
        self.le = le
        self.lf = lf
        self.lg = lg
        self.joint_limit_deg = joint_limit
        self.joint_limit_rad = np.deg2rad(joint_limit)
    
    def __get_t03(self, j):
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
        t03 = np.matrix([ 
                [ c1*c23,  s1, -c1*s23,  px ],
                [ s1*c23, -c1, -s1*s23,  py ],
                [   -s23, 0.0,    -c23,  pz ],
                [    0.0, 0.0,     0.0, 1.0 ]])
        return t03
 
    def __get_t36(self,j):
        s4 = np.sin(j.j4())
        s5 = np.sin(j.j5())
        s6 = np.sin(j.j6())
        c4 = np.cos(j.j4())
        c5 = np.cos(j.j5())
        c6 = np.cos(j.j6())

        rx = np.matrix([
                [ 1.0, 0.0, 0.0, 0.0 ],
                [ 0.0,  c4, -s4, 0.0 ],
                [ 0.0,  s4,  c4, 0.0 ],
                [ 0.0, 0.0, 0.0, 1.0 ]])
        ry = np.matrix([
                [  c5, 0.0,  s5, 0.0 ],
                [ 0.0, 1.0, 0.0, 0.0 ],
                [ -s5, 0.0,  c5, 0.0 ],
                [ 0.0, 0.0, 0.0, 1.0 ]])
        rz = np.matrix([
                [  c6, -s6, 0.0, 0.0 ], 
                [  s6,  c6, 0.0, 0.0 ],
                [ 0.0, 0.0, 1.0, 0.0 ],
                [ 0.0, 0.0, 0.0, 1.0 ]])
        tmp = np.dot(rz,ry)
        t36 = np.dot(tmp,rx)
        return t36
   
    def __get_t6h(self):
        t6h = np.matrix([
                [  1.0, 0.0, 0.0,     0.0 ],
                [  0.0, 1.0, 0.0,     0.0 ],
                [  0.0, 0.0, 1.0, self.lg ],
                [  0.0, 0.0, 0.0,     1.0 ]])
        return t6h
        
    def forward(self, j):
        t03 = self.__get_t03(j.deg2rad())
        j_ = j.deg2rad()
        j_.data[4] = -j_.data[4]
        t36 = self.__get_t36(j_)
        t06 = np.dot(t03, t36)
        tb6 = t06
        tb6[(2,3)] = tb6[(2,3)] + self.la
        t6h = self.__get_t6h()
        tbh = np.dot(tb6, t6h)
        Logger.log(Logger.ELogLevel.TRACE, "T(0->3) =\n%s", t03)
        Logger.log(Logger.ELogLevel.TRACE, "T(3->6) =\n%s", t36)
        Logger.log(Logger.ELogLevel.TRACE, "T(B->6) =\n%s", tb6)
        Logger.log(Logger.ELogLevel.TRACE, "T(6->H) =\n%s", t6h)
        Logger.log(Logger.ELogLevel.INFO_, "T(B->H) =\n%s", tbh)
        return Kinematics.mat2pose(tbh)

    @classmethod
    def mat2pose(cls, mat):
        pose = Pose(mat[(0,3)], mat[(1,3)], mat[(2,3)])
        cy = np.sqrt(mat[(2,1)]**2.0 + mat[(2,2)]**2.0)
        if cy == 0.0:
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
        nx = cz * cy
        ny = sz * cy
        nz = -sy
        sx = -sz*cx + cz*sy*sx
        sy = cz*cx + sz*sy*sx
        sz = cy*sx
        ax = sz*sx + cz*sy*cx
        ay = -cz*sx + sz*sy*cx
        az = cy*cx
        mat = np.matrix([
            [ nx, sx, ax, p.px()],
            [ ny, sy, ay, p.py()],
            [ nz, sz, az, p.pz()],
            [  0,  0,  0, 1    ]])
        return mat

    def inverse(self, pose):
        sol = []
        j1 = []

        tbh = Kinematics.pose2mat(pose)
        print(tbh)
        t6h = self.__get_t6h()
        print(t6h)
        inv_t6h = np.linalg.inv(t6h)
        print(inv_t6h)
        tb6 = np.dot(tbh, inv_t6h)
        print(tb6)
        t06 = tb6
        t06[(2,3)] = t06[(2,3)] - self.la
        p = Kinematics.mat2pose(t06)
        print(p)
        lbd = self.lb - self.ld
        px2ppy2 = p.px() ** 2.0 + p.py() ** 2.0
        sqr_px2ppy2 = np.sqrt(px2ppy2)
        a = lbd / sqr_px2ppy2

        if np.abs(a) > 1.0:
            return Kinematics.EKinErr.no_solution, None
    
        if px2ppy2 == 0.0:
            if self.lb != self.ld:
                return Kinematics.EKinErr.no_solution, None
            else:
                j1.append(0.0)
        else:
            j1.append(np.arctan2(p.py(), p.px()) - np.arctan2(a,  np.sqrt(1.0 - a ** 2.0)))
            j1.append(np.arctan2(p.py(), p.px()) - np.arctan2(a, -np.sqrt(1.0 - a ** 2.0)))

        px2ppy2ppz2 = px2ppy2 + p.pz() ** 2.0

        if px2ppy2ppz2 == 0.0:
            return Kinematics.EKinErr.out_of_range, None

        sol123 = []
        for i in range(len(j1)):
            if np.abs(j1[i]) <= self.joint_limit_rad:
                err, tmp = self.__inverse23(p, j1[i])
                if err is Kinematics.EKinErr.none:
                    sol123.extend(tmp)

        if len(sol123) == 0:
            return Kinematics.EKinErr.no_solution, None

        for i in range(len(sol123)):
            err, sol456 = self.__inverse456(p, Joint(sol123[i][0], sol123[i][1], sol123[i][2]))
            if err is Kinematics.EKinErr.none:    
                sol.extend(sol456)

        if len(sol) == 0:
            return Kinematics.EKinErr.out_of_range, None

        return Kinematics.EKinErr.none, sol
        
    def __inverse456(self, p, j):
        sol = []
        j4 = []
        t03 = self.__get_t03(j)
        t06 = Kinematics.pose2mat(p)
        t36 = np.dot(np.linalg.inv(t03), t06)
        ax = t36[(0,2)]
        ay = t36[(1,2)]
        ax2pay2 = (ax**2.0 + ay**2.0)
        if ax2pay2 == 0.0:
            j4.append(0.0)
        else:
            j4.append(np.arctan(ay/ax))
            j4.append(np.arctan(ay/ax) + np.pi)

        for i in range(len(j4)):
            if np.abs(j4[i]) <= self.joint_limit_rad:
                j5 = None
                j6 = None
                if ax2pay2 != 0.0:
                    j5, j6 = self.__inverse56(t36, j4[i])
                else:
                    #j5, j6 = self.__inverse56(t36, j4[i])
                    pass

                if np.abs(j5) <= self.joint_limit_rad and np.abs(j6) <= self.joint_limit_rad:
                    sol.append(Joint(j.j1(),j.j2(),j.j3(),j4[i],j5,j6).rad2deg())

        if len(sol) == 0:
            return Kinematics.EKinErr.out_of_range, None

        return Kinematics.EKinErr.none, sol

    def __inverse56(self, t36, j4):
        ax = t36[(0,2)]
        ay = t36[(1,2)]
        az = t36[(2,2)]
        sx = t36[(0,1)]
        sy = t36[(1,1)]
        nx = t36[(0,0)]
        ny = t36[(1,0)]
        c4 = np.cos(j4)
        s4 = np.sin(j4)

        s = np.arctan2(ax*c4 + ay*s4, az)
        j5 = -s
        j6 = np.arctan2(-nx*s4 + ny*c4, -sx*s4 + sy*c4)
        return (j5, j6)
 
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
            return Kinematics.EKinErr.no_solution, None

        z.append(np.arctan2(c,  np.sqrt(1.0 - c**2.0)) - e)
        z.append(np.arctan2(c, -np.sqrt(1.0 - c**2.0)) - e)

        for i in range(len(z)):
            j2, j3 = self.__inverseZ(p, b, z[i])
            Logger.log(Logger.ELogLevel.INFO_, "j1 = %-8.3f, j2 = %-8.3f, j3 = %-8.3f" % (np.rad2deg(j1), np.rad2deg(j2), np.rad2deg(j3)))
            if np.abs(j2) <= self.joint_limit_rad and np.abs(j3) <= self.joint_limit_rad:
                ret.append([j1,j2,j3])
        if len(ret) == 0:
            return Kinematics.EKinErr.out_of_range, None

        return Kinematics.EKinErr.none, ret

    def __inverseZ(self, p, b, z):
        sz = np.sin(z)
        cz = np.cos(z)
        j2 = np.arctan2(-p.pz() - self.le*sz - self.lf*cz, b - self.le * cz + self.lf * sz)
        j3 = z - j2
        return (j2, j3)

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
                home_position = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                for id in range(6):
                    self.controller.move(id, home_position[id], 300)
                    self.status[Controller.EStatKey.joint].data[id] = home_position[id]
                gevent.sleep(3)
                self.__update_pose()
                self.__callback(msg) 

            elif msg[Controller.EMsgKey.type] is Controller.EConType.move_ptp:
                Logger.log(Logger.ELogLevel.INFO_, "move_ptp start")
                trajectory = []     
                for id in range(6): 
                    trajectory.append(
                            Trajectory.interporate_poly5d(self.status[Controller.EStatKey.joint].data[id], 
                            msg[Controller.EMsgKey.target].data[id], self.controll_period, self.max_speed))
                
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
                    self.controller.move(params)
                    gevent.sleep(interval)

                for id in range(6):
                    self.status[Controller.EStatKey.joint].data[id] = msg[Controller.EMsgKey.target].data[id]

                self.__update_pose()
                self.__callback(msg) 
                Logger.log(Logger.ELogLevel.INFO_, "move_ptp end")
            
            else:
                Logger.log(Logger.ELogLevel.ERROR, "invalid message type, msg = %s", msg)
            
            gevent.sleep(0)
    
    def __update_pose(self):
        self.status[Controller.EStatKey.pose] = self.kinematics.forward(self.status[Controller.EStatKey.joint])
        Logger.log(Logger.ELogLevel.INFO_, "joint = %s, pose = %s", self.status[Controller.EStatKey.joint], self.status[Controller.EStatKey.pose])
        err, sol = self.kinematics.inverse(self.status[Controller.EStatKey.pose])
        if err is Kinematics.EKinErr.none:
            for i in range(len(sol)):
                Logger.log(Logger.ELogLevel.INFO_, "inverse kinematics solution = %s" % sol[i])
        else:
            Logger.log(Logger.ELogLevel.ERROR, "inverse kinematics error = %s" % err.name)

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
    def interporate_poly5d(cls, src_, dest_, controll_period_, max_speed_):
        trajectory = []
        src = float(src_)
        dest = float(dest_)
        controll_period = float(controll_period_)
        max_speed = float(max_speed_)
        last_period = cls.get_last_period(src, dest, controll_period, max_speed)
        Logger.log(Logger.ELogLevel.INFO_, "interporate_5poly start, src = %f, dest = %f, last_period = %d", src, dest, last_period)
        
        for i in range(1, last_period + 1, 1):
            pos = cls.resolve_poly5d(src, dest, i, last_period)
            trajectory.append(pos)
            Logger.log(Logger.ELogLevel.DEBUG, "period = %d, pos = %f", i, pos)

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
    c = Controller()
    c.torque(True)
    c.home()
    c.move_ptp(Joint(   0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint(  30.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint(  45.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint(  60.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint(  90.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint( 120.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint( 150.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint( -30.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint( -45.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint( -60.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint( -90.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint(-120.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    #c.move_ptp(Joint(-150.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    c.torque(False)
