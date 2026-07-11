import logging
from pathlib import Path


def get_my_logger(name):
    logging.basicConfig(level=logging.INFO)
    # HTTPクライアントの低レベルログは冗長なので抑制する
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    log_dir = Path("../log")
    log_dir.mkdir(exist_ok=True)
    handler = logging.FileHandler(log_dir / 'log')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
