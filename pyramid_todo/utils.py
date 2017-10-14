from pyramid.request import Request
from pyramid.request import Response


def request_factory(environ):
    """Setting up the request factory."""
    request = Request(environ)
    if request.is_xhr:
        request.response = Response()
        request.response.headerlist = []
        request.response.headerlist.extend(
            (
                ('Access-Control-Allow-Origin', '*'),
                ('Content-Type', 'application/json')
            )
        )
    return request


def includeme(config):
    config.set_request_factory(request_factory)
