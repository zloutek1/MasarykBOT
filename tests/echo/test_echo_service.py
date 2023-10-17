import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_echo(bot):
    await bot.load_extension("bot.echo.echo_cog")
    await dpytest.message("!echo Hello world")
    assert dpytest.verify().message().contains().content("Hello")
