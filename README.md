# Discord Moderation Bot

Multi-functional Discord bot with moderation tools, ticket system, warnings, and auto-moderation. Fully configurable for any Discord server.

## Features

- **Auto-Moderation** - Filter banned words with progressive punishments (mute → warn → ban)
- **Warning System** - Issue temporary warnings that automatically expire
- **Ticket System** - Create support tickets with custom modal forms
- **Application System** - Handle clan/guild applications with review workflow
- **Moderation Logging** - Track all moderation actions in dedicated log channel
- **Slash Commands** - Modern Discord slash command interface

## Installation

### Requirements

- Python 3.8+
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- Discord Server with Administrator permissions

### Quick Setup

1. **Clone the repository**
```bash
git clone https://github.com/Duke7z/Discord-Bot.git
cd Discord-Bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run setup wizard**
```bash
python setup_wizard.py
```

The wizard will guide you through:
- Bot token configuration
- Server ID setup
- Channel IDs (logs, tickets, applications)
- Role IDs (moderator, support, admin)
- Auto-moderation settings

4. **Start the bot**
```bash
python main.py
```

## Manual Configuration

If you prefer to configure manually:

1. **Create `.env` file**
```env
DISCORD_TOKEN=your_bot_token_here
```

2. **Copy and edit config**
```bash
cp config.json.example config.json
```

Edit `config.json` and replace all placeholder IDs with your server's IDs.

### Getting Discord IDs

1. Enable Developer Mode: `Settings → Advanced → Developer Mode`
2. Right-click on server/channel/role → `Copy ID`

## Configuration

### config.json Structure

```json
{
  "bot": {
    "prefix": "?",
    "description": "Bot description"
  },
  "guild": {
    "id": "YOUR_GUILD_ID"
  },
  "channels": {
    "logs": "LOG_CHANNEL_ID",
    "tickets": "TICKET_CHANNEL_ID",
    "applications": "APPLICATION_CHANNEL_ID"
  },
  "roles": {
    "moderator": "MOD_ROLE_ID",
    "support": "SUPPORT_ROLE_ID"
  },
  "automod": {
    "enabled": true,
    "banned_words": ["word1", "word2"]
  }
}
```

## Commands

### Moderation

- `/warn <user> <time> [reason]` - Issue warning to user
- `/unwarn <user> <warn_id>` - Remove warning from user
- `/warns [user]` - View warnings for user
- `/mute <user> <time> [reason]` - Mute user temporarily
- `/ban <user> [reason]` - Ban user from server

### Tickets

Users can create tickets through button interactions. Tickets are automatically managed with:
- Private channels with permissions
- Close/Reopen functionality
- Log export to text file
- Automatic cleanup

### Applications

Similar to tickets, but for clan/guild applications:
- Custom modal form
- Accept/Deny workflow
- Notification system

## Database

Bot uses SQLite for data persistence:
- `database.db` - Main database (tickets, applications, user data)
- `amod.db` - Auto-moderation infractions
- `warns.db` - Warning system (legacy, migrated to database.db)

## Development

### Project Structure

```
discord-bot/
├── main.py              # Bot entry point
├── config_loader.py     # Configuration loader
├── setup_wizard.py      # Interactive setup tool
├── config.json          # Bot configuration
├── .env                 # Bot token (not in repo)
├── cogs/
│   ├── AutoMod.py      # Auto-moderation
│   ├── warns_db.py     # Warning system
│   ├── ticket.py       # Ticket system
│   ├── modals.py       # Application system
│   ├── logs.py         # Logging system
│   └── slashcommands.py # Slash commands
└── requirements.txt
```

### Adding Cogs

Cogs are automatically loaded from the `cogs/` directory. To add a new cog:

1. Create `cogs/your_cog.py`
2. Define your cog class
3. Add `setup(bot)` function
4. Restart bot

## Troubleshooting

### Bot not responding
- Check bot token in `.env`
- Verify bot has proper permissions
- Check `config.json` for correct IDs

### Commands not showing
- Ensure `test_guilds` is set to your guild ID in `main.py`
- Wait a few minutes for Discord to sync commands
- Try re-inviting bot with proper scopes

### Permission errors
- Bot needs these permissions:
  - Manage Roles
  - Manage Channels
  - Kick Members
  - Ban Members
  - Moderate Members (timeout)
  - Read/Send Messages
  - Use Slash Commands

## Bot Permissions

When inviting the bot, use these permissions:
- Administrator (recommended for full functionality)

Or specifically:
- Manage Roles
- Manage Channels  
- Kick Members
- Ban Members
- Moderate Members
- Manage Messages
- Read Message History
- Use Slash Commands

Invite link format:
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=8&scope=bot%20applications.commands
```

## Security Notes

- **Never commit `.env` or `config.json` with real tokens/IDs**
- Keep your bot token secret
- Use environment variables for sensitive data
- Regularly review bot permissions

## License

MIT

## Author

Volodymyr Akimov · [GitHub](https://github.com/duke7z) · akimovvova7@gmail.com

## Support

If you encounter issues:
1. Check the Troubleshooting section
2. Review logs for error messages
3. Open an issue on GitHub with details

## Changelog

### v2.0.0 (2026-08-03)
- Complete refactor to support multiple servers
- Added interactive setup wizard
- Moved configuration to JSON + environment variables
- Removed hardcoded server/channel/role IDs
- Added comprehensive documentation
- Improved error handling

### v1.0.0
- Initial release
- Basic moderation features
