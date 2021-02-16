import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(threadName)s - %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
