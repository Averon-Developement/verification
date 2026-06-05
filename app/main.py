from .client import Client
from core import cfg


if __name__ == "__main__":
    Client().run(cfg.TOKEN)