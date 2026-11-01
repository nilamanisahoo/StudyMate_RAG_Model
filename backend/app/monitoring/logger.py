
import json
import logging

from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Convert normal log records into JSON format.
    """

    def format(self, record):

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        extra_data = getattr(record, "extra_data", None)

        if isinstance(extra_data, dict):
            log_data.update(extra_data)

        return json.dumps(log_data, default=str)


def get_logger(name: str = "studymate-api") -> logging.Logger:
    """
    Create and return the application logger.
    """

    logger = logging.getLogger(name)

    if not logger.handlers:

        handler = logging.StreamHandler()

        handler.setFormatter(JSONFormatter())

        logger.addHandler(handler)

        logger.setLevel(logging.INFO)

        logger.propagate = False

    return logger
