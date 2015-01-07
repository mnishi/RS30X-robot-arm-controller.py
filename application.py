import copy
import json
import gevent
from gevent.queue import Queue, Empty
from geventwebsocket import WebSocketApplication, WebSocketError
import enum 
from RS30X.RS30X import *

class RS30XControllerWebSocketApp(WebSocketApplication):
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
        if RS30XControllerWebSocketApp.initialized is not True:
            RS30XControllerWebSocketApp.controller.set_notifier(RS30XControllerWebSocketApp.notify_status)
            gevent.spawn(self.__handle_message)
            RS30XControllerWebSocketApp.initialized = True

        RS30XControllerWebSocketApp.add_client(self)
        RS30XControllerWebSocketApp.send_status(self.ws)

    def __jog(self, msg):
      target = None
      if msg[RS30XControllerWebSocketApp.EJogParam.target_type] is RS30XControllerWebSocketApp.EJogTarType.pose:
          target = copy.deepcopy(RS30XControllerWebSocketApp.controller.status[RS30XControllerWebSocketApp.controller.EStatKey.pose]) 
      else:
          target = copy.deepcopy(RS30XControllerWebSocketApp.controller.status[RS30XControllerWebSocketApp.controller.EStatKey.joint]) 
      index = msg[RS30XControllerWebSocketApp.EJogParam.target].value - 1
      volume = 10.0
      if msg[RS30XControllerWebSocketApp.EJogParam.volume] is RS30XControllerWebSocketApp.EJogVol.medium:
          volume = 1.0
      elif msg[RS30XControllerWebSocketApp.EJogParam.volume] is RS30XControllerWebSocketApp.EJogVol.small:
          volume = 0.1
      if msg[RS30XControllerWebSocketApp.EJogParam.direction] is RS30XControllerWebSocketApp.EJogDir.dec:
          volume = -volume
      target.data[index] = target.data[index] + volume
      RS30XControllerWebSocketApp.controller.move_ptp(target)

    def __handle_message(self):
        msg = None
        while True:
            msg = self.queue.get()
            if msg is None:
                pass
            elif msg[RS30XControllerWebSocketApp.EMsgKey.msg_type] is RS30XControllerWebSocketApp.EMsgType.add_client:
                self.clients.add(msg[RS30XControllerWebSocketApp.EMsgKey.client])
            elif msg[RS30XControllerWebSocketApp.EMsgKey.msg_type] is RS30XControllerWebSocketApp.EMsgType.remove_client:
                self.clients.discard(msg[RS30XControllerWebSocketApp.EMsgKey.client])
            elif msg[RS30XControllerWebSocketApp.EMsgKey.msg_type] is RS30XControllerWebSocketApp.EMsgType.jog:
                self.__jog(msg)
            elif msg[RS30XControllerWebSocketApp.EMsgKey.msg_type] is RS30XControllerWebSocketApp.EMsgType.status:
                j = RS30XControllerWebSocketApp.jsonize_status() 
                for client in self.clients:
                    RS30XControllerWebSocketApp.send_status(client.ws, j)
            else:
                Logger.log(Logger.ELogLevel.ERROR, "invalid message, msg_type = %s", msg[RS30XControllerWebSocketApp.EMsgKey.msg_type])
            gevent.sleep(0.02)

    def on_message(self, recvmes):
        if recvmes is None:
            return
        recvmes = json.loads(recvmes)
        if recvmes[RS30XControllerWebSocketApp.EMsgKey.msg_type.name] == RS30XControllerWebSocketApp.EMsgType.status.name:
            RS30XControllerWebSocketApp.send_status(self.ws)
        elif recvmes[RS30XControllerWebSocketApp.EMsgKey.msg_type.name] == RS30XControllerWebSocketApp.EMsgType.jog.name:
            msg = { 
                RS30XControllerWebSocketApp.EMsgKey.msg_type: RS30XControllerWebSocketApp.EMsgType.jog,
                RS30XControllerWebSocketApp.EJogParam.target_type: RS30XControllerWebSocketApp.EJogTarType.__members__[recvmes[RS30XControllerWebSocketApp.EJogParam.target_type.name]],
                RS30XControllerWebSocketApp.EJogParam.direction: RS30XControllerWebSocketApp.EJogDir.__members__[recvmes[RS30XControllerWebSocketApp.EJogParam.direction.name]],
                RS30XControllerWebSocketApp.EJogParam.volume: RS30XControllerWebSocketApp.EJogVol.medium,
                }
            if msg[RS30XControllerWebSocketApp.EJogParam.target_type] is RS30XControllerWebSocketApp.EJogTarType.pose: 
                msg[RS30XControllerWebSocketApp.EJogParam.target] = RS30XControllerWebSocketApp.EPoseComp.__members__[recvmes[RS30XControllerWebSocketApp.EJogParam.target.name]]
            else:
                msg[RS30XControllerWebSocketApp.EJogParam.target] = RS30XControllerWebSocketApp.EJointComp.__members__[recvmes[RS30XControllerWebSocketApp.EJogParam.target.name]]
            RS30XControllerWebSocketApp.queue.put(msg)
        else:
            Logger.log(Logger.ELogLevel.ERROR, "invalid message, msg = %s", recvmes)

    @classmethod 
    def jsonize_status(cls):
        map = {
            RS30XControllerWebSocketApp.controller.EStatKey.pose.name: RS30XControllerWebSocketApp.controller.status[RS30XControllerWebSocketApp.controller.EStatKey.pose].data,
            RS30XControllerWebSocketApp.controller.EStatKey.joint.name: RS30XControllerWebSocketApp.controller.status[RS30XControllerWebSocketApp.controller.EStatKey.joint].data}
        j = json.dumps({
            RS30XControllerWebSocketApp.EMsgKey.msg_type.name: RS30XControllerWebSocketApp.EMsgType.status.name,
            RS30XControllerWebSocketApp.EMsgType.status.name: map})
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
        RS30XControllerWebSocketApp.remove_client(self)

    @classmethod
    def add_client(cls, client):
        msg = { 
            RS30XControllerWebSocketApp.EMsgKey.msg_type: RS30XControllerWebSocketApp.EMsgType.add_client,
            RS30XControllerWebSocketApp.EMsgKey.client: client}
        cls.queue.put(msg)

    @classmethod
    def remove_client(cls, client):
        msg = { 
            RS30XControllerWebSocketApp.EMsgKey.msg_type: RS30XControllerWebSocketApp.EMsgType.remove_client,
            RS30XControllerWebSocketApp.EMsgKey.client: client}
        cls.queue.put(msg)

    @classmethod
    def notify_status(cls):
        msg = { RS30XControllerWebSocketApp.EMsgKey.msg_type: RS30XControllerWebSocketApp.EMsgType.status }
        cls.queue.put(msg)

