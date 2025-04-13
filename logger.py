import os
import logging
from dotenv import load_dotenv;load_dotenv()

# Get the path to the log file from environment variables
P_LOG_PATH = os.getenv("P_LOG_PATH")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Create a file handler
file_handler = logging.FileHandler(P_LOG_PATH)
file_handler.setLevel(logging.INFO)
# Create a formatter and set it for the handler
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
# Add the handler to the logger
logger.addHandler(file_handler)
