import discord
from discord.ext import commands

import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from io import StringIO
import pandas as pd

class Corona(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(aliases=("covid", "covid19", "covid-19", "korona"))
    async def corona(self, ctx):
        embed = discord.Embed(
            title=f"COVID-19",
            description="⁣ ",
            color=0x000000)

        try:
            cz_headers, cz_data, cz_date = await self.parse_cz()
            embed.add_field(
                name="Česko",
                value="\n".join([
                    f"**{header}**: {int(value)}"
                    for header, value in zip(cz_headers, cz_data)]),
                inline=False)

        except Exception as err:
            await ctx.send(f"Error while loading the czech data. Got `{err}`")

        try:
            global_headers, global_data, global_date = await self.parse_global()

            embed.add_field(
                name="Worldwide",
                value="\n".join([
                    f"**{header}**: {int(value)}"
                    for header, value in zip(global_headers, global_data)]),
                inline=False)

        except Exception as err:
            await ctx.send(f"Error while loading the global data. Got `{err}`")

        embed.set_footer(text=f"Czech data updated at {cz_date}\nGloal data updated at {global_date}")

        await ctx.send(embed=embed)



    @staticmethod
    async def parse_cz():
        url = "http://koronavirusvcr.cz/"
        headers = []
        values = []

        res = requests.get(url)
        if not res.ok:
            return

        soup = BeautifulSoup(res.content, "lxml")
        counters = soup.find_all("div", {"class": "w-counter"})
        for counter in counters:
            title = counter.find("h3", {"class": "w-counter-title"}).text
            value = int(counter.find("span", {"class": "type_number"}).text.replace(' ', ''))

            headers.append(title)
            values.append(value)

        date = soup.find(text="Poslední aktualizace dat:")
        if date is not None:
            data = date.next

        return tuple(headers), tuple(values), date

    @staticmethod
    async def parse_global():
        url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{mmddyyyy}.csv"
        today = datetime.now().strftime("%m-%d-%Y")
        yesterday = (datetime.now()  - timedelta(days=1)).strftime("%m-%d-%Y")

        res = requests.get(url.format(mmddyyyy=today))
        date = today
        if not res.ok:
            res = requests.get(url.format(mmddyyyy=yesterday))
            date = yesterday
            if not res.ok:
                return

        content = StringIO(res.content.decode('utf-8'))
        df = pd.read_csv(content)
        dk = df.groupby(df.columns[1]).sum()

        total = dk.sum().to_dict()
        result = {key: val for key, val in total.items() if key in ('Confirmed', 'Deaths', 'Recovered')}
        return tuple(result.keys()), tuple(result.values()), date


def setup(bot):
    bot.add_cog(Corona(bot))
