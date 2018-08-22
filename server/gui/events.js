////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// CONFIG
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// var URL_BASE = "https://watchtower.turing-capital.com:4443";
var URL_BASE = "../../";
var PASSWORD = undefined;
var EVENTS_PRESETS = [];
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
    if (key in dict) {return dict[key];}
    else {return defaultValue;}
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
    if (timeString == "last day") {return 24 * 60 * 60;}
    if (timeString == "last 2 days") {return 2 * 24 * 60 * 60;}
    if (timeString == "last week") {return 7 * 24 * 60 * 60;}
    if (timeString == "last hour") {return 1 * 60 * 60;}
    else {return 0;}
}

/////////////////////////////////////////////////////////
function getDateClass(dateSeconds) {
    var now = nowInSecs();
    if (now - dateSeconds < 30 * 60) {return "very-recent";}
    else if (now - dateSeconds < 2 * 60 * 60) {return "recent";}
    else {return "old";}
}

/////////////////////////////////////////////////////////
function _error(message, afterCallback) {
    var callbacks = {};
    if (afterCallback != undefined) {callbacks["afterClose"] = afterCallback;}
    new Noty({"text": message, "timeout": 3000, "type": "error", "theme": "sunset", "layout": "bottomCenter", "callbacks": callbacks}).show();
}

/////////////////////////////////////////////////////////
function _success(message, afterCallback) {
    var callbacks = {};
    if (afterCallback != undefined) {callbacks["afterClose"] = afterCallback;}
    new Noty({"text": message, "timeout": 1000, "type": "success", "theme": "sunset", "layout": "bottomCenter", "callbacks": callbacks}).show();
}

/////////////////////////////////////////////////////////
function _login() {
    $("#filter-form-hook").empty();
    $("#events-hook").empty();
    $("#login-hook").html(renderTemplate("tpl-login", {}));
    $("#login").click(function (e) {
        e.preventDefault();
        _hello($("#password").val());
    })
}

/////////////////////////////////////////////////////////
function _hello(password) {
    $("#loading").show();
    var p = getJSONPromised("{}/hello".format(URL_BASE), password, {});
    p.done(function (content) {
        var resultCode = getFromDict(content, "result", 0);
        if (resultCode !== 200) {
            _error("Can't login: result {}".format(resultCode));
            _login();
        }
        else {
            PASSWORD = password;
            Cookies.set("password", password, {expires: 365});
            SERVER_VERSION = getFromDict(content, "version", 0);
            var clientVersion = Cookies.get("version");
            if (clientVersion === undefined) {clientVersion = SERVER_VERSION;}
            if (clientVersion != SERVER_VERSION) {
                Cookies.remove("version");
                _error("New version available, reloading...", function () {
                    location.reload();
                });
            }
            else {
                Cookies.set("version", SERVER_VERSION, {expires: 365});
            }
            EVENTS_PRESETS = getFromDict(content, "eventsPresets", []);
            _events();
        }
        $("#loading").stop().fadeOut();
    });
    p.fail(function (err) {
        _error("Can't login: {}".format(err.stack));
        $("#loading").stop().fadeOut();
        _login();
    });
}

/////////////////////////////////////////////////////////
function _events() {

    $("#login-hook").empty();

    $("#filter-form-hook").html(renderTemplate("tpl-filter", {"eventsPresets": EVENTS_PRESETS}));
    $("#filter-preset").change(function () {
        var preset = {};
        var presetName = $("#filter-preset").val();
        for (var i = 0; i < EVENTS_PRESETS.length; i++) {
            if (EVENTS_PRESETS[i].name === presetName) {
                preset = EVENTS_PRESETS[i];
                break;
            }
        }
        $("#filter-service").val(getFromDict(preset, "service", ""));
        $("#filter-message").val(getFromDict(preset, "message", ""));
        $("#update-events").click();
    });

    $(".event .message").readmore("destroy");
    PullToRefresh.destroyAll();
    PullToRefresh.init({
        mainElement: "#content",
        onRefresh: function () {
            $("#update-events").click();
        }
    });

    $("#filter-since").change(function () {
        $("#update-events").click();
    });

    $("#update-events").click(function (e) {
        $("#loading").show();
        $("#update-events").val("...");
        e.preventDefault();
        var params = {};
        var service = $("#filter-service").val();
        if (service !== undefined) {params["service"] = service;}
        var message = $("#filter-message").val();
        if (message !== undefined) {params["message"] = message;}
        params["to"] = nowInSecs();
        params["from"] = nowInSecs() - getTimeOffsetInSecsFromString($("#filter-since").val());
        var p = getJSONPromised("{}/events".format(URL_BASE), PASSWORD, params);
        p.done(function (content) {
            try {
                var resultCode = getFromDict(content, "result", 0);
                if (resultCode !== 200) {throw "Request error {}".format(resultCode);}
                var events = getFromDict(content, "events", []);
                for (var i = 0; i < events.length; i++) {
                    events[i].dateClass = getDateClass(events[i].date);
                    events[i].date = moment.unix(events[i].date).format("YYYY-MM-DD @ HH:mm:ss");
                    events[i].color = intToRGB(hashCode(events[i].service.toUpperCase()));
                    events[i].service = capitalizeString(events[i].service);
                }
                $("#events-hook").html(renderTemplate("tpl-events", {"events": events, "hasEvents": events.length > 0}));
                $(".events .event").each(function () {
                    $(this).find(".service").css({"background-color": "#{}".format($(this).data("color"))});
                });
                $(".event .message").readmore();
                _success("{} events loaded".format(events.length));
            }
            catch (e) {_error("Can't load events: {}".format(e));}
            finally {
                $("#loading").stop().fadeOut();
                $("#update-events").val("Update");
            }
        });
        p.fail(function (err) {
            _error("Can't load events: {}".format(err.stack));
            $("#loading").stop().fadeOut();
            $("#update-events").val("Update");
        });
    });

    $("#update-events").click();
}

/////////////////////////////////////////////////////////
function _main() {
    PASSWORD = Cookies.get("password");
    if (PASSWORD === undefined) {_login();}
    else {_hello(PASSWORD);}
}
