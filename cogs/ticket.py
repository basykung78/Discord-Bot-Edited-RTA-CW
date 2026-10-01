import sqlite3
import disnake
import io
import asyncio
from disnake.ext import commands
from disnake.ui import View, Button
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.append(str(Path(__file__).parent.parent))
from config_loader import config

bot = commands.Bot(command_prefix="!", help_command=None, intents=disnake.Intents.all())
try:
    bot.test_guilds = [config.guild_id]
except ValueError:
    pass  # Will be handled by main.py

db = sqlite3.connect("database.db")
cursor = db.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS tickets (
        user_id INTEGER PRIMARY KEY,
        channel_id INTEGER,
        status INTEGER
    )
    """
)
db.commit()


# ==========================
# Ticket modal
# ==========================
class TicketModal(disnake.ui.Modal):
    def __init__(self, bot, inter):
        self.bot = bot
        self.inter = inter
        components = [
            disnake.ui.TextInput(label="Nickname in Minecraft", placeholder="Enter your nickname", custom_id="Nickname"),
            disnake.ui.TextInput(label="Reason", placeholder="Enter the reason", custom_id="Reason"),
            disnake.ui.TextInput(label="Amount", placeholder="Enter the amount", custom_id="Amount"),
            disnake.ui.TextInput(label="Type of Receipt/Contribution", placeholder="Debt / Donation / Distribution", custom_id="Type"),
        ]
        super().__init__(title="Application for Treasury", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        guild = inter.guild

        # Get role IDs from config with fallback
        try:
            support_role_id = config.get_role_id('support')
            mod_role_id = config.get_role_id('moderator')
            additional_1_id = config.get('roles.additional_support_1')
            additional_2_id = config.get('roles.additional_support_2')
        except ValueError as e:
            await inter.response.send_message(f"❌ Configuration error: {e}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            inter.author: disnake.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
        }

        # Add configured roles to overwrites
        if support_role_id:
            support_role = guild.get_role(int(support_role_id))
            if support_role:
                overwrites[support_role] = disnake.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)

        if additional_1_id:
            role_1 = guild.get_role(int(additional_1_id))
            if role_1:
                overwrites[role_1] = disnake.PermissionOverwrite(view_channel=True, send_messages=True)

        if mod_role_id:
            mod_role = guild.get_role(int(mod_role_id))
            if mod_role:
                overwrites[mod_role] = disnake.PermissionOverwrite(view_channel=True, send_messages=True)

        # Get category from config
        try:
            category_id = config.get_channel_id('ticket_category')
            category = guild.get_channel(category_id)
        except ValueError:
            category = None
        channel = await guild.create_text_channel(
            name=f"ticket-{inter.author.name}",
            overwrites=overwrites,
            category=category,
        )

        embed = disnake.Embed(title="Application for Treasury", color=disnake.Color.green())
        for key, value in inter.text_values.items():
            embed.add_field(name=key, value=value, inline=False)

        view = disnake.ui.View()
        view.add_item(Button(label="Close Ticket", style=disnake.ButtonStyle.red, custom_id="close_ticket"))

        await channel.send(content=f"{inter.author.mention}", embed=embed, view=view)

        cursor.execute("INSERT INTO tickets (user_id, channel_id, status) VALUES (?, ?, ?)", (inter.author.id, channel.id, 0))
        db.commit()

        await inter.response.send_message("Your ticket has been created!", ephemeral=True)


# ==========================
# Close confirmation
# ============================
class ConfirmCloseView(View):
    def __init__(self):
        super().__init__(timeout=30)
        self.add_item(Button(label="✅ Yes, close", style=disnake.ButtonStyle.red, custom_id="confirm_close"))
        self.add_item(Button(label="❌ Cancel", style=disnake.ButtonStyle.gray, custom_id="cancel_close"))


# ==========================
# Ticket management (after closure)
# ==========================
class ClosedTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="📂 Save Log", style=disnake.ButtonStyle.blurple, custom_id="save_log"))
        self.add_item(Button(label="♻️ Reopen", style=disnake.ButtonStyle.green, custom_id="reopen_ticket"))
        self.add_item(Button(label="🗑️ Delete", style=disnake.ButtonStyle.red, custom_id="delete_ticket"))


# ==========================
# Main cog
# ==========================
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🎟️ Create Ticket", style=disnake.ButtonStyle.green, custom_id="create_ticket"))


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    @bot.event
    async def on_ready(self):
        try:
            channel_id = config.get_channel_id('tickets')
            channel = self.bot.get_channel(channel_id)
        except ValueError:
            print("⚠️  Ticket channel not configured. Tickets system disabled.")
            return

        if channel:
            messages = await channel.history(limit=1).flatten()
            if not messages:
                view = TicketView()
                embed = disnake.Embed(
            title="Treasury",
            description="Click the button below to open a ticket.",
            color=disnake.Color.blurple()
        )
                await channel.send(embed=embed, view=view)
            else:
                print("Message 'ticket' already exists.")
        else:
            print("Channel not found.")


    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        guild = inter.guild
        user_id = inter.author.id

        # Ticket creation
        if inter.data.custom_id == "create_ticket":
            cursor.execute("SELECT * FROM tickets WHERE user_id=?", (user_id,))
            result = cursor.fetchone()
            if result:
                await inter.response.send_message("You already have an open ticket!", ephemeral=True)
                return

            modal = TicketModal(self.bot, inter)
            await inter.response.send_modal(modal)

        # Closing the ticket (initial click)
        elif inter.data.custom_id == "close_ticket":
            if inter.channel.name.startswith("ticket-"):
                view = ConfirmCloseView()
                await inter.response.send_message(
                    "Are you sure you want to close the ticket?",
                    view=view,
                    ephemeral=True
                )

        # Close confirmation
        elif inter.data.custom_id == "confirm_close":
            ticket_owner_id = cursor.execute("SELECT user_id FROM tickets WHERE channel_id=?", (inter.channel.id,)).fetchone()
            if ticket_owner_id:
                member = guild.get_member(ticket_owner_id[0])
                if member:
                    await inter.channel.set_permissions(member, overwrite=None)

            try:
                support_role_id = config.get_role_id('support')
                support_role = guild.get_role(int(support_role_id))
            except ValueError:
                support_role = None

            if support_role:
                await inter.channel.set_permissions(support_role, overwrite=None)

            cursor.execute("UPDATE tickets SET status=? WHERE channel_id=?", (1, inter.channel.id))
            db.commit()

            closed_embed = disnake.Embed(
                title="Ticket Closed",
                description="Moderation can save the log, reopen, or delete the channel.",
                color=disnake.Color.orange()
            )
            view = ClosedTicketView()
            await inter.channel.send(embed=closed_embed, view=view)
            await inter.response.edit_message(content="Ticket closed!", view=None)

        # Cancel close
        elif inter.data.custom_id == "cancel_close":
            await inter.response.edit_message(content="Ticket closure cancelled ❌", view=None)

        # Save log
        elif inter.data.custom_id == "save_log":
            try:
                log_channel_id = config.get_channel_id('ticket_logs')
                log_channel = guild.get_channel(log_channel_id)
            except ValueError:
                await inter.response.send_message("⚠️  Ticket log channel not configured", ephemeral=True)
                return

            messages = [
                f"[{m.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {m.author}: {m.content}"
                async for m in inter.channel.history(limit=None, oldest_first=True)
            ]
            log_text = "\n".join(messages) if messages else "No messages."

            file = disnake.File(io.StringIO(log_text), filename=f"{inter.channel.name}_log.txt")

            if log_channel:
                await log_channel.send(content=f"📂 Ticket Log {inter.channel.name}", file=file)
                await inter.response.send_message("Log saved and sent to the log channel.", ephemeral=True)

        # Reopen
        elif inter.data.custom_id == "reopen_ticket":
            ticket_owner_id = cursor.execute("SELECT user_id FROM tickets WHERE channel_id=?", (inter.channel.id,)).fetchone()
            if ticket_owner_id:
                member = guild.get_member(ticket_owner_id[0])
                if member:
                    await inter.channel.set_permissions(member, view_channel=True, send_messages=True)
            cursor.execute("UPDATE tickets SET status=? WHERE channel_id=?", (0, inter.channel.id))
            db.commit()

            await inter.response.send_message("Ticket reopened!", ephemeral=True)

        # Delete ticket
        elif inter.data.custom_id == "delete_ticket":
            cursor.execute("DELETE FROM tickets WHERE channel_id=?", (inter.channel.id,))
            db.commit()
            await inter.response.send_message("Ticket will be deleted in 5 seconds.", ephemeral=True)
            await asyncio.sleep(5)
            try:
                await inter.channel.delete(reason=f"Deleted by moderator {inter.author} ({inter.author.id})")
            except disnake.NotFound:
                pass


def setup(bot):
    bot.add_cog(Tickets(bot))
