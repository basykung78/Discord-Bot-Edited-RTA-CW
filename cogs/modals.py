import sqlite3
import disnake
from disnake.ext import commands
from disnake import ButtonStyle
from disnake.ui import View, Button, Select, role_select
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.append(str(Path(__file__).parent.parent))
from config_loader import config

bot = commands.Bot(command_prefix="!", help_command=None, intents=disnake.Intents.all())
db = sqlite3.connect("database.db")
cursor = db.cursor()

class InviteButton(View):
  def __init__(self):

    super().__init__()

    self.add_item(Button(style=ButtonStyle.green, label="Send Application", custom_id="create"))
    self.add_item(Button(style=ButtonStyle.red, label="Delete", custom_id="delete"))

class AcceptButton(View):
  def __init__(self):
    super().__init__()
    self.add_item(Button(style=ButtonStyle.green, emoji="✔", custom_id="accept"))
    self.add_item(Button(style=ButtonStyle.red, emoji="❌", custom_id="deny"))

class Invite(disnake.ui.Modal, commands.Cog):

  def __init__(self, bot, channel_id=None):
    self.bot = bot
    self.channel_id = channel_id
    self.messid = {}
    components = [
      disnake.ui.TextInput(
        label="Name In Roblox",
        placeholder="Enter your nickname",
        custom_id="Nickname"
      ),
      disnake.ui.TextInput(
        label="Age",
        placeholder="Enter your age",
        custom_id="Age",
      ),
      disnake.ui.TextInput(
        label="Game Experience on Private Servers",
        placeholder="Write where you played and for how long",
        custom_id="Game Experience on Private Servers",
      ),
      disnake.ui.TextInput(
        label="What do you like to do in the game and in life?",
        placeholder="Describe your gaming and life interests, if building then attach screenshots",
        custom_id="What do you like to do in the game and in life?",
        style=disnake.TextInputStyle.paragraph
      ),
      disnake.ui.TextInput(
        label="What do you expect from the clan?",
        placeholder="Write what you want (friendly community, high activity, project implementation, self-realization, etc.)",
        custom_id="What do you expect from the clan?",
        style=disnake.TextInputStyle.paragraph
      ),

    ]

    super().__init__(
      title="Application to the Clan",
      components=components
    )

  @commands.Cog.listener()
  @bot.event
  async def on_ready(self):
    try:
      channel_id = config.get_channel_id('applications')
      channel = self.bot.get_channel(channel_id)
    except ValueError:
      print("⚠️  Application channel not configured. Applications system disabled.")
      return

    if channel:
      messages = await channel.history(limit=1).flatten()
      if not messages:
          view = InviteButton()
          embed = disnake.Embed(title="Send Application", description="""**Welcome.** 

If you want to join the clan without doing anything, go to the voice channels or you can choose not to submit an application, you won't last long with us.

But if you still want to join, click the green button **"Send Application"** and fill in the required fields.

""", color=disnake.Color.green())


          await channel.send(embed=embed, view=view)
      else:
          print("The 'modals' message already exists.")
    else:
      print("Channel not found.")

  @commands.Cog.listener()
  @bot.event
  async def on_button_click(self, inter):
    if isinstance(inter, disnake.MessageInteraction):
      data = inter.data
      custom_id = data.get("custom_id")
      if custom_id == "create":
        cursor.execute(
          """
          CREATE TABLE IF NOT EXISTS anketa (
          user_id INTEGER PRIMARY KEY,
          message_id INTEGER,
          status INTEGER,
          FOREIGN KEY (user_id) REFERENCES users (user_id)
          )
          """
        )
        user_id = inter.author.id
        cursor.execute("SELECT user_id FROM anketa WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        if result:
          await inter.response.send_message("You have already submitted your application.", ephemeral=True)
        else:
          modal = Invite(bot)
          await inter.response.send_modal(modal=modal)
      elif custom_id == "delete":
        user = inter.author
        cursor.execute("SELECT message_id, status FROM anketa WHERE user_id=?", (user.id,))
        result = cursor.fetchone()

        if result:
          status = result[1]
          if status != 0:
            await inter.response.send_message("You cannot delete your application as it has already been reviewed.", ephemeral=True)
          else:
            message_id = result[0]
            try:
              review_channel_id = config.get_channel_id('application_review')
              channel = inter.guild.get_channel(review_channel_id)
            except ValueError:
              await inter.response.send_message("⚠️  Review channel not configured", ephemeral=True)
              return

            message = await channel.fetch_message(message_id)
            cursor.execute("DELETE FROM anketa WHERE user_id=?", (user.id,))
            db.commit()
            await message.delete()
            await inter.response.send_message("Application successfully deleted.", ephemeral=True)
        else:
          await inter.response.send_message("Application not found.", ephemeral=True)

      elif custom_id == "accept":
        try:
          admin_role_id = config.get_role_id('admin')
          mod_role_id = config.get_role_id('moderator')
          allowed_roles = [int(admin_role_id), int(mod_role_id)]
        except ValueError:
          allowed_roles = []

        if not any(role.id in allowed_roles for role in inter.author.roles):
          await inter.response.send_message("You do not have permission to review applications.", ephemeral=True)
          return

        cursor.execute("UPDATE anketa SET status=? WHERE message_id=?", (1, inter.message.id))
        db.commit()

        new_embed = inter.message.embeds[0]
        new_embed.color = disnake.Color.green()
        new_embed.add_field(name="Status", value="✅ Approved", inline=False)

        await inter.message.edit(embed=new_embed, view=None)
        await inter.response.send_message("Application approved!", ephemeral=True)

      elif custom_id == "deny":
        try:
          admin_role_id = config.get_role_id('admin')
          mod_role_id = config.get_role_id('moderator')
          allowed_roles = [int(admin_role_id), int(mod_role_id)]
        except ValueError:
          allowed_roles = []

        if not any(role.id in allowed_roles for role in inter.author.roles):
          await inter.response.send_message("You do not have permission to review applications.", ephemeral=True)
          return

        cursor.execute("UPDATE anketa SET status=? WHERE message_id=?", (2, inter.message.id))
        db.commit()

        new_embed = inter.message.embeds[0]
        new_embed.color = disnake.Color.red()
        new_embed.add_field(name="Status", value="❌ Denied", inline=False)

        await inter.message.edit(embed=new_embed, view=None)
        await inter.response.send_message("Application denied!", ephemeral=True)

  async def callback(self, inter: disnake.Interaction):
    embed = disnake.Embed(title="Application for Clan", color=disnake.Color.dark_gold())
    view = AcceptButton()
    status=0
    for key, value in inter.text_values.items():
      embed.add_field(name=key.capitalize(), value=value, inline=False)
    embed.add_field(
      name="Applicant:",
      value=f"{inter.author.mention}",
    )
    await inter.response.send_message('Application submitted! Please wait for an administrator to review it.', ephemeral=True)
    guild = inter.guild

    try:
      review_channel_id = config.get_channel_id('application_review')
      admin_role_id = config.get_role_id('admin')
      channel = guild.get_channel(review_channel_id)
      admin_role = guild.get_role(int(admin_role_id))
    except ValueError as e:
      print(f"⚠️  Configuration error: {e}")
      return

    if channel:
      mention = admin_role.mention if admin_role else ""
      sent = await channel.send(content=mention, embed=embed, view=view)
      cursor.execute("INSERT INTO anketa (user_id, message_id, status) VALUES (?, ?, ?)", (inter.author.id, sent.id, status))
      db.commit()
    else:
      print("Log channel not found!")



def setup(bot):
  bot.add_cog(Invite(bot))