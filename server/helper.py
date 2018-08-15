###################################################################################
import datetime
import os
import coloredlogs
import json
import logging.handlers
import logging
from threading import Thread, Event
import zlib
import binascii
import dateutil
import arrow
import csv
import uuid

###################################################################################
ROOT_FOLDER = os.path.dirname(os.path.realpath(__file__))
DATA_FOLDER = ROOT_FOLDER + "/data"
CONFIG_FOLDER = ROOT_FOLDER + "/config"
CONFIG_FILE = CONFIG_FOLDER + "/config.json"
CERTIFICATE_KEY_FILE = CONFIG_FOLDER + "/server.key"
CERTIFICATE_CRT_FILE = CONFIG_FOLDER + "/server.crt"
LOG_FORMAT = "%(asctime)-15s - %(levelname)-7s - %(message)s"
LOG_LOGGER = "main"
LOG_FOLDER = ROOT_FOLDER + "/log"
LOG_FILENAME = LOG_FOLDER + "/all.log"
AVAILABLE_ALERT_TYPES = {"pushover"}
SPLASH_FILE = ROOT_FOLDER + "/config/splash.txt"
###################################################################################
if os.path.exists(CONFIG_FILE): CONFIG = json.load(open(CONFIG_FILE))
else: CONFIG = {}
###################################################################################
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(coloredlogs.ColoredFormatter(fmt="%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger(LOG_LOGGER).addHandler(consoleHandler)
logging.getLogger(LOG_LOGGER).setLevel(logging.DEBUG)
if CONFIG.get("storeLog", False):
    if not os.path.exists(LOG_FOLDER): os.mkdir(LOG_FOLDER)
    fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10e6, backupCount=5)
    fileHandler.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger(LOG_LOGGER).addHandler(fileHandler)
if not os.path.exists(DATA_FOLDER): os.mkdir(DATA_FOLDER)


###################################################################################
def displaySplash():
    try: print(open(SPLASH_FILE, encoding="utf-8").read())
    except: pass


################################################################################
def uniqueID():
    return str(uuid.uuid4())

###################################################################################
def logInfo(*args):
    logging.getLogger(LOG_LOGGER).info(" - ".join(str(a) for a in args))


###################################################################################
def logWarning(*args):
    logging.getLogger(LOG_LOGGER).warning(" - ".join(str(a) for a in args))


###################################################################################
def logDebug(*args):
    if CONFIG.get("debug", False):
        logging.getLogger(LOG_LOGGER).debug(" - ".join(str(a) for a in args))


###################################################################################
def objectToString(object):
    return str(object.__dict__)


###################################################################################
def timestampToDatetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d %H:%M:%S')


###################################################################################
def timestampToTime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')


###################################################################################
def timestampToDay(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d')


###################################################################################
class AbortInterrupt(Exception):
    pass


###################################################################################
class InterruptibleThread(Thread):
    def __init__(self, stopEvent=None, abortEvent=None, **kwargs):
        Thread.__init__(self, **kwargs)
        if stopEvent is None: stopEvent = Event()
        self.stopEvent = stopEvent
        if abortEvent is None: abortEvent = Event()
        self.abortEvent = abortEvent

    def join(self, timeout=None):
        Thread.join(self, timeout)

    def sleep(self, time):
        self.abortEvent.wait(time)

    def abort(self):
        self.abortEvent.set()

    def shutdown(self):
        self.stopEvent.set()
        self.join()

    def abortBreakoutPoint(self):
        if self.checkAbortEvent(): raise AbortInterrupt("user requested abort")

    def checkAbortEvent(self):
        return self.abortEvent.isSet()

    def checkStopEvent(self):
        return self.stopEvent.isSet()


################################################################################
def removeLineBreaks(string):
    return string.replace('\n', ' ').replace('\r', ' ')


################################################################################
def writeToCSV(data, filePath, append=False, csvSep=";", csvSepSafe="---"):
    mode = "w" if not append else "a"
    csvFile = open(filePath, mode)
    for line in data:
        lineString = ""
        first = True
        for item in line:
            if not first:
                lineString += csvSep
            else:
                first = False
            lineString += removeLineBreaks(str(item).replace(csvSep, csvSepSafe))
        csvFile.write(lineString + "\n")
    csvFile.close()


################################################################################
def readCSV(filePath, csvSEP=";", hasHeaders=True, encoding="utf-8"):
    try:
        f = open(filePath, "r", encoding=encoding)
        reader = csv.reader(f, delimiter=csvSEP)
        rows = []
        firstRow = True
        for row in reader:
            if firstRow:
                firstRow = False
                if hasHeaders: continue
            rows.append(row)
        return rows
    except:
        return []


###################################################################################
def formatException(e):
    return str(e).replace("\n", "////")


################################################################################
def dictionnaryDeepGet(dic, *keys, default=None):
    for key in keys:
        if isinstance(dic, dict): dic = dic.get(key, default)
        else: return default
    return dic


################################################################################
def dictionnaryDeepSet(dic, value, *keys):
    for key in keys[:-1]: dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


################################################################################
def compressString(string, asString=False):
    compressed = zlib.compress(string.encode("utf8"))
    if asString: compressed = binascii.hexlify(compressed)
    return compressed


################################################################################
def decompressString(string, asString=False):
    if asString: string = binascii.unhexlify(string)
    return zlib.decompress(string).decode("utf8")


################################################################################
def getDateTimeFromTimestamp(timestamp, timezone):
    return datetime.datetime.fromtimestamp(timestamp, tz=dateutil.tz.gettz(timezone))


################################################################################
def parseDate(dateString, dateFormat, timezone):
    if not timezone: return arrow.get(dateString, dateFormat).timestamp
    else: return arrow.get(dateString, dateFormat).replace(tzinfo=dateutil.tz.gettz(timezone)).timestamp


################################################################################
def formatTimestamp(timestamp, dateFormat, timezone):
    if dateFormat == "iso": return arrow.get(timestamp).to(timezone).isoformat()
    return arrow.get(timestamp).to(timezone).format(dateFormat)


################################################################################
def getDaysList(dayFromTS, dayToTS, timezone):
    dayFrom = getDateTimeFromTimestamp(dayFromTS, timezone)
    dayTo = getDateTimeFromTimestamp(dayToTS, timezone)
    dateTimes, days, daysIndexes, naiveDateTimes = [], [], {}, []
    index = 0
    for currentDayArrow in arrow.Arrow.range("day", dayFrom, dayTo):
        currentDay = int(currentDayArrow.strftime('%Y%m%d'))
        days.append(currentDay)
        dateTimes.append(currentDayArrow.date())
        naiveDateTimes.append(currentDayArrow.naive)
        daysIndexes[currentDay] = index
        index += 1
    return days, daysIndexes, dateTimes, naiveDateTimes


################################################################################
def makePath(*args):
    args = [arg.rstrip("/") for arg in args]
    return '/'.join(str(x) for x in args)


################################################################################
def makeDir(path):
    if not os.path.isdir(path): os.makedirs(path)
    return path


################################################################################
def makeDirPath(*args):
    return makeDir(makePath(*args))

################################################################################
def now():
    return arrow.now().timestamp


################################################################################
def parseInt(intString, defaultValue):
    try:
        return int(intString)
    except ValueError:
        return defaultValue
