import asyncio

from core import cfg
from core.api import create_app
from app.client import Client


async def main():
    quart_app = create_app()
    bot = Client()

    await asyncio.gather(
        quart_app.run_task(host="0.0.0.0", port=5000),
        bot.start(cfg.TOKEN),
    )


if __name__ == "__main__":
    asyncio.run(main())