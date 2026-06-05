import httpx

from core import cfg, logger, colors, disc

async def send_verification_log(
    client: httpx.AsyncClient,
    channel_id: int,
    user: dict,
    role_id: int | None = None,
) -> bool:
    """
    Send a verification log message to a Discord channel.

    :param client: The HTTP client used for the request.
    :param channel_id: The ID of the channel to send the log to.
    :param user: The verified user's Discord data.
    :param role_id: The role granted to the user, if any.
    :return: Whether the log message was sent successfully.
    """
    role_text = ""
    if role_id:
        role_text = (
            f"> Granted role: <@&{role_id}> `({role_id})`"
        )

    response = await client.post(
        f"{disc.DISCORD_API}/channels/{channel_id}/messages",
        headers={
            "Authorization": f"Bot {cfg.TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "flags": 32768,
            "allowed_mentions": {
                "parse": [],
            },
            "components": [
                {
                    "type": 17,
                    "accent_color": colors.green,
                    "components": [
                        {
                            "type": 10,
                            "content": (
                                "## Verification Log\n"
                                f"<@{user['id']}> has completed "
                                "verification successfully.\n\n"
                                f"-# User ID: {user['id']}"
                            ),
                        },
                        {
                            "type": 14,
                        },
                        {
                            "type": 10,
                            "content": (
                                f"{role_text}"
                            ),
                        },
                    ],
                }
            ],
        },
    )

    if response.status_code not in (200, 201):
        logger.error(
            "Failed to send verification log: %s %s",
            response.status_code,
            response.text,
        )
        return False

    return True