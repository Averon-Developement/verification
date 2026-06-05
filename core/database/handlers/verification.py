from core.database import Cursor, async_ensure_cursor


class VerifyHandler:
    """
    Manage verification data for users and guild members.
    """
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
        """
        Save a user's OAuth credentials.

        :param discord_id: The Discord ID of the user.
        :param access_token: The OAuth access token.
        :param refresh_token: The OAuth refresh token.
        :param expires_in: The token lifetime in seconds.
        """
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
        """
        Add a verified member to a guild.

        :param guild_id: The Discord guild ID.
        :param discord_id: The Discord ID of the user.
        """
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