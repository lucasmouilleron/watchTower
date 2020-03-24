/////////////////////////////////////////////////////////
function events(eventsPresets) {
    $("#main-hook").empty();

    $("#main-hook").html(renderTemplate("tpl-events", {}));
    $("#events-filter-form-hook").html(renderTemplate("tpl-events-filter", {"eventsPresets": eventsPresets}));
    $("#filter-preset").change(function () {
        var preset = {};
        var presetName = $("#filter-preset").val();
        for (var i = 0; i < eventsPresets.length; i++) {
            if (eventsPresets[i].name === presetName) {
                preset = eventsPresets[i];
                break;
            }
        }
        $("#filter-service").val(getFromDict(preset, "service", ""));
        $("#filter-message").val(getFromDict(preset, "message", ""));
        updateEvents();
    });

    $(".event .message").readmore("destroy");
    PullToRefresh.destroyAll();
    PullToRefresh.init({
        mainElement: "#body",
        onRefresh: function () {
            updateEvents();
        }
    });

    $("#filter-since").change(function () {
        updateEvents();
    });

    $("#update-events").click(function (e) {
        e.preventDefault();
        updateEvents();
    });

    updateEvents();
}

/////////////////////////////////////////////////////////
function updateEvents() {
    $("#loading").show();
    $("#update-events").val("...");
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
            $("#events-list-hook").html(renderTemplate("tpl-events-list", {"events": events, "hasEvents": events.length > 0}));
            $(".events .event").each(function () {
                $(this).find(".service").css({"background-color": "#{}".format($(this).data("color"))});
            });
            $(".event .message").readmore();
            success("{} events loaded".format(events.length));
        } catch (e) {
            error("Can't load events: {}".format(e));
        }
    });
    p.fail(function (err) {
        error("Can't load events: {}".format(err.stack));
    });
    p.always(function () {
        $("#loading").stop().fadeOut();
        $("#update-events").val("Update");
    });
}