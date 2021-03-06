###################################################################################
# IMPORTS
###################################################################################
import time
from typing import Dict
from threading import Lock
import copy
import helper as h
import alert as a
import event as ev

###################################################################################
# GLOBALS
###################################################################################
heartBeats = {}  # type:Dict[heartBeat]
deadHeartBeats = {}  # type:Dict[heartBeat]
lock = Lock()
beatsFolder = h.makeDirPath("%s/beats" % h.DATA_FOLDER)


###################################################################################
###################################################################################
###################################################################################
class heartBeat:

    ###################################################################################
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
###################################################################################
###################################################################################
class Manager(h.InterruptibleThread):

    ###################################################################################
    def __init__(self, alertsDispatcher: a.Dispatcher, eventsPersister: ev.Persister):
        super().__init__()
        self.daemon = True
        self.alertsDispatcher = alertsDispatcher
        self.eventsPersister = eventsPersister

    ###################################################################################
    def _heartBeatStore(self, hb: heartBeat, action):
        if not h.dictionnaryDeepGet(h.CONFIG, "storeDatas", default=False): return
        csvFile = ""
        try:
            csvFile = "%s/%s.csv" % (beatsFolder, h.timestampToDay(hb.last))
            h.writeToCSV([[hb.service, hb.nextIn, h.timestampToDay(hb.last), h.timestampToTime(hb.last), hb.expected, h.timestampToTime(hb.expected), action]], csvFile, append=True)
            h.logDebug("Writing data file", hb.service, csvFile)
        except Exception as e:
            h.logWarning("Can't store", hb.service, csvFile, h.formatException(e))

    ###################################################################################
    def _heartBeatAlert(self, hb: heartBeat, alertType="not pulsing"):
        try:
            h.logDebug("Alerting heartbeat", hb.service, hb.alertType, hb.alertTarget, alertType)
            alertTitle, alertBody = "Alert", "Alert"
            if alertType == "not pulsing":
                alertTitle = "Service %s has not pulsed" % hb.service
                alertBody = "The service %s is not pulsing since %s" % (hb.service, h.timestampToDatetime(hb.last))
            if alertType == "pulsing again":
                alertTitle = "Service %s is pulsing again" % hb.service
                alertBody = "The service %s is pulsing again" % hb.service

            self.eventsPersister.store(ev.Event(h.now(), 0, "%s - %s" % (alertTitle, alertBody), hb.service))
            self.alertsDispatcher.add(a.Alert(alertTitle, alertBody, hb.alertTarget, hb.alertType))

        except Exception as e:
            h.logWarning("Can't alert", hb.service, hb.alertType, hb.alertTarget, h.formatException(e))

    ###################################################################################
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
                        self._heartBeatAlert(hb, "not pulsing")
                        self._heartBeatStore(hb, "alert")
                lock.release()
                self.sleep(h.dictionnaryDeepGet(h.CONFIG, "heartbeatLoopSleep", default=5))
            except Exception as e:
                h.logWarning("Error checking heartBeats", h.formatException(e))
                if lock.locked(): lock.release()
        h.logWarning("HeartBeat cworker exit")

    ###################################################################################
    def heartBeatList(self):
        lock.acquire()
        hbsCopy = {k: copy.copy(heartBeats[k]) for k in heartBeats}
        lock.release()
        return hbsCopy

    ###################################################################################
    def heartBeatCancel(self, service):
        if service in heartBeats:
            lock.acquire()
            heartBeatToCancel = heartBeats[service]
            heartBeatToCancel.cancelled = True
            lock.release()
            self._heartBeatStore(heartBeatToCancel, "cancel")
            h.logInfo("Service cancelled", heartBeatToCancel.service)
            return heartBeatToCancel
        else: return None

    ###################################################################################
    def heartBeatPulse(self, service, alertType, alertTarget, nextIn):
        now = int(time.time())
        expected = now + nextIn
        heartBeatToAdd = heartBeat(service, alertType, alertTarget, nextIn, now, expected)
        lock.acquire()
        heartBeats[service] = heartBeatToAdd
        if service in deadHeartBeats:
            self._heartBeatAlert(heartBeatToAdd, "pulsing again")
            h.logInfo("Service is pulsing again", heartBeatToAdd.service, h.objectToString(heartBeatToAdd))
            deadHeartBeats.pop(service)
        lock.release()
        self._heartBeatStore(heartBeatToAdd, "pulse")
        h.logInfo("Service pulsed", heartBeatToAdd.service, h.objectToString(heartBeatToAdd))
        return heartBeatToAdd
