import os

from dotenv import load_dotenv
import factionData

from pprint import pformat

from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


bot = commands.Bot(command_prefix='!')

@bot.command(name='ShowExpansion', 
help='Usage: ShowExpansion <targetSystem>: Shows expansion targets around the target system ')
async def expansion(ctx):
    data = factionData.showExpansionData()
    response = pformat(data)
    await ctx.send(response[0:1999])

bot.run(TOKEN)