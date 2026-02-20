import logging

try:
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s"))
    logger.addHandler(handler)
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("app")

def custom_logger():
    return logger

