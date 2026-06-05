import asyncio
import httpx

from quart import Blueprint, jsonify

from core import cfg, logger
from core.database.handlers import RestoreHandler


restore_bp = Blueprint("restore", __name__, url_prefix="/restore")

DISCORD_API = "https://discord.com/api/v10"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"


@restore_bp.post("/<guild_id>")
async def restore(guild_id: str):
    handler = RestoreHandler(guild_id)
    members = await handler.get_members_with_tokens()

    if not members:
        return jsonify({"error": "No verified members found for this guild."}), 404

    results = {"success": [], "failed": [], "token_refreshed": []}

    async with httpx.AsyncClient() as client:
        for member in members:
            access_token = member.access_token

            if member.token_expired:
                refreshed = await _refresh_token(
                    client=client,
                    handler=handler,
                    discord_id=member.discord_id,
                    refresh_token=member.refresh_token,
                )

                if not refreshed:
                    results["failed"].append({
                        "discord_id": member.discord_id,
                        "reason": "Token refresh failed.",
                    })
                    continue

                access_token = refreshed
                results["token_refreshed"].append(member.discord_id)

            success = await _add_member_to_guild(
                client=client,
                guild_id=guild_id,
                discord_id=member.discord_id,
                access_token=access_token,
            )

            if success:
                results["success"].append(member.discord_id)
            else:
                results["failed"].append({
                    "discord_id": member.discord_id,
                    "reason": "Failed to add to guild.",
                })

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
    stats = await RestoreHandler(guild_id).get_guild_stats()

    if stats is None:
        return jsonify({"error": "Failed to fetch guild stats."}), 500

    return jsonify({
        "guild_id": guild_id,
        "total_members": stats.total,
        "valid_tokens": stats.valid,
        "expired_tokens": stats.expired,
    }), 200


async def _add_member_to_guild(
    client: httpx.AsyncClient,
    guild_id: str,
    discord_id: str,
    access_token: str,
) -> bool:
    try:
        response = await client.put(
            f"{DISCORD_API}/guilds/{guild_id}/members/{discord_id}",
            json={"access_token": access_token},
            headers={"Authorization": f"Bot {cfg.TOKEN}"},
        )
        return response.status_code in (201, 204)

    except Exception as e:
        logger.error(f"Failed to add {discord_id} to {guild_id}: {e}")
        return False


async def _refresh_token(
    client: httpx.AsyncClient,
    handler: RestoreHandler,
    discord_id: str,
    refresh_token: str,
) -> str | None:
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