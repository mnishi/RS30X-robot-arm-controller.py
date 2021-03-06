import copy
import json
import gevent
from gevent.queue import Queue, Empty
from geventwebsocket import WebSocketApplication, WebSocketError
import enum 
from RS30X.RS30X import *

class RS30XControllerWebSocketApplication(WebSocketApplication):
    EMsgKey = enum.Enum("EMsgKey", "msg_type client")
    EMsgType = enum.Enum("EMsgType", "add_client remove_client status jog move speed error area_check")
    EAreaChkParam = enum.Enum("EAreaChkParam", "target")
    EAreaChkType = enum.Enum("EAreaChkType", "on off")
    EErrParam = enum.Enum("EErrType", "error")
    EJogParam = enum.Enum("EJogParam", "target_type target direction volume interpolate_type")
    EMoveParam = enum.Enum("EMoveParam", "target_type target interpolate_type")
    ESpeedParam = enum.Enum("ESpeedParam", "target")
    EJogDir = enum.Enum("EJogDir", "dec inc")
    EJogVol = enum.Enum("EJogVol", "small medium large")
    ETarType = enum.Enum("ETarType", "pose joint")
    EIntpType = enum.Enum("EIntpType", "line ptp")
    EPoseComp = enum.Enum("EPoseComp", "px py pz rx ry rz")
    EJointComp = enum.Enum("EJointComp", "j1 j2 j3 j4 j5 j6")

    controller = None
    initialized = False
    queue = Queue()
    clients = set() 

    @classmethod
    def set_controller(cls, controller):
        cls.controller = controller

    def on_open(self):
        if self.initialized is not True:
            self.controller.set_status_notifier(self.notify_status)
            self.controller.set_error_notifier(self.notify_error)
            gevent.spawn(self.__handle_message)
            self.initialized = True

        self.add_client(self)
        self.send_status(self.ws)

    @classmethod
    def __jog(cls, msg):
        target = None
        if msg[cls.EJogParam.target_type] is cls.ETarType.pose:
            target = copy.deepcopy(cls.controller.status[cls.controller.EStatKey.pose]) 
        else:
            target = copy.deepcopy(cls.controller.status[cls.controller.EStatKey.joint]) 
        index = msg[cls.EJogParam.target].value - 1
        volume = 10.0
        if msg[cls.EJogParam.volume] is cls.EJogVol.medium:
            volume = 1.0
        elif msg[cls.EJogParam.volume] is cls.EJogVol.small:
            volume = 0.1
        if msg[cls.EJogParam.direction] is cls.EJogDir.dec:
            volume = -volume
        target.data[index] = target.data[index] + volume
        if msg[cls.EJogParam.target_type] is cls.ETarType.pose and msg[cls.EJogParam.interpolate_type] is cls.EIntpType.line:
            cls.controller.move_line(target)
        else:
            cls.controller.move_ptp(target)
        return
  
    def __handle_message(self):
        msg = None
        while True:
            msg = self.queue.get()
            if msg is None:
                pass
            elif msg[self.EMsgKey.msg_type] is self.EMsgType.add_client:
                self.clients.add(msg[self.EMsgKey.client])
            elif msg[self.EMsgKey.msg_type] is self.EMsgType.remove_client:
                self.clients.discard(msg[self.EMsgKey.client])
            elif msg[self.EMsgKey.msg_type] is self.EMsgType.jog:
                self.__jog(msg)
            elif msg[self.EMsgKey.msg_type] is self.EMsgType.move:
                if msg[self.EMoveParam.target_type] is self.ETarType.pose and msg[self.EMoveParam.interpolate_type] is self.EIntpType.line:
                    self.controller.move_line(msg[self.EMoveParam.target])
                else:
                    self.controller.move_ptp(msg[self.EMoveParam.target])
            elif msg[self.EMsgKey.msg_type] is self.EMsgType.status:
                j = self.jsonize_status() 
                for client in self.clients:
                    self.send_status(client.ws, j)
            elif msg[self.EMsgKey.msg_type] is self.EMsgType.error:
                j = self.jsonize_error(msg[self.EErrParam.error]) 
                for client in self.clients:
                    self.send_error(client.ws, j)
            else:
                Logger.log(Logger.ELogLevel.ERROR, "invalid message, msg_type = %s", msg[self.EMsgKey.msg_type])
            gevent.sleep(0.02)

    def on_message(self, recvmes):
        if recvmes is None:
            return
        recvmes = json.loads(recvmes)
        if recvmes[self.EMsgKey.msg_type.name] == self.EMsgType.status.name:
            self.send_status(self.ws)
        elif recvmes[self.EMsgKey.msg_type.name] == self.EMsgType.jog.name:
            msg = { 
                self.EMsgKey.msg_type: self.EMsgType.jog,
                self.EJogParam.target_type: self.ETarType.__members__[recvmes[self.EJogParam.target_type.name]],
                self.EJogParam.direction: self.EJogDir.__members__[recvmes[self.EJogParam.direction.name]],
                self.EJogParam.volume: self.EJogVol.__members__[recvmes[self.EJogParam.volume.name]],
                self.EJogParam.interpolate_type: self.EIntpType.__members__[recvmes[self.EJogParam.interpolate_type.name]]
                }
            if msg[self.EJogParam.target_type] is self.ETarType.pose: 
                msg[self.EJogParam.target] = self.EPoseComp.__members__[recvmes[self.EJogParam.target.name]]
            else:
                msg[self.EJogParam.target] = self.EJointComp.__members__[recvmes[self.EJogParam.target.name]]
            self.queue.put(msg)
        elif recvmes[self.EMsgKey.msg_type.name] == self.EMsgType.move.name:
            msg = { 
                self.EMsgKey.msg_type: self.EMsgType.move,
                self.EMoveParam.target_type: self.ETarType.__members__[recvmes[self.EMoveParam.target_type.name]],
                self.EMoveParam.interpolate_type: self.EIntpType.__members__[recvmes[self.EMoveParam.interpolate_type.name]]
                }
            target = None
            from controller import Pose, Joint
            if msg[self.EMoveParam.target_type] is self.ETarType.pose: 
                target = Pose()
            else:
                target = Joint()
            for i in range(6):
                target.data[i] = recvmes[self.EJogParam.target.name][i]
            msg[self.EMoveParam.target] = target
            self.queue.put(msg)
        elif recvmes[self.EMsgKey.msg_type.name] == self.EMsgType.speed.name:
            speed_rate = float(recvmes[self.ESpeedParam.target.name])
            self.controller.status[self.controller.EStatKey.speed_rate] = speed_rate 
            Logger.log(Logger.ELogLevel.INFO_, "speed_rate changed, target = %f", speed_rate)
        elif recvmes[self.EMsgKey.msg_type.name] == self.EMsgType.area_check.name:
            target = True
            if recvmes[self.EAreaChkParam.target.name] == self.EAreaChkType.off.name:
                target = False
            self.controller.status[self.controller.EStatKey.area_check] = target
            Logger.log(Logger.ELogLevel.INFO_, "area_check changed, target = %s", target)
        else:
            Logger.log(Logger.ELogLevel.ERROR, "invalid message, msg = %s", recvmes)

    @classmethod 
    def jsonize_status(cls):
        map = {
            cls.controller.EStatKey.speed_rate.name: cls.controller.status[cls.controller.EStatKey.speed_rate],
            cls.controller.EStatKey.pose.name: cls.controller.status[cls.controller.EStatKey.pose].data,
            cls.controller.EStatKey.joint.name: cls.controller.status[cls.controller.EStatKey.joint].data,
            cls.controller.EStatKey.busy.name: cls.controller.status[cls.controller.EStatKey.busy]}
        joints = []
        for i in range(len(cls.controller.status[cls.controller.EStatKey.joint_pose])):
            joints.append(cls.controller.status[cls.controller.EStatKey.joint_pose][i].data)
        map[cls.controller.EStatKey.joint_pose.name] = joints
        links = []
        for i in range(len(cls.controller.status[cls.controller.EStatKey.link_pose])):
            links.append(cls.controller.status[cls.controller.EStatKey.link_pose][i].data)
        map[cls.controller.EStatKey.link_pose.name] = links

        j = json.dumps({
            cls.EMsgKey.msg_type.name: cls.EMsgType.status.name,
            cls.EMsgType.status.name: map})
        return j
    
    @classmethod
    def jsonize_error(cls, error):
        j = json.dumps({
            cls.EMsgKey.msg_type.name: cls.EMsgType.error.name,
            cls.EMsgType.error.name: error.name})
        return j

    @classmethod
    def send_error(cls, ws, jsonized_error):
        Logger.log(Logger.ELogLevel.TRACE, "send_error, error = %s", jsonized_error)
        try:
            ws.send(jsonized_error)
        except:
            Logger.log(Logger.ELogLevel.TRACE, "send error, client = %s", id(ws))

    @classmethod
    def send_status(cls, ws, jsonized_status = None):
        Logger.log(Logger.ELogLevel.TRACE, "send_status, start")
        j = jsonized_status 
        if j is None:
            j = cls.jsonize_status()
        try:
            ws.send(j)
        except:
            Logger.log(Logger.ELogLevel.INFO_, "send error, client = %s", id(ws))
        Logger.log(Logger.ELogLevel.TRACE, "send_status, end")

    def on_close(self, reason):
        self.remove_client(self)

    @classmethod
    def add_client(cls, client):
        msg = { 
            cls.EMsgKey.msg_type: cls.EMsgType.add_client,
            cls.EMsgKey.client: client}
        cls.queue.put(msg)

    @classmethod
    def remove_client(cls, client):
        msg = { 
            cls.EMsgKey.msg_type: cls.EMsgType.remove_client,
            cls.EMsgKey.client: client}
        cls.queue.put(msg)

    @classmethod
    def notify_status(cls):
        Logger.log(Logger.ELogLevel.TRACE, "notify_status, start")
        msg = { cls.EMsgKey.msg_type: cls.EMsgType.status }
        gevent.spawn(cls.put_message, msg)
        Logger.log(Logger.ELogLevel.TRACE, "notify_status, end")

    @classmethod
    def notify_error(cls, error):
        Logger.log(Logger.ELogLevel.TRACE, "notify_error, start")
        msg = { cls.EMsgKey.msg_type: cls.EMsgType.error,
                cls.EErrParam.error: error}
        gevent.spawn(cls.put_message, msg)
        Logger.log(Logger.ELogLevel.TRACE, "notify_error, end")

    @classmethod
    def put_message(cls, msg):
        cls.queue.put(msg)


