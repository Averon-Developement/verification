CREATE DATABASE averon;
USE averon;

CREATE TABLE IF NOT EXISTS settings (
    guild_id BIGINT PRIMARY KEY,
    role_id BIGINT NULL,
    logs_channel_id BIGINT NULL,
    dm_user BOOLEAN NOT NULL DEFAULT FALSE
)