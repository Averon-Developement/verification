import asyncio
import httpx

from quart import Blueprint, jsonify, request

from core import cfg
from core.database.handlers import RestoreHandler
from ..utils import refresh_token, add_member_to_guild


restore_bp = Blueprint("restore", __name__, url_prefix="/restore")


@restore_bp.before_request
async def auth():
    if request.headers.get("X-API-Key") != cfg.API_KEY:
        return jsonify({"error": "Unauthorized"}), 401


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
                refreshed = await refresh_token(
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

            success = await add_member_to_guild(
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