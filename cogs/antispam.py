import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File

from datetime import datetime, timedelta

warnBuffer = 3
maxBuffer = 5
interval = timedelta(milliseconds=2000)
warningMessage = "Don't type so quickly!"
banMessage = "You would have been baned from spam"
maxDuplicatesWarning = 7
maxDuplicatesBan = 10
deleteMessagesAfterBanForPastDays = 7
exemptRoles = []
exemptUsers = []


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.authors = []
        self.warned = []
        self.banned = []
        self.messageLog = []

    async def banUser(self, msg, ban_message):
        self.banned.append(msg.author.id)

        user = discord.utils.get(msg.guild.members, id=msg.author.id)
        if (user):
            try:
                # await user.ban(delete_message_days=deleteMessagesAfterBanForPastDays)
                await msg.channel.send(f"<@!{msg.author.id}>, {ban_message}")
                return True
            except Exception as e:
                print(e)
                await msg.channel.send(f"Oops, seems like i don't have sufficient permissions to ban <@!{msg.author.id}>!")
                return False

    async def warnUser(self, msg, reply):
        self.warned.append(msg.author.id)
        await msg.channel.send(f"<@{msg.author.id}>, {reply}")  # Regular Mention Expression for Mentions

    @commands.Cog.listener()
    async def on_message(self, message):
        if (message.author.bot):
            return

        if (message.channel is discord.TextChannel or not message.author or not message.guild or not message.channel.guild):
            return

        if (message.author.id is not self.bot.user.id):
            currentTime = datetime.now()
            self.authors.append({
                "time": currentTime,
                "author": message.author.id
            })

            self.messageLog.append({
                "message": message.content,
                "author": message.author.id
            })

            msgMatch = 0
            for i in range(len(self.messageLog)):
                if (self.messageLog[i]["message"] == message.content and (self.messageLog[i]["author"] == message.author.id) and (message.author.id is not self.bot.user.id)):
                    msgMatch += 1

            if (msgMatch == maxDuplicatesWarning and message.author.id not in self.warned):
                print("duplicity warn")
                self.warnUser(message, warningMessage)

            if (msgMatch == maxDuplicatesBan and message.author.id not in self.banned):
                print("duplicity ban")
                self.banUser(message, banMessage)

            matched = 0
            for i, author in enumerate(self.authors):
                if (author["time"] > currentTime - interval):
                    matched += 1
                    if (matched == warnBuffer and message.author.id not in self.warned):
                        print("type too often warn")
                        await self.warnUser(message, warningMessage)

                    elif (matched == maxBuffer and message.author.id not in self.banned):
                        print("type too often ban")
                        await self.banUser(message, banMessage)

                elif (author["time"] < currentTime - interval):
                    self.authors.pop(i)

                    if author in self.warned:
                        self.warned.remove(self.warned.index(author))

                    if author in self.banned:
                        self.banned.remove(self.warned.index(author))

                if (len(self.messageLog) >= 200):
                    self.messageLog.pop(0)


def setup(bot):
    bot.add_cog(AntiSpam(bot))
    print("Cog loaded: AntiSpam")
