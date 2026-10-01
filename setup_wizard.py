"""
Interactive Setup Wizard for Discord Bot
Helps users configure the bot without editing JSON files manually
"""
import json
import os
from pathlib import Path

def print_header():
    print("\n" + "="*60)
    print("  🤖 Discord Moderation Bot - Setup Wizard")
    print("="*60 + "\n")

def print_step(step: int, total: int, title: str):
    print(f"\n[{step}/{total}] {title}")
    print("-" * 40)

def get_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default value"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("⚠️  This field is required!")

def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes', 'ใช่']:
            return True
        if response in ['n', 'no', 'ไม่']:
            return False
        print("⚠️  Please enter 'y' or 'n'")

def setup_bot_token():
    """Step 1: Setup bot token"""
    print_step(1, 5, "Bot Token Configuration")
    print("\n📝 How to get your bot token:")
    print("1. Go to https://discord.com/developers/applications")
    print("2. Create a new application (or select existing)")
    print("3. Go to 'Bot' section")
    print("4. Click 'Reset Token' and copy it")
    print("\n⚠️  Keep your token secret! Never share it publicly.\n")

    token = get_input("Enter your bot token")

    # Save to .env file
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(f"DISCORD_TOKEN={token}\n")

    print("✅ Token saved to .env file")

def setup_guild():
    """Step 2: Setup guild (server) ID"""
    print_step(2, 5, "Server Configuration")
    print("\n📝 How to get your server ID:")
    print("1. Enable Developer Mode in Discord (Settings → Advanced)")
    print("2. Right-click on your server name")
    print("3. Click 'Copy Server ID'\n")

    guild_id = get_input("Enter your Discord server ID")

    return guild_id

def setup_channels():
    """Step 3: Setup channel IDs"""
    print_step(3, 5, "Channel Configuration")
    print("\n📝 How to get channel IDs:")
    print("1. Right-click on a channel")
    print("2. Click 'Copy Channel ID'\n")

    channels = {}

    print("Required channels:")
    channels['logs'] = get_input("  • Log channel ID (for moderation logs)")

    if get_yes_no("\nEnable ticket system?"):
        channels['tickets'] = get_input("  • Ticket creation channel ID")
        channels['ticket_logs'] = get_input("  • Ticket logs channel ID")
        channels['ticket_category'] = get_input("  • Ticket category ID")

    if get_yes_no("\nEnable application system?"):
        channels['applications'] = get_input("  • Application channel ID")
        channels['application_review'] = get_input("  • Application review channel ID")

    return channels

def setup_roles():
    """Step 4: Setup role IDs"""
    print_step(4, 5, "Role Configuration")
    print("\n📝 How to get role IDs:")
    print("1. Right-click on a role in Server Settings → Roles")
    print("2. Click 'Copy Role ID'\n")

    roles = {}

    print("Required roles:")
    roles['moderator'] = get_input("  • Moderator role ID")

    if get_yes_no("\nAdd support role?"):
        roles['support'] = get_input("  • Support role ID")

    if get_yes_no("\nAdd admin role?"):
        roles['admin'] = get_input("  • Admin role ID")

    return roles

def setup_automod():
    """Step 5: Setup auto-moderation"""
    print_step(5, 5, "Auto-Moderation Configuration")

    automod = {
        "enabled": get_yes_no("\nEnable auto-moderation?"),
        "banned_words": [],
        "punishments": {
            "first_offense": {
                "type": "mute",
                "duration": 60,
                "reason": "Use of prohibited words (1st offense)"
            },
            "second_offense": {
                "type": "mute_warn",
                "mute_duration": 180,
                "warn_duration": 10080,
                "reason": "Use of prohibited words (2nd offense)"
            },
            "third_offense": {
                "type": "ban",
                "reason": "Repeated use of prohibited words"
            }
        }
    }

    if automod['enabled']:
        print("\n📝 Enter banned words (one per line, empty line to finish):")
        while True:
            word = input("  • ").strip()
            if not word:
                break
            automod['banned_words'].append(word)

        if not automod['banned_words']:
            print("⚠️  No banned words added. You can edit config.json later to add them.")

    return automod

def create_config(guild_id, channels, roles, automod):
    """Create config.json file"""
    config = {
        "bot": {
            "prefix": get_input("\nBot command prefix", "?"),
            "description": "Discord moderation bot with tickets, warns, and auto-moderation"
        },
        "guild": {
            "id": guild_id
        },
        "channels": channels,
        "roles": roles,
        "automod": automod,
        "tickets": {
            "modal_title": "Ticket Request",
            "fields": [
                {
                    "label": "Minecraft Username",
                    "placeholder": "Enter your username",
                    "custom_id": "Username",
                    "required": True
                },
                {
                    "label": "Reason",
                    "placeholder": "Enter the reason",
                    "custom_id": "Reason",
                    "required": True
                },
                {
                    "label": "Quantity",
                    "placeholder": "Enter the quantity",
                    "custom_id": "Quantity",
                    "required": True
                },
                {
                    "label": "Type of Receipt/Contribution",
                    "placeholder": "Debt / Donation / Distribution",
                    "custom_id": "Type",
                    "required": True
                }
            ]
        },
        "applications": {
            "modal_title": "Ticket Request",
            "embed_description": "**Welcome!**\n\nClick the button below to submit a ticket.",
            "fields": [
                {
                    "label": "Minecraft Username",
                    "placeholder": "Enter your username",
                    "custom_id": "Username",
                    "required": True
                },
                {
                    "label": "Age",
                    "placeholder": "Enter your age",
                    "custom_id": "Age",
                    "required": True
                }
            ]
        }
    }

    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("\n✅ Configuration saved to config.json")

def main():
    """Run the setup wizard"""
    print_header()

    print("This wizard will help you configure your Discord bot.")
    print("You'll need:")
    print("  • Bot token from Discord Developer Portal")
    print("  • Server ID")
    print("  • Channel IDs")
    print("  • Role IDs")

    if not get_yes_no("\nReady to start?"):
        print("\n❌ Setup cancelled.")
        return

    # Check if config already exists
    if Path('config.json').exists():
        if not get_yes_no("\n⚠️  config.json already exists. Overwrite?", default=False):
            print("\n❌ Setup cancelled.")
            return

    try:
        # Run setup steps
        setup_bot_token()
        guild_id = setup_guild()
        channels = setup_channels()
        roles = setup_roles()
        automod = setup_automod()

        # Create config file
        create_config(guild_id, channels, roles, automod)

        # Success message
        print("\n" + "="*60)
        print("  ✅ Setup Complete!")
        print("="*60)
        print("\nYour bot is ready to run!")
        print("\nNext steps:")
        print("  1. Review config.json (optional)")
        print("  2. Install dependencies: pip install -r requirements.txt")
        print("  3. Run the bot: python main.py")
        print("\n📚 Need help? Check README.md for more information.\n")

    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Error during setup: {e}")
        print("Please try again or configure manually.")

if __name__ == "__main__":
    main()
