import asyncio
import httpx

from quart import Blueprint, jsonify

from core import cfg, logger
from core.database import async_ensure_cursor, Cursor


restore_bp = Blueprint("restore", __name__, url_prefix="/restore")

DISCORD_API = "https://discord.com/api/v10"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"


@restore_bp.post("/<guild_id>")
async def restore(guild_id: str):
    members = await _fetch_members_with_tokens(guild_id=guild_id)

    if not members:
        return jsonify({"error": "No verified members found for this guild."}), 404

    results = {"success": [], "failed": [], "token_refreshed": []}

    async with httpx.AsyncClient() as client:
        for member in members:
            discord_id = member["discord_id"]
            access_token = member["access_token"]

            # Refresh the token if it has expired
            if member["token_expired"]:
                refreshed = await _refresh_token(
                    client=client,
                    discord_id=discord_id,
                    refresh_token=member["refresh_token"],
                )

                if not refreshed:
                    results["failed"].append({
                        "discord_id": discord_id,
                        "reason": "Token refresh failed.",
                    })
                    continue

                access_token = refreshed
                results["token_refreshed"].append(discord_id)

            # Attempt to add the member back to the guild
            success = await _add_member_to_guild(
                client=client,
                guild_id=guild_id,
                discord_id=discord_id,
                access_token=access_token,
            )

            if success:
                results["success"].append(discord_id)
            else:
                results["failed"].append({
                    "discord_id": discord_id,
                    "reason": "Failed to add to guild.",
                })

            # Small delay to avoid hitting Discord rate limits
            await asyncio.sleep(0.5)

    return jsonify({
        "guild_id": guild_id,
        "total": len(members),
        "restored": len(results["success"]),
        "failed": len(results["failed"]),
        "tokens_refreshed": len(results["token_refreshed"]),
        "details": results,
    }), 200


@restore_bp.get("/<guild_id>/status")
async def restore_status(guild_id: str):
    """
    Returns a summary of verified members for a guild —
    how many tokens are valid, expired, etc.
    Useful for checking the health of a guild before triggering restore.

    :param guild_id: The Discord guild ID.
    """
    stats = await _fetch_guild_stats(guild_id=guild_id)

    if stats is None:
        return jsonify({"error": "Failed to fetch guild stats."}), 500

    return jsonify({
        "guild_id": guild_id,
        "total_members": stats["total"],
        "valid_tokens": stats["valid"],
        "expired_tokens": stats["expired"],
    }), 200


async def _add_member_to_guild(
    client: httpx.AsyncClient,
    guild_id: str,
    discord_id: str,
    access_token: str,
) -> bool:
    """
    Call Discord's API to add a user back to a guild.

    :param client: The shared httpx client.
    :param guild_id: The Discord guild ID.
    :param discord_id: The Discord user ID.
    :param access_token: The user's OAuth access token.
    :return: True if successful, False otherwise.
    """
    try:
        response = await client.put(
            f"{DISCORD_API}/guilds/{guild_id}/members/{discord_id}",
            json={"access_token": access_token},
            headers={"Authorization": f"Bot {cfg.TOKEN}"},
        )

        # 201 = added, 204 = already in server (both are fine)
        return response.status_code in (201, 204)

    except Exception as e:
        logger.error(f"Failed to add {discord_id} to {guild_id}: {e}")
        return False


async def _refresh_token(
    client: httpx.AsyncClient,
    discord_id: str,
    refresh_token: str,
) -> str | None:
    """
    Use a refresh token to get a new access token from Discord,
    then update it in the database.

    :param client: The shared httpx client.
    :param discord_id: The Discord user ID.
    :param refresh_token: The stored refresh token.
    :return: The new access token, or None if refresh failed.
    """
    try:
        response = await client.post(
            DISCORD_TOKEN_URL,
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

        await _update_token(
            discord_id=discord_id,
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data["expires_in"],
        )

        return data["access_token"]

    except Exception as e:
        logger.error(f"Token refresh failed for {discord_id}: {e}")
        return None


@async_ensure_cursor
async def _fetch_members_with_tokens(guild_id: str, cursor: Cursor = None):
    """
    Fetch all members for a guild along with their tokens.
    Also returns a flag indicating whether each token is expired.

    :param guild_id: The Discord guild ID.
    :param cursor: The database cursor (injected by decorator).
    :return: List of member rows with token data.
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
        (guild_id,),
    )

    return cursor.fetchall()


@async_ensure_cursor
async def _fetch_guild_stats(guild_id: str, cursor: Cursor = None):
    """
    Get a count of total, valid, and expired tokens for a guild.

    :param guild_id: The Discord guild ID.
    :param cursor: The database cursor (injected by decorator).
    :return: Dict with total, valid, expired counts.
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
        (guild_id,),
    )

    return cursor.fetchone()


@async_ensure_cursor
async def _update_token(
    discord_id: str,
    access_token: str,
    refresh_token: str,
    expires_in: int,
    cursor: Cursor = None,
):
    """
    Update a user's tokens in the database after a refresh.

    :param discord_id: The Discord user ID.
    :param access_token: The new access token.
    :param refresh_token: The new refresh token.
    :param expires_in: Seconds until the new token expires.
    :param cursor: The database cursor (injected by decorator).
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
