from discord.ext import commands
from . import errors


def is_owner():
    """Command can only be executed by the bot owner."""
    async def predicate(ctx):
        res = await ctx.bot.is_owner(ctx.author)
        if not res:
            raise errors.UnathorizedUser("You are not allowed to use this command.")
        return True
    return commands.check(predicate)


async def check_permissions(ctx, perms):
    """Checks if the user has the specified permissions in the current channel."""
    if await ctx.bot.is_owner(ctx.author):
        return True

    permissions = ctx.channel.permissions_for(ctx.author)
    return all(getattr(permissions, name, None) == value for name, value in perms.items())


def has_permissions(**perms):
    """Command can only be used if the user has the provided permissions."""
    async def pred(ctx):
        ret = await check_permissions(ctx, perms)
        if not ret:
            raise commands.MissingPermissions(perms)
        return True

    return commands.check(pred)
