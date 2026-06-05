from os import getenv
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


@dataclass
class Config:
    """
    Application configuration loaded from environment variables.
    """
    TOKEN: str = getenv("TOKEN")

    # add everything in the .env file here


cfg = Config()