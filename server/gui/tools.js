////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// CONFIG
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// var URL_BASE = "https://watchtower.turing-capital.com:4443";
var URL_BASE = "../../";
var PASSWORD = undefined;
var SERVER_VERSION = 0;

/////////////////////////////////////////////////////////
String.prototype.format = function () {
    var i = 0, args = arguments;
    return this.replace(/{}/g, function () {
        return typeof args[i] != 'undefined' ? args[i++] : '';
    });
};

/////////////////////////////////////////////////////////
function capitalizeString(str) {
    return str.replace(/\w\S*/g, function (txt) {
        // return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        return txt.charAt(0).toUpperCase() + txt.substr(1);
    });
}

/////////////////////////////////////////////////////////
function nowInSecs() {
    return Math.floor(new Date().getTime() / 1000);
}

/////////////////////////////////////////////////////////
function getJSONPromised(url, password, params) {
    var dfd = $.Deferred();
    $.ajax({url: url, dataType: "json", data: params, timeout: 7000, headers: {"password": password}}).done(function (data) {
        dfd.resolve(data);
    }).fail(function (data) {
        dfd.reject(data);
    });
    return dfd;
}

/////////////////////////////////////////////////////////
function renderTemplate(tplID, datas) {
    var template = $("#{}".format(tplID)).html();
    Mustache.parse(template);
    return Mustache.render(template, datas);
}

/////////////////////////////////////////////////////////
function getFromDict(dict, key, defaultValue) {
    if (key in dict) {return dict[key];} else {return defaultValue;}
}

/////////////////////////////////////////////////////////
function hashCode(str) {
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return hash;
}

/////////////////////////////////////////////////////////
function intToRGB(i) {
    var c = (i & 0x00FFFFFF).toString(16).toUpperCase();
    return "00000".substring(0, 6 - c.length) + c;
}

/////////////////////////////////////////////////////////
function getTimeOffsetInSecsFromString(timeString) {
    timeString = timeString.toLowerCase();
    if (timeString === "last day") {return 24 * 60 * 60;}
    if (timeString === "last 2 days") {return 2 * 24 * 60 * 60;}
    if (timeString === "last week") {return 7 * 24 * 60 * 60;}
    if (timeString === "last hour") {return 1 * 60 * 60;} else {return 0;}
}

/////////////////////////////////////////////////////////
function getDateClass(dateSeconds) {
    var now = nowInSecs();
    if (now - dateSeconds < 30 * 60) {return "very-recent";} else if (now - dateSeconds < 2 * 60 * 60) {return "recent";} else {return "old";}
}

/////////////////////////////////////////////////////////
function error(message, afterCallback) {
    var callbacks = {};
    if (afterCallback !== undefined) {callbacks["afterClose"] = afterCallback;}
    new Noty({"text": message, "timeout": 3000, "type": "error", "theme": "sunset", "layout": "bottomCenter", "callbacks": callbacks}).show();
}

/////////////////////////////////////////////////////////
function success(message, afterCallback) {
    var callbacks = {};
    if (afterCallback !== undefined) {callbacks["afterClose"] = afterCallback;}
    new Noty({"text": message, "timeout": 1000, "type": "success", "theme": "sunset", "layout": "bottomCenter", "callbacks": callbacks}).show();
}