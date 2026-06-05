from quart import Blueprint, jsonify

from core.database import async_ensure_cursor, Cursor


members_bp = Blueprint("members", __name__, url_prefix="/members")


@members_bp.get("/<guild_id>")
async def get_members(guild_id: str):
    members = await _fetch_members(guild_id=guild_id)

    if members is None:
        return jsonify({"error": "Failed to fetch members."}), 500

    return jsonify({
        "guild_id": guild_id,
        "count": len(members),
        "members": members,
    }), 200


@members_bp.delete("/<guild_id>/<discord_id>")
async def delete_member(guild_id: str, discord_id: str):
    await _remove_member(guild_id=guild_id, discord_id=discord_id)

    return jsonify({
        "message": f"Deleted data for {discord_id} in guild {guild_id}."
    }), 200


@async_ensure_cursor
async def _fetch_members(guild_id: str, cursor: Cursor = None):
    cursor.execute(
        """
        SELECT u.discord_id, sm.verified_at
        FROM server_members sm
        JOIN users u ON u.discord_id = sm.discord_id
        WHERE sm.guild_id = %s
        """,
        (guild_id,),
    )

    return cursor.fetchall()


@async_ensure_cursor
async def _remove_member(guild_id: str, discord_id: str, cursor: Cursor = None):
    cursor.execute(
        "DELETE FROM server_members WHERE guild_id = %s AND discord_id = %s",
        (guild_id, discord_id),
    )

    # Clean up the user entirely if they're no longer in any server
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
