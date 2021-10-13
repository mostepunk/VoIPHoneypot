const url = require("url");

function normalizeUrl(url_) {
  let protocol, path, hostname, _;

  try {
    protocol,
      path,
      hostname,
      (_ = { protocol, path, port, hostname } = url.parse(url_));
  } catch (e) {
    return null;
  }

  let useProtocol = protocol;
  let usePath = path;
  let useHostname = hostname;
  let usePort = port;
  let useProxyUrl = null;

  if (protocol !== null) {
    if (protocol.indexOf(".") !== -1) {
      // > url.parse("vicesight.com:443/1")
      // Url {
      //   protocol: 'vicesight.com:',
      //   slashes: null,
      //   auth: null,
      //   host: '443',
      //   port: null,
      //   hostname: '443',
      //   hash: null,
      //   search: null,
      //   query: null,
      //   pathname: '/1',
      //   path: '/1',
      //   href: 'vicesight.com:443/1' }
      // >
      useProtocol = hostname === "443" ? "https:" : "http:";
      useHostname = protocol.slice(0, -1);

      if (path === null) {
        usePath = "/";
      }

      usePort = parseInt(hostname);

      useProxyUrl = `http://${useHostname}:${usePort}${usePath}`;
    } else {
      if (usePort === null) {
        if (protocol === "http:") {
          usePort = 80;
        } else if (protocol === "https:") {
          usePort = 443;
        } else {
          console.error("Unknown protocol:", protocol);
        }
      }
    }
  } else {
    if (path) {
      useHostname = path.slice(0, path.indexOf("/"));
      usePath = path.slice(path.indexOf("/"));
      useProtocol = "http"; // or https
    } else {
      console.error("Undefined url schema:", url_);
    }
  }

  // console.log(
  //   protocol,
  //   path,
  //   port,
  //   hostname,
  //   `${useProtocol}//${useHostname}${usePath}`
  // );

  // {http(s)://}{www.google.com}{/?q=search}
  return {
    url: `${useProtocol}//${useHostname}${usePath}`,
    proxyUrl: useProxyUrl,
    hostname: useHostname,
    port: usePort,
  };
}

function getHeadersFromArray(headersArray) {
  const headers = {};

  for (let headerString of headersArray.slice(1)) {
    const splitterIndex = headerString.indexOf(": ");

    let key = headerString.slice(0, splitterIndex);
    let value = headerString.slice(splitterIndex + 2);

    headers[key] = value;
  }

  return headers;
}

function parseHeadersData(headersEnd, data) {
  let headers = {};

  // response
  let status = null;
  let dataWithoutHeaders = data.toString("utf-8");

  // request
  let method;

  // universal
  let httpVersion;
  let contentLength;
  let chunked;

  const headersArray = data
    .slice(0, headersEnd)
    .toString("utf-8")
    .split("\r\n");

  const mainHeaderParts = headersArray[0].split(/\s/gm);

  if (headersArray[0].startsWith("HTTP")) {
    // response
    // HTTP/1.1 302 Found
    httpVersion = mainHeaderParts.slice[0];

    status = mainHeaderParts.slice(1, 2)[0];

    // check if status is a number
    if (!isNaN(status)) {
      status = parseInt(status);
    } else {
      console.error("Unknown status code:", status);
      console.log(headersArray[0], responseHeaderParts);
    }
  } else {
    // request
    // GET /.git/HEAD HTTP/1.1

    httpVersion = mainHeaderParts.slice(-1)[0];

    method = mainHeaderParts.slice(0, 1)[0];
  }

  headers = getHeadersFromArray(headersArray.slice(1));

  dataWithoutHeaders = data.slice(headersEnd + 4).toString("utf-8");

  if (headers["Content-Length"]) {
    contentLength = parseInt(headers["Content-Length"]);
  }

  if (
    headers["Transfer-Encoding"] &&
    headers["Transfer-Encoding"] === "chunked"
  ) {
    chunked = true;
  } else {
    chunked = false;
  }

  return {
    httpVersion,
    method,
    status,
    headers,
    dataWithoutHeaders,
    contentLength,
    chunked,
  };
}
// add method, http v. recognition
function parseHeaders(data, fullResponseData) {
  let headersEnd = data.indexOf("\r\n\r\n");

  if (headersEnd !== -1) {
    return parseHeadersData(headersEnd, data);
  }

  headersEnd = fullResponseData.indexOf("\r\n\r\n");

  if (headersEnd !== -1) {
    return parseHeadersData(fullResponseData);
  }

  return null;
}

module.exports = {
  normalizeUrl,
  getHeadersFromArray,
  parseHeaders,
};
