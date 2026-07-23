import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

from pymongo import MongoClient

from settings import MONGODB_DATABASE, MONGODB_LOG_COLLECTION, MONGODB_URI


class MongoDBHandler(logging.Handler):
    """Store log records in MongoDB without letting Mongo failures stop the API."""

    def __init__(self, uri: str, database: str, collection: str):
        super().__init__()
        self.client = MongoClient(
            uri,
            connect=False,
            connectTimeoutMS=2000,
            serverSelectionTimeoutMS=2000,
        )
        self.collection = self.client[database][collection]
        self.retry_after = 0.0
        self.error_reported = False

    def emit(self, record: logging.LogRecord):
        if monotonic() < self.retry_after:
            return

        document = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }
        if record.exc_info:
            document["exception"] = self.format(record).splitlines()[-1]

        try:
            self.collection.insert_one(document)
            self.error_reported = False
        except Exception as exc:
            # Keep logging non-fatal and retry MongoDB after a short cooldown.
            self.retry_after = monotonic() + 30
            if not self.error_reported:
                sys.stderr.write(
                    f"MongoDB logging unavailable ({type(exc).__name__}); "
                    "file and console logging remain active.\n"
                )
                self.error_reported = True

    def close(self):
        self.client.close()
        super().close()

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("online_shop")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    for handler in (
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler(),
        MongoDBHandler(
            MONGODB_URI,
            MONGODB_DATABASE,
            MONGODB_LOG_COLLECTION,
        ),
    ):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
