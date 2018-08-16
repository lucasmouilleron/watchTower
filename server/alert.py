###################################################################################
# IMPORTS
###################################################################################
import helper as h
from pushover import Client
import queue
import time


###################################################################################
###################################################################################
###################################################################################
class Alert:
    def __init__(self, title, message, target, alertType):
        self.message = message
        self.title = title
        self.type = alertType
        self.target = target


###################################################################################
###################################################################################
###################################################################################
class Dispatcher(h.InterruptibleThread):

    ###################################################################################
    def __init__(self, alertsActivated=True):
        super().__init__()
        self.daemon = True
        self.queue = queue.Queue()
        self.alertsActivated = alertsActivated

    ###################################################################################
    def run(self):
        if not self.alertsActivated: return
        while not self.checkAbortEvent():
            try:
                while not self.queue.empty():
                    a = self.queue.get(0)
                    h.logDebug("Alerting", a.title, a.message, a.target, a.type)
                    if a.type == "pushover": pushoverAlert(a)
                    else: raise Exception("Alert type unknown", a.type)
            finally: time.sleep(2)
        h.logWarning("Alert dispatcher worker exit")

    ###################################################################################
    def add(self, a: Alert):
        self.queue.put(a, block=False)


###################################################################################
def pushoverAlert(a: Alert):
    try: Client(a.target, api_token=h.dictionnaryDeepGet(h.CONFIG, "alert", "pushoverAPIKey", default="")).send_message(a.message, title=a.title)
    except Exception as e: h.logWarning("Can't alert via pushover", a.title, a.message, a.target, h.formatException(e))
