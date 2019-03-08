###################################################################################
# IMPORTS
###################################################################################
import helper as h
import alert as a
import event as e
from typing import List
import time
import requests
from threading import Thread


###################################################################################
###################################################################################
###################################################################################
class Ping:
    def __init__(self, service, url, frequency, alertType, alertTarget, method="get", login=None, password=None, timeout=10, expectedCode=200, proxyURL=None):
        self.service = service
        self.url = url
        self.frequency = frequency
        self.alertType = alertType
        self.alertTarget = alertTarget
        self.method = method
        self.login = login
        self.password = password
        self.timeout = timeout
        self.expectedCode = expectedCode
        self.proxyURL = proxyURL

        if self.timeout > self.frequency:
            self.timeout = self.frequency / 2
            h.logWarning("Timeout is > than frequency, set timeout to frequency / 2")

        self.lastPing = 0
        self.lastPingSuccess = h.now()
        self.alerted = False


###################################################################################
###################################################################################
###################################################################################
class Pinger(h.InterruptibleThread):

    ###################################################################################
    def __init__(self, dispatcher: a.Dispatcher, eventsPersister: e.Persister):
        super().__init__()
        self.daemon = True
        self.dispatcher = dispatcher
        self.eventsPersister = eventsPersister
        self.pings = []  # type: List[Ping]
        self.threads = []

    ###################################################################################
    def run(self):
        while not self.checkAbortEvent():
            try:
                for p in self.pings:
                    if p.lastPing + p.frequency < h.now():
                        h.logDebug("Trigger ping", p.service)
                        p.lastPing = h.now()
                        t = Thread(target=self.ping, args=[p])
                        t.start()
                        self.threads.append(t)
                time.sleep(5)
                self.threads = [t for t in self.threads if t.isAlive()]
            except: print(h.getLastExceptionAndTrace())
        h.logWarning("Pinger worker exit")

    ###################################################################################
    def ping(self, p: Ping):
        try:
            p.lastPing = h.now()
            proxies = {}
            if p.proxyURL is not None: proxies["http"], proxies["http"] = p.proxyURL, p.proxyURL
            r = requests.request(p.method, p.url, headers={}, verify=False, timeout=p.timeout, proxies=proxies)
            result = p.expectedCode == r.status_code
        except:
            result = False
        if not result:
            if not p.alerted:
                p.alerted = True
                alertTitle, alertBody = "Service %s has not ponged" % p.service, "The service %s has not ponged since %s" % (p.service, h.timestampToDatetime(p.lastPingSuccess))
                self.eventsPersister.store(e.Event(h.now(), 0, "%s - %s" % (alertTitle, alertBody), p.service))
                self.dispatcher.add(a.Alert(alertTitle, alertBody, p.alertTarget, p.alertType))
            else: h.logDebug("Service is still not ponging", p.service)
        else:
            h.logDebug("Service pinged", p.service)
            p.lastPingSuccess = h.now()
            p.alerted = False

    ###################################################################################
    def add(self, p: Ping):
        self.pings.append(p)
        h.logDebug("Ping added", p.__dict__)
