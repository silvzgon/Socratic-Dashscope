import logging
import logging.handlers

logger = logging.getLogger('dialogue_logger')
logger.setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler(
    './log/dialogue.log',
    maxBytes=5 * 1024 * 1024,
)

formatter = logging.Formatter('%(asctime)s - %(message)s')

handler.setFormatter(formatter)
logger.addHandler(handler)