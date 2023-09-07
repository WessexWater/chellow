import typing as t
from functools import lru_cache

from chellow.models import Contract, Session


if t.TYPE_CHECKING:
    from wsgiref.types import StartResponse
    from wsgiref.types import WSGIApplication
    from wsgiref.types import WSGIEnvironment


@lru_cache()
def _get_proto_override():
    with Session() as sess:
        config_contract = Contract.get_non_core_by_name(sess, "configuration")
        props = config_contract.make_properties()
        proto = props.get("redirect_scheme")
    return proto


class MsProxy:
    def __init__(
        self,
        app: "WSGIApplication",
    ) -> None:
        self.app = app
        self.x_proto = None

    def __call__(
        self, environ: "WSGIEnvironment", start_response: "StartResponse"
    ) -> t.Iterable[bytes]:
        try:
            x_proto = environ["HTTP_X_FORWARDED_PROTO"]
        except KeyError:
            x_proto = _get_proto_override()

        if x_proto is not None:
            environ["wsgi.url_scheme"] = x_proto

        x_host = environ.get("HTTP_X_FORWARDED_HOST")
        if x_host is not None:
            environ["HTTP_HOST"] = x_host
            parts = x_host.split(":", 1)
            environ["SERVER_NAME"] = parts[0]
            if len(parts) == 2:
                environ["SERVER_PORT"] = parts[1]

        return self.app(environ, start_response)
