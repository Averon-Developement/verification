from dataclasses import dataclass

from core.database import Cursor, ensure_cursor


@dataclass(slots=True, frozen=True)
class VerificationSettings:
    """
    Verification settings for a guild.
    """
    guild_id: int
    role_id: int | None
    logs_channel_id: int | None
    dm_user: bool


class SettingsHandler:
    """
    Manage guild verification settings.
    """
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

    @ensure_cursor
    def set_role(
        self,
        role_id: int | None,
        *,
        cursor: Cursor=None
    ) -> None:
        """
        Set the verification role.

        :param role_id: The role ID to assign on verification.
        """
        cursor.execute(
            """
            INSERT INTO settings (guild_id, role_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                role_id=VALUES(role_id)
            """,
            (self.guild_id, role_id,)
        )

    @ensure_cursor
    def set_logs_channel(
        self,
        channel_id: int | None,
        *,
        cursor: Cursor=None
    ) -> None:
        """
        Set the verification logs channel.

        :param channel_id: The channel ID to send verification logs to.
        """
        cursor.execute(
            """
            INSERT INTO settings (guild_id, logs_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                logs_channel_id=VALUES(logs_channel_id)
            """,
            (self.guild_id, channel_id,)
        )

    @ensure_cursor
    def set_dm_user(
        self,
        enabled: bool,
        *,
        cursor: Cursor=None
    ) -> None:
        """
        Enable or disable verification DMs.

        :param enabled: Whether verified users should receive a direct message.
        """
        cursor.execute(
            """
            INSERT INTO settings (guild_id, dm_user) 
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                dm_user=VALUES(dm_user)
            """,
            (self.guild_id, enabled,)
        )

    @ensure_cursor
    def get_settings(
        self, *, cursor: Cursor=None
    ) -> VerificationSettings:
        """
        Get the guild's verification settings.
        Creates default settings if none exist.

        :return VerificationSettings: The fetched verification settings.
        """
        cursor.execute(
            "SELECT * FROM settings WHERE guild_id=%s",
            (self.guild_id,)
        )

        result = cursor.fetchone()
        
        if result is None:
            cursor.execute(
                "INSERT INTO settings (guild_id) VALUES (%s)",
                (self.guild_id,)
            )

            return VerificationSettings(
                guild_id=self.guild_id,
                role_id=None,
                logs_channel_id=None,
                dm_user=False
            )
        
        return VerificationSettings(**result)