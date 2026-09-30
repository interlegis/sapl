# sapl/logging/filters.py
import logging
import contextvars

_request_id = contextvars.ContextVar("request_id", default="-")


def set_request_id(value: str):
    _request_id.set(value)


def get_request_id() -> str:
    return _request_id.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # garante que SEMPRE existe
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id()
        return True
