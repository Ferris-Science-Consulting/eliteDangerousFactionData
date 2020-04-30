import os
from dotenv import load_dotenv
import factionData
import findExpandingSystems

from pprint import pformat

from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TESTBOT_TOKEN')


bot = commands.Bot(command_prefix='#',case_insensitive=True)


@bot.command(name='FET',
help='<baseSystem> - Find Expansion Targets around the <baseSystem>')
async def findExpansionTargets(ctx,baseSystem):
    factionData.findExpansionCandidate(baseSystem)
    response = 'Data loaded'
    factionData.logging.info(ctx.invoked_with+str(ctx.args))
    factionData.logging.info(ctx.message)
    await ctx.send(response)

@bot.command(name='FES',
help='<targetSystem> - Find Expanding Systems around the <targetSystem>')
async def findExpandingTargetsCommand(ctx,baseSystem):
    findExpandingSystems.findExpandingSystems(baseSystem)
    factionData.logging.info(ctx.invoked_with+str(ctx.args))
    factionData.logging.info(ctx.message)
    response = 'Data loaded'
    await ctx.send(response)

@bot.command(name='SET', 
help='- Show expansion targets around the calculated base-system ')
async def showExpansion(ctx):
    factionData.logging.info(ctx.invoked_with+str(ctx.args))
    factionData.logging.info(ctx.message)
    data = factionData.showExpansionData()
    await ctx.send(data[0:1999])

@bot.command(name='SES',
help = '- Show expanding systems around the target system')
async def showExpanding(ctx):
    factionData.logging.info(ctx.invoked_with+str(ctx.args))
    factionData.logging.info(ctx.message)
    data = findExpandingSystems.showExpandingData()
    await ctx.send(data[0:1999])

@bot.event
async def on_ready():
    factionData.logging.info(bot.user.display_name + ' has connected to Discord')
    print(f'{bot.user} has connected to Discord')

@bot.command(name='text')
async def text(ctx):
    string = 'Here is some text\nAnd here\t is\t some more'
    await ctx.send(string)

@bot.event
async def on_command_error(ctx,error):
    if isinstance(error,commands.errors.CommandNotFound):
        factionData.logging.warning(error)
        await ctx.send("Command not found. Type !help")


bot.run(TOKEN)