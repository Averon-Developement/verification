from dataclasses import dataclass
from datetime import datetime

from core.database import async_ensure_cursor, Cursor


@dataclass
class Member:
    """Verified member information."""
    discord_id: int
    verified_at: datetime


class MemberHandler:
    """
    Manage verified members for a guild.
    """
    def __init__(self, guild_id: str):
        self.guild_id = guild_id

    @async_ensure_cursor
    async def get_global_stats(self, *, cursor: Cursor = None) -> dict:
        cursor.execute("SELECT COUNT(DISTINCT discord_id) AS total_users FROM users")
        users = cursor.fetchone()

        cursor.execute("SELECT COUNT(DISTINCT guild_id) AS total_guilds FROM server_members")
        guilds = cursor.fetchone()

        return {
            "total_users": users["total_users"] if users else 0,
            "total_guilds": guilds["total_guilds"] if guilds else 0,
        }

    @async_ensure_cursor
    async def get_members(self, *, cursor: Cursor = None) -> list[Member]:
        """
        Get all verified members for the guild.

        :return: A list of verified members.
        """
        cursor.execute(
            """
            SELECT u.discord_id, sm.verified_at
            FROM server_members sm
            JOIN users u ON u.discord_id = sm.discord_id
            WHERE sm.guild_id = %s
            """,
            (self.guild_id,),
        )

        rows = cursor.fetchall()
        
        return [Member(**row) for row in rows] if rows else []

    @async_ensure_cursor
    async def remove_member(
        self,
        discord_id: str,
        *, cursor: Cursor = None
    ) -> None:
        """
        Remove a verified member from the guild.

        :param discord_id: The Discord ID of the member.
        """
        cursor.execute(
            "DELETE FROM server_members WHERE guild_id = %s AND discord_id = %s",
            (self.guild_id, discord_id),
        )

        cursor.execute(
            """
            DELETE FROM users
            WHERE discord_id = %s
            AND NOT EXISTS (
                SELECT 1 FROM server_members WHERE discord_id = %s
            )
            """,
            (discord_id, discord_id),
        )
