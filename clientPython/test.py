###################################################################################
import client as hbClient

###################################################################################
URL = "https://localhost"
PORT = 4443
PASSWORD = "change me"
ALERT_TYPE = "pushover"
ALERT_TARGET = "pushoverTargetID"
###################################################################################
client = hbClient.client(URL, PORT, PASSWORD)
client.pulse("testPython", ALERT_TYPE, ALERT_TARGET, 60)
client.cancel("testPython")
client.list()

client.sendEvent("test4", "my message", 4, inThread=False)
client.listEvent()
