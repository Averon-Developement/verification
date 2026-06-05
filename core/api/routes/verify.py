import httpx

from quart import Blueprint, redirect, request, jsonify

from core import cfg
from core.database import async_ensure_cursor, Cursor


verify_bp = Blueprint("verify", __name__, url_prefix="/verify")

DISCORD_API = "https://discord.com/api/v10"
DISCORD_OAUTH_URL = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"

SCOPES = "identify guilds.join"


@verify_bp.get("/")
async def verify():
    guild_id = request.args.get("guild_id")

    if not guild_id:
        return jsonify({"error": "Missing guild_id parameter."}), 400

    params = (
        f"?client_id={cfg.DISCORD_CLIENT_ID}"
        f"&redirect_uri={cfg.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPES.replace(' ', '%20')}"
        f"&state={guild_id}"
    )

    return redirect(DISCORD_OAUTH_URL + params)


@verify_bp.get("/callback")
async def callback():
    code = request.args.get("code")
    guild_id = request.args.get("state")

    if not code:
        return jsonify({"error": "No code provided by Discord."}), 400

    if not guild_id:
        return jsonify({"error": "No guild_id in state parameter."}), 400

    async with httpx.AsyncClient() as client:
        # Swap the temporary code for a real access + refresh token
        token_response = await client.post(
            DISCORD_TOKEN_URL,
            data={
                "client_id": cfg.DISCORD_CLIENT_ID,
                "client_secret": cfg.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": cfg.DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_response.status_code != 200:
            return jsonify({"error": "Failed to exchange code for token."}), 500

        token_data = token_response.json()

        # Use the access token to fetch the users Discord info
        user_response = await client.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )

        if user_response.status_code != 200:
            return jsonify({"error": "Failed to fetch user info from Discord."}), 500

        user = user_response.json()

    discord_id = user["id"]

    # Save tokens and link user to the guild
    await _save_user(
        discord_id=discord_id,
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        expires_in=token_data["expires_in"],
    )

    await _save_server_member(
        guild_id=guild_id,
        discord_id=discord_id,
    )

    return jsonify({"message": f"Successfully verified {user['username']}."}), 200


@async_ensure_cursor
async def _save_user(
    discord_id: str,
    access_token: str,
    refresh_token: str,
    expires_in: int,
    cursor: Cursor = None,
):
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
async def _save_server_member(
    guild_id: str,
    discord_id: str,
    cursor: Cursor = None,
):
    cursor.execute(
        """
        INSERT IGNORE INTO servers (guild_id, owner_discord_id)
        VALUES (%s, %s)
        """,
        (guild_id, discord_id),
    )

    # Link the user to the guild
    cursor.execute(
        """
        INSERT IGNORE INTO server_members (guild_id, discord_id)
        VALUES (%s, %s)
        """,
        (guild_id, discord_id),
    )