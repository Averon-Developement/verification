import asyncio
from urllib.parse import urlencode

import httpx
from quart import (
    Blueprint,
    redirect,
    render_template,
    request
)

from core import cfg, logger, disc
from core.database.handlers import SettingsHandler, VerifyHandler

from ..utils import send_verification_log


verify_bp = Blueprint(
    "verify",
    __name__,
    url_prefix="/verify"
)


async def render_result(title: str, description: str, status: int = 200):
    return await render_template("result.html", title=title, description=description), status


async def render_error():
    return await render_result(
        title="Verification Failed",
        description="Something went wrong. If this issue persists, please contact a server Administrator.",
        status=400,
    )


@verify_bp.get("/")
async def verify():
    guild_id = request.args.get("guild_id")

    if not guild_id:
        logger.error("Missing guild_id parameter")
        return await render_error()

    if not guild_id.isdigit():
        logger.error("Invalid guild_id parameter")
        return await render_error()

    params = urlencode(
        {
            "client_id": cfg.DISCORD_CLIENT_ID,
            "redirect_uri": cfg.DISCORD_REDIRECT_URI,
            "response_type": "code",
            "scope": disc.SCOPES,
            "state": guild_id,
        }
    )

    return redirect(f"{disc.DISCORD_OAUTH_URL}?{params}")


@verify_bp.get("/callback")
async def callback():
    try:
        code = request.args.get("code")
        guild_id = request.args.get("state")

        if not code:
            logger.error("No code provided by Discord")
            return await render_error()

        if not guild_id or not guild_id.isdigit():
            logger.error("Invalid or missing guild_id in state")
            return await render_error()

        async with httpx.AsyncClient(timeout=10.0) as client:
            token_response = await client.post(
                disc.DISCORD_TOKEN_URL,
                data={
                    "client_id": cfg.DISCORD_CLIENT_ID,
                    "client_secret": cfg.DISCORD_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": cfg.DISCORD_REDIRECT_URI,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
            )

            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                return await render_error()

            token_data = token_response.json()

            user_response = await client.get(
                f"{disc.DISCORD_API}/users/@me",
                headers={
                    "Authorization": f"Bearer {token_data['access_token']}"
                },
            )

            if user_response.status_code != 200:
                logger.error(f"User fetch failed: {user_response.text}")
                return await render_error()

            user = user_response.json()
            discord_id = user["id"]

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

            settings = await asyncio.to_thread(
                SettingsHandler(int(guild_id)).get_settings
            )

            if settings.role_id:
                member_response = await client.get(
                    f"{disc.DISCORD_API}/guilds/{guild_id}/members/{discord_id}",
                    headers={
                        "Authorization": f"Bot {cfg.TOKEN}"
                    },
                )

                if member_response.status_code == 200:
                    member = member_response.json()

                    if str(settings.role_id) in member.get("roles", []):
                        return await render_result(
                            title="Already Verified",
                            description="You are already verified. If you believe this is a mistake, please contact a server Administrator.",
                        )

            join_response = await client.put(
                f"{disc.DISCORD_API}/guilds/{guild_id}/members/{discord_id}",
                json={
                    "access_token": token_data["access_token"]
                },
                headers={
                    "Authorization": f"Bot {cfg.TOKEN}"
                },
            )

            if join_response.status_code not in (201, 204):
                logger.error(
                    "Guild join failed: %s %s",
                    join_response.status_code,
                    join_response.text,
                )
                return await render_error()

            if settings.role_id:
                role_response = await client.put(
                    (
                        f"{disc.DISCORD_API}/guilds/{guild_id}"
                        f"/members/{discord_id}"
                        f"/roles/{settings.role_id}"
                    ),
                    headers={
                        "Authorization": f"Bot {cfg.TOKEN}",
                        "Content-Type": "application/json",
                    },
                )

                if role_response.status_code != 204:
                    logger.error(
                        f"Role assignment failed for {discord_id}: {role_response.status_code} {role_response.text}"
                    )
                    return await render_error()

            if settings.logs_channel_id:
                await send_verification_log(
                    client=client,
                    channel_id=settings.logs_channel_id,
                    user=user,
                    role_id=settings.role_id,
                )

            if settings.dm_user:
                pass

            return await render_result(
                title="Successfully Verified",
                description="You may now return back to Discord.",
            )

    except Exception:
        logger.exception("Unhandled verification error")
        return await render_error()