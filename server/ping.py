###################################################################################
# IMPORTS
###################################################################################
import helper as h
from typing import List
import time
import requests


###################################################################################
###################################################################################
###################################################################################
class Ping:
    def __init__(self, url, frequency, method="get", login=None, password=None, timeout=3, expectedCode=200):
        self.url = url
        self.frequency = frequency
        self.method = "get"
        self.loging = login
        self.password = password
        self.timeout = timeout
        self.expectedCode = expectedCode


###################################################################################
###################################################################################
###################################################################################
class Pinger(h.InterruptibleThread):

    ###################################################################################
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.pings = []  # type: List[Ping]

    ###################################################################################
    def run(self):
        while not self.checkAbortEvent():
            try:
                print("pinging")
                for p in self.pings:
                    try:
                        r = requests.request(p.method, p.url, headers={}, verify=False, timeout=p.timeout)
                        if p.expectedCode != r.status_code:
                            # todo alert
                            pass
                    except:
                        # todo alert
                        pass
                time.sleep(5)
            except:
                pass
        h.logWarning("Pinger worker exit")

    ###################################################################################
    def add(self, p: Ping):
        self.pings.append(p)
