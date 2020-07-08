watchTower
==========

![Screenshot](http://grabs.lucasmouilleron.com/Screen%20Shot%202018-08-13%20at%2009.32.57.png)

A simple watchtower service.
Heartbeat monitoring + event agregator.

Hearbeat definitions
--------------------
- The `server` is in charge of monitoring `services`
- When a `service` is considered dead, the `server` then `alerts` its owner
- A `service` is a pulsing agent
- A `pulse` is a sign of aliveness
- When a `service` pulse the `server`, it tells him when he will `pulse` again in the worst case
- If the `service` has not `pulsed` again in time, the `server` considers the `service` dead and `alerts` its owner
- When a `service` is no longer required, it must inform the `server` to avoid a false dead `alerts`
- An `alert` can be a mail, a pushover message, etc.

Event definitions
-----------------
- The `server` is in charge or recieving `events`
- When a `service` sends an `event`, the server stores it
- On demand, `events` can be retrieved for consultation
- An event is: `service` + `message` + `level` + `date of registration`

Implementation
--------------
- HTTP client / server architecture
- All queries protected by password set in HTTP headers under "password"
- Heartbeat protocol: 
    - Pulse: 
        - `POST /`
        - `{"service":"SERVICE_NAME","alertType":"ALERT_TYPE","alertTarget":"TARGET_NAME","nextIn":EXPECTED_NEXT_HEARTBEAT_IN_SECS}`
    - Cancel: 
        - `DELETE /`
        - `{"service":"SERVICE_NAME"}`
    - List: 
        - `GET /`
- Event protocol: 
    - Add:
        - `POST /add-event`
        - `{"service":"SERVICE_NAME", "level":"level", "message":"the message"}`
    - List: 
        - `GET /list-events`
        - optional params: `service` (is), `from` (above), `to` (below), `level` (above), `message` (contains)

Server
------
- `./server`
- python3
- Dependencies: `pip install -r requirements.txt`
- Config: 
    - `config/config.json`: main config (`cp config/sample.json config/config.json`)
    - `config/server.crt`, `config/server.key`: SSL certificate, used only if SSL activated
- Datas: `data`
- Deploy:
    - Optionnaly define pyenv-virtualenv: `pyenv virtualenv -f 3.6.8 watchTower` 
    - Install dependencies: `pip install --upgrade pip ; pip install -r requirements.txt`
    - Setup config
    - Generate ssl certificates (optional)
    - Hook in with upstart (optional, `./server/config/sample.upstart.conf`, http://upstart.ubuntu.com/getting-started.html)
- Run: `python server.py`
- Docker: 
    - `./docker`
    - Config: place server config files in `./docker/config` 
    - Interactive: `cd docker && tools/dockerBuild && tools/dockerRun`
    - Detached: `cd docker && tools/dockerBuild && tools/dockerRunDetached`

Server GUI
----------
- `https://hostname.com:443/gui`

Java Client
-----------
- `./clientJava`
- Java 7+
- No dependencies
- Run test: 

Python Client
-------------
- `./clientPython`
- python3
- Dependencies: `requests` (`pip install requests`)
- Run test: `python test.py`

Javascript client
-----------------
- `./clientJavascript`
- `client.js` is a node module
- Dependencies: `packages.json` -> `devDependencies` (`npm install`)
- Run test: `node test.js`
- Run test in browser: `browserify test.js -o bundle.js` and open `test.html` in browser

Certificates
------------
- Self signed: `openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt`
- Letsencrypt: TODO
    
TODO
----
- Put data writing in a queue
- Put alert sending in a queue
- (Way) better events persister 