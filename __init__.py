from logging import getLogger, FileHandler, Formatter, INFO
import configparser
from dotenv import dotenv_values


def get_logger():
    """
    Initializes and returns a logger that logs INFO level messages to log.log.

    The logger uses a file handler with a standard log message format,
    suppresses duplicate handlers, and is intended for application-wide usage.

    Returns:
        logging.Logger: Configured logger for this application.
    """
    logger = getLogger("log.log")
    logger.setLevel(INFO)
    file_handler = FileHandler("log.log")
    file_handler.setLevel(INFO)
    formatter = Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def read_config():
    """
    Reads the configuration from the 'config.ini' file and returns a dictionary
    of configuration values.

    Returns:
        dict: A dictionary containing the configuration values.
    """
    config = configparser.ConfigParser()
    config.read("config.ini")
    DB_NAME = config.get("General", "DB_NAME")
    SEED_PAGE_NAME = config.get("General", "SEED_PAGE_NAME")
    SIM_THRESHOLD = config.get("General", "SIM_THRESHOLD")
    LANG_CODES = config.get("General", "LANG_CODES").split(",")
    SBERT_MODEL_NAME = config.get("General", "SBERT_MODEL_NAME")

    config_values = {
        "DB_NAME": DB_NAME,
        "SEED_PAGE_NAME": SEED_PAGE_NAME,
        "SIM_THRESHOLD": SIM_THRESHOLD,
        "LANG_CODES": LANG_CODES,
        "SBERT_MODEL_NAME": SBERT_MODEL_NAME
    }
    return config_values


def get_headers():
    """
    Reads the access token, app name, and email from the '.env' file and
    returns a headers dictionary.

    Returns:
        dict: A headers dictionary with Authorization and User-Agent keys
              for Wikipedia API requests.
    """
    env_vars = {**dotenv_values()}
    ACCESS_TOKEN = env_vars["ACCESS_TOKEN"]
    APP_NAME = env_vars["APP_NAME"]
    EMAIL = env_vars["EMAIL"]
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "User-Agent": f"{APP_NAME} ({EMAIL})"
        }
    return headers


logger = get_logger()

config = read_config()

headers = get_headers()
