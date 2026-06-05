class Colors:
    green: int = 0x89FF91
    red: int = 0xFE3641

colors = Colors()

class DiscordLinks:
    DISCORD_API: str = "https://discord.com/api/v10"
    DISCORD_OAUTH_URL: str = "https://discord.com/oauth2/authorize"
    DISCORD_TOKEN_URL: str = "https://discord.com/api/oauth2/token"
    SCOPES = "identify guilds.join"

disc = DiscordLinks()