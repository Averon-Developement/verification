import asyncio
import httpx

from quart import Blueprint, redirect, request, jsonify
from urllib.parse import urlencode

from core import cfg, logger
from core.database.handlers import VerifyHandler, SettingsHandler

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

    if not guild_id.isdigit():
        return jsonify({"error": "Invalid guild_id."}), 400

    params = urlencode({
        "client_id": cfg.DISCORD_CLIENT_ID,
        "redirect_uri": cfg.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": guild_id,
    })

    return redirect(f"{DISCORD_OAUTH_URL}?{params}")


@verify_bp.get("/callback")
async def callback():
    code = request.args.get("code")
    guild_id = request.args.get("state")

    if not code:
        return jsonify({"error": "No code provided by Discord."}), 400

    if not guild_id or not guild_id.isdigit():
        return jsonify({"error": "Invalid or missing guild_id in state."}), 400

    async with httpx.AsyncClient(timeout=10.0) as client:
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
            logger.error(f"Token exchange failed: {token_response.text}")
            return jsonify({"error": "Failed to exchange code for token."}), 500

        token_data = token_response.json()

        user_response = await client.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )

        if user_response.status_code != 200:
            logger.error(f"User fetch failed: {user_response.text}")
            return jsonify({"error": "Failed to fetch user info from Discord."}), 500

        user = user_response.json()
        discord_id = user["id"]

        # Save to DB
        handler = VerifyHandler()
        await handler.save_user(
            discord_id=discord_id,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data["expires_in"],
        )
        await handler.save_server_member(
            guild_id=guild_id,
            discord_id=discord_id,
        )

        # SettingsHandler is sync/blocking — run it in a thread
        settings = await asyncio.to_thread(
            SettingsHandler(int(guild_id)).get_settings
        )

        logger.info(f"Settings for {guild_id}: role_id={settings.role_id}, logs={settings.logs_channel_id}, dm={settings.dm_user}")

        # Add to guild via guilds.join scope
        join_response = await client.put(
            f"{DISCORD_API}/guilds/{guild_id}/members/{discord_id}",
            json={"access_token": token_data["access_token"]},
            headers={"Authorization": f"Bot {cfg.TOKEN}"},
        )
        logger.info(f"Guild join: {join_response.status_code} {join_response.text}")

        # Assign verification role
        if settings.role_id:
            role_response = await client.put(
                f"{DISCORD_API}/guilds/{guild_id}/members/{discord_id}/roles/{settings.role_id}",
                headers={
                    "Authorization": f"Bot {cfg.TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            logger.info(f"Role assign: {role_response.status_code} {role_response.text}")

            if role_response.status_code not in (204, 204):
                logger.error(f"Role assignment failed for {discord_id}: {role_response.status_code} {role_response.text}")
        else:
            logger.warning(f"No role_id configured for guild {guild_id}, skipping role assignment.")

        # Log to channel
        if settings.logs_channel_id:
            print() # do something here

        # DM user
        if settings.dm_user:
            print() # do something here

    return jsonify({"message": f"Successfully verified {user['username']}."}), 200