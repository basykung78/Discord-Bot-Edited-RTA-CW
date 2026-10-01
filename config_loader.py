"""
Configuration loader for Discord Bot
Loads settings from config.json and environment variables
"""
import json
import os
from typing import Any, Dict
from pathlib import Path

class Config:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please copy config.json.example to config.json and configure it."
            )

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key (e.g., 'guild.id')"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    @property
    def bot_token(self) -> str:
        """Get bot token from environment variable"""
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError(
                "DISCORD_TOKEN not found in environment variables.\n"
                "Please create .env file with DISCORD_TOKEN=your_token_here"
            )
        return token

    @property
    def guild_id(self) -> int:
        """Get guild ID from config"""
        guild_id = self.get('guild.id')
        if not guild_id or guild_id == "YOUR_GUILD_ID_HERE":
            raise ValueError(
                "Guild ID not configured in config.json.\n"
                "Please set 'guild.id' to your Discord server ID."
            )
        return int(guild_id)

    @property
    def prefix(self) -> str:
        """Get bot command prefix"""
        return self.get('bot.prefix', '?')

    def get_channel_id(self, channel_key: str) -> int:
        """Get channel ID by key (e.g., 'logs', 'tickets')"""
        channel_id = self.get(f'channels.{channel_key}')
        if not channel_id or isinstance(channel_id, str) and channel_id.startswith('YOUR_'):
            raise ValueError(
                f"Channel '{channel_key}' not configured in config.json.\n"
                f"Please set 'channels.{channel_key}' to your channel ID."
            )
        return int(channel_id)

    def get_role_id(self, role_key: str) -> int:
        """Get role ID by key (e.g., 'moderator', 'admin')"""
        role_id = self.get(f'roles.{role_key}')
        if not role_id or isinstance(role_id, str) and role_id.startswith('YOUR_'):
            raise ValueError(
                f"Role '{role_key}' not configured in config.json.\n"
                f"Please set 'roles.{role_key}' to your role ID."
            )
        return int(role_id)

    @property
    def banned_words(self) -> list:
        """Get list of banned words for automod"""
        return self.get('automod.banned_words', [])

    def validate(self) -> bool:
        """Validate that all required config values are set"""
        required_checks = [
            ('guild.id', 'Guild ID'),
            ('channels.logs', 'Log Channel'),
            ('roles.moderator', 'Moderator Role'),
        ]

        errors = []
        for key, name in required_checks:
            value = self.get(key)
            if not value or (isinstance(value, str) and value.startswith('YOUR_')):
                errors.append(f"- {name} ({key})")

        if errors:
            print("\n⚠️  Configuration incomplete! Please set the following in config.json:")
            for error in errors:
                print(error)
            return False

        return True

# Global config instance
config = Config()
