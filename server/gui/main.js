/////////////////////////////////////////////////////////
var URL_BASE = "../../";
var PASSWORD = undefined;
var EVENTS_PRESETS = undefined;
var SERVER_VERSION = 0;

/////////////////////////////////////////////////////////
function _login() {
    $("#filter-form-hook").empty();
    $("#main-hook").empty();
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
            error("Can't login: result {}".format(resultCode));
            _login();
        } else {
            PASSWORD = password;
            Cookies.set("password", password, {expires: 365});
            SERVER_VERSION = getFromDict(content, "version", "0");
            var clientVersion = Cookies.get("version");
            if (clientVersion === undefined) {clientVersion = SERVER_VERSION;}
            if (clientVersion !== SERVER_VERSION) {
                Cookies.remove("version");
                error("New version available, reloading...", function () {
                    location.reload();
                });
            } else {
                Cookies.set("version", SERVER_VERSION, {expires: 365});
            }
            $("#login-hook").empty();
            EVENTS_PRESETS = getFromDict(content, "eventsPresets", []);
            setupMenu();
        }
        $("#loading").stop().fadeOut();
    });
    p.fail(function (err) {
        error("Can't login: {}".format(err.stack));
        $("#loading").stop().fadeOut();
        _login();
    });
}

/////////////////////////////////////////////////////////
function setupMenu() {

    setInterval(function () {
        $(".menu .now").html(moment.unix(nowInSecs()).format("YYYY-MM-DD @ HH:mm:ss"));
    }, 1000);


    $(".menu .events").click(function (e) {
        e.preventDefault();
        $(".menu .item").removeClass("current");
        $(this).addClass("current");
        events(EVENTS_PRESETS);

    });
    $(".menu .heartbeats").click(function (e) {
        e.preventDefault();
        $(".menu .item").removeClass("current");
        $(this).addClass("current");
        heartbeats();
    });
    $(".menu .events").click();
}

/////////////////////////////////////////////////////////
function main() {
    PASSWORD = Cookies.get("password");
    if (PASSWORD === undefined) {_login();} else {_hello(PASSWORD);}
}

