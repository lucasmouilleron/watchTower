###################################################################################
# IMPORTS
###################################################################################
import signal
import json
import heartbeat as hb
import event as e
import alert as a
import ping as p
import helper as h
from threading import Thread
from gevent.wsgi import WSGIServer
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS

###################################################################################
# CONFIG
###################################################################################
SERVER_TIMEZONE = "Europe/Paris"


###################################################################################
# FUNCTIONS
###################################################################################

###################################################################################
###################################################################################
###################################################################################
class Server(Thread):

    ###################################################################################
    def __init__(self, port, ssl=False, certificateKeyFile=None, certificateCrtFile=None, fullchainCrtFile=""):
        Thread.__init__(self)
        self.app = Flask(__name__)
        self.port = port
        self.ssl = ssl
        self.certificateKeyFile = certificateKeyFile
        self.certificateCrtFile = certificateCrtFile
        self.fullchainCrtFile = fullchainCrtFile
        self.httpServer = None

        self._addRoute("/hello", self._routeHello, ["GET"])
        self._addRoute("/heartbeats", self._routeHeartbeatList, ["GET"])
        self._addRoute("/heartbeat/<service>", self._routeHeartbeatGet, ["GET"])
        self._addRoute("/heartbeat", self._routeheartbeatPulse, ["POST"])
        self._addRoute("/heartbeat", self._routeHeartbeatCancel, ["DELETE"])
        self._addRoute("/event", self._routeEventAdd, ["POST"])
        self._addRoute("/events", self._routeEventList, ["GET"])
        self._addRouteRaw("/", self._routeIndex, ["GET"])
        self._addRouteRaw("/gui", self._routeGUIEventsIndex, ["GET"])
        self._addRouteRaw("/gui/events", self._routeGUIEventsIndex, ["GET"])
        self._addRouteRaw("/gui/<path:path>", self._routeGUI, ["GET"])

        # legacy routes
        self._addRoute("/add-event", self._routeEventAdd, ["POST"])

        self._addRoute("/get/<service>", self._routeHeartbeatGet, ["GET"])
        self._addRoute("/", self._routeheartbeatPulse, ["POST"])
        self._addRoute("/", self._routeHeartbeatCancel, ["DELETE"])

    ###################################################################################
    def run(self):
        CORS(self.app)
        if self.ssl: self.httpServer = WSGIServer(("0.0.0.0", self.port), self.app, log=None, keyfile=self.certificateKeyFile, certfile=self.certificateCrtFile, ca_certs=self.fullchainCrtFile)
        else: self.httpServer = WSGIServer(("0.0.0.0", self.port), self.app, log=None)
        self.httpServer.serve_forever()

    ###################################################################################
    def stop(self):
        self.httpServer.stop()

    ###################################################################################
    def _testPassword(self, headers):
        if h.dictionnaryDeepGet(h.CONFIG, "server", "password", default="") != headers.get("password"):
            h.logDebug("Non authentified request")
            return False
        else: return True

    ###################################################################################
    def _addRoute(self, rule, callback, methods=["GET"], endpoint=None):
        def callbackReal(*args, **kwargs):
            try: return jsonify(callback(*args, **kwargs))
            except Exception as e:
                h.logWarning("Error processing request", request.data.decode("utf-8"), request.endpoint, h.formatException(e))
                if hb.lock.locked(): hb.lock.release()
                return jsonify({"result": 500, "hint": h.formatException(e)})

        if endpoint is None: endpoint = h.uniqueID()
        self.app.add_url_rule(rule, endpoint, callbackReal, methods=methods)

    ###################################################################################
    def _addRouteRaw(self, rule, callback, methods, endpoint=None):
        if endpoint is None: endpoint = h.uniqueID()
        self.app.add_url_rule(rule, endpoint, callback, methods=methods)

    ###################################################################################
    def _routeIndex(self):
        return redirect("/gui")

    ###################################################################################
    def _routeGUI(self, path):
        return send_from_directory("gui", path)

    ###################################################################################
    def _routeGUIEventsIndex(self):
        return send_from_directory("gui", "events.html")

    ###################################################################################
    def _routeHello(self):
        if not self._testPassword(request.headers): return {"result": 403}
        return {"result": 200, "world": h.now(), "eventsPresets": h.dictionnaryDeepGet(h.CONFIG, "eventsPresets", default=[]), "version": h.dictionnaryDeepGet(h.CONFIG, "version", default=0)}

    ###################################################################################
    def _routeHeartbeatList(self):
        if not self._testPassword(request.headers): return {"result": 403}
        return {"result": 200, "heartBeats": [v.__dict__ for v in heartbeatsManager.heartBeatList().values()]}

    ###################################################################################
    def _routeHeartbeatGet(self, service):
        if not self._testPassword(request.headers): return {"result": 403}
        hbs = heartbeatsManager.heartBeatList()
        if service in hbs: return {"result": 200, "heartBeat": hbs[service].__dict__}
        else: return {"result": 500, "hint": "service not found"}

    ###################################################################################
    def _routeheartbeatPulse(self):
        if not self._testPassword(request.headers): return {"result": 403}
        datas = json.loads(request.data.decode("utf-8"))
        if not "service" in datas: return {"result": 500, "hint": "no service provided"}
        if not "nextIn" in datas: return {"result": 500, "hint": "no nextIn provided"}
        if not "alertTarget" in datas: return {"result": 500, "hint": "no alert target provided"}
        if not "alertType" in datas: return {"result": 500, "hint": "no alert type provided"}
        heartBeatToAdd = heartbeatsManager.heartBeatPulse(datas["service"], datas["alertType"], datas["alertTarget"], int(datas["nextIn"]))
        return {"result": 200, "action": "pulse", "heartBeat": heartBeatToAdd.__dict__}

    ###################################################################################
    def _routeHeartbeatCancel(self):
        if not self._testPassword(request.headers): return {"result": 403}
        datas = json.loads(request.data.decode("utf-8"))
        if not "service" in datas: return {"result": 500, "hint": "no service provided"}
        heartBeatToCancel = heartbeatsManager.heartBeatCancel(datas["service"])
        if heartBeatToCancel: return {"result": 200, "action": "cancel", "heartBeat": heartBeatToCancel.__dict__}
        else: return {"result": 200, "action": "cancel", "heartBeat": datas["service"]}

    ###################################################################################
    def _routeEventAdd(self):
        if not self._testPassword(request.headers): return {"result": 403}
        datas = json.loads(request.data.decode("utf-8"))
        if not "service" in datas: return {"result": 500, "hint": "no service provided"}
        if not "message" in datas: return {"result": 500, "hint": "no message provided"}
        event = e.Event(h.now(), datas.get("level", 0), datas["message"], datas["service"])
        eventsPersister.store(event)
        if datas.get("alert", False): alertsDispatcher.add(event.convertToAlert(h.dictionnaryDeepGet(h.CONFIG, "alert", "defaultTarget"), h.dictionnaryDeepGet(h.CONFIG, "alert", "defaultType")))
        return {"result": 200}

    ###################################################################################
    def _routeEventList(self):
        if not self._testPassword(request.headers): return {"result": 403}
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

