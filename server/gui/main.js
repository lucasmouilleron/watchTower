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
            // var eventsPresets = getFromDict(content, "eventsPresets", []);
            // events(eventsPresets);
            // TODO UNCOMMENT
            heartbeats();
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
function main() {
    PASSWORD = Cookies.get("password");
    if (PASSWORD === undefined) {_login();} else {_hello(PASSWORD);}
}

