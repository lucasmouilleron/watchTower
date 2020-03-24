/////////////////////////////////////////////////////////
function heartbeats() {
    $("#main-hook").empty();

    PullToRefresh.destroyAll();
    PullToRefresh.init({
        mainElement: "#content",
        distThreshold: 80,
        distMax: 100,
        distReload: 100,
        onRefresh: function () {
            updateHeartbeats();
        }
    });

    updateHeartbeats();
}


/////////////////////////////////////////////////////////
function updateHeartbeats() {
    $("#loading").show();
    var phbs = getJSONPromised("{}/heartbeats".format(URL_BASE), PASSWORD, {});
    var pps = getJSONPromised("{}/pings".format(URL_BASE), PASSWORD, {});
    var p = $.when(phbs, pps);
    p.done(function (heartbeats, pings) {
        var now = moment.unix(nowInSecs()).format("YYYY-MM-DD @ HH:mm:ss");
        var items = [];
        heartbeats = heartbeats["heartBeats"];
        pings = pings["pings"];

        for (var i = 0; i < heartbeats.length; i++) {
            var color = intToRGB(hashCode(heartbeats[i].service.toUpperCase()));
            var ok = nowInSecs() < heartbeats[i].last + heartbeats[i].nextIn;
            var dateClass = ok ? "on-time" : "late";
            var last = heartbeats[i].last;
            var lastDate = moment.unix(last).format("YYYY-MM-DD @ HH:mm:ss");
            var service = heartbeats[i].service;
            var params = "frequency: {}".format(heartbeats[i].nextIn);
            items.push({type: "heartbeat", color: color, ok: ok, dateClass: dateClass, lastDate: lastDate, service: service, params: params, last: last});
        }

        for (var i = 0; i < pings.length; i++) {
            var color = intToRGB(hashCode(pings[i].service.toUpperCase()));
            var ok = nowInSecs() < (pings[i].lastPingSuccess + 2 * pings[i].frequency);
            var dateClass = ok ? "on-time" : "late";
            var last = pings[i].lastPingSuccess;
            var lastDate = moment.unix(last).format("YYYY-MM-DD @ HH:mm:ss");
            var service = pings[i].service;
            var params = "frequency: {} - url: {}".format(pings[i].frequency, pings[i].url);
            items.push({type: "ping", color: color, ok: ok, dateClass: dateClass, lastDate: lastDate, service: service, params: params, last: last});
        }
        items.sort(function (a, b) {
            if (a.ok === b.ok) return a.lastDate - b.lastDate;
            return a.ok - b.ok;
        });
        success("{} items loaded".format(items.length));
        $("#main-hook").html(renderTemplate("tpl-heartbeats", {"items": items, "now": now}));
        $(".heartbeats .item").each(function () {
            $(this).find(".service").css({"background-color": "#{}".format($(this).data("color"))});
        });
    });
    p.fail(function (err) {
        error("Can't load heartbeats and/or pings: {}".format(err.statusText));
    });
    p.always(function () {
        $("#loading").stop().fadeOut();
    });
}