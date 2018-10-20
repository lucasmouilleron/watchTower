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
client.heartbeats()

client.add("test4", "my m\"es\nsage", 4, inThread=False)
client.events()
