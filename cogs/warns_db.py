import disnake
from disnake.ext import commands
import sqlite3
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.append(str(Path(__file__).parent.parent))
from config_loader import config

bot = commands.Bot(command_prefix="!", help_command=None, intents=disnake.Intents.all())
db = sqlite3.connect("database.db")
cursor = db.cursor()
scheduler = AsyncIOScheduler()
moderators = {}

class warndb(commands.Cog):
    cog_name = "❗ Warns"
    def __init__(self, bot):
        self.bot = bot

    async def remove_warn(self, user_id, warn_id, expires_at):
        print(f"Removing warn for user {user_id}, warn_id {warn_id}")  # Debug output
        user = self.bot.get_user(user_id)
        cursor.execute("SELECT reason, moder_id FROM warns WHERE user_id=? AND warn_id=?", (user_id, warn_id))
        result = cursor.fetchone()
        if result:
            reason = result[0]
            moderator_id = result[1]
            moderator = self.bot.get_user(moderator_id)
            embed = disnake.Embed(
                title="🌦️ | Warning expired",
                description=f"The warning for user {user.name}({user.mention}) has expired.",
                color=disnake.Color.brand_green(),
            )
            embed.add_field(
                name="Moderator",
                value=f"{moderator.name}({moderator.mention})",
                inline=False
            )
            embed.add_field(
                name="Warning reason",
                value=f"{reason}",
                inline=False
            )
            embed.add_field(
                name="Warning number",
                value=f"{warn_id}",
                inline=False
            )
            embed.set_footer(
                text=f"Member ID: {user.id}",
                icon_url=user.display_avatar
            )
            try:
                log_channel_id = config.get_channel_id('logs')
                log_channel = self.bot.get_channel(log_channel_id)
            except ValueError:
                print("⚠️  Warning: Log channel not configured in config.json")
                log_channel = None

            if log_channel:
                await log_channel.send(embed=embed)
            else:
                print("Log channel not found!")
        cursor.execute("DELETE FROM warns WHERE user_id=? AND warn_id=?", (user_id, warn_id))
        db.commit()
        job_id = f"unwarn_{user_id}_{warn_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        else:
            pass

    async def setup_timers(self):
        cursor.execute("SELECT user_id, warn_id, expires_at, timer_id FROM warns")
        results = cursor.fetchall()
        for user_id, warn_id, expires_at, timer_id in results:
            if expires_at:
                expires_at_datetime = datetime.fromisoformat(expires_at)
                if expires_at_datetime >= datetime.now():
                    interval = expires_at_datetime - datetime.now()
                    trigger = IntervalTrigger(seconds=interval.total_seconds())
                    await self.remove_warn(user_id, warn_id, expires_at)
                    scheduler.add_job(self.remove_warn, trigger=trigger, id=timer_id,
                                          kwargs={'user_id': user_id, 'warn_id': warn_id, 'expires_at': expires_at})

    @commands.Cog.listener()
    async def on_ready(self):
        cursor.execute("SELECT user_id, warn_id, reason, expires_at, timer_id, task_id FROM warns")
        results = cursor.fetchall()

        for user_id, warn_id, reason, expires_at, timer_id, task_id in results:
            if expires_at:
                expires_at_datetime = datetime.fromisoformat(expires_at)
                if expires_at_datetime >= datetime.now():
                    interval = expires_at_datetime - datetime.now()
                    trigger = IntervalTrigger(seconds=interval.total_seconds())
                    scheduler.add_job(self.remove_warn, trigger=trigger, id=timer_id,
                                      kwargs={'user_id': user_id, 'warn_id': warn_id, 'expires_at': expires_at})
                elif expires_at_datetime <= datetime.now():
                    # Timer finished, remove the warning
                    await self.remove_warn(user_id, warn_id, expires_at)
        scheduler.start()

    @commands.slash_command(name="warn", description="Issue a warning to someone on the server")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, user: disnake.Member, time: str, reason="Violated the server rules"):
        target = user
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS warns (
            user_id INTEGER,
            moder_id INTEGER,
            warns INTEGER,
            warn_id INTEGER PRIMARY KEY,
            reason TEXT,
            expires_at TEXT,
            timer_id TEXT,
            task_id TEXT, -- Column declaration for task identification
            FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """
        )
        cursor.execute("SELECT MAX(warn_id) FROM warns")
        result = cursor.fetchone()
        max_warn_id = result[0]

        if max_warn_id is None:
            warn_id = 1
        else:
            warn_id = max_warn_id + 1

        timer_id = f"unwarn_{target.id}_{warn_id}"
        task_id = f"task_{target.id}_{warn_id}"
        trigger = IntervalTrigger(minutes=int(time))
        expires_at = datetime.now() + timedelta(minutes=int(time))
        scheduler.add_job(self.remove_warn, trigger=trigger, id=timer_id,
                          kwargs={'user_id': target.id, 'warn_id': warn_id, 'expires_at': expires_at})
        cursor.execute(
            "INSERT INTO warns (user_id, moder_id, warn_id, reason, expires_at, timer_id, task_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (target.id, ctx.author.id, warn_id, reason, expires_at, timer_id, task_id))
        db.commit()

        try:
            log_channel_id = config.get_channel_id('logs')
            log_channel = self.bot.get_channel(log_channel_id)
        except ValueError:
            print("⚠️  Warning: Log channel not configured in config.json")
            log_channel = None

        if log_channel:
            embed = disnake.Embed(
                title="🎟️ | Warning issued",
                description=f"A warning was issued to {user.name}({user.mention}).",
                color=disnake.Color.dark_orange(),
            )
            embed.add_field(
                name="Moderator",
                value=f"{ctx.author.name}({ctx.author.mention})",
                inline=False
            )
            embed.add_field(
                name="Reason",
                value=f"{reason}",
                inline=False
            )
            embed.add_field(
                name="Warning number",
                value=f"{warn_id}",
                inline=False
            )
            embed.add_field(
                name="Duration",
                value=f"{expires_at.strftime('%d.%m.%Y %H:%M')}",
                inline=False
            )
            embed.set_footer(
                text=f"Member ID: {user.id}",
                icon_url=user.display_avatar
            )
            await log_channel.send(embed=embed)
        await ctx.send("Warning issued", ephemeral=True)


    @commands.slash_command(name="unwarn", description="Remove a warning from someone on the server")
    @commands.has_permissions(moderate_members=True)
    async def unwarn(self, ctx, user: disnake.Member, warn_id: int):
        target = user
        user_id = target.id
        cursor.execute("SELECT reason, expires_at FROM warns WHERE user_id=? AND warn_id=?", (target.id, warn_id))
        result = cursor.fetchone()
        if result:
            reason, expires_at = result
            expires_at_datetime = datetime.fromisoformat(expires_at)
            if expires_at_datetime >= datetime.now():
                cursor.execute("DELETE FROM warns WHERE user_id=? AND warn_id=?", (target.id, warn_id))
                db.commit()

                try:
                    log_channel_id = config.get_channel_id('logs')
                    log_channel = self.bot.get_channel(log_channel_id)
                except ValueError:
                    print("⚠️  Warning: Log channel not configured in config.json")
                    log_channel = None

                if log_channel:
                    embed = disnake.Embed(
                        title="🚬 | Warning removed",
                        description=f"A warning was removed from user {user.name}({user.mention}).",
                        color=disnake.Color.brand_green(),
                    )
                    embed.add_field(
                        name="Moderator",
                        value=f"{ctx.author.name}({ctx.author.mention})",
                        inline=False
                    )
                    embed.add_field(
                        name="Warning reason",
                        value=f"{reason}",
                        inline=False
                    )
                    embed.add_field(
                        name="Warning number",
                        value=f"{warn_id}",
                        inline=False
                    )
                    embed.set_footer(
                        text=f"Member ID: {user.id}",
                        icon_url=user.display_avatar
                    )
                    await log_channel.send(embed=embed)
                    scheduler.remove_job(f"unwarn_{user_id}_{warn_id}")
                await ctx.send("Warning removed.", ephemeral=True)
            else:
                await ctx.send("Unable to remove the warning. The warning has expired or you do not have enough permissions.", ephemeral=True)
        else:
            await ctx.send("No warning with the specified identifier was found.", ephemeral=True)


    @commands.slash_command(name="warns", description="Show warnings")
    async def warns(self, ctx, user: disnake.Member = None):
        if user is None:
            user = ctx.author
        cursor.execute("SELECT warns, warn_id, reason, expires_at FROM warns WHERE user_id=?", (user.id,))
        results = cursor.fetchall()
        if user == ctx.author:
            if not results:
                embed = disnake.Embed(
                    title="You have no warnings",
                    color=disnake.Color.green()
                )
                await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(
                    title="Your warnings",
                    color=disnake.Color.red()
                )
                for index, (warns, warn_id, reason, expires_at) in enumerate(results, 1):
                    if expires_at:
                        expires_at_datetime = datetime.fromisoformat(expires_at)
                        if expires_at_datetime >= datetime.now():
                            embed.add_field(
                                name=f"Warning with id: {warn_id}",
                                value=f"Reason: {reason}\nExpires: {expires_at_datetime.strftime('%d.%m.%Y at %H:%M')}",
                                inline=False
                            )
                    else:
                        embed.add_field(
                            name=f"Warning {warn_id}",
                            value=f"Reason: {reason}\nNo expiry date",
                            inline=False
                        )
                    await ctx.send(embed=embed, ephemeral=True)
        if user != ctx.author:
            if ctx.author.guild_permissions.moderate_members:
                if not results:
                    embed = disnake.Embed(
                        title=f"User {user.display_name} has no warnings",
                        color=disnake.Color.green()
                    )
                    await ctx.send(embed=embed, ephemeral=True)
                else:
                    embed = disnake.Embed(
                        title=f"Warnings for user {user.display_name}",
                        color=disnake.Color.red()
                    )
                    for index, (warns, warn_id, reason, expires_at) in enumerate(results, 1):
                        if expires_at:
                            expires_at_datetime = datetime.fromisoformat(expires_at)
                            if expires_at_datetime >= datetime.now():
                                embed.add_field(
                                    name=f"Warning with id: {warn_id}",
                                    value=f"Reason: {reason}\nExpires: {expires_at_datetime.strftime('%d.%m.%Y at %H:%M')}",
                                    inline=False
                                )
                        else:
                            embed.add_field(
                                name=f"Warning with id: {warn_id}",
                                value=f"Reason: {reason}\nNo expiry date",
                                inline=False
                            )
                    await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(
                    title="You do not have permission to view other users' warnings.",
                    color=disnake.Color.red()
                )
                await ctx.send(embed=embed, ephemeral=True)



def setup(bot):
    bot.add_cog(warndb(bot))