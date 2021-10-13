const http = require("http");
const url = require("url");
const fs = require("fs");
const { networkInterfaces } = require("os");
const path = require("path");
const dateFormat = require("dateformat");
const https = require("https");
const querystring = require("querystring");
const uuid4 = require("uuid4");
const sqlite = require("better-sqlite3");

const { getHeadersFromArray, parseHeaders } = require("./utils");

const LOG_FILE = "/temp/cowrie/data/log/web.ndjson";
// 60s
const ATTACK_TIMEOUT = 60 * 1000;
const INTERFACE = process.env.interface || "eth0";
// declary any ip of any subset (it doesn't matter)

// delete database if it exists
try {
  fs.accessSync("honeypot.db");
  fs.unlinkSync("honeypot.db");
} catch (e) {}

// create new, emptry database
const db = new sqlite("honeypot.db");

const fingerprintsDb = new sqlite("/home/node/data/history.db");

// create table to store data of attacks
db.prepare(
  "CREATE TABLE attacks(ip text, port integer, dest_port integer, protocol text, session text, attempts integer, datetime text)"
).run();

// transaction-based operations with db.
// They are safe even in async mode
const insertSession = db.transaction(
  (ip, port, dest_port, protocol, session, attempts, datetime) => {
    db.prepare(
      `INSERT INTO attacks(ip, port, dest_port, protocol, session, attempts, datetime) VALUES(?, ?, ?, ?, ?, ?, ?)`
    ).run(ip, port, dest_port, protocol, session, attempts, datetime);
  }
);

const updateAttack = db.transaction(
  (session, port, dest_port, protocol, datetime) => {
    db.prepare(
      `UPDATE attacks SET port=?, dest_port=?, protocol=?, datetime=? WHERE session=?`
    ).run(port, dest_port, protocol, datetime, session);
  }
);

const updateAttackAttempts = db.transaction((session, attempts) => {
  db.prepare(`UPDATE attacks SET attempts=? WHERE session=?`).run(
    attempts,
    session
  );
});

const deleteExpiredAttacks = db.transaction((datetime) => {
  db.prepare(`DELETE FROM attacks WHERE datetime <= '${datetime}'`).run();
});

const nets = networkInterfaces();
const interfaces = Object.create(null); // or just '{}', an empty object

for (const name of Object.keys(nets)) {
  for (const net of nets[name]) {
    // skip over non-ipv4 and internal (i.e. 127.0.0.1) addresses
    if (net.family === "IPv4" && !net.internal) {
      if (!interfaces[name]) {
        interfaces[name] = [];
      }

      interfaces[name].push(net.address);
    }
  }
}

const DEST_IP = interfaces[INTERFACE][0];

// Create LOG_FILE if required
try {
  fs.accessSync(LOG_FILE);
} catch (err) {
  const folder_path = path.dirname(LOG_FILE);

  try {
    fs.accessSync(folder_path);
  } catch (err1) {
    fs.mkdirSync(folder_path, { recursive: true });
  }

  fs.writeFile(LOG_FILE, "", { flag: "wx" }, function (err) {
    if (err) throw err;
  });
}

function getSession(req) {
  // remove ipv6 prefix and remain ipv4 address
  const src_ip = req.connection.remoteAddress.replace(/^.*:/, "");

  let session = db.prepare(`SELECT * FROM attacks WHERE ip = ?`).get(src_ip);

  if (session === undefined) {
    session = uuid4();

    const date = new Date().toISOString();

    insertSession(
      src_ip,
      req.connection.remotePort,
      req.connection.encrypted ? 443 : 80,
      req.connection.encrypted ? "https" : "http",
      session,
      0,
      date
    );

    fs.appendFile(
      LOG_FILE,
      JSON.stringify({
        dest_ip: DEST_IP,
        src_ip: src_ip,
        dest_port: req.connection.encrypted ? 443 : 80,
        src_port: req.connection.remotePort,
        session: session,
        protocol: req.connection.encrypted ? "https" : "http",
        eventid: "connection",
        type: "d_link_dph150s",
        timestamp: date,
      }) + "\n",
      function (err) {
        if (err) console.log("Unable to write to LOG_FILE");
      }
    );

    session = db.prepare(`SELECT * FROM attacks WHERE ip = ?`).get(src_ip);
  }

  return session;
}

function prepareHeaders(headers) {
  const headersToDelete = ["Cookie", "User-Agent"];
  const variableHeadersToDelete = ["Host"];

  for (const header of headersToDelete) {
    if (headers[header]) {
      delete headers[header];
    }
  }

  for (const header of variableHeadersToDelete) {
    if (headers[header]) {
      delete headers[header];
    }
  }

  return headers;
}

