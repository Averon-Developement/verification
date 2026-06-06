import httpx

from core import cfg, disc, logger, colors


class DiscordService:
    """
    Wrapper around the Discord API.
    """
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @property
    def bot_headers(self) -> dict:
        """
        Get bot authorization headers.
        """
        return {
            "Authorization": f"Bot {cfg.TOKEN}",
        }

    @staticmethod
    def bearer_headers(token: str) -> dict:
        """
        Create bearer authorization headers.

        :param token: The OAuth access token.
        :return: Authorization headers.
        """
        return {
            "Authorization": f"Bearer {token}",
        }

    async def exchange_code(self, code: str) -> dict | None:
        """
        Exchange an OAuth authorization code for tokens.

        :param code: The OAuth authorization code.
        :return: The token response, if successful.
        """
        try:
            response = await self.client.post(
                disc.DISCORD_TOKEN_URL,
                data={
                    "client_id": cfg.DISCORD_CLIENT_ID,
                    "client_secret": cfg.DISCORD_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": cfg.DISCORD_REDIRECT_URI,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if response.status_code != 200:
                logger.error(
                    "Token exchange failed: %s",
                    response.text,
                )
                return None

            return response.json()

        except Exception:
            logger.exception("Failed to exchange OAuth code")
            return None

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> dict | None:
        """
        Refresh an OAuth access token.

        :param refresh_token: The OAuth refresh token.
        :return: The token response, if successful.
        """
        try:
            response = await self.client.post(
                disc.DISCORD_TOKEN_URL,
                data={
                    "client_id": cfg.DISCORD_CLIENT_ID,
                    "client_secret": cfg.DISCORD_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if response.status_code != 200:
                logger.error(
                    "Token refresh failed: %s",
                    response.text,
                )
                return None

            return response.json()

        except Exception:
            logger.exception("Failed to refresh token")
            return None

    async def get_user(
        self,
        access_token: str,
    ) -> dict | None:
        """
        Get the authenticated Discord user.

        :param access_token: The OAuth access token.
        :return: The Discord user payload, if successful.
        """
        try:
            response = await self.client.get(
                f"{disc.DISCORD_API}/users/@me",
                headers=self.bearer_headers(access_token),
            )

            if response.status_code != 200:
                logger.error(
                    "Failed to fetch user: %s",
                    response.text,
                )
                return None

            return response.json()

        except Exception:
            logger.exception("Failed to get user")
            return None

    async def get_member(
        self,
        guild_id: str,
        discord_id: str,
    ) -> dict | None:
        """
        Get a guild member.

        :param guild_id: The Discord guild ID.
        :param discord_id: The Discord ID of the user.
        :return: The guild member payload, if found.
        """
        try:
            response = await self.client.get(
                f"{disc.DISCORD_API}/guilds/{guild_id}/members/{discord_id}",
                headers=self.bot_headers,
            )

            if response.status_code != 200:
                return None

            return response.json()

        except Exception:
            logger.exception(
                "Failed to fetch member %s in guild %s",
                discord_id,
                guild_id,
            )
            return None

    async def add_member(
        self,
        guild_id: str,
        discord_id: str,
        access_token: str,
    ) -> bool:
        """
        Add a user to a guild.

        :param guild_id: The Discord guild ID.
        :param discord_id: The Discord ID of the user.
        :param access_token: The user's OAuth access token.
        :return: Whether the user was added successfully.
        """
        try:
            response = await self.client.put(
                f"{disc.DISCORD_API}/guilds/{guild_id}/members/{discord_id}",
                json={
                    "access_token": access_token,
                },
                headers=self.bot_headers,
            )

            return response.status_code in (201, 204)

        except Exception:
            logger.exception(
                "Failed to add %s to guild %s",
                discord_id,
                guild_id,
            )
            return False

    async def add_role(
        self,
        guild_id: str,
        discord_id: str,
        role_id: int,
    ) -> bool:
        """
        Assign a role to a guild member.

        :param guild_id: The Discord guild ID.
        :param discord_id: The Discord ID of the user.
        :param role_id: The role ID to assign.
        :return: Whether the role was assigned successfully.
        """
        try:
            response = await self.client.put(
                (
                    f"{disc.DISCORD_API}/guilds/{guild_id}"
                    f"/members/{discord_id}"
                    f"/roles/{role_id}"
                ),
                headers={
                    **self.bot_headers,
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 204:
                logger.error(
                    "Role assignment failed for %s: %s %s",
                    discord_id,
                    response.status_code,
                    response.text,
                )
                return False

            return True

        except Exception:
            logger.exception(
                "Failed to assign role %s to %s",
                role_id,
                discord_id,
            )
            return False
        
    async def get_guild(
        self,
        guild_id: str,
    ) -> dict | None:
        """
        Get a guild.

        :param guild_id: The Discord guild ID.
        :return: The guild payload, if found.
        """
        response = await self.client.get(
            f"{disc.DISCORD_API}/guilds/{guild_id}",
            headers=self.bot_headers,
        )

        if response.status_code != 200:
            return None

        return response.json()