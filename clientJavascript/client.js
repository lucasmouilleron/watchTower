var request = require("request");
var requestPromise = require("request-promise");
var https = require("https");

var client = {

    ////////////////////////////////////////////////////////////////////////////////
    host: "",
    port: 443,
    password: "",
    agent: {},
    // var agentOptions = {host: host, port: port, path: '/', rejectUnauthorized: false};
    // var agent = new https.Agent(agentOptions);

    ////////////////////////////////////////////////////////////////////////////////
    init: function (host, port, password) {
        this.host = host;
        this.port = port;
        this.password = password;
    },

    ////////////////////////////////////////////////////////////////////////////////
    listHeartbeats: function () {
        var headers = {password: this.password};
        return requestPromise.get({url: this.host + ":" + this.port+"/heartbeats", agent: this.agent, headers: headers});
    },

    ////////////////////////////////////////////////////////////////////////////////
    pulse: function (service, alertType, alertTarget, nextIn) {
        var headers = {password: this.password};
        var datas = {"service": service, "alertType": alertType, "alertTarget": alertTarget, "nextIn": nextIn};
        return requestPromise.post({url: this.host + ":" + this.port+"/heartbeat", agent: this.agent, headers: headers, form: datas, json: true});
    },

    ////////////////////////////////////////////////////////////////////////////////
    cancel: function (service) {
        var headers = {password: this.password};
        var datas = {"service": service};
        return requestPromise.del({url: this.host + ":" + this.port+"/heartbeat", agent: this.agent, headers: headers, form: datas, json: true});
    }
};

module.exports = client;