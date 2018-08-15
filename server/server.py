###################################################################################
# IMPORTS
###################################################################################
import signal
import json
import heartbeat as hb
import event as e
import helper as h
from threading import Thread, Event
from gevent.wsgi import WSGIServer
from flask import Flask, request, logging, jsonify, send_from_directory
from flask_cors import CORS

###################################################################################
# CONFIG
###################################################################################
SERVER_TIMEZONE = "Europe/Paris"


###################################################################################
# FUNCTIONS
###################################################################################
class ServerThread(Thread):
    def __init__(self, port, ssl=False, certificateKeyFile=None, certificateCrtFile=None):
        Thread.__init__(self)
        self.app = Flask(__name__)
        self.port = port
        self.ssl = ssl
        self.certificateKeyFile = certificateKeyFile
        self.certificateCrtFile = certificateCrtFile
        self.httpServer = None

        self.addRoute("/hello", self.routeHello, ["GET"])
        self.addRoute("/heartbeats", self.routeHeartbeatList, ["GET"])
        self.addRoute("/heartbeat/<service>", self.routeHeartbeatGet, ["GET"])
        self.addRoute("/heartbeat", self.routeheartbeatPulse, ["POST"])
        self.addRoute("/heartbeat", self.routeHeartbeatCancel, ["DELETE"])
        self.addRoute("/event", self.routeEventAdd, ["POST"])
        self.addRoute("/events", self.routeEventList, ["GET"])
        self.addRouteRaw("/gui", self.routeGUIEventsIndex, ["GET"])
        self.addRouteRaw("/gui/events", self.routeGUIEventsIndex, ["GET"])
        self.addRouteRaw("/gui/<path:path>", self.routeGUI, ["GET"])

        # legacy routes
        self.addRoute("/add-event", self.routeEventAdd, ["POST"])
        self.addRoute("/", self.routeHeartbeatList, ["GET"])
        self.addRoute("/get/<service>", self.routeHeartbeatGet, ["GET"])
        self.addRoute("/", self.routeheartbeatPulse, ["POST"])
        self.addRoute("/", self.routeHeartbeatCancel, ["DELETE"])

    def run(self):
        # logging.getLogger('werkzeug').setLevel(logging.ERROR)
        # if self.ssl is not None: sslContext = (self.certificateCrtFile, self.certificateKeyFile)
        # else: sslContext = None
        # self.app.run(host="0.0.0.0", port=self.port, ssl_context=sslContext)
        CORS(self.app)
        if self.ssl: self.httpServer = WSGIServer(('0.0.0.0', self.port), server.app, log=None, keyfile=self.certificateKeyFile, certfile=self.certificateCrtFile)
        else: self.httpServer = WSGIServer(('0.0.0.0', self.port), server.app, log=None)
        self.httpServer.serve_forever()

    def stop(self):
        self.httpServer.stop()

    def addRoute(self, rule, callback, methods=["GET"], endpoint=None):
        def callbackReal(*args, **kwargs):
            try: return jsonify(callback(*args, **kwargs))
            except Exception as e:
                h.logWarning("Error processing request", request.data.decode("utf-8"), request.endpoint, h.formatException(e))
                if hb.lock.locked(): hb.lock.release()
                return jsonify({"result": 500, "hint": h.formatException(e)})

        if endpoint is None: endpoint = h.uniqueID()
        self.app.add_url_rule(rule, endpoint, callbackReal, methods=methods)

    def addRouteRaw(self, rule, callback, methods, endpoint=None):
        if endpoint is None: endpoint = h.uniqueID()
        self.app.add_url_rule(rule, endpoint, callback, methods=methods)

    def routeGUI(self, path):
        return send_from_directory("gui", path)

    def routeGUIEventsIndex(self):
        return send_from_directory("gui", "events.html")

    def routeHello(self):
        if not hb.heartBeatTestPassword(request.headers): return {"result": 403}
        return {"result": 200, "world": h.now(), "eventsPresets": h.dictionnaryDeepGet(h.CONFIG, "eventsPresets", default=[])}

    def routeHeartbeatList(self):
        if not hb.heartBeatTestPassword(request.headers): return {"result": 403}
        return {"result": 200, "heartBeats": [v.__dict__ for v in hb.heartBeatList().values()]}

    def routeHeartbeatGet(self, service):
        if not hb.heartBeatTestPassword(request.headers): return {"result": 403}
        hbs = hb.heartBeatList()
        if service in hbs: return {"result": 200, "heartBeat": hbs[service].__dict__}
        else: return {"result": 500, "hint": "service not found"}

    def routeheartbeatPulse(self):
        if not hb.heartBeatTestPassword(request.headers): return {"result": 403}
        datas = json.loads(request.data.decode("utf-8"))
        if not "service" in datas: return {"result": 500, "hint": "no service provided"}
        if not "nextIn" in datas: return {"result": 500, "hint": "no nextIn provided"}
        if not "alertTarget" in datas: return {"result": 500, "hint": "no alert target provided"}
        if not "alertType" in datas: return {"result": 500, "hint": "no alert type provided"}
        heartBeatToAdd = hb.heartBeatPulse(datas["service"], datas["alertType"], datas["alertTarget"], int(datas["nextIn"]))
        return {"result": 200, "action": "pulse", "heartBeat": heartBeatToAdd.__dict__}

    def routeHeartbeatCancel(self):
        if not hb.heartBeatTestPassword(request.headers): return {"result": 403}
        datas = json.loads(request.data.decode("utf-8"))
        if not "service" in datas: return {"result": 500, "hint": "no service provided"}
        heartBeatToCancel = hb.heartBeatCancel(datas["service"])
        if heartBeatToCancel: return {"result": 200, "action": "cancel", "heartBeat": heartBeatToCancel.__dict__}
        else: return {"result": 200, "action": "cancel", "heartBeat": datas["service"]}

    def routeEventAdd(self):
        if not hb.heartBeatTestPassword(request.headers): return {"result": 403}
        datas = json.loads(request.data.decode("utf-8"))
        if not "service" in datas: return {"result": 500, "hint": "no service provided"}
        if not "message" in datas: return {"result": 500, "hint": "no message provided"}
        eventsPersister.store(e.Event(h.now(), datas.get("level", 0), datas["message"], datas["service"]))
        return {"result": 200}

    def routeEventList(self):
        if not hb.heartBeatTestPassword(request.headers): return {"result": 403}
        defaultFrom, defaultTo = h.now() - 24 * 60 * 60, h.now()
        humanDates = request.args.get("humanDates", "0") == "1"
        events = eventsPersister.load(h.parseInt(request.args.get("from", default=defaultFrom), defaultFrom), h.parseInt(request.args.get("to", default=defaultTo), defaultTo), request.args.get("level"), request.args.get("service"), request.args.get("message"))
        finalEvents = []
        for e in events:
            if humanDates: e.date = h.formatTimestamp(e.date, "YYYY-MM-DD HH:mm:ss", SERVER_TIMEZONE)
            finalEvents.append(e.__dict__)
        return {"result": 200, "events": finalEvents}


###################################################################################
# MAIN
###################################################################################
h.displaySplash()

eventsPersister = e.EventPersister(h.makePath(h.DATA_FOLDER, "events"))
h.logInfo("Events persister started")

heartbeatsThread = hb.heartBeatThread()
heartbeatsThread.start()
h.logInfo("Heartbeats started")

server = ServerThread(h.dictionnaryDeepGet(h.CONFIG, "server", "port", default=5000), h.dictionnaryDeepGet(h.CONFIG, "server", "ssl", default=False), h.CERTIFICATE_KEY_FILE, h.CERTIFICATE_CRT_FILE)
server.start()
h.logInfo("Server started", server.port, server.ssl)

signal.pause()
server.stop()
heartbeatsThread.abort()
