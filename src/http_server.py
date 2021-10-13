from twisted.web import resource
import os

from webserver import settings

# 'Transfer-Encoding': 'chunked',
headers = {
    'Server': 'Rapid Logic/1.1',
    'MIME-version': '1.0',
    'Content-Type': 'text/html; charset=UTF-8',
    'Set-Cookie': 'auth=c0a80a4f0002984d; path=/',
    'Connection': 'Keep-Alive'
}

def get_template(page):
    with open(os.path.join(settings.TEMPLATES_DIR, f'{page}.html')) as file:
        return file.read()

class RobotsTxt(resource.Resource):
    """ /robots.txt link.
    """
    isLeaf = True
    def render_GET(self, request):
        request.responseHeaders.removeHeader("Server")
        for header in headers:
            request.setHeader(header, headers[header])
        # request.setHeader("Accept-Ranges", "bytes")
        # request.setHeader("Connection", "close")
        # request.setHeader("Content-Type", "text/plain")

        # return b"User-agent: *\nDisallow: /\n"
        request.setResponseCode(404)
        return get_template('404').encode()

class FaviconIco(resource.Resource):
    """ /favicon.ico link.
    """
    isLeaf = True
    def render_GET(self, request):
        request.responseHeaders.removeHeader("Server")
        for header in headers:
            request.setHeader(header, headers[header])
        # request.setHeader("Accept-Ranges", "bytes")
        # request.setHeader("Connection", "close")
        # request.setHeader("Content-Type", "text/html; charset=ISO-8859-1")

        request.setResponseCode(404)
        return get_template('404').encode()

class RootURL(resource.Resource):
    """ / link. """
    isLeaf = True

    def render_GET(self, request):
        request.setResponseCode(200)
        request.responseHeaders.removeHeader("Server")
        for header in headers:
            request.setHeader(header, headers[header])
        # request.setHeader("Accept-Ranges", "bytes")
        # request.setHeader("Connection", "close")
        # request.setHeader("Content-Type", "text/html; charset=ISO-8859-1")
        return get_template('200').encode()

    def render_HEAD(self, request):
        request.setResponseCode(200)
        request.responseHeaders.removeHeader("Server")
        for header in headers:
            request.setHeader(header, headers[header])
        # request.setHeader("Accept-Ranges", "bytes")
        # request.setHeader("Connection", "close")
        # request.setHeader("Content-Type", "text/html; charset=ISO-8859-1")
        return b""

    def render_OPTIONS(self, request):
        request.setResponseCode(501)

        request.responseHeaders.removeHeader("Server")
        for header in headers:
            request.setHeader(header, headers[header])

        # request.setHeader("Accept-Ranges", "bytes")
        # request.setHeader("Connection", "close")
        # request.setHeader("Content-Type", "text/html; charset=ISO-8859-1")
        return get_template('501').encode()

    def render_POST(self, request):
        request.setResponseCode(500)

        request.responseHeaders.removeHeader("Server")
        for header in headers:
            request.setHeader(header, headers[header])
        # request.setHeader("Accept-Ranges", "bytes")
        # request.setHeader("Connection", "close")
        # request.setHeader("Content-Type", "text/html; charset=ISO-8859-1")
        return get_template('500').encode()

class OtherURLs(resource.Resource):
    """ Any other link.
    """
    isLeaf = True
    def render_GET(self, request):
        request.responseHeaders.removeHeader("Server")
        for header in headers:
            request.setHeader(header, headers[header])

        # request.setHeader("WWW-Authenticate", 'Basic realm="realmname"')
        # return b"Authorization required."
        request.setResponseCode(404)
        return get_template('404').encode()

class HTTPHandler(resource.Resource):
    """ Link dispatcher.
    """
    def getChild(self, name, request):
        if name == b"":
            return RootURL()
        elif name == b"robots.txt":
            return RobotsTxt()
        elif name == b"favicon.ico":
            return FaviconIco()
        else:
            return OtherURLs()

