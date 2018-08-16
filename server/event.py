###################################################################################
# IMPORTS
###################################################################################
import helper as h
import alert as a
from typing import List
import os
from threading import Lock
import re

###################################################################################
# CONFIG
###################################################################################
PERSITER_TIMEZONE = "Europe/Paris"

###################################################################################
# GLOBALS
###################################################################################
lock = Lock()


###################################################################################
###################################################################################
###################################################################################
class Event:

    ###################################################################################
    def __init__(self, date, level, message, service, alert=False):
        self.date = date
        self.level = level
        self.message = message
        self.service = service
        self.alert = alert

    ###################################################################################
    def convertToAlert(self, target, alertType):
        return a.Alert(self.service, self.message, target, alertType)


###################################################################################
###################################################################################
###################################################################################
class Persister:

    ###################################################################################
    def __init__(self, folder, alertsDispatcher: a.Dispatcher, timezone=PERSITER_TIMEZONE):
        self.folder = h.makeDirPath(folder)
        self.timezone = timezone
        self.alertsDispatcher = alertsDispatcher

    ###################################################################################
    def _getFiles(self, fromDate, toDate, service) -> List[str]:
        return [h.makePath(self.folder, "%s.csv" % day) for day in h.getDaysList(fromDate, toDate, self.timezone)[0]]

    ###################################################################################
    def _getEventFile(self, event: Event):
        return h.makePath(self.folder, "%s.csv" % h.formatTimestamp(event.date, "YYYYMMDD", self.timezone))

    ###################################################################################
    def _filterEvents(self, events: List[Event], fromDate, toDate, level=None, service=None, message=None) -> List[Event]:
        finalEvents = []
        if message is not None: message = re.compile(message, re.I)
        if service is not None: service = re.compile(service, re.I)
        if level is not None: level = h.parseInt(level, None)
        for e in events:
            if e.date < fromDate: continue
            if e.date > toDate: continue
            if level is not None and e.level < level: continue
            if service is not None and not service.search(e.service): continue
            if message is not None and not message.search(e.message): continue
            finalEvents.append(e)
        return finalEvents

    ###################################################################################
    def store(self, event: Event):
        try:
            lock.acquire()
            eventFile = self._getEventFile(event)
            h.writeToCSV([[h.formatTimestamp(event.date, "YYYYMMDD", self.timezone), h.formatTimestamp(event.date, "HH:mm:ss", self.timezone), event.level, event.message, event.service]], eventFile, append=os.path.exists(eventFile))
        finally:
            lock.release()

    ###################################################################################
    def load(self, fromDate, toDate, level=None, service=None, message=None) -> List[Event]:
        files = self._getFiles(fromDate, toDate, service)
        events = []
        for f in files:
            try:
                lock.acquire()
                for d in h.readCSV(f, hasHeaders=False):
                    try:
                        edate = h.parseDate("%s %s" % (d[0], d[1]), "YYYYMMDD HH:mm:ss", self.timezone)
                        elevel, emessage, eservice = h.parseInt(d[2], 0), d[3], d[4]
                        events.append(Event(edate, elevel, emessage, eservice))
                    except: pass
            finally: lock.release()
        return self._filterEvents(events, fromDate, toDate, level, service, message)[::-1]
