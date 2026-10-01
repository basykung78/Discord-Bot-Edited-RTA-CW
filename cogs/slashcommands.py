from datetime import datetime, timedelta
import disnake
from disnake.ext import commands
from .warns_db import warndb


bot = commands.Bot(command_prefix="!", intents=disnake.Intents.all())
moderators = {}

class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class Moder(commands.Cog):
        cog_name = "🛡️  Moderation "

        def __init__(self, bot):
            self.bot = bot

        @commands.slash_command(name="clear", description="Clear messages in the channel")
        @commands.has_permissions(manage_messages=True)
        async def clear_messages(self, inter: disnake.ApplicationCommandInteraction, amount: int):
            channel = inter.channel
            # Make sure the number of messages to delete is at least 1
            if amount < 1:
                await inter.response.send_message("Please specify a number greater than 0.", ephemeral=True)
                return
            messages = await channel.history(limit=amount).flatten()
            if messages:
                await channel.purge(limit=amount)  # Delete messages
                await inter.response.send_message(f"{amount} messages were deleted successfully.", ephemeral=True)
            else:
                await inter.response.send_message("There are no messages to delete.", ephemeral=True)

        @commands.slash_command(name="kick", description="Kick someone from the server")
        @commands.has_permissions(kick_members=True)
        async def kick(self, ctx, user: disnake.Member, reason="Rule violation"):
            moderators[user.id] = ctx.author.id
            await user.kick(reason=reason)
            await ctx.response.send_message("User kicked", ephemeral=True)

        @commands.slash_command(name="ban", description="Ban someone on the server")
        @commands.has_permissions(ban_members=True)
        async def ban(self, ctx, user: disnake.User, reason="Rule violation"):
            moderators[user.id] = ctx.author.id
            await ctx.guild.ban(user, reason=reason)
            await ctx.response.send_message("Ban issued", ephemeral=True)

        @commands.slash_command(name="mute", description="Mute a member",
                                usage="mute <member> <time> [reason]")
        @commands.has_permissions(moderate_members=True)
        async def mute(self, ctx, user: disnake.Member, time: int, reason="Did not follow the language rules"):
            expired_at = datetime.now() + timedelta(minutes=int(time))
            moderators[user.id] = ctx.author.id
            await user.timeout(reason=reason, until=expired_at)
            await ctx.response.send_message("Mute issued", ephemeral=True)

        @commands.slash_command(name="unban", description="Unban someone from the server")
        @commands.has_permissions(ban_members=True)
        async def unban(self, ctx, user: disnake.User, reason="Paid the debt"):
            moderators[user.id] = ctx.author.id
            await ctx.guild.unban(user, reason=reason)
            await ctx.response.send_message("User unbanned", ephemeral=True)

        @commands.slash_command(name="unmute", description="Unmute someone on the server")
        @commands.has_permissions(moderate_members=True)
        async def unmute(self, ctx, user: disnake.Member, reason="Proper behavior"):
            moderators[user.id] = ctx.author.id
            await user.timeout(until=None, reason=reason)
            await ctx.response.send_message("Mute removed", ephemeral=True)

    class Info(commands.Cog):
        cog_name = "📋  Information "

        def __init__(self, bot):
            self.bot = bot

        @commands.slash_command(name="help", description="Shows the list of available commands")
        async def help(self, ctx):
            categories = [Slash.Moder, Slash.Info, warndb]
            embed = disnake.Embed(title="Here is your list of commands:", color=disnake.Color.blue())

            for category in categories:
                cog_instance = category(self.bot)  # Create an instance of the cog
                commands_info = [f"/{command.name}: {command.description}" for command in
                                 cog_instance.get_slash_commands()]
                if commands_info:
                    embed.add_field(name=category.cog_name, value="\n".join(commands_info), inline=False)

            await ctx.send(embed=embed)


bot.add_cog(Slash(bot))


def setup(bot):
    bot.add_cog(Slash(bot))
    bot.add_cog(Slash.Moder(bot))
    bot.add_cog(Slash.Info(bot))
