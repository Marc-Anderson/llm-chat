import logging
import os


# region config

MODEL_NAME = "gpt-4.1"

# endregion config

# region configure logging

CHAT_LOG_FILEPATH = "chat_log.txt"
# CHAT_LOG_FILEPATH = Path("data") / "chat_log.txt"


logging.basicConfig(
    filename=CHAT_LOG_FILEPATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
    force=True,
)
logger = logging.getLogger(__name__)

# endregion configure logging


# region api key handling


def load_env():
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value.replace('"', "").strip()


load_env()

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError(
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )


# endregion api key handling
