/////////////////////////////////////////////////////////
function events(eventsPresets) {

    $("#login-hook").empty();

    $("#filter-form-hook").html(renderTemplate("tpl-filter", {"eventsPresets": eventsPresets}));
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
                $("#main-hook").html(renderTemplate("tpl-events", {"events": events, "hasEvents": events.length > 0}));
                $(".events .event").each(function () {
                    $(this).find(".service").css({"background-color": "#{}".format($(this).data("color"))});
                });
                $(".event .message").readmore();
                success("{} events loaded".format(events.length));
            } catch (e) {error("Can't load events: {}".format(e));} finally {
                $("#loading").stop().fadeOut();
                $("#update-events").val("Update");
            }
        });
        p.fail(function (err) {
            error("Can't load events: {}".format(err.stack));
            $("#loading").stop().fadeOut();
            $("#update-events").val("Update");
        });
    });

    $("#update-events").click();
}
