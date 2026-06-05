from dataclasses import dataclass
from datetime import datetime

from core.database import async_ensure_cursor, Cursor

@dataclass
class Member:
    discord_id: int
    verified_at: datetime


@dataclass
class GuildStats:
    total: int
    valid: int
    expired: int


@dataclass
class MemberWithTokens:
    discord_id: int
    access_token: str
    refresh_token: str
    token_expired: bool

class MemberHandler:
    def __init__(self, guild_id: str):
        self.guild_id = guild_id

    @async_ensure_cursor
    async def get_members(self, *, cursor: Cursor = None) -> list[Member]:
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
    async def remove_member(self, discord_id: str, *, cursor: Cursor = None) -> None:
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


class RestoreHandler:
    def __init__(self, guild_id: str):
        self.guild_id = guild_id

    @async_ensure_cursor
    async def get_members_with_tokens(self, *, cursor: Cursor = None) -> list[MemberWithTokens]:
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
    async def get_guild_stats(self, *, cursor: Cursor = None) -> GuildStats | None:
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


class VerifyHandler:
    @async_ensure_cursor
    async def save_user(
        self,
        discord_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        *,
        cursor: Cursor = None,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO users (discord_id, access_token, refresh_token, token_expires_at)
            VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL %s SECOND))
            ON DUPLICATE KEY UPDATE
                access_token = VALUES(access_token),
                refresh_token = VALUES(refresh_token),
                token_expires_at = VALUES(token_expires_at)
            """,
            (discord_id, access_token, refresh_token, expires_in),
        )

    @async_ensure_cursor
    async def save_server_member(
        self,
        guild_id: str,
        discord_id: str,
        *,
        cursor: Cursor = None,
    ) -> None:
        cursor.execute(
            """
            INSERT IGNORE INTO servers (guild_id, owner_discord_id)
            VALUES (%s, %s)
            """,
            (guild_id, discord_id),
        )

        cursor.execute(
            """
            INSERT IGNORE INTO server_members (guild_id, discord_id)
            VALUES (%s, %s)
            """,
            (guild_id, discord_id),
        )