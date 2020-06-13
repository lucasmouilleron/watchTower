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
            var cancelled = heartbeats[i].cancelled;
            var ok = nowInSecs() < heartbeats[i].last + heartbeats[i].nextIn;
            if (cancelled) {var dateClass = "cancelled";} else {var dateClass = ok ? "on-time" : "late";}
            var last = heartbeats[i].last;
            var lastDate = moment.unix(last).format("YYYY-MM-DD @ HH:mm:ss");
            var service = heartbeats[i].service;
            var params = "frequency: {}".format(heartbeats[i].nextIn);
            var status = 0;
            if (!ok) {status = 3;} else if (cancelled) { status = 1;} else if (ok) { status = 2;}
            items.push({type: "heartbeat", status: status, color: color, ok: ok, dateClass: dateClass, lastDate: lastDate, service: service, params: params, last: last});
        }

        for (var i = 0; i < pings.length; i++) {
            var color = intToRGB(hashCode(pings[i].service.toUpperCase()));
            var ok = nowInSecs() < (pings[i].lastPingSuccess + 2 * pings[i].frequency);
            var dateClass = ok ? "on-time" : "late";
            var last = pings[i].lastPingSuccess;
            var lastDate = moment.unix(last).format("YYYY-MM-DD @ HH:mm:ss");
            var service = pings[i].service;
            var params = {"frequency": pings[i].frequency, "url": pings[i].url};
            if (pings[i].proxyURL !== null) params["proxyURL"] = pings[i].proxyURL;
            if (!ok) {status = 3;} else if (ok) { status = 2;}
            var paramss = [];
            for (var k in params) paramss.push(["{}: {}".format(k, params[k])]);
            paramss = paramss.join(" - ");
            items.push({type: "ping", color: color, status: status, ok: ok, dateClass: dateClass, lastDate: lastDate, service: service, params: paramss, last: last});
        }
        items.sort(function (a, b) {
            if (a.status === b.status) return a.lastDate - b.lastDate;
            return a.status - b.status;
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