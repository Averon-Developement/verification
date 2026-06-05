
from dataclasses import dataclass

from core.database import async_ensure_cursor, Cursor


@dataclass
class GuildStats:
    """Verification statistics for a guild."""
    total: int
    valid: int
    expired: int

@dataclass
class MemberWithTokens:
    """Verified member token information."""
    discord_id: int
    access_token: str
    refresh_token: str
    token_expired: bool


class RestoreHandler:
    """
    Manage member restoration and token updates.
    """
    def __init__(self, guild_id: str):
        self.guild_id = guild_id

    @async_ensure_cursor
    async def get_members_with_tokens(
        self,
        *,
        cursor: Cursor = None
    ) -> list[MemberWithTokens]:
        """
        Get verified members and their token information.

        :return: A list of members with token data.
        """
        cursor.execute(
            """
            SELECT
                u.discord_id,
                u.access_token,
                u.refresh_token,
                u.token_expires_at <= NOW() AS token_expired
            FROM server_members sm
            JOIN users u ON u.discord_id = sm.discord_id
            WHERE sm.guild_id = %s
            """,
            (self.guild_id,),
        )

        rows = cursor.fetchall()
        return [MemberWithTokens(**row) for row in rows] if rows else []

    @async_ensure_cursor
    async def get_guild_stats(
        self,
        *,
        cursor: Cursor = None
    ) -> GuildStats | None:
        """
        Get verification statistics for the guild.

        :return: The guild statistics, if available.        
        """
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN u.token_expires_at > NOW() THEN 1 ELSE 0 END) AS valid,
                SUM(CASE WHEN u.token_expires_at <= NOW() THEN 1 ELSE 0 END) AS expired
            FROM server_members sm
            JOIN users u ON u.discord_id = sm.discord_id
            WHERE sm.guild_id = %s
            """,
            (self.guild_id,),
        )

        row = cursor.fetchone()
        return GuildStats(**row) if row else None

    @async_ensure_cursor
    async def update_token(
        self,
        discord_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        *,
        cursor: Cursor = None,
    ) -> None:
        """
        Update a member's OAuth tokens.

        :param discord_id: The Discord ID of the member.
        :param access_token: The new access token.
        :param refresh_token: The new refresh token.
        :param expires_in: The token lifetime in seconds.
        """
        cursor.execute(
            """
            UPDATE users
            SET
                access_token = %s,
                refresh_token = %s,
                token_expires_at = DATE_ADD(NOW(), INTERVAL %s SECOND)
            WHERE discord_id = %s
            """,
            (access_token, refresh_token, expires_in, discord_id),
        )