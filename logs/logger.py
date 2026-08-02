import logging
import json
from pathlib import Path
from datetime import datetime, timezone

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

_handler = logging.FileHandler(LOG_DIR / "nullvault.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(message)s"))

_logger = logging.getLogger("nullvault")
_logger.setLevel(logging.DEBUG)
_logger.addHandler(_handler)


def _emit(level: str, event: str, **kwargs):
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": event,
        **kwargs,
    }
    getattr(_logger, level.lower())(json.dumps(record))


def log_info(event: str, **kwargs):
    _emit("INFO", event, **kwargs)


def log_warning(event: str, **kwargs):
    _emit("WARNING", event, **kwargs)


def log_error(event: str, **kwargs):
    _emit("ERROR", event, **kwargs)
