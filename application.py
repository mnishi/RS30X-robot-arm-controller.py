import copy
import json
import gevent
from gevent.queue import Queue, Empty
from geventwebsocket import WebSocketApplication, WebSocketError
import enum 
from RS30X.RS30X import *

class RS30XControllerWebSocketApplication(WebSocketApplication):
    EMsgKey = enum.Enum("EMsgKey", "msg_type client")
    EMsgType = enum.Enum("EMsgType", "add_client remove_client status jog")
    EJogParam = enum.Enum("EJogParam", "target_type target direction volume")
    EJogDir = enum.Enum("EJogDir", "dec inc")
    EJogVol = enum.Enum("EJogVol", "small medium large")
    EJogTarType = enum.Enum("EJogTarType", "pose joint")
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
            self.controller.set_notifier(self.notify_status)
            gevent.spawn(self.__handle_message)
            self.initialized = True

        self.add_client(self)
        self.send_status(self.ws)

    @classmethod
    def __jog(cls, msg):
      target = None
      if msg[cls.EJogParam.target_type] is cls.EJogTarType.pose:
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
      cls.controller.move_ptp(target)

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
            elif msg[self.EMsgKey.msg_type] is self.EMsgType.status:
                j = self.jsonize_status() 
                for client in self.clients:
                    self.send_status(client.ws, j)
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
                self.EJogParam.target_type: self.EJogTarType.__members__[recvmes[self.EJogParam.target_type.name]],
                self.EJogParam.direction: self.EJogDir.__members__[recvmes[self.EJogParam.direction.name]],
                self.EJogParam.volume: self.EJogVol.__members__[recvmes[self.EJogParam.volume.name]]
                }
            if msg[self.EJogParam.target_type] is self.EJogTarType.pose: 
                msg[self.EJogParam.target] = self.EPoseComp.__members__[recvmes[self.EJogParam.target.name]]
            else:
                msg[self.EJogParam.target] = self.EJointComp.__members__[recvmes[self.EJogParam.target.name]]
            self.queue.put(msg)
        else:
            Logger.log(Logger.ELogLevel.ERROR, "invalid message, msg = %s", recvmes)

    @classmethod 
    def jsonize_status(cls):
        map = {
            cls.controller.EStatKey.pose.name: cls.controller.status[cls.controller.EStatKey.pose].data,
            cls.controller.EStatKey.joint.name: cls.controller.status[cls.controller.EStatKey.joint].data}
        j = json.dumps({
            cls.EMsgKey.msg_type.name: cls.EMsgType.status.name,
            cls.EMsgType.status.name: map})
        return j

    @classmethod
    def send_status(cls, ws, jsonized_status = None):
        j = jsonized_status 
        if j is None:
            j = cls.jsonize_status()
        try:
            ws.send(j)
        except:
            Logger.log(Logger.ELogLevel.INFO_, "send error, client = %s", id(ws))

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
        msg = { cls.EMsgKey.msg_type: cls.EMsgType.status }
        cls.queue.put(msg)

