CREATE DATABASE IF NOT EXISTS verification;
USE verification;

CREATE TABLE IF NOT EXISTS servers (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    guild_id         BIGINT UNIQUE NOT NULL,
    owner_discord_id BIGINT NOT NULL,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    discord_id       BIGINT UNIQUE NOT NULL,
    access_token     TEXT NOT NULL,
    refresh_token    TEXT NOT NULL,
    token_expires_at DATETIME NOT NULL,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS server_members (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    guild_id    BIGINT NOT NULL,
    discord_id  BIGINT NOT NULL,
    verified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_member (guild_id, discord_id),
    FOREIGN KEY (guild_id) REFERENCES servers(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (discord_id) REFERENCES users(discord_id) ON DELETE CASCADE
);