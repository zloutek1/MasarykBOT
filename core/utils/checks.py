from discord.ext import commands


def needs_embed(ctx):
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return True
    if ctx.channel.permissions_for(ctx.guild.me).embed_links:
        return True
    raise exceptions.EmbedError


@commands.check
def needs_database(ctx):
    return bool(ctx.db)