function handler(req, res) {
  const attack = getSession(req);
  const url_path = url.parse(req.url, true).pathname;
  const query = url.parse(req.url, true).query;

  const dest_port = req.connection.encrypted ? 443 : 80;
  const protocol = req.connection.encrypted ? "https" : "http";
  const src_ip = req.connection.remoteAddress.replace(/^.*:/, "");
  const date = new Date().toISOString();

  function logHttpRequest(form = {}) {
    fs.appendFile(
      LOG_FILE,
      JSON.stringify({
        dest_ip: DEST_IP,
        src_ip: src_ip,
        dest_port: dest_port,
        src_port: req.connection.remotePort,
        session: attack.session,
        protocol: protocol,
        eventid: "http_request",
        url: req.url,
        method: req.method,
        headers: req.headers,
        form: form,
        type: "d_link_dph150s",
        timestamp: date,
      }) + "\n",
      function (err) {
        if (err) console.log("Unable to write to LOG_FILE");
      }
    );
  }

  updateAttack(
    attack.session,
    req.connection.remotePort,
    dest_port,
    protocol,
    new Date().toISOString()
  );

  logHttpRequest();

  res.removeHeader("Date");

  const httpVersion = `HTTP/${req.httpVersion}`;
  const method = req.method;

  const headers = {};

  for (let i = 0; i !== req.rawHeaders.length; i++) {
    if (i % 2 == 0) {
      headers[req.rawHeaders[i]] = req.rawHeaders[i + 1];
    }
  }

  const preparedHeaders = prepareHeaders(headers);

  let url_ = req.url;

  let sqlrequest = "SELECT * FROM requests WHERE instr(data, ?) > 0";
  let sqlargs = [];

  if (url_.startsWith("/nmaplowercheck")) {
    url_ = "/nmaplowercheck";
    sqlargs.push(
      JSON.stringify({ protocol: httpVersion, method, url: url_ }).slice(0, -2)
    );
  } else {
    sqlargs.push(
      JSON.stringify({ protocol: httpVersion, method, url: url_ }).slice(0, -1)
    );
  }

  for (const headerKey of Object.keys(preparedHeaders)) {
    const headerValue = preparedHeaders[headerKey];

    sqlrequest = `${sqlrequest} AND instr(data, ?) > 0`;
    sqlargs.push(
      JSON.stringify({
        [headerKey]: headerValue,
      }).slice(1, -1)
    );
  }

  // protocol, method, url - strict match
  // headers - partial
  // const request = fingerprintsDb
  //   .prepare(`SELECT * from requests WHERE instr(data, ?) > 0`)
  //   .get(
  //     JSON.stringify({
  //       protocol: httpVersion,
  //       method,
  //       url: url_,
  //       headers: preparedHeaders,
  //     })
  //   );

  const request = fingerprintsDb.prepare(sqlrequest).get(...sqlargs);

  if (request) {
    console.log("Found: %s, %s", req.url, req.method);

    const response = fingerprintsDb
      .prepare(`SELECT * from responses WHERE request = ?`)
      .get(request.id);

    res.socket.end(response.rawData);
  } else {
    // answer as 404 based on nmaplowercheck (if possible)

    // console.log(
    //   "Not found: %s, %s, %s\n%s",
    //   req.url,
    //   req.method,
    //   JSON.stringify(headers),
    //   JSON.stringify({
    //     protocol: httpVersion,
    //     method,
    //     url: url_,
    //     headers: preparedHeaders,
    //   })
    // );

    const request = fingerprintsDb
      .prepare(`SELECT * from requests WHERE instr(data, ?) > 0`)
      .get(
        JSON.stringify({ protocol: httpVersion, method, url: url_ }).slice(
          0,
          -2
        )
      );

    if (request) {
      const response = fingerprintsDb
        .prepare(`SELECT * from responses WHERE request = ?`)
        .get(request.id);

      res.socket.end(response.rawData);
    }
  }

  // TODO:
  // res.setHeader(
  //   "Date",
  //   dateFormat(new Date(), "ddd, d mmm yyyy hh:mm:ss") + " GMT"
  // );
}

const http_server = http.createServer(function (req, res) {
  handler(req, res);
});

http_server.on("clientError", (err, socket) => {
  if (err.code === "ECONNRESET" || !socket.writable) {
    return;
  }

  // TODO:
  // socket.end(
  //   "HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Type: text/plain\r\nTransfer-Encoding: chunked\r\n\r\n"
  // );
  // socket.end('HTTP/1.1 400 Bad Request\r\n\r\n');
});
http_server.listen(80, () => {
  console.log("Http server started on", 80);
});

setInterval(() => {
  const now = new Date();
  const now_iso = now.toISOString();
  const now_minus_minute = new Date();
  now_minus_minute.setTime(now.getTime() - ATTACK_TIMEOUT);

  const expiredAttacks = db
    .prepare(
      `SELECT * from attacks WHERE datetime <= '${now_minus_minute.toISOString()}'`
    )
    .iterate();

  for (const attack of expiredAttacks) {
    const { session, ip, port, dest_port, protocol } = attack;

    fs.appendFile(
      LOG_FILE,
      JSON.stringify({
        dest_ip: DEST_IP,
        src_ip: ip,
        dest_port: dest_port,
        src_port: port,
        session: session,
        protocol: protocol,
        eventid: "disconnection",
        type: "d_link_dph150s",

        timestamp: now_iso,
      }) + "\n",
      function (err) {
        if (err) console.log("Unable to write to LOG_FILE");
      }
    );
  }

  deleteExpiredAttacks(now_minus_minute);
}, ATTACK_TIMEOUT);
