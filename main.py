import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core import cfg
from core.api import create_app
from core.database.handlers import MemberHandler
from app.client import Client

console = Console()


async def main():
    stats = await MemberHandler(None).get_global_stats()

    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column(style="cyan", justify="right")
    table.add_column(style="white")

    table.add_row("Verified Users", f"{stats['total_users']:,}")
    table.add_row("Guilds", f"{stats['total_guilds']:,}")
    table.add_row("", "")
    table.add_row("Database", f"{cfg.DBUSER}@{cfg.DBHOST}:{cfg.DBPORT}/{cfg.DBNAME}")
    table.add_row("", "")
    table.add_row("Verify URL", cfg.VERIFICATION_URI)
    table.add_row("Privacy URL", cfg.PRIVACY_POLICY_URI)

    console.print(
        Panel(
            table,
            title="[bold blue]Averon Verification[/bold blue]",
            border_style="blue",
            expand=False,
        )
    )

    await asyncio.gather(
        create_app().run_task(host="0.0.0.0", port=5000),
        Client().start(cfg.TOKEN),
    )


if __name__ == "__main__":
    asyncio.run(main())