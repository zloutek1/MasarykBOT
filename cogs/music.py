import discord
from discord.ext import commands

import core.utils.get

import youtube_dl
import os


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('summon',))
    async def join(self, ctx):
        channel = ctx.author.voice.channel
        voice = core.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()

        await ctx.send(f"Joined {channel}")

    @commands.command()
    async def leave(self, ctx):
        channel = ctx.author.voice.channel
        voice = core.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            await ctx.send(f"Left {channel}")
        else:
            await ctx.send("Don't think I am in a voice channel")

    @commands.command()
    async def play(self, ctx, url: str):

        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3")
                print("Removed old song file")
        except PermissionError:
            await ctx.send("ERROR: Music playing")
            return

        await ctx.send("Getting everything ready now")

        voice = core.utils.get(self.bot.voice_clients, guild=ctx.guild)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio now\n")
            ydl.download([url])

        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                name = file
                print(f"Renamed File: {file}\n")
                os.rename(file, "song.mp3")

        voice.play(discord.FFmpegPCMAudio("song.mp3"),
                   after=lambda e: print("Song done!"))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.2

        await ctx.send(f"Playing: {name}")

    @commands.command()
    async def pause(self, ctx):
        voice = core.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.pause()

    @commands.command()
    async def resume(self, ctx):
        voice = core.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_paused():
            voice.resume()

    @commands.command()
    async def stop(self, ctx):
        voice = core.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.stop()


def setup(bot):
    bot.add_cog(Music(bot))
