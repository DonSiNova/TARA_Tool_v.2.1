# config/logging.py
import logging
import os


def configure_logging(output_dir: str):
    """
    Configure the shared AutoTARA logger to write inside the provided
    output directory. Existing handlers are replaced so switching run
    directories updates the log destination.
    """
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "tara.log")

    logger = logging.getLogger("AutoTARA")
    logger.setLevel(logging.INFO)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
