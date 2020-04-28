import os

from dotenv import load_dotenv
import factionData
import findExpandingSystems

from pprint import pformat

from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


bot = commands.Bot(command_prefix='!')

@bot.command(name='CalculateExpansion',
help='Calculate expansion targets and expanding systems')
async def calculateExpansion(ctx):
    factionData.findExpansionCandidate('Meliae')
    findExpandingSystems.findExpandingSystems('Dahan')
    response = pformat('Data loaded')
    await ctx.send(response)


@bot.command(name='ShowTargets', 
help='Show targets around the target system ')
async def showExpansion(ctx):
    data = factionData.showExpansionData()
    response = pformat(data)
    await ctx.send(response[0:1999])

@bot.command(name='ShowExpandingSystems',
help = 'Show expanding systems around the target')
async def showExpanding(ctx):
    data = findExpandingSystems.showExpandingData()
    response = pformat(data)
    await ctx.send(response[0:1999])

bot.run(TOKEN)