alertsDispatcher = a.Dispatcher(h.dictionnaryDeepGet(h.CONFIG, "alert", "activated", default=False))
alertsDispatcher.start()
h.logInfo("Alerts dispatcher started")

eventsPersister = e.Persister(h.makePath(h.DATA_FOLDER, "events"), alertsDispatcher)
h.logInfo("Events persister started")

pinger = p.Pinger(alertsDispatcher, eventsPersister)
for pr in h.CONFIG.get("pings", []):
    if not "service" in pr or not "url" in pr or not "alertType" in pr or not "alertTarget" in pr: continue
    pinger.add(p.Ping(pr["service"], pr["url"], pr.get("frequency", 30), pr["alertType"], pr["alertTarget"]))
pinger.start()
h.logInfo("Pinger started")

heartbeatsManager = hb.Manager(alertsDispatcher, eventsPersister)
heartbeatsManager.start()
h.logInfo("Heartbeats manager started")

server = Server(h.dictionnaryDeepGet(h.CONFIG, "server", "port", default=5000), h.dictionnaryDeepGet(h.CONFIG, "server", "ssl", default=False), h.CERTIFICATE_KEY_FILE, h.CERTIFICATE_CRT_FILE, h.FULLCHAIN_CRT_FILE)
server.start()
h.logInfo("Server started", server.port, server.ssl)

signal.pause()
server.stop()
heartbeatsManager.abort()
alertsDispatcher.abort()
pinger.abort()
