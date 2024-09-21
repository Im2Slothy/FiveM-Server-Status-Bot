import json
import discord
import requests as rq
from discord.ext import commands, tasks

# Initialize the bot with intents
intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

# Load configuration
def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

def save_config(data):
    with open("config.json", 'w') as file:
        json.dump(data, file, indent=2)

def create_default_config():
    default_config = {
        "Server_ip": None,
        "prefix": "!",
        "Channel_id": None,
        "Message_id": None,
        "color_filter": ["^0", "^1", "^2", "^3", "^4", "^5", "^6", "^7", "^8", "^9"]
    }
    save_config(default_config)

# Event when bot is ready
@client.event
async def on_ready():
    print('FiveM Status... Online!')

# Command to set server status and post it to a channel
@client.command(aliases=['ss', 'setstatus'])
async def set_status(ctx, *, channel: discord.TextChannel = None):
    if not ctx.author.guild_permissions.administrator:
        msg = await ctx.send(f"{ctx.message.author}, you don't have permission to use this command.")
        await msg.delete(delay=5)
        return

    try:
        config = load_config()
    except FileNotFoundError:
        create_default_config()
        config = load_config()

    ip = config.get("Server_ip")
    
    if not ip:
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Set the IP in the config file!"))
        embed = discord.Embed(description="Set the IP and Port in the config file", color=0xe40000)
        embed.set_footer(text="Updated automatically every 60 seconds")
        await ctx.send(embed=embed)
        return

    if channel:
        try:
            dynamic_response = rq.get(f'http://{ip}/dynamic.json', timeout=5)
            players_response = rq.get(f'http://{ip}/players.json', timeout=5)
        except rq.RequestException:
            await ctx.send("Server is offline or IP address is incorrect.")
            return

        if dynamic_response.status_code == 200 and players_response.status_code == 200:
            dynamic_data = dynamic_response.json()
            players_data = players_response.json()

            hostname = dynamic_data["hostname"]
            for color in config["color_filter"]:
                hostname = hostname.replace(color, "")

            embed = discord.Embed(description=f"**Players: {dynamic_data['clients']}/{dynamic_data['sv_maxclients']}**", color=0x404EED)
            embed.set_author(name=hostname)
            embed.set_footer(text="Updated automatically every 60 seconds")

            msg = await channel.send(embed=embed)
            config["Channel_id"] = channel.id
            config["Message_id"] = msg.id
            save_config(config)
        else:
            await ctx.send("Failed to retrieve server status.")
    else:
        await ctx.send("Please specify a channel to set the server status.")

# Loop to check player count and update status every 60 seconds
@tasks.loop(seconds=60)
async def check_players():
    await client.wait_until_ready()

    try:
        config = load_config()
    except FileNotFoundError:
        create_default_config()
        config = load_config()

    ip = config.get("Server_ip")
    if not ip:
        return

    channel_id = config.get("Channel_id")
    message_id = config.get("Message_id")
    if channel_id and message_id:
        try:
            dynamic_response = rq.get(f'http://{ip}/dynamic.json', timeout=5)
            players_response = rq.get(f'http://{ip}/players.json', timeout=5)
        except rq.RequestException:
            channel = client.get_channel(channel_id)
            msg = await channel.fetch_message(message_id)
            embed = discord.Embed(description="Server is Offline", color=0xe40000)
            embed.set_footer(text="Updated automatically every 60 seconds")
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Server is Offline"))
            await msg.edit(embed=embed)
            return

        if dynamic_response.status_code == 200 and players_response.status_code == 200:
            dynamic_data = dynamic_response.json()
            hostname = dynamic_data["hostname"]
            for color in config["color_filter"]:
                hostname = hostname.replace(color, "")

            embed = discord.Embed(
                description=f"Player Count: {dynamic_data['clients']}/{dynamic_data['sv_maxclients']}",
                color=0x404EED
            )
            embed.set_author(name=hostname)
            embed.set_footer(text="Updated automatically every 60 seconds")

            channel = client.get_channel(channel_id)
            msg = await channel.fetch_message(message_id)
            await msg.edit(embed=embed)

            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"Players: {dynamic_data['clients']}/{dynamic_data['sv_maxclients']}"))

# Command to manually check and display server status
@client.command()
async def status(ctx):    
    ip = config.get("Server_ip")
    try:
        dynamic_response = rq.get(f'http://{ip}/dynamic.json', timeout=5)
        players_response = rq.get(f'http://{ip}/players.json', timeout=5)
    except rq.RequestException:
        await ctx.send("Failed to retrieve server status.")
        return

    if dynamic_response.status_code == 200 and players_response.status_code == 200:
        dynamic_data = dynamic_response.json()

        embed = discord.Embed(
            description=f"Server 1\nPlayer Count: {dynamic_data['clients']}/{dynamic_data['sv_maxclients']}\n\n**Third Party Services**\n[Discord Status](https://discordstatus.com/)\n[FiveM Status](https://status.cfx.re/)\n[Steam](https://steamstat.us/)",
            color=0x404EED
        )
        await ctx.send(embed=embed)

# Start the check_players loop
check_players.start()

# Run the bot
client.run('YOUR_BOT_TOKEN')
