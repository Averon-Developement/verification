from os import getenv
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


@dataclass
class Config:
    TOKEN: str = getenv("TOKEN")

    # Database
    DBHOST: str = getenv("DBHOST")
    DBPORT: int = getenv("DBPORT")
    DBNAME: str = getenv("DBNAME")
    DBUSER: str = getenv("DBUSER")
    DBPASSWORD: str = getenv("DBPASS")

    # Discord OAuth
    DISCORD_CLIENT_ID: str = getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET: str = getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI: str = getenv("DISCORD_REDIRECT_URI")

    # Verification URI
    VERIFICATION_URI: str = getenv("VERIFICATION_URI")
    PRIVACY_POLICY_URI: str = getenv("PRIVACY_POLICY_URI")

cfg = Config()
