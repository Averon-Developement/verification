from quart import Blueprint

from core.database.handlers import MemberHandler
from ..utils import apikey_required, success


members_bp = Blueprint(
    "members",
    __name__,
    url_prefix="/members"
)

members_bp.before_request(apikey_required)


@members_bp.get("/<guild_id>")
async def get_members(guild_id: str):
    members = await MemberHandler(guild_id).get_members()

    return success(
        data={
            "guild_id": guild_id,
            "count": len(members),
            "members": [
                {
                    "discord_id": member.discord_id,
                    "verified_at": str(member.verified_at),
                }
                for member in members
            ],
        },
        status=200,
    )


@members_bp.delete("/<guild_id>/<discord_id>")
async def delete_member(guild_id: str, discord_id: str):
    await MemberHandler(guild_id).remove_member(discord_id)

    return success(
        data={
            "message": (
                f"Deleted data for {discord_id} "
                f"in guild {guild_id}."
            )
        },
        status=200,
    )