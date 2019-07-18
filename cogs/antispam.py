import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File

from datetime import datetime, timedelta

warnBuffer = 3
maxBuffer = 5
interval = timedelta(seconds=2)
warningMessage = "Don't type so quickly!"
muteMessage = "I said... **DON'T SPAM!**. @muted c(**(c"
deleteMessagesAfterBanForPastDays = 7
muteTimeout = timedelta(seconds=10)
exemptRoles = []
exemptUsers = []


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.authors = []
        self.warned = []
        self.muted = []
        self.messageLog = []

        self.task_running = False

    async def muteUser(self, msg, ban_message):
        self.muted.append({
            "author": msg.author,
            "time": datetime.now(),
            "guild": msg.guild,
            "channel": msg.channel
        })

        user = discord.utils.get(msg.guild.members, id=msg.author.id)
        if (user):
            try:
                # await user.ban(delete_message_days=deleteMessagesAfterBanForPastDays)
                await msg.author.add_roles(msg.guild.get_role(601467564589187095), reason="spam")
                await msg.channel.send(f"<@!{msg.author.id}>, {muteMessage}")

                self.bot.add_background_task(self.unmuteExpiredUsers, timer=60)
                self.task_running = True
                return True

            except Exception as e:
                await msg.channel.send(f"Oops, seems like i don't have sufficient permissions to ban <@!{msg.author.id}>!")
                return False

    async def warnUser(self, msg, reply):
        self.warned.append({
            "author": msg.author,
            "time": datetime.now(),
            "guild": msg.guild,
            "channel": msg.channel
        })
        await msg.channel.send(f"<@{msg.author.id}>, {reply}")  # Regular Mention Expression for Mentions

    async def unmuteExpiredUsers(self):
        currentTime = datetime.now()

        for i, author in enumerate(self.muted):
            if (author["time"] < currentTime - muteTimeout):
                await author["author"].remove_roles(author["guild"].get_role(601467564589187095), reason="mute for spam ran out")
                await author["channel"].send(f"<@!{author['author'].id}>, You are no longer muted, but behave!")
                self.muted.pop(i)

    @commands.Cog.listener()
    async def on_message(self, message):
        if (message.author.bot):
            return

        # valid message
        if (message.channel is discord.TextChannel or not message.author or not message.guild or not message.channel.guild):
            return

        # is not bot
        if (message.author.id is not self.bot.user.id):
            currentTime = datetime.now()

            # store author
            self.authors.append({
                "time": currentTime,
                "author": message.author.id
            })

            matched = 0
            for i, author in enumerate(self.authors):

                # message still in interval
                if (author["time"] > currentTime - interval):
                    matched += 1
                    if (matched == warnBuffer and message.author.id not in map(lambda s: s["author"].id, self.warned)):
                        await self.warnUser(message, warningMessage)

                    elif (matched == maxBuffer and message.author.id not in map(lambda s: s["author"].id, self.muted)):
                        await self.muteUser(message, muteMessage)

                # message outside of interval, clear
                elif (author["time"] < currentTime - interval):
                    self.authors.pop(i)

                    if author in self.warned:
                        self.warned.remove(map(lambda s: s["author"].id, self.warned).index(author))

                    if author in self.muted:
                        self.muted.remove(map(lambda s: s["author"].id, self.warned).index(author))


def setup(bot):
    bot.add_cog(AntiSpam(bot))
    print("Cog loaded: AntiSpam")
