import asyncio
import httpx

from quart import Blueprint

from core.database.handlers import RestoreHandler
from ..utils import (
    apikey_required,
    success,
    error
)
from ..services import DiscordService


restore_bp = Blueprint(
    "restore",
    __name__,
    url_prefix="/restore"
)

restore_bp.before_request(apikey_required)


@restore_bp.post("/<guild_id>")
async def restore(guild_id: str):
    handler = RestoreHandler(guild_id)
    members = await handler.get_members_with_tokens()

    if not members:
        return error(
            data={"error": "No verified members found for this guild."},
            status=404
        )

    results = {
        "success": [],
        "failed": [],
        "token_refreshed": [],
    }

    async with httpx.AsyncClient() as client:
        discord = DiscordService(client)

        for member in members:
            access_token = member.access_token

            if member.token_expired:
                token_data = await discord.refresh_token(
                    member.refresh_token
                )

                if not token_data:
                    results["failed"].append({
                        "discord_id": member.discord_id,
                        "reason": "Token refresh failed.",
                    })
                    continue

                await handler.update_token(
                    discord_id=member.discord_id,
                    access_token=token_data["access_token"],
                    refresh_token=token_data["refresh_token"],
                    expires_in=token_data["expires_in"],
                )

                access_token = token_data["access_token"]

                results["token_refreshed"].append(
                    member.discord_id
                )

            added = await discord.add_member(
                guild_id=guild_id,
                discord_id=member.discord_id,
                access_token=access_token,
            )

            if added:
                results["success"].append(
                    member.discord_id
                )
            else:
                results["failed"].append({
                    "discord_id": member.discord_id,
                    "reason": "Failed to add to guild.",
                })

            await asyncio.sleep(0.5)

    return success(
        data={
            "guild_id": guild_id,
            "total": len(members),
            "restored": len(results["success"]),
            "failed": len(results["failed"]),
            "tokens_refreshed": len(results["token_refreshed"]),
            "details": results,
        },
        status=200,
    )


@restore_bp.get("/<guild_id>/status")
async def restore_status(guild_id: str):
    stats = await RestoreHandler(guild_id).get_guild_stats()

    if stats is None:
        return error(
            data={"error": "Failed to fetch guild stats."},
            status=500
        )

    return success(
        data={
            "guild_id": guild_id,
            "total_members": stats.total,
            "valid_tokens": stats.valid,
            "expired_tokens": stats.expired,
        },
        status=200
    )