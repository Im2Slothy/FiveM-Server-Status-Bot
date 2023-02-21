import datetime
import math
import os
import random
import time
import typing
import json

import discord
import requests as rq
from discord.ext import commands, tasks
from discord.utils import get

intents = discord.Intents.all()

client = commands.Bot(command_prefix='!', intents=intents)

#---------------------------------------------------------------------------#

@client.event
async def on_ready():
    print('FiveM Status... Online!')

#------------------------------------FIVEM------------------------------------------------


# Read The Config And Get Token Discord Bot From Config.json
with open('config.json', 'r') as file:
    config = json.load(file)
    IP = config["Server_ip"]


def create_data():
    """
    If the config file is deleted, this file will be re-created with the help of this function and the steps will be completed.
    The bot token is held and there is no need to reset it.
    NOTE: Please do not change the color filters list.
    Changing this list will cause problems with the bot.
    """

    base_config = {
        "Server_ip": IP,
        "prefix": "!",
        "Channel_id": None,
        "Message_id": None,
        "color_filter": ["^0", "^1", "^2", "^3", "^4", "^5", "^6", "^7", "^8", "^9"]
    }
    # Save Data
    with open("config.json", 'w') as file:
        json.dump(base_config, file, indent=2)


@client.command(aliases=['ss', 'setstatus'])
async def set_status(ctx, *, Channel: discord.TextChannel = None):
    """
    This command sends the information and shows the status of the server.
    """
    authorperms = ctx.author.guild_permissions
    if authorperms.administrator:
        try:
            with open('config.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            # if not found config file , re-create config file
            create_data()
            await asyncio.sleep(2)
        ip = data["Server_ip"]
        if not ip:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Enter the IP into the Config file!"))
            embed = discord.Embed(color=0xe40000)
            embed.description = "Set the IP and Port into the config file"
            embed.set_footer(text="Updated automatically every 60 seconds")
            try:
                msg = await ctx.send(embed=embed)
            except Exception:
                print("\u001b[33mMessage not editable, please use the set_status command")
                create_data()
        else:
            if Channel is not None:
                # ip = data["Server_ip"]
                try:
                    Get_dynamic = rq.get(f'http://{ip}/dynamic.json', timeout=5)
                    Get_players = rq.get(f'http://{ip}/players.json', timeout=5)
                except:
                    print("\u001b[33mThe server is offline Please check again when the server is online or check the IP address")
                else:
                    if not ip:
                        await ctx.send("Please enter the IP in the config.json file")
                        print("\u001b[33mPlease enter the IP in the config.json file")
                    elif Get_dynamic.status_code == 200 or Get_players.status_code == 200:
                        data["Channel_id"] = Channel.id
                        Get_dynamic = Get_dynamic.json()
                        Get_players = Get_players.json()
                        Host_name = Get_dynamic["hostname"]
                        # FiveM colored words are filtered here so that they are not displayed
                        for i in data["color_filter"]:
                            Host_name = Host_name.replace(i, "")
                        embed=discord.Embed(color=0x404EED)
                        embed.description = "**Players: " + str(Get_dynamic["clients"]) + "/" + str(Get_dynamic["sv_maxclients"]) +"**\n"
                        #embed.description = f"**Players: {Get_dynamic["clients"]}/{Get_dynamic["sv_maxclients"]}**\n"
                        embed.set_author(name=Host_name)
                        for x in Get_players:
                            embed.description += f"" # THIS IS THE CODE THAT SHOWS ALL THE PLAYERS WITH IDs - embed.description += f"\n" + "> " + "[" + str(x["id"]) + "] " + "`" + str(x["name"]) + "`" #
                        embed.set_footer(text="Updated automatically every 60 seconds")
                        msg = await Channel.send(embed=embed)
                        data["Message_id"] = msg.id
                        try :
                            with open ("config.json", 'w') as file :
                                json.dump(data, file, indent=2)
                        except FileNotFoundError:
                            # if not found config file  , re-created config file
                            create_data()
                    elif Get_dynamic.status_code != 200 or Get_players.status_code != 200 :
                        await ctx.send("The server is offline Please check again when the server is online or check the IP address")
                        print("\u001b[33mThe server is offline Please check again when the server is online or check the IP address")
    elif ip == None :
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Enter the IP into the Config file!"))
            embed=discord.Embed(color=0xe40000)
            embed.description = "Set the IP and Port into the config file"
            embed.set_footer(text="Updated automatically every 60 seconds")
            try:
                msg = await ctx.send(embed=embed)
            except Exception:
                print("\u001b[33mMessage not editable, please use the set_status command")
                create_data()
    else:
        msg = await ctx.send(f"{ctx.message.author} You Do Not have permission To Use This Command")
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass

# For Calculating Count Of Users IP Server
Old_Players = -1
@tasks.loop(seconds = 60)
async def Check_players():
    # bot until ready : To avoid any problems using this function, we will make sure that the bot is fully set up to start checking the IP server.
    await client.wait_until_ready()
    global Old_Players
    try :
        with open ("config.json", 'r') as file :
            data = json.load(file)
    except FileNotFoundError:
        create_data()
        await asyncio.sleep(2)
    ip = data["Server_ip"]
    if ip != None :
        # If the IP is set, the bot will check and try to connect to the server, and if all goes well, the message sent by the bot will be edited.
        if data["Channel_id"] and data["Message_id"] != None:
            try:
                Get_dynamic = rq.get(f'http://{ip}/dynamic.json', timeout=5)
                Get_players = rq.get(f'http://{ip}/players.json', timeout=5)
            except Exception:

                # If for any reason the robot can not connect to the server, the text of the server unavailability is displayed in the status bot.
                channel = client.get_channel(data["Channel_id"])
                msg = await channel.fetch_message(data["Message_id"])
                await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Server is Offline"))
                embed=discord.Embed(color=0xe40000)
                embed.description = "Server is Offline"
                embed.set_footer(text="Updated automatically every 60 seconds")
                try:
                    await msg.edit(embed=embed)
                except Exception:
                    # If the message sent by the bot is deleted, the information will return to the previous state so that the robot can continue working.
                    print("\u001b[33mMessage not editable, please use the set_status command")
                    create_data()
            else:
                if Get_dynamic.status_code == 200 or Get_players.status_code == 200 :
                    Get_dynamic = Get_dynamic.json()
                    Get_players = Get_players.json()
                    Host_name = Get_dynamic["hostname"]
                    for i in data["color_filter"] :
                        if i in Host_name :
                            Host_name = Host_name.replace(i, "")
                    embed=discord.Embed(color=0x404EED)
                    embed.description = "Below is the live updated status for SERVER\n\n**Server 1**\nPlayer Count: " + str(Get_dynamic["clients"]) + "/" + str(Get_dynamic["sv_maxclients"]) +"\n\n**Third Party Services**\n[Discord Status Page](https://discordstatus.com/)\n[FiveM Status Page](https://status.cfx.re/)\n[Steam](https://steamstat.us/)"#Enter your servers name in "SERVER"#
                    embed.set_author(name=Host_name)
                    for x in Get_players:
                        embed.description += f""
                    embed.set_footer(text="Updated automatically every 60 seconds")
                    try:
                        channel = client.get_channel(data["Channel_id"])
                        msg = await channel.fetch_message(data["Message_id"])
                        await msg.edit(embed=embed)
                    except Exception:
                        print("\u001b[33mMessage not editable, please use the set_status command")
                        create_data()
                if Get_dynamic["clients"] == Old_Players:
                    pass
                elif Get_dynamic["clients"] != Old_Players:
                    Old_Players = Get_dynamic["clients"]
                    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name= "Players: " + str(Get_dynamic["clients"]) + "/" + str(Get_dynamic["sv_maxclients"])))
    elif ip == None :
        # If the IP is not set, it will be executed
        if data["Channel_id"] and data["Message_id"] != None:
            channel = client.get_channel(data["Channel_id"])
            msg = await channel.fetch_message(data["Message_id"])
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Enter the IP and the Port in the config file!"))
            embed=discord.Embed(color=0xe40000)
            embed.description = "Enter the IP and the Port in the config file!"
            embed.set_footer(text="Updated automatically every 60 seconds")
            try:
                await msg.edit(embed=embed)
            except Exception:
                print("\u001b[33mMessage not editable, please use the set_status command")
                create_data()

# Task Created. It will start every 60 seconds updating info
Check_players.start()

#status command for channel anyone can run
@client.command()
async def status(ctx):
    ip = "123.123.123" #ENTER YOUR SERVER IP HERE
    Get_dynamic = rq.get(f'http://{ip}/dynamic.json', timeout=5)
    Get_players = rq.get(f'http://{ip}/players.json', timeout=5)
    if Get_dynamic.status_code == 200 or Get_players.status_code == 200 :
            Get_dynamic = Get_dynamic.json()
            Get_players = Get_players.json()
            embed=discord.Embed(color=0x404EED)
            embed.description = "SERVER\n\n**Server 1**\nPlayer Count: " + str(Get_dynamic["clients"]) + "/" + str(Get_dynamic["sv_maxclients"]) +"\n\n**Third Party Services**\n[Discord Status Page](https://discordstatus.com/)\n[FiveM Status Page](https://status.cfx.re/)\n[Steam](https://steamstat.us/)" #Again Enter your server name in "SERVER"#
            await ctx.send(embed=embed)

