import discord
from discord.ext import commands
import os
from utils import Expandor,music_cog,help_cog,Backend

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$',intents=intents)

bot.remove_command('help')
bot.add_cog(help_cog(bot))
bot.add_cog(music_cog(bot))



@bot.command()
async def gen(ctx, prompt: str):
    manager = Backend(prompt)
    url = manager.generateImg()
    await ctx.send(url)

@bot.command()
async def binom(ctx, expr: str):
    expr = expr.replace(" ","")
    print(expr,"Unedited")
    expandor = Expandor(expr)
    await ctx.send("```"+"%s (Expanded) -> "%expr+"%s"%expandor.expand()+"```")

#bot.run(os.getenv("TOKEN"))
bot.run("MTA2NTc0MjI2NDk2MzQ0ODg1Mw.GY16Tt.VIbAQ8qcZtby6iiP3MMhuB2qglgeiA4AlayU-4")