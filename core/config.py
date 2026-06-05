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
    DBHOST: str = getenv("DBHOST")
    DBPORT: int = getenv("DBPORT")
    DBNAME: str = getenv("DBNAME")
    DBUSER: str = getenv("DBUSER")
    DBPASSWORD: str = getenv("DBPASS")

    # add everything in the .env file here


cfg = Config()