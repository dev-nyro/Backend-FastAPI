import logging
import json
from datetime import datetime
import sys
from pathlib import Path

# Get absolute path
LOGS_DIR = Path(__file__).parents[3] / "logs"
LOGS_DIR.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_object = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "funcName": record.funcName,
            "pathname": record.pathname,
            "lineno": record.lineno
        }
        if hasattr(record, "correlation_id"):
            log_object["correlation_id"] = record.correlation_id
        return json.dumps(log_object)

def setup_logger():
    logger = logging.getLogger("fastapi_app")
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File Handler with immediate flush
    file_handler = logging.FileHandler(str(LOGS_DIR / "app.log"), mode='a')
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # Error Handler
    error_handler = logging.FileHandler(str(LOGS_DIR / "error.log"), mode='a')
    error_handler.setFormatter(JSONFormatter())
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)
    
    # Force flush on every log
    logger.propagate = False
    
    # Test log
    logger.info("Logger initialized successfully")
    
    return logger

logger = setup_logger()

__all__ = ['logger']