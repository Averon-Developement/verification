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

from ..utils import send_verification_log, render_error, render_result
from ..services import DiscordService


verify_bp = Blueprint(
    "verify",
    __name__,
    url_prefix="/verify"
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
            discord = DiscordService(client)

            token_data = await discord.exchange_code(code)

            if not token_data:
                return await render_error()

            user = await discord.get_user(
                token_data["access_token"]
            )

            if not user:
                return await render_error()

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
                member = await discord.get_member(
                    guild_id=guild_id,
                    discord_id=discord_id,
                )

                if member:
                    if str(settings.role_id) in member.get("roles", []):
                        return await render_result(
                            title="Already Verified",
                            description=(
                                "You are already verified. "
                                "If you believe this is a mistake, "
                                "please contact a server Administrator."
                            ),
                        )

            joined = await discord.add_member(
                guild_id=guild_id,
                discord_id=discord_id,
                access_token=token_data["access_token"],
            )

            if not joined:
                return await render_error()

            if settings.role_id:
                role_added = await discord.add_role(
                    guild_id=guild_id,
                    discord_id=discord_id,
                    role_id=settings.role_id,
                )

                if not role_added:
                    return await render_error()
                
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