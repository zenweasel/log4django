import logging
from datetime import datetime

from django.utils.timezone import make_aware, get_default_timezone

import jsonpickle

from .settings import DEFAULT_APP_ID

LogRecord = None


class BaseFormatter(logging.Formatter):

    DEFAULT_PROPERTIES = logging.LogRecord('', '', '', '', '', '', '', '').__dict__.keys()

    def _get_extra(self, record):
        """Standard record decorated with extra contextual information."""
        extra = {}
        contextual_extra = set(record.__dict__).difference(set(self.DEFAULT_PROPERTIES))
        contextual_extra.remove('message')
        contextual_extra.remove('asctime')
        for key in contextual_extra:
            extra[key] = getattr(record, key)
        return extra


class ModelFormatter(BaseFormatter):

    def format(self, record):
        # Lazy models imports.
        global LogRecord
        if LogRecord is None:
            from .models import LogRecord
        # Basic record data.
        log_record = LogRecord(
            loggerName=record.name, level=record.levelno,
            timestamp=make_aware(datetime.fromtimestamp(record.created), get_default_timezone()),
            message=record.getMessage(), fileName=record.pathname, lineNumber=record.lineno,
            thread=record.thread, app_id=getattr(record, 'app_id', DEFAULT_APP_ID)
        )
        # Exception data if available.
        if record.exc_info is not None:
            log_record.exception_message = str(record.exc_info[1])
            log_record.exception_traceback = self.formatException(record.exc_info)
        # Extra data.
        log_record.extra = self._get_extra(record)
        return log_record


class GearmanFormatter(BaseFormatter):

    def format(self, record):
        # Basic record data.
        record_dict = dict(
            loggerName=record.name, level=record.levelno,
            timestamp=str(make_aware(datetime.fromtimestamp(record.created), get_default_timezone())),
            message=record.getMessage(), fileName=record.pathname, lineNumber=record.lineno,
            thread=record.thread, app_id=getattr(record, 'app_id', DEFAULT_APP_ID)
        )
        # Exception data if available.
        if record.exc_info is not None:
            record_dict['exception_message'] = str(record.exc_info[1])
            record_dict['exception_traceback'] = self.formatException(record.exc_info)
        # Extra data.
        record_dict['extra'] = self._get_extra(record)
        return jsonpickle.encode(record_dict)