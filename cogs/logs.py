import disnake
from disnake.ext import commands

intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


class AuditLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    @bot.event
    async def on_member_ban(self, guild, user):
        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.ban):
            if entry.target == user:
                from .slashcommands import moderators
                log_channel = guild.get_channel(1075111715085230200)
                if log_channel:
                    embed = disnake.Embed(
                        title="🚧 | Ban",
                        description=f"User {user.name}({user.mention}) has been banned.",
                        color=disnake.Color.red(),
                    )
                    if user.id in moderators:
                        moderator_id = moderators[user.id]
                        moderator = guild.get_member(moderator_id)
                        if moderator:
                            # Log this
                            embed.add_field(
                                name=f"Moderator",
                                value=f"{moderator.name}({moderator.mention})",
                                inline=False
                            )
                    else:
                        embed.add_field(
                            name=f"Moderator",
                            value=f"{entry.user.name}({entry.user.mention})",
                            inline=False
                        )
                    if entry.reason != None:
                        embed.add_field(
                            name=f"Reason",
                            value=f"{entry.reason}",
                            inline=False
                        )
                    embed.set_footer(
                        text=f"ID participant: {user.id}",
                        icon_url=user.display_avatar
                    )
                    await log_channel.send(embed=embed)

    @commands.Cog.listener()
    @bot.event
    async def on_member_unban(self, guild, user):
        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.unban):
            if entry.target == user:
                from .slashcommands import moderators
                log_channel = guild.get_channel(1075111715085230200)
                if log_channel:
                    embed = disnake.Embed(
                        title="🤙 | Unban",
                        description=f"User {user.name}({user.mention}) has been unbanned.",
                        color=disnake.Color.green(),
                    )
                    if user.id in moderators:
                        moderator_id = moderators[user.id]
                        moderator = guild.get_member(moderator_id)
                        if moderator:
                            # Log this
                            embed.add_field(
                                name=f"Moderator",
                                value=f"{moderator.name}({moderator.mention})",
                                inline=False
                            )
                    else:
                        embed.add_field(
                            name=f"Moderator",
                            value=f"{entry.user.name}({entry.user.mention})",
                            inline=False
                        )
                    if entry.reason != None:
                        embed.add_field(
                            name=f"Reason",
                            value=f"{entry.reason}",
                            inline=False
                        )
                    embed.set_footer(
                        text=f"ID participant: {user.id}",
                        icon_url=user.display_avatar
                    )
                    await log_channel.send(embed=embed)

    @commands.Cog.listener()
    @bot.event
    async def on_member_remove(self, user):
        async for entry in user.guild.audit_logs(limit=1):
            if entry.target == user:
                if entry.action == disnake.AuditLogAction.kick:
                    # Log the kick to the text channel
                    from .slashcommands import moderators
                    log_channel = user.guild.get_channel(1075111715085230200)
                    if log_channel:
                        embed = disnake.Embed(
                            title="🚪 | Kick",
                            description=f"User {user.name}({user.mention}) has been kicked.",
                            color=disnake.Color.red(),
                        )
                        if user.id in moderators:
                            moderator_id = moderators[user.id]
                            moderator = user.guild.get_member(moderator_id)
                            if moderator:
                                # Log this
                                embed.add_field(
                                    name=f"Moderator",
                                    value=f"{moderator.name}({moderator.mention})",
                                    inline=False
                                )
                        else:
                            embed.add_field(
                                name=f"Moderator",
                                value=f"{entry.user.name}({entry.user.mention})",
                                inline=False
                            )
                        if entry.reason != None:
                            embed.add_field(
                                name=f"Reason",
                                value=f"{entry.reason}",
                                inline=False
                            )
                        embed.set_footer(
                            text=f"ID participant: {user.id}",
                            icon_url=user.display_avatar
                        )
                        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    @bot.event
    async def on_member_update(self, after, user):
        guild = after.guild
        log_channel = guild.get_channel(1075111715085230200)
        async for entry in guild.audit_logs(limit=1):
            if entry.target == user:
                if entry.action == disnake.AuditLogAction.member_update:
                    changes = entry.changes
                    if "nick" in changes.before.__dict__ and "nick" in changes.after.__dict__:
                        nick_before = changes.before.__dict__["nick"]
                        nick_after = changes.after.__dict__["nick"]
                        if nick_before != nick_after:
                            if nick_before == None:
                                nick_before = user.name
                            if nick_after == None:
                                nick_after = user.name
                            # Log this
                            embed = disnake.Embed(
                                title="🔁 | Nickname Change",
                                description=f"User {user.name}({user.mention}) changed their nickname.",
                                color=disnake.Color.dark_magenta(),
                            )
                            embed.add_field(
                                name=f"Nickname Before",
                                value=f"{nick_before}",
                                inline=True
                            )
                            embed.add_field(
                                name=f"Nickname After",
                                value=f"{nick_after}",
                                inline=True
                            )
                            embed.set_footer(
                                text=f"ID participant: {user.id}",
                                icon_url=user.display_avatar
                            )

                            await log_channel.send(embed=embed)
                    if "timeout" in changes.after.__dict__ and changes.after.__dict__["timeout"] is not None:
                        timeout_after = changes.after.__dict__["timeout"]
                        from .slashcommands import moderators
                        # Log this
                        embed = disnake.Embed(
                            title="🔇 | Mute",
                            description=f"User {user.name}({user.mention}) has been muted.",
                            color=disnake.Color.red(),
                        )
                        if user.id in moderators:
                            moderator_id = moderators[user.id]
                            moderator = user.guild.get_member(moderator_id)
                            embed.add_field(
                                name=f"Moderator",
                                value=f"{moderator.name}({moderator.mention})",
                                inline=False
                            )
                        else:
                            embed.add_field(
                                name=f"Moderator",
                                value=f"{entry.user.name}({entry.user.mention})",
                                inline=False
                            )
                        if entry.reason != None:
                            embed.add_field(
                                name=f"Reason",
                                value=f"{entry.reason}",
                                inline=False
                            )
                        embed.add_field(
                            name=f"Duration",
                            value=f"{timeout_after.strftime('%d.%m.%Y %H:%M')}",
                            inline=False
                        )
                        embed.set_footer(
                            text=f"ID participant: {user.id}",
                            icon_url=user.display_avatar
                        )
                        await log_channel.send(embed=embed)
                    elif "timeout" in changes.before.__dict__ and changes.after.__dict__.get("timeout") is None:
                        from .slashcommands import moderators

                        # Log this
                        embed = disnake.Embed(
                            title="🔊 | Unmute",
                            description=f"User {user.name}({user.mention}) has been unmuted.",
                            color=disnake.Color.green(),
                        )
                        if user.id in moderators:
                            moderator_id = moderators[user.id]
                            moderator = user.guild.get_member(moderator_id)
                            embed.add_field(
                                name=f"Moderator",
                                value=f"{moderator.name}({moderator.mention})",
                                inline=False
                            )
                        else:
                            embed.add_field(
                                name=f"Moderator",
                                value=f"{entry.user.name}({entry.user.mention})",
                                inline=False
                            )
                        if entry.reason != None:
                            embed.add_field(
                                name=f"Reason",
                                value=f"{entry.reason}",
                                inline=False
                            )
                        embed.set_footer(
                            text=f"ID participant: {user.id}",
                            icon_url=user.display_avatar
                        )
                        await log_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(AuditLog(bot))