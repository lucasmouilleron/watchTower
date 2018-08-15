###################################################################################
# IMPORTS
###################################################################################
import time
from pushover import Client
from typing import Dict
from threading import Lock
import copy
import helper as h

###################################################################################
# GLOBALS
###################################################################################
heartBeats = {}  # type:Dict[heartBeat]
deadHeartBeats = {}  # type:Dict[heartBeat]
lock = Lock()
beatsFolder = h.makeDirPath("%s/beats" % h.DATA_FOLDER)


###################################################################################
# FUNCTIONS
###################################################################################


###################################################################################
class heartBeat:
    def __init__(self, service, alertType, alertTarget, heartbeat, last, expected):
        self.service = service
        self.alertType = alertType
        self.alertTarget = alertTarget
        self.nextIn = heartbeat
        self.last = last
        self.expected = expected
        self.alerted = False
        self.cancelled = False


###################################################################################
class heartBeatThread(h.InterruptibleThread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        while not self.checkAbortEvent():
            try:
                now = int(time.time())
                lock.acquire()
                for key in heartBeats:
                    hb = heartBeats[key]
                    if hb.expected < now and not hb.alerted and not hb.cancelled:
                        hb.alerted = True
                        h.logInfo("Service has not pulsed as expected", key, h.objectToString(hb))
                        deadHeartBeats[key] = hb
                        heartBeatAlert(hb, "not pulsing")
                        heartBeatStore(hb, "alert")
                lock.release()
                self.sleep(h.dictionnaryDeepGet(h.CONFIG, "heartbeatLoopSleep", default=5))
            except Exception as e:
                h.logWarning("Error checking heartBeats", h.formatException(e))
                if lock.locked(): lock.release()
        h.logWarning("HeartBeat cworker exit")


###################################################################################
def heartBeatStore(hb: heartBeat, action):
    if not h.dictionnaryDeepGet(h.CONFIG, "storeDatas", default=False): return
    csvFile = ""
    try:
        csvFile = "%s/%s.csv" % (beatsFolder, h.timestampToDay(hb.last))
        h.writeToCSV([[hb.service, hb.nextIn, h.timestampToDay(hb.last), h.timestampToTime(hb.last), hb.expected, h.timestampToTime(hb.expected), action]], csvFile, append=True)
        h.logDebug("Writing data file", hb.service, csvFile)
    except Exception as e:
        h.logWarning("Can't store", hb.service, csvFile, h.formatException(e))


###################################################################################
def heartBeatAlert(hb:heartBeat, alertType="not pulsing"):
    if not h.dictionnaryDeepGet(h.CONFIG, "alert", "activated", default=False): return
    try:
        h.logDebug("Alerting", hb.service, hb.alertType, hb.alertTarget, alertType)
        alertTitle, alertBody = "Alert", "Alert"
        if alertType == "not pulsing":
            alertTitle = "Service %s has not pulsed" % hb.service
            alertBody = "The service %s is not pulsing since %s" % (hb.service, h.timestampToDatetime(hb.last))
        if alertType == "pulsing again":
            alertTitle = "Service %s is pulsing again" % hb.service
            alertBody = "The service %s is pulsing again" % hb.service
        if hb.alertType == "pushover":
            Client(hb.alertTarget, api_token=h.dictionnaryDeepGet(h.CONFIG, "alert", "pushoverAPIKey", default="")).send_message(alertBody, title=alertTitle)
        else: raise Exception("Alert type unknown", hb.service, hb.alertType)
    except Exception as e:
        h.logWarning("Can't alert", hb.service, hb.alertType, hb.alertTarget, h.formatException(e))


###################################################################################
def heartBeatList():
    lock.acquire()
    hbsCopy = copy.copy(heartBeats)
    lock.release()
    return hbsCopy


###################################################################################
def heartBeatCancel(service):
    if service in heartBeats:
        lock.acquire()
        heartBeatToCancel = heartBeats[service]
        heartBeatToCancel.cancelled = True
        lock.release()
        heartBeatStore(heartBeatToCancel, "cancel")
        h.logInfo("Service cancelled", heartBeatToCancel.service)
        return heartBeatToCancel
    else: return None


###################################################################################
def heartBeatPulse(service, alertType, alertTarget, nextIn):
    now = int(time.time())
    expected = now + nextIn
    heartBeatToAdd = heartBeat(service, alertType, alertTarget, nextIn, now, expected)
    lock.acquire()
    heartBeats[service] = heartBeatToAdd
    if service in deadHeartBeats:
        heartBeatAlert(heartBeatToAdd, "pulsing again")
        h.logInfo("Service is pulsing again", heartBeatToAdd.service, h.objectToString(heartBeatToAdd))
        deadHeartBeats.pop(service)
    lock.release()
    heartBeatStore(heartBeatToAdd, "pulse")
    h.logInfo("Service pulsed", heartBeatToAdd.service, h.objectToString(heartBeatToAdd))
    return heartBeatToAdd


###################################################################################
def heartBeatTestPassword(headers):
    if h.dictionnaryDeepGet(h.CONFIG, "server", "password", default="") != headers.get("password"):
        h.logDebug("Non authentified request")
        return False
    else: return True
