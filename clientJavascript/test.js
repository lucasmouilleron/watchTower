var client = require("./client");
var host = "https://localhost";
var port = 4443;
var password = "test";

client.init(host, port, password);
client.pulse("testJS", "pushover", "pushoverID", 60);
client.listHeartbeats().then(function (data) {
    console.log(data);
});
// client.cancel("testJS");