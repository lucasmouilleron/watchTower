################################################################################
################################################################################
################################################################################
import requests
import threading
import time
import urllib3
from urllib3.exceptions import InsecureRequestWarning

###################################################################################
urllib3.disable_warnings(InsecureRequestWarning)


###################################################################################
###################################################################################
###################################################################################
class client:

    ###################################################################################
    def __init__(self, url, port, password):
        self.url = url
        self.port = port
        self.password = password
        self.timeout = 10

    ###################################################################################
    def _processResult(self, result):
        if result.status_code != 200: raise Exception("Status KO", result.content)
        content = result.json()
        if content.get("result", 0) != 200: raise Exception("Result KO", result.content)
        return content

    ###################################################################################
    def pulse(self, service, alertType, alertTarget, nextIn):
        try: self._processResult(requests.post("%s:%s/heartbeat" % (self.url, self.port), json={"service": service, "alertType": alertType, "alertTarget": alertTarget, "nextIn": nextIn}, headers={"password": self.password}, verify=False, timeout=self.timeout))
        except Exception as e: raise Exception("Can't pulse service", str(e))

    ###################################################################################
    def cancel(self, service):
        try: self._processResult(requests.delete("%s:%s/heartbeat" % (self.url, self.port), json={"service": service}, headers={"password": self.password}, verify=False, timeout=self.timeout))
        except Exception as e: raise Exception("Can't pulse service", str(e))

    ###################################################################################
    def add(self, service, message, level=0, inThread=False, throwsException=False):
        def doSend():
            self._processResult(requests.post("%s:%s/event" % (self.url, self.port), json={"service": service, "level": level, "message": message}, headers={"password": self.password}, verify=False, timeout=self.timeout))

        try:
            if inThread: threading.Thread(target=doSend, args=[]).start()
            else: doSend()
        except Exception as e:
            if throwsException: raise Exception("Can't send event", str(e))
            else: print(("Can't send event", str(e)))

    ###################################################################################
    def heartbeats(self):
        try:
            content = self._processResult(requests.get("%s:%s/heartbeats" % (self.url, self.port), headers={"password": self.password}, verify=False, timeout=self.timeout))
            return content.get("heartBeats", [])
        except Exception as e: raise Exception("Can't list heartbeats", str(e))

    ###################################################################################
    def events(self, dayFrom=None, dayTo=None, service=None, level=None, message=None):
        try:
            params = {}
            if service is not None: params["service"] = service
            if level is not None: params["level"] = level
            if message is not None: params["message"] = message
            if dayFrom is not None: params["from"] = dayFrom
            if dayTo is not None: params["to"] = dayTo
            content = self._processResult(requests.get("%s:%s/events" % (self.url, self.port), params=params, headers={"password": self.password}, verify=False, timeout=self.timeout))
            return content.get("events", [])
        except Exception as e: raise Exception("Can't list events", str(e))


################################################################################
################################################################################
################################################################################
class HearbeatManager(threading.Thread):

    ################################################################################
    def __init__(self, service, url, port, password, alertType, alertTarget, freqInSeconds):
        threading.Thread.__init__(self)
        self._interrupt = False
        self._exitEvent = threading.Event()
        self.freqInSeconds = freqInSeconds
        self.alertType = alertType
        self.alertTarget = alertTarget
        self.client = client(url, port, password)
        self.service = service
        self.lastSent = 0

    ################################################################################
    def run(self):
        print("Hearbeat manager started")
        while not self._interrupt and not self._exitEvent.isSet():
            try:
                now = int(time.time())
                if self.lastSent < now - self.freqInSeconds / 2:
                    self.client.pulse(self.service, self.alertType, self.alertTarget, self.freqInSeconds)
                    self.lastSent = now
            except: print("Can't HB pulse service", self.service)
            finally: self._exitEvent.wait(5)

        print("Hearbeat manager stoped")
        self.client.cancel(self.service)

    ################################################################################
    def interrupt(self):
        self.client.cancel(self.service)
        self._interrupt = True
        self._exitEvent.set()
