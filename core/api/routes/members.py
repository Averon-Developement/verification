from quart import Blueprint, jsonify, request

from core import cfg
from core.database.handlers import MemberHandler


members_bp = Blueprint("members", __name__, url_prefix="/members")


@members_bp.before_request
async def auth():
    if request.headers.get("X-API-Key") != cfg.API_KEY:
        return jsonify({"error": "Unauthorized"}), 401


@members_bp.get("/<guild_id>")
async def get_members(guild_id: str):
    members = await MemberHandler(guild_id).get_members()

    return jsonify({
        "guild_id": guild_id,
        "count": len(members),
        "members": [{
            "discord_id": m.discord_id,
            "verified_at": str(m.verified_at)
        } for m in members],
    }), 200


@members_bp.delete("/<guild_id>/<discord_id>")
async def delete_member(guild_id: str, discord_id: str):
    await MemberHandler(guild_id).remove_member(discord_id)

    return jsonify({
        "message": f"Deleted data for {discord_id} in guild {guild_id}."
    }), 200