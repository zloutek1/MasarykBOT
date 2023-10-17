
class EchoService:
    def __init__(self, bot):
        self.bot = bot

    async def echo(self, ctx, message: str):
        await ctx.send(message)