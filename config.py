import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    USERNAME = os.getenv("USERNAME").strip()
    PASSWORD = os.getenv("PASSWORD").strip()
    CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS").strip()
    RELATED_ADDRESS = os.getenv("RELATED_ADDRESS").strip()
    RECEIVER_ADDRESS = os.getenv("RECEIVER_ADDRESS").strip()
    LOAD_TIMEOUT = float(os.getenv("LOAD_TIMEOUT").strip())
    USER_AGENT = os.getenv("USER_AGENT").strip()
