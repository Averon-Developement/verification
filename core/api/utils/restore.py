import httpx

from core import cfg, logger, disc
from core.database.handlers import RestoreHandler


async def add_member_to_guild(
    client: httpx.AsyncClient,
    guild_id: str,
    discord_id: str,
    access_token: str,
) -> bool:
    """
    Add a user to a Discord guild.

    :param client: The HTTP client used for the request.
    :param guild_id: The Discord guild ID.
    :param discord_id: The Discord ID of the user.
    :param access_token: The user's OAuth access token.
    :return: Whether the user was added successfully.
    """
    try:
        response = await client.put(
            f"{disc.DISCORD_API}/guilds/{guild_id}/members/{discord_id}",
            json={"access_token": access_token},
            headers={"Authorization": f"Bot {cfg.TOKEN}"},
        )
        return response.status_code in (201, 204)

    except Exception as e:
        logger.error(f"Failed to add {discord_id} to {guild_id}: {e}")
        return False


async def refresh_token(
    client: httpx.AsyncClient,
    handler: RestoreHandler,
    discord_id: str,
    refresh_token: str,
) -> str | None:
    """
    Refresh a user's OAuth access token.

    :param client: The HTTP client used for the request.
    :param handler: The restore handler used to update stored tokens.
    :param discord_id: The Discord ID of the user.
    :param refresh_token: The user's OAuth refresh token.
    :return: The new access token, if successful.
    """
    try:
        response = await client.post(
            disc.DISCORD_TOKEN_URL,
            data={
                "client_id": cfg.DISCORD_CLIENT_ID,
                "client_secret": cfg.DISCORD_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            return None

        data = response.json()

        await handler.update_token(
            discord_id=discord_id,
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data["expires_in"],
        )

        return data["access_token"]

    except Exception as e:
        logger.error(f"Token refresh failed for {discord_id}: {e}")
        return None