import discord
import responses
import asyncio
import re
import emoji
import unidecode
import time
import random
import tutorial
import sqlite3
import json
import os
import psycopg2
from psycopg2 import sql

server_data = {}
collection_messages = {}
user_transfer_tasks = {}
user_refund_bool = {}
user_daily = {}
user_claim_count = {}

TOKEN = os.environ.get('TOKEN')
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

DATABASE_URL = os.environ.get('DATABASE_URL')

def replace_quotes(data):
    if isinstance(data, str):
        return data.replace("'", '"')
    elif isinstance(data, dict):
        return {key: replace_quotes(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [replace_quotes(item) for item in data]
    else:
        return data

def create_tables():
    """
    Create database tables if they don't exist.

    This function connects to the database using the DATABASE_URL environment variable,
    creates the 'server_data' table if it doesn't exist, and commits the changes.

    Args:
        None

    Returns:
        None
    """
    
    # Connect to the database
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()

    # Create the server_data table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_data (
            server_id TEXT PRIMARY KEY,
            data JSONB
        )
    ''')
    
    # Commit the changes
    conn.commit()
    
    # Close the cursor and connection
    cursor.close()
    conn.close()

def connect_to_database():
    """
    Establish a connection to the PostgreSQL database.

    This function retrieves the database connection information from the DATABASE_URL environment variable
    and returns a connection object to the database.

    Args:
        None

    Returns:
        psycopg2.extensions.connection: A connection object to the PostgreSQL database.
    """
    # Connect to the database
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def save_server_data(server_id, data_to_store):
    """
    Save server-specific data to the database.

    This function connects to the database, serializes the data, and inserts or updates
    the data in the 'server_data' table based on the server_id. It handles conflicts by updating
    the existing data.

    Args:
        server_id (str): The ID of the server (guild) for which data is being saved.
        data_to_store (dict): The data to be saved for the server.

    Returns:
        None
    """
    conn = connect_to_database()
    cursor = conn.cursor()
    
    # Replace single quotes with double quotes in the dictionary
    new_data_to_store = replace_quotes(data_to_store)
    
    # Convert the dictionary to JSON-encoded string
    data_to_store_json = json.dumps(new_data_to_store)

    # Insert or replace the server data using an upsert (ON CONFLICT) query
    insert_query = sql.SQL('''
        INSERT INTO server_data (server_id, data)
        VALUES (%s, %s)
        ON CONFLICT (server_id)
        DO UPDATE SET data = EXCLUDED.data
    ''')
    cursor.execute(insert_query, (str(server_id), data_to_store_json))

    conn.commit()
    cursor.close()
    conn.close()

def load_server_data(server_id):
    """
    Load server-specific data from the database.

    This function connects to the database, retrieves the data associated with the specified server_id,
    and returns it as a Python dictionary. If the data does not exist, it returns None.

    Args:
        server_id (str): The ID of the server (guild) for which data is being loaded.

    Returns:
        dict or None: The loaded server data as a dictionary, or None if no data is found.
    """
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT data FROM server_data WHERE server_id = %s
        ''', (str(server_id),))

        data = cursor.fetchone()

        if data:
            # Parse the JSON-encoded data into a dictionary
            return json.loads(json.dumps(data[0]))
        else:
            return None

    except Exception as e:
        print("Error loading server data:", e)
        return None

    finally:
        conn.close()

def format_time(seconds):
    """
    Format a duration in seconds into a string representing hours, minutes, and seconds.

    Args:
        seconds (int): The duration in seconds to be formatted.

    Returns:
        str: A formatted string representing the duration in the format "Xh Ym Zs".
    """
    # Calculate hours, minutes, and remaining seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Create a formatted string
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
def get_time_remaining(server_id, user):
    """
    Get the remaining time for a specific user's task.

    This function checks if the user has an ongoing task and calculates the remaining time
    until completion. If there is no ongoing task, it returns an empty string.

    Args:
        server_id (str): The ID of the server (guild) where the user's task is occurring.
        user (discord.User): The user for whom to check the remaining time.

    Returns:
        str: A formatted string representing the remaining time in the format "Xh Ym Zs", or an empty string if no task is ongoing.
    """
    user_id = str(user.id)
    
    # Check if the user has an ongoing task
    if user_id in user_transfer_tasks:
        task = user_transfer_tasks[user_id]
        if task is not None and not task.done():
            # Calculate the remaining time
            time_remaining = server_data[server_id]["user_market_wait"][user_id] - time.time()
            
            # Format the remaining time as a string
            return format_time(time_remaining)
    
    # Return an empty string if no task is ongoing
    return ""  

async def show_collection(user, msg, page_num, mention):
    """
    Show a user's collection of players at a specific page.
    
    This function allows the user to show a user's collection of players at a specific page and updates the server data accordingly.
    
    Args:
        user (discord.User): The user for whom to display the collection.
        msg (discord.Message): The message that triggered the command.
        page_num (int): The page number of the collection to display.
        mention (str): Mentioned user to display their collection (empty string if none).
        
    Returns:
        None
    """
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    
    # Check if user's current page is initialized; if not, initialize it to 0
    if user_id not in server_data[server_id]["user_current_page"]:
        server_data[server_id]["user_current_page"][user_id] = 0
        
    mention_id = 0
        
    if mention == "":
        mention_id = str(user_id)
    else:
        mention_id = await extract_user_id(mention)
    
    # Check if the mentioned user has a collection
    if mention_id in server_data[server_id]["user_collections"]:
        collection = server_data[server_id]["user_collections"][mention_id]
        
        # Check if the requested page number is within bounds
        if 0 <= page_num < len(collection):
            server_data[server_id]["user_current_page"][mention_id] = page_num
            
            #Retrieve user's collection
            embed_data = collection[page_num]
            
            embed_to_show = discord.Embed(
                title=embed_data[0],
                description=embed_data[1],
                color=discord.Colour(int(embed_data[2]))
            )
            
            # Add fields to the embed
            for field in embed_data[3]:
                embed_to_show.add_field(name=field[0], value=field[1], inline=field[2])
            
            if embed_data[5] is not None:
                embed_to_show.set_image(url=embed_data[5])
                
            # Set the footer with page information
            embed_to_show.set_footer(text=embed_data[4].split(", ")[0] + ", " + embed_data[4].split(", ")[1][0:5] + " --- " + f"{server_data[server_id]['user_current_page'][user_id] + 1}/{len(server_data[server_id]['user_collections'][mention_id])}")
        
            if user_id in collection_messages:
                #Edit previous collection message
                collection_msg = collection_messages[user_id]
                await collection_msg.clear_reactions()
                await collection_msg.edit(embed=embed_to_show)     
            else:
                # Create new message to display collection
                collection_msg = await msg.channel.send(embed=embed_to_show)
                await collection_msg.clear_reactions()
                collection_messages[user_id] = collection_msg
                
            # Add navigation reactions
            await collection_msg.add_reaction("⬅️")
            await collection_msg.add_reaction("➡️")
            
            # Check if it's a tutorial completion
            if mention == "":    
                if not server_data[server_id]["user_tutorial_completion"][user_id][2][1]:
                    server_data[server_id]["user_tutorial_completion"][user_id][2][1] = True
                    
                    await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                    
                    print(server_data[server_id]["user_tutorial_completion"][user_id][2])
                    
                    # Reward the user and update tutorial progress
                    if user_id not in server_data[server_id]["user_max_rolls"]:
                        server_data[server_id]["user_max_rolls"][user_id] = 9
                            
                    if False not in server_data[server_id]["user_tutorial_completion"][user_id][2]:
                        server_data[server_id]["user_max_rolls"][user_id] += 1
                        server_data[server_id]["user_current_tutorial"][user_id] = 3
                        await msg.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**! Type %tuto for the next steps!")
            else:
                if not server_data[server_id]["user_tutorial_completion"][user_id][2][5]:
                    server_data[server_id]["user_tutorial_completion"][user_id][2][5] = True
                    
                    await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                    
                    print(server_data[server_id]["user_tutorial_completion"][user_id][2])
                    
                    # Reward the user and update tutorial progress
                    if user_id not in server_data[server_id]["user_max_rolls"]:
                        server_data[server_id]["user_max_rolls"][user_id] = 9
                            
                    if False not in server_data[server_id]["user_tutorial_completion"][user_id][2]:
                        server_data[server_id]["user_max_rolls"][user_id] += 1
                        server_data[server_id]["user_current_tutorial"][user_id] = 3
                        await msg.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**! Type %tuto for the next steps!")
        else:
            await msg.channel.send("Error: Page not found.")
    else:
        await msg.channel.send("Error : No players found in your collection.")

async def rename_club(msg, user, name):
    """
    Rename the user's club.

    This function allows the user to rename their club and updates the server data accordingly.

    Args:
        msg (discord.Message): The Discord message object that triggered the command.
        user (discord.User): The user who is renaming their club.
        name (list): A list of strings representing the new club name (or an empty list to reset).

    Returns:
        None
    """
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    
    if "user_club_name" not in server_data[server_id]:
        server_data[server_id]["user_club_name"] = {}
        
    if user_id not in server_data[server_id]["user_club_name"]:
        server_data[server_id]["user_club_name"][user_id] = ""
        
    if name == []:
        server_data[server_id]["user_club_name"][user_id] = ""
        await msg.channel.send(f"{user.mention} Your club's name has been reset to default.")
        return
    
    rename = " ".join(name)
    
    server_data[server_id]["user_club_name"][user_id] = rename
    
    await msg.channel.send(f"{user.mention} Your club has been renamed to **{rename}**!")
    
    if not server_data[server_id]["user_tutorial_completion"][user_id][4][4]:
        server_data[server_id]["user_tutorial_completion"][user_id][4][4] = True
        
        if user_id not in server_data[server_id]["user_coins"]:
            server_data[server_id]["user_coins"][user_id] = 0
            
        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                
        if False not in server_data[server_id]["user_tutorial_completion"][user_id][4]:
            server_data[server_id]["user_coins"][user_id] += 500
            server_data[server_id]["user_current_tutorial"][user_id] = 5
            await msg.channel.send("Tutorial 5 complete! You have been rewarded **500 \U0001f4a0**! Type %tuto for the next steps!")

async def move_player(msg, user, player, position):
    server_id = str(msg.guild.id)
    user_id = str(user.id)

    if user_id not in server_data[server_id]["user_collections"]:
        server_data[server_id]["user_collections"][user_id] = []
        
    if (position > len(server_data[server_id]["user_collections"][user_id])) or position < 1:
        await msg.channel.send("Error: Invalid position.")
        return
    
    collection = server_data[server_id]["user_collections"][user_id]
    player_to_move = None
    search_terms = player
    normalized_search_terms = [unidecode.unidecode(term.lower()) for term in search_terms]
    i = 0
    for embed in collection:
        embed_title = unidecode.unidecode(embed[0].lower().strip())
        if embed_title == " ".join(normalized_search_terms):
            player_to_move = collection.pop(i)
            break
        i += 1
        
    if player_to_move is None:
        await msg.channel.send(f"Error: {' '.join(player)} was not found in your collection.")
        return
  
    collection.insert(position - 1, player_to_move)
    await msg.channel.send(f"Succesfully moved {player_to_move[0]}!")
    
    if not server_data[server_id]["user_tutorial_completion"][user_id][2][3]:
        server_data[server_id]["user_tutorial_completion"][user_id][2][3] = True
        
        if user_id not in server_data[server_id]["user_max_rolls"]:
            server_data[server_id]["user_max_rolls"][user_id] = 9
            
        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                
        if False not in server_data[server_id]["user_tutorial_completion"][user_id][2]:
            server_data[server_id]["user_max_rolls"][user_id] += 1
            server_data[server_id]["user_current_tutorial"][user_id] = 3
            await msg.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**! Type %tuto for the next steps!")
     
async def sort_collection(msg, user):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
        
    if user_id not in server_data[server_id]["user_collections"]:
        server_data[server_id]["user_collections"][user_id] = []
        
    def get_embed_value(embed):
        for field in embed[3]:
            if "Value:" in field[0]:
                print(int(field[0].split()[1]))
                return int(field[0].split()[1])
                                  
    collection = server_data[server_id]["user_collections"][user_id]
    collection.sort(key=get_embed_value, reverse=True)

    await msg.channel.send("Your collection has been successfully sorted from highest to lowest value.")
    
    if not server_data[server_id]["user_tutorial_completion"][user_id][2][2]:
        server_data[server_id]["user_tutorial_completion"][user_id][2][2] = True
        
        print(server_data[server_id]["user_tutorial_completion"][user_id][2])
        
        if user_id not in server_data[server_id]["user_max_rolls"]:
            server_data[server_id]["user_max_rolls"][user_id] = 9
            
        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                
        if False not in server_data[server_id]["user_tutorial_completion"][user_id][2]:
            server_data[server_id]["user_max_rolls"][user_id] += 1
            server_data[server_id]["user_current_tutorial"][user_id] = 3
            await msg.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**! Type %tuto for the next steps!")
            
async def dailies(msg, user):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
        
    if user_id not in server_data[server_id]["user_daily_bool"]:
        server_data[server_id]["user_daily_bool"][user_id] = True
        
    if user_id not in server_data[server_id]["user_daily_wait"]:
        server_data[server_id]["user_daily_wait"][user_id] = 0
        
    if server_data[server_id]["user_daily_bool"][user_id]:
        chance = random.randint(0, 100)
        daily_reward = 0
        
        if chance < 7:
            daily_reward = float(random.randint(700, 900))
        else:
            daily_reward = float(random.randint(300, 550))
            
        if server_data[server_id]["user_upgrades"][user_id][1] != 0:
            daily_reward += daily_reward * (responses.board_upgrades[server_data[server_id]["user_upgrades"][user_id][1] - 1] / 100)
            
        await msg.channel.send(f"{user.mention} You have been given **+{int(daily_reward)}** \U0001f4a0!")
        server_data[server_id]["user_coins"][user_id] += int(daily_reward)
        server_data[server_id]["user_daily_bool"][user_id] = False
        server_data[server_id]["user_daily_wait"][user_id] = time.time() + 86400
        
        if not server_data[server_id]["user_tutorial_completion"][user_id][1][2]:
            server_data[server_id]["user_tutorial_completion"][user_id][1][2] = True
            
            if user_id not in server_data[server_id]["user_coins"]:
                server_data[server_id]["user_coins"][user_id] = 0
                
            await msg.channel.send("Substep complete! Type %tuto for the next steps!")
        
            if False not in server_data[server_id]["user_tutorial_completion"][user_id][1]:
                server_data[server_id]["user_coins"][user_id] += 250
                server_data[server_id]["user_current_tutorial"][user_id] = 2
                await msg.channel.send("Tutorial 2 complete! You have been rewarded **250 \U0001f4a0**! Type %tuto for the next steps!")
        try:
            await asyncio.sleep(86400)
            server_data[server_id]["user_daily_bool"][user_id] = True
        except Exception as e:
            print("not working")
            
    else:
        time_left = format_time(server_data[server_id]["user_daily_wait"][user_id] - time.time())
        await msg.channel.send(f"Your daily reward is not available yet. Please wait **{time_left}**.")
        
async def team_rewards(msg, user, value):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    
    if "playerids" not in server_data[server_id]:
        server_data[server_id]["playerids"] = []
        
    if "usernames" not in server_data[server_id]:
        server_data[server_id]["usernames"] = []
        
    if value == 700:
        f = open('../data/ultra_rare_players_list.txt', 'r', encoding='utf-8')
        players_list = f.readlines()
                
        reward = random.choice(players_list)
        
        player_info = reward.strip().split(", ")
        player_name, player_positions, player_club, player_nationality, player_value, player_imageURL, player_id = player_info
        player_value += " " + emoji.emojize(":diamond_with_a_dot:")
            

        embed = discord.Embed(
            title=player_name,
            description=player_club + "\n" + player_nationality,
            color=0xAF0000
        )
            
        embed.add_field(name=player_positions, value="", inline=False)
        embed.add_field(name= player_value, value="", inline=False)
        embed.set_image(url=player_imageURL)
        embed.set_footer(text="Fantasy Football Draft, " + player_id)
            
        player_status = f"**Claimed by {user.name}**"
        embed.description += ("\n" + player_status)
        
        if user_id not in server_data[server_id]["user_collections"]:
            server_data[server_id]["user_collections"][user_id] = []
            
        player_embed_data = [
            embed.title,
            embed.description,
            embed.color.value,
            [(field.name, field.value, field.inline) for field in embed.fields],
            embed.footer.text,
            embed.image.url if embed.image else None
        ]
            
        server_data[server_id]["user_collections"][user_id].append(player_embed_data)

        player_id = embed.footer.text.split(", ")[1]
        server_data[server_id]["playerids"].append(player_id)
        server_data[server_id]["usernames"].append(user.name)
        
        await msg.channel.send(embed=embed)
        
    elif value == 800:
        f = open('../data/legends_list.txt', 'r', encoding='utf-8')
        legends_list = f.readlines()

        reward = random.choice(legends_list)
        
        player_info = reward.strip().split(", ")
        player_name, player_positions, player_club, player_nationality, player_value, player_imageURL, player_id = player_info
        player_value += " " + emoji.emojize(":diamond_with_a_dot:")
            

        embed = discord.Embed(
            title=player_name,
            description=player_club + "\n" + player_nationality,
            color=0xFFD700
        )
            
        embed.add_field(name=player_positions, value="", inline=False)
        embed.add_field(name= player_value, value="", inline=False)
        embed.set_image(url=player_imageURL)
        embed.set_footer(text="Fantasy Football Draft, " + player_id)
            
        player_status = f"**Claimed by {user.name}**"
        embed.description += ("\n" + player_status)
        
        if user_id not in server_data[server_id]["user_collections"]:
            server_data[server_id]["user_collections"][user_id] = []
            
        player_embed_data = [
            embed.title,
            embed.description,
            embed.color.value,
            [(field.name, field.value, field.inline) for field in embed.fields],
            embed.footer.text,
            embed.image.url if embed.image else None
        ]
            
        server_data[server_id]["user_collections"][user_id].append(player_embed_data)

        player_id = embed.footer.text.split(", ")[1]
        server_data[server_id]["playerids"].append(player_id)
        server_data[server_id]["usernames"].append(user.name)
        
        await msg.channel.send(embed=embed)
        
async def free_claim(msg, user):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    
    if "user_free_claims" not in server_data[server_id]:
        server_data[server_id]["user_free_claims"] = {}
    
    if user_id not in server_data[server_id]["user_free_claims"]:
        server_data[server_id]["user_free_claims"][user_id] = 0
        
    if server_data[server_id]["user_free_claims"][user_id] != 0:
        confirmation_msg = await msg.channel.send(f"You have **{server_data[server_id]['user_free_claims'][user_id]}** free claim(s). Are you sure you want to use a free claim? Make sure you don't already have a claim ready. (y/n/yes/no)")
        try:
            response = await client.wait_for('message', timeout=30, check=lambda m: m.author == msg.author and m.channel == msg.channel)
            response_content = response.content.lower()
            if response_content == 'yes' or response_content == 'y':
                server_data[server_id]["user_can_claim"][user_id] = True
                server_data[server_id]["user_free_claims"][user_id] -= 1
                await msg.channel.send(f"{user.mention} Successfully used a free claim!")
            elif response_content == 'no' or response_content == 'n':
                await msg.channel.send("Process cancelled.")
        except asyncio.TimeoutError:
            await msg.channel.send("Confirmation timed out. Process cancelled.")
    else:
        await msg.channel.send(f"{user.mention} You do not have any free claims.")

async def claim_timer():
    
    while True:
        for server_id in server_data:
            if "claim_reset_time" not in server_data[server_id]:
                server_data[server_id]["claim_reset_time"] = time.time()

            server_data[server_id]["claim_reset_time"] = time.time()

            if "user_can_claim" not in server_data[server_id]:
                server_data[server_id]["user_can_claim"] = {}

            for key in server_data[server_id]["user_can_claim"]:
                server_data[server_id]["user_can_claim"][key] = True

        await asyncio.sleep(7200)

async def roll_timer():
    while True:
        for server_id in server_data:
            if "roll_reset_time" not in server_data[server_id]:
                server_data[server_id]["roll_reset_time"] = time.time()

            server_data[server_id]["roll_reset_time"] = time.time()

            if "user_rolls" not in server_data[server_id]:
                server_data[server_id]["user_rolls"] = {}
                server_data[server_id]["user_max_rolls"] = {}

            for user_id in server_data[server_id]["user_max_rolls"]:
                server_data[server_id]["user_rolls"][user_id] = server_data[server_id]["user_max_rolls"][user_id]

        await asyncio.sleep(3600)

async def clean_up_rolled_times():
    while True:
        current_time = time.time()

        for server_id in server_data:
            if "rolled_times" not in server_data[server_id]:
                server_data[server_id]["rolled_times"] = {}

            expired_players = []

            for player_id, (rolled_time, expiration_time) in server_data[server_id]["rolled_times"].items():
                if current_time > expiration_time:
                    expired_players.append(player_id)

            for player_id in expired_players:
                del server_data[server_id]["rolled_times"][player_id]

        await asyncio.sleep(60)

async def transfer_market(msg, user, player_to_list, command):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    
    if user_id not in server_data[server_id]["user_upgrades"]:
        server_data[server_id]["user_upgrades"][user_id] = [0, 0, 0, 0]
        
    if user_id not in server_data[server_id]["user_market"]:
        server_data[server_id]["user_market"][user_id] = 0
        
    if user_id not in server_data[server_id]["user_market_bool"]:
        server_data[server_id]["user_market_bool"][user_id] = False
        
    if user_id not in server_data[server_id]["user_market_player"]:
        server_data[server_id]["user_market_player"][user_id] = ""
        
    if user_id not in user_transfer_tasks:
        user_transfer_tasks[user_id] = None
        
    if user_id not in server_data[server_id]["user_market_wait"]:
        server_data[server_id]["user_market_wait"][user_id] = 0
        
    if user_id not in server_data[server_id]["user_refund"]:
        server_data[server_id]["user_refund"][user_id] = 0
        
    if user_id not in server_data[server_id]["user_team_players"]:
        server_data[server_id]["user_team_players"][user_id] = []
    
    print(command)
    
    async def transfer_time(time_to_wait, player):
        try:
            await msg.channel.send(f"{user.mention} Successfully added {player[0]} to the transfer list.")
            task = asyncio.create_task(asyncio.sleep(time_to_wait))
            task.starttime = time.time()
            user_transfer_tasks[user_id] = task
            server_data[server_id]["user_market_wait"][user_id] = time.time() + time_to_wait
                            
            new_value = float(server_data[server_id]["user_market"][user_id] * 1.5)
            if server_data[server_id]["user_upgrades"][user_id][1] != 0:
                new_value += new_value * (responses.board_upgrades[server_data[server_id]["user_upgrades"][user_id][1] - 1] / 100)
                                
            server_data[server_id]["user_refund"][user_id] += int(new_value)
            
            try:
                await task
            except Exception as e:
                print(e)
            
            server_data[server_id]["user_refund"][user_id] = 0
                                
            server_data[server_id]["user_coins"][user_id] += int(new_value)
            await msg.channel.send(f"{user.mention} {player[0]} has been sold for {int(new_value)} \U0001f4a0 !")
                
            for player in server_data[server_id]["user_team_players"][user_id]:
                if player[0].lower() == server_data[server_id]["user_market"][user_id].lower():
                    await responses.handle_responses(msg, f"%t rm {player[0]}", msg.author)
                
            server_data[server_id]["user_market_player"][user_id] = ""
            server_data[server_id]["user_market"][user_id] = 0
            server_data[server_id]["user_market_bool"][user_id] = False
            server_data[server_id]["user_market_wait"][user_id] = 0
            
            collection = server_data[server_id]["user_collections"][user_id]
            found_player = None
            i = 0
            for embed in collection:
                if embed[0].lower() == player[0].lower():
                    found_player = embed
                    break
                i += 1
            
            removed_embed = collection.pop(i)
           
            removed_player_id = removed_embed[4].split(", ")[1]
            j = 0
            for player_id in server_data[server_id]["playerids"]:
                if removed_player_id == player_id:
                    server_data[server_id]["playerids"].pop(j)
                    server_data[server_id]["usernames"].pop(j)
                j += 1 
                                
            if not server_data[server_id]["user_tutorial_completion"][user_id][6][3]:
                server_data[server_id]["user_tutorial_completion"][user_id][6][3] = True
                                                        
                if user_id not in server_data[server_id]["user_coins"]:
                    server_data[server_id]["user_coins"][user_id] = 0
                                                        
                await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                                                        
                if False not in server_data[server_id]["user_tutorial_completion"][user_id][6]:
                    server_data[server_id]["user_tutorial_completion"][user_id][7][0] = True
                    server_data[server_id]["user_coins"][user_id] += 750
                    server_data[server_id]["user_current_tutorial"][user_id] = 7
                    await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**! Type %tuto for the next steps!")
        except Exception as e:
            await msg.channel.send("Failed to list player.")
            return        
                        
    if command == "add":
        print("this happened")
        if not server_data[server_id]["user_market_bool"][user_id]:
            search_terms = player_to_list
            normalized_search_terms = [unidecode.unidecode(term.lower()) for term in search_terms]
            collection = server_data[server_id]["user_collections"][user_id]
            
            for player in collection:
                normalized_title = unidecode.unidecode(player[0].lower())
                if all(term.lower() in normalized_title for term in normalized_search_terms):
                    for field in player[3]:
                        if "Value:" in field[0]:
                            server_data[server_id]["user_market"][user_id] = int(field[0].split()[1])
                            break
                    
                    server_data[server_id]["user_market_player"][user_id] = player[0]
                    server_data[server_id]["user_market_bool"][user_id] = True
                    
                    if not server_data[server_id]["user_tutorial_completion"][user_id][6][2]:
                        server_data[server_id]["user_tutorial_completion"][user_id][6][2] = True
                            
                        if user_id not in server_data[server_id]["user_coins"]:
                            server_data[server_id]["user_coins"][user_id] = 0
                                    
                        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                                    
                        if False not in server_data[server_id]["user_tutorial_completion"][user_id][6]:
                            server_data[server_id]["user_tutorial_completion"][user_id][7][0] = True
                            server_data[server_id]["user_coins"][user_id] += 750
                            server_data[server_id]["user_current_tutorial"][user_id] = 7
                            await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**! Type %tuto for the next steps!")
                    
                    if server_data[server_id]["user_upgrades"][user_id][3] == 1:
                        await transfer_time(172800, player)
                    elif server_data[server_id]["user_upgrades"][user_id][3] == 2:
                        await transfer_time(86400, player)
                    elif server_data[server_id]["user_upgrades"][user_id][3] == 3:
                        await transfer_time(43200, player)
                    elif server_data[server_id]["user_upgrades"][user_id][3] == 4:
                        await transfer_time(10800, player)
                    else:
                        await transfer_time(259200, player)
       
                
        else:
            await msg.channel.send(f"Error. You already have a player listed in the transfer market.")
            return
        
    if command == "rm":
        print("this also happened")
        if server_data[server_id]["user_market_bool"][user_id]:
            server_data[server_id]["user_market_player"][user_id] = ""
            server_data[server_id]["user_market"][user_id] = 0
            server_data[server_id]["user_market_bool"][user_id] = False
            server_data[server_id]["user_refund"][user_id] = 0
            
            try:
                user_transfer_tasks[user_id].cancel()
                try:
                    await user_transfer_tasks[user_id]
                    await msg.channel.send("Failed to remove player from transfer list.")
                except:
                    await msg.channel.send("Succesfully emptied transfer list.")
                    return
                        
            except asyncio.CancelledError:
                await msg.channel.send("Failed to remove player from transfer list.")
                return
        else:
            await msg.channel.send("Error. You have no player listed on the transfer market.")

    if command == "":
        menu = "**Welcome to the Transfer Market \U0001f4dc !**\n"
        if server_data[server_id]["user_upgrades"][user_id][3] != 0:
            menu += f"Here you can add a player from your collection to the transfer list, and in **{responses.transfer_upgrades[server_data[server_id]['user_upgrades'][user_id][3] - 1]}**, you will receive 150% of the value of the player you sold!\n" + "\n"
        else:
            menu += f"Here you can add a player from your collection to the transfer list, and in **3 days**, you will receive 150% of the value of the player you sold!\n" + "\n"
            
        menu += "To add a player to the transfer list, type %tm add [player_name]. You may only add one player at a time. Example: %tm add Erling Haaland\n"
        menu += "To remove a player from your transfer list, type %tm rm [player_name]. Example: %tm rm Erling Haaland\n" + "\n"
        menu += "**Transfer List:**\n"
        if server_data[server_id]["user_market_bool"][user_id]:
            menu += f"{server_data[server_id]['user_market_player'][user_id]} - Player will be sold in **{get_time_remaining(server_id, user)}**"
        else:
            menu += "Ready to add a player from your collection!"
            
        print("Sending menu...")
        await msg.channel.send(menu)
        
        if not server_data[server_id]["user_tutorial_completion"][user_id][6][1]:
            server_data[server_id]["user_tutorial_completion"][user_id][6][1] = True
            
            if user_id not in server_data[server_id]["user_coins"]:
                server_data[server_id]["user_coins"][user_id] = 0
                
            await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                                    
            if False not in server_data[server_id]["user_tutorial_completion"][user_id][6]:
                server_data[server_id]["user_tutorial_completion"][user_id][7][0] = True
                server_data[server_id]["user_coins"][user_id] += 750
                server_data[server_id]["user_current_tutorial"][user_id] = 7
                await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**! Type %tuto for the next steps!")
                
async def purchase_confirmation(price_to_upgrade, user, msg):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    
    if server_data[server_id]["user_coins"][user_id] >= price_to_upgrade:
        confirmation_msg = await msg.channel.send(f"Are you sure you want to spend {price_to_upgrade} \U0001f4a0 on this upgrade? You will have {server_data[server_id]['user_coins'][user_id] - price_to_upgrade} \U0001f4a0 left after this purchase. (y/n/yes/no)")
        try:
            response = await client.wait_for('message', timeout=30, check=lambda m: m.author == msg.author and m.channel == msg.channel)
            response_content = response.content.lower()
            if response_content == 'yes' or response_content == 'y':
                return True
            elif response_content == 'no' or response_content == 'n':
                await msg.channel.send("Purchase cancelled.")
                return False
        except asyncio.TimeoutError:
            await msg.channel.send("Confirmation timed out. Purchase cancelled.")
            return False
            
async def set_favorite_club(msg, user, club):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    
    if user_id not in server_data[server_id]["user_favorite_club"]:
        server_data[server_id]["user_favorite_club"][user_id] = ""
    
    with open('../data/players_list.txt', 'r', encoding='utf-8') as f:
        players_list = f.readlines()
    
    search_terms = club 
    normalized_search_terms = [unidecode.unidecode(term.lower()) for term in search_terms]
    favorite_club = ""
    clubs_found = []
    found = False
    
    for line in players_list:
        normalized_line = unidecode.unidecode(line.lower())
        club_search = " ".join(normalized_search_terms)
        if club_search.lower() == normalized_line.split(", ")[2]:
            favorite_club = line.strip().split(", ")[2]
            server_data[server_id]["user_favorite_club"][user_id] = favorite_club
            found = True
            await msg.channel.send(f"{user.mention} Your favorite club has been set to {favorite_club}")
            
            if not server_data[server_id]["user_tutorial_completion"][user_id][1][1]:
                server_data[server_id]["user_tutorial_completion"][user_id][1][1] = True
                
                if user_id not in server_data[server_id]["user_coins"]:
                    server_data[server_id]["user_coins"][user_id] = 0
                    
                await msg.channel.send("Substep complete! Type %tuto for the next steps!")
            
                if False not in server_data[server_id]["user_tutorial_completion"][user_id][1]:
                    server_data[server_id]["user_coins"][user_id] += 250
                    server_data[server_id]["user_current_tutorial"][user_id] = 2
                    await msg.channel.send("Tutorial 2 complete! You have been rewarded **250 \U0001f4a0**! Type %tuto for the next steps!")
            
            break
    
    if not found:
        for line in players_list:
            normalized_line = unidecode.unidecode(line.lower())

            if line.strip().split(", ")[2] not in clubs_found:
                for term in normalized_search_terms:
                    if term in normalized_line.split(", ")[2]:
                        club_found = line.strip().split(", ")[2]
                        clubs_found.append(club_found)
        
        if len(clubs_found) == 0:
            await msg.channel.send("Club not found in our database.")
            return
        
        mult_msg = f"{len(clubs_found)} matches. Please retype the command with one of the names below.\n"
        for clubs in clubs_found:   
            mult_msg += clubs + "\n"
        
        try:
            await msg.channel.send(mult_msg)
        except:
            await msg.channel.send("Error has occurred. Too many matches.")
        return    
            
async def display_profile(msg, user):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    
    if user_id not in server_data[server_id]["user_coins"]:
        server_data[server_id]["user_coins"][user_id] = 0
        
    if user_id not in server_data[server_id]["user_max_rolls"]:
        server_data[server_id]["user_max_rolls"][user_id] = 9
            
    if user_id not in server_data[server_id]["user_rolls"]:
        server_data[server_id]["user_rolls"][user_id] = server_data[server_id]["user_max_rolls"][user_id]
            
    if user_id not in server_data[server_id]["user_can_claim"]:
        server_data[server_id]["user_can_claim"][user_id] = True
        
    if user_id not in server_data[server_id]["user_favorite_club"]:
        server_data[server_id]["user_favorite_club"][user_id] = ""
        
    if user_id not in server_data[server_id]["user_daily_bool"]:
        server_data[server_id]["user_daily_bool"][user_id] = True
        
    if user_id not in server_data[server_id]["user_daily_wait"]:
        server_data[server_id]["user_daily_wait"][user_id] = 0
        
    if user_id not in server_data[server_id]["user_collections"]:
        server_data[server_id]["user_collections"][user_id] = []
        
    profile = f"**{user.name}'s Profile**\n"
    curr_time = time.time()
    
    time_left_claim = format_time(7200 - (curr_time - server_data[server_id]["claim_reset_time"]))
    if server_data[server_id]["user_can_claim"][user_id]:
        profile += f"You can __claim__ now! Claim reset is in **{time_left_claim}**.\n"
    else:
        profile += f"You can't claim for another **{time_left_claim}**.\n"
    
    time_left_rolls = format_time(3600 - (curr_time - server_data[server_id]["roll_reset_time"]))
    profile += f"You have **{server_data[server_id]['user_rolls'][user_id]}** rolls left. Rolls will replenish in **{time_left_rolls}**.\n" + "\n"
    
    time_left_daily = format_time(server_data[server_id]["user_daily_wait"][user_id] - curr_time)
    if server_data[server_id]["user_daily_bool"][user_id]:
        profile += "__Your daily reward is ready!__\n" + "\n"
    else:
        profile += f"Your daily reward will be ready in **{time_left_daily}**.\n" + "\n"
    
    if server_data[server_id]["user_favorite_club"][user_id] != "":
        profile += f"Your favorite club is set to **{server_data[server_id]['user_favorite_club'][user_id]}**.\n"
        
    profile += f"You have **{len(server_data[server_id]['user_collections'][user_id])}** player(s) in your collection.\n" + "\n"
    
    profile += "You have " + str(server_data[server_id]["user_coins"][user_id]) + " \U0001f4a0"
    
    await msg.channel.send(profile)
    
    if not server_data[server_id]["user_tutorial_completion"][user_id][1][0]:
        server_data[server_id]["user_tutorial_completion"][user_id][1][0] = True
        
        if user_id not in server_data[server_id]["user_coins"]:
            server_data[server_id]["user_coins"][user_id] = 0
            
        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
    
        if False not in server_data[server_id]["user_tutorial_completion"][user_id][1]:
            server_data[server_id]["user_coins"][user_id] += 250
            server_data[server_id]["user_current_tutorial"][user_id] = 2
            await msg.channel.send("Tutorial 2 complete! You have been rewarded **250 \U0001f4a0**! Type %tuto for the next steps!")        

async def extract_user_id(mention):
    pattern = r"<@!?(\d+)>"
    match = re.match(pattern, mention)
    if match:
        user_id = match.group(1)
        return str(user_id)
    else:
        return None

async def send_message(msg, user_msg, is_private):
    try:
        response = await responses.handle_responses(msg, user_msg, msg.author)
        print("it is about to send")
        await msg.author.send(embed=response) if is_private else await msg.channel.send(embed=response)
        print("it sent")
            
    except Exception as e:
        print(e)

async def remove_player(user, msg, player):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    
    if user_id not in server_data[server_id]["user_upgrades"]:
        server_data[server_id]["user_upgrades"][user_id] = [0, 0, 0, 0]
        
    if user_id not in server_data[server_id]["user_coins"]:
        server_data[server_id]["user_coins"][user_id] = 0
    
    if user_id in server_data[server_id]["user_collections"]:
        collection = server_data[server_id]["user_collections"][user_id]
        i = 0
        found_player = None
        found_player_value = 0
        
        for embed in collection:
            if embed[0].lower() == player.lower():
                found_player = embed
                break
            i += 1
            
        if found_player:
            for field in found_player[3]:
                if "Value:" in field[0]:
                    found_player_value = float(field[0].split()[1])
            
            if server_data[server_id]["user_upgrades"][user_id][1] != 0:
                found_player_value += found_player_value * (responses.board_upgrades[server_data[server_id]["user_upgrades"][user_id][1] - 1] / 100)
                found_player_value = int(found_player_value)
                
            confirmation_msg = await msg.channel.send(f"Are you sure you want to remove {found_player[0]} from your collection? You will receive {int(found_player_value)} \U0001f4a0 (y/n/yes/no)")
            try:
                response = await client.wait_for('message', timeout=30, check=lambda m: m.author == msg.author and m.channel == msg.channel)
                response_content = response.content.lower()
                if response_content == 'yes' or response_content == 'y':
                    removed_embed = collection.pop(i)
                    
                    removed_player_id = removed_embed[4].split(", ")[1]
                    j = 0
                    for player_id in server_data[server_id]["playerids"]:
                        if removed_player_id == player_id:
                            server_data[server_id]["playerids"].pop(j)
                            server_data[server_id]["usernames"].pop(j)
                        j += 1
                    
                    server_data[server_id]["user_coins"][user_id] += int(found_player_value)
                    await msg.channel.send(f"{removed_embed[0]} was removed from {user.mention}'s collection.")
                    
                    if user_id not in server_data[server_id]["user_team_players"]:
                        server_data[server_id]["user_team_players"][user_id] = []
                    
                    for players in server_data[server_id]["user_team_players"][user_id]:
                        if players[0] == removed_embed[0]:
                            await responses.handle_responses(msg, f"%t rm {removed_embed[0]}", msg.author)
                            
                    if user_id not in server_data[server_id]["user_market_player"]:
                        server_data[server_id]["user_market_player"][user_id] = ""
                        
                    print(player)
                    print(server_data[server_id]["user_market_player"][user_id])        
                    if player.lower() == server_data[server_id]["user_market_player"][user_id].lower():
                        await transfer_market(msg, user, player, "rm")
                    
                    print(server_data[server_id]["user_tutorial_completion"][user_id][2][4])
                    if not server_data[server_id]["user_tutorial_completion"][user_id][2][4]:
                        print("remove step worked")
                        server_data[server_id]["user_tutorial_completion"][user_id][2][4] = True
                        
                        if user_id not in server_data[server_id]["user_max_rolls"]:
                            server_data[server_id]["user_max_rolls"][user_id] = 9
                            
                        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                    
                        if False not in server_data[server_id]["user_tutorial_completion"][user_id][2]:
                            print("works")
                            server_data[server_id]["user_max_rolls"][user_id] += 1
                            server_data[server_id]["user_current_tutorial"][user_id] = 3
                            await msg.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**! Type %tuto for the next steps!")
                    
                elif response_content == 'no' or response_content == 'n':
                    await msg.channel.send("Removal cancelled.")
            except asyncio.TimeoutError:
                await msg.channel.send("Confirmation timed out. Removal cancelled.")
        else:
            await msg.channel.send(f"Error: {player} was not found in your collection.")
    else:
        await msg.channel.send("Error: No players found in your collection.")
        
async def match(user, msg):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    
    if user_id not in server_data[server_id]["user_team_players"]:
        server_data[server_id]["user_team_players"][user_id] = []
        
    user_team = server_data[server_id]["user_team_players"][user_id]
    
    if len(user_team) != 11:
        await msg.channel.send("Not enough players on your team.")
        return
    
    
    wager_msg = await msg.channel.send(f"{user.mention} Enter how many coins you would like to wager (500 coins minimum). Type c to cancel.")
    
    repeat = True
    while repeat:
        try:
            response = await client.wait_for('message', timeout=30, check=lambda m: m.author == msg.author and m.channel == msg.channel)
            response_content = response.content.lower()
            
            if response_content == "c".lower():
                repeat = False
                await msg.channel.send(f"Match cancelled.")
                continue
            
            try:
                if int(response_content) < 500 or int(response_content) > server_data[server_id]["user_coins"][user_id]:
                    second_wager_msg = await msg.channel.send(f"{user.mention} Mention the user you would like to play against. Type c to cancel.")
                    repeat_2 = True
                    while repeat_2:
                        try:
                            response_2 = await client.wait_for('message', timeout=60, check=lambda m: m.author == msg.author and m.channel == msg.channel)
                            response_content_2 = response_2.content.lower()
                    
                            other_id = await extract_user_id(response_content_2)
                            
                            if other_id not in server_data[server_id]["user_team_players"]:
                                server_data[server_id]["user_team_players"][other_id] = []
                                
                            other_team = server_data[server_id]["user_team_players"][other_id]
                            
                            if response_content_2 == "c":
                                repeat_2 = False
                                continue
                            
                            if len(other_team) != 11:
                                await msg.channel.send("Not enough players on opponent's team.")
                                repeat_2 = False
                                continue
                                
                            try:
                                if int(response_content) > server_data[server_id]["user_coins"][other_id]:
                                    confirm_msg = await msg.channel.send(f"<@{other_id}> Do you agree to initiate this match? ({response_content} coins) (y/n/yes/no).")
                                    
                                    response_3 = await client.wait_for('message', timeout=300, check=lambda m: m.author == client.get_user(int(other_id)) and m.channel == msg.channel)
                                    response_content_3 = response_3.content.lower()
                                    
                                    if response_content_3 == "yes" or response_content_3 == "y":
                                        await match_start(user, msg, other_id)
                                        repeat = False
                                        repeat_2 = False
                                    elif response_content_3 == "no" or response_content_3 == "n":
                                        await msg.channel.send(f"Match cancelled.")
                                        repeat = False
                                        repeat_2 = False
                                else:
                                    await msg.channel.send(f"Opponent does not have enough coins. Match cancelled.")
                                    return
                            except KeyError:
                                await msg.channel.send(f"No coins found. Match cancelled.")
                                return
                                            
                        except asyncio.TimeoutError:
                            await msg.channel.send(f"<@{other_id}> You took too long to respond. Match cancelled.")
                            return
                            
                else:
                    await msg.channel.send(f"Unsufficent coins. Match cancelled.")
                    return
                    
            except KeyError:
                await msg.channel.send(f"No coins found. Match cancelled.")
                return
                
                
                                    
        except asyncio.TimeoutError:
            await msg.channel.send(f"<@{user_id}> You took too long to respond. Match cancelled.")
            return
            


async def match_start(user, msg, other_id):
    
    await msg.channel.send("Test worked")
    return
    
    """
    await msg.channel.send("Match rules:" + "\n" + "Winner takes all the money wagered. If the game ends in a draw, both players will receive back the money they wagered." + "/n" + "Both teams will have shots on goal randomly throughout the match. A stronger defense and goalkeeper will increase the chances of a shot getting blocked, while stronger forwards will contributing to higher goal scoring chance. Midfielders contribute both to defense and offense.")
    
    user_team_players = server_data[server_id]["user_team_players"][user_id] 
    other_team_players = server_data[server_id]["user_team_players"][other_id]
    
    user_team = server_data[server_id]["user_teams"][user_id] 
    other_team = server_data[server_id]["user_teams"][other_id]
    
    forward_pos = ["LW", "ST", "RW", "CF"]
    midfield_pos = ["CAM", "LM", "RM", "CM", "CDM"]
    defense_pos = ["LWB", "RWB", "LB", "RB", "CB", "SW", "GK"]
    
    fpos = ["F1", "F2", "F3"]
    mpos = ["M1", "M2", "M3", "M4"]
    dpos = ["D1", "D2", "D3", "GK"]
    
    user_f_count = []
    user_m_count = []
    user_d_count = []
    
    other_f_count = []
    other_m_count = []
    other_d_count = []
    
    for player in user_team[3]:
        for player_to_compare in user_team_players:
            if player[1].trim() == player_to_compare[0].trim():
                if player[0].trim() in fpos:
                    user_f_count.append(int(player_to_compare[3][1][0].split()[1]))
                if player[0].trim() in mpos:
                    user_m_count.append(int(player_to_compare[3][1][0].split()[1]))
                if player[0].trim() in dpos:
                    user_d_count.append(int(player_to_compare[3][1][0].split()[1]))
                    
    for player in other_team[3]:
        for player_to_compare in other_team_players:
            if player[1].trim() == player_to_compare[0].trim():
                if player[0].trim() in fpos:
                    other_f_count.append(int(player_to_compare[3][1][0].split()[1]))
                if player[0].trim() in mpos:
                    other_m_count.append(int(player_to_compare[3][1][0].split()[1]))
                if player[0].trim() in dpos:
                    other_d_count.append(int(player_to_compare[3][1][0].split()[1]))
    
    """       
        
    
    
                            
                            
                    
                    
 
async def trade_player(user, msg, player, mention):
    server_id = str(msg.guild.id)
    
    user_id = str(user.id)
    other_id = await extract_user_id(mention)
    
    if user_id not in server_data[server_id]["user_team_players"]:
        server_data[server_id]["user_team_players"][user_id] = []
    
    other_user = client.get_user(int(other_id))
    
    user_collection = server_data[server_id]["user_collections"][user_id]
    other_collection = server_data[server_id]["user_collections"][other_id]
    
    user_embed_trade = None
    other_embed_trade = None
    
    user_i = 0
    other_i = 0
    
    for embed in user_collection:
        if embed[0].lower() == player.lower():
            user_embed_trade = embed
            break
        user_i += 1
    
    if not user_embed_trade:
        await msg.channel.send(f"Error: {player} was not found in your collection.")
        return
    
    repeat = True
    while repeat:
        trade_msg = await msg.channel.send(f"<@{other_id}> Please enter the player you would like to trade or type n/no to decline.")
        
        def check_response(m):
            return m.author.id == int(other_id) and m.channel == msg.channel
        
        try:
            response = await client.wait_for('message', timeout=180, check=check_response)
            response_content = response.content.lower()
            
            if response_content == "n" or response_content == "no":
                await msg.channel.send("Trade cancelled.")
                repeat = False
            else:
                other_i = 0
                for embed in other_collection:
                    if embed[0].lower() == response_content:
                        print(embed[0].lower())
                        print(other_i)
                        other_embed_trade = embed
                        repeat = False
                        break
                        
                    other_i += 1
                    
                if not other_embed_trade:
                    await msg.channel.send(f"<@{other_id}> Could not find that player in your collection. Please try again.")
                          
        except asyncio.TimeoutError:
            await msg.channel.send(f"<@{other_id}> You took too long to respond. Trade cancelled.")
            return
        
        user_confirm = False
        
        if other_embed_trade:
            confirmation_msg = await msg.channel.send(f"{user.mention} You are trading {user_embed_trade[0]} for {other_embed_trade[0]}. Do you confirm this trade? (y/n/yes/no)")
            
            def check_user_response(m):
                    return m.author.id == int(user_id) and m.channel == msg.channel
            
            try:
                response = await client.wait_for('message', timeout=100, check=check_user_response)
                response_content = response.content.lower()
                if response_content == 'yes' or response_content == 'y':
                    user_confirm = True
                elif response_content == 'no' or response_content == 'n':
                    await msg.channel.send("Trade cancelled.")
            except asyncio.TimeoutError:
                await msg.channel.send("Confirmation timed out. Trade cancelled.")
        
        if user_confirm:
            confirmation_msg = await msg.channel.send(f"<@{other_id}> You are trading {other_embed_trade[0]} for {user_embed_trade[0]}. Do you confirm this trade? (y/n/yes/no)")
            
            def check_response(m):
                return m.author.id == int(other_id) and m.channel == msg.channel
        
            try:
                response = await client.wait_for('message', timeout=100, check=check_response)
                response_content = response.content.lower()
                
                if response_content == 'yes' or response_content == 'y':
                    j = 0
                    
                    user_removed = user_collection.pop(user_i)
                    print(other_i)
                    other_removed = other_collection.pop(other_i)
                    
                    user_removed_playerid = user_removed[4].split(", ")[1]
                    other_removed_playerid = other_removed[4].split(", ")[1]
                    
                    for playerid in server_data[server_id]["playerids"]:
                        if user_removed_playerid == playerid:
                            server_data[server_id]["playerids"].pop(j)
                            server_data[server_id]["usernames"].pop(j)
                        if other_removed_playerid == playerid:
                            server_data[server_id]["playerids"].pop(j)
                            server_data[server_id]["usernames"].pop(j)
                        j += 1
                    
                    server_data[server_id]["playerids"].append(user_removed_playerid)
                    server_data[server_id]["usernames"].append(other_user.name)
                    
                    server_data[server_id]["playerids"].append(other_removed_playerid)
                    server_data[server_id]["usernames"].append(user.name)
                    
                    user_removed[1] = user_removed[1].replace(f"**Claimed by {user.name}**", f"**Claimed by {other_user.name}**") 
                    other_removed[1] = other_removed[1].replace(f"**Claimed by {other_user.name}**", f"**Claimed by {user.name}**")
                    
                    server_data[server_id]["user_collections"][user_id].append(other_removed)
                    server_data[server_id]["user_collections"][other_id].append(user_removed)
                    
                    for player in server_data[server_id]["user_team_players"][user_id]:
                        if player[0] == user_removed[0]:
                            await responses.handle_responses(msg, f"%t rm {user_removed[0]}", msg.author)
                            
                    for player in server_data[server_id]["user_team_players"][other_id]:
                        if player[0] == other_removed[0]:
                            await responses.handle_responses(msg, f"%t rm {other_removed[0]}", msg.author) 
                    
                    await msg.channel.send("Trade successful!")
                    
                    if not server_data[server_id]["user_tutorial_completion"][user_id][6][0]:
                        server_data[server_id]["user_tutorial_completion"][user_id][6][0] = True
                        
                        if user_id not in server_data[server_id]["user_coins"]:
                            server_data[server_id]["user_coins"][user_id] = 0
                            
                        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                            
                        if False not in server_data[server_id]["user_tutorial_completion"][user_id][6]:
                            server_data[server_id]["user_tutorial_completion"][user_id][7][0] = True
                            server_data[server_id]["user_coins"][user_id] += 750
                            server_data[server_id]["user_current_tutorial"][user_id] = 7
                            await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**! Type %tuto for the next steps!")
                    
                elif response_content == 'no' or response_content == 'n':
                    await msg.channel.send("Trade cancelled.")
            
            except asyncio.TimeoutError:
                await msg.channel.send("Confirmation timed out. Trade cancelled.")

async def give_player(user, msg, player, mention):
    server_id = str(msg.guild.id)
    user_id = str(user.id)
    mention_id = await extract_user_id(mention)
    
    mention_user = client.get_user(int(mention_id))
    
    user_collection = server_data[server_id]["user_collections"][user_id]
    other_collection = server_data[server_id]["user_collections"][mention_id]
    
    player_to_give = None
    
    for embed in user_collection:
        if embed[0].lower() == player.lower():
            player_to_give = embed
            break
        
    if player_to_give is None:
        await msg.channel.send(f"{player} was not found in your collection")
        return
    
    confirmation_msg = await msg.channel.send(f"Are you sure you want to give {player} to <@{mention_id}> ? (y/n/yes/no)")
    repeat = True
    
    while repeat:
        try:
            response = await client.wait_for('message', timeout=30, check=lambda m: m.author == msg.author and m.channel == msg.channel)
            response_content = response.content.lower()
            
            if response_content == 'yes' or response_content == 'y':
                player_to_give_id = player_to_give[4].split(", ")[1]
                
                j = 0
                for playerid in server_data[server_id]["playerids"]:
                    if playerid == player_to_give_id:
                        server_data[server_id]["playerids"].pop(j)
                        server_data[server_id]["usernames"].pop(j)
                        break
                    
                    j += 1
                    
                player_to_give[1] = player_to_give[1].replace(f"**Claimed by {user.name}**", f"**Claimed by {mention_user.name}**")
                
                server_data[server_id]["playerids"].append(player_to_give_id)
                server_data[server_id]["usernames"].append(mention_user.name)
                
                server_data[server_id]["user_collections"][mention_id].append(player_to_give)
                
                await msg.channel.send(f"<@{mention_id}> You have received {player} from <@{user_id}>!")
                
                repeat = False
                
            elif response_content == 'no' or response_content == 'n':
                await msg.channel.send("Process cancelled.")
                repeat = False
                
        except asyncio.TimeoutError:
            await msg.channel.send("Confirmation timed out. Process cancelled.")
            repeat = False
                            
def run_discord_bot():
    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')
        
        create_tables()
        
        for guild in client.guilds:
            server_id = str(guild.id)
            loaded_data = load_server_data(server_id)
            
            if loaded_data:
                print("this happened")
                server_data[server_id] = loaded_data
            else:
                print("this happened instead")
                server_data.setdefault(server_id, {
                    "user_collections": {},
                    "user_current_page": {},
                    "user_coins": {},
                    "user_favorite_club": {},
                    "user_free_claims": {},
                    "user_club_name": {},
                    "mentioned_user": {},
                    "user_daily_wait": {},
                    "user_daily_bool": {},
                    "user_market": {},
                    "user_market_player": {},
                    "user_market_bool": {},
                    "user_refund": {},
                    "user_market_wait": {},
                    "playerids": [],
                    "usernames": [],
                    "roll_reset_time": time.time(),
                    "claim_reset_time": time.time(),
                    "user_teams": {},
                    "user_team_players": {},
                    "user_upgrades": {},
                    "user_team_rewards": {},
                    "rolled_times": {},
                    "user_max_rolls": {},
                    "user_rolls": {},
                    "user_can_claim": {},
                    "user_tutorial": {},
                    "user_tutorial_completion": {},
                    "user_current_tutorial": {},
            })
        
        client.loop.create_task(clean_up_rolled_times())
        client.loop.create_task(roll_timer())
        client.loop.create_task(claim_timer())
        
        
    @client.event
    async def on_message(msg):
        print("bruh")
        
        if msg.author == client.user:
            return
        
        server_id = str(msg.guild.id)
        
        username = str(msg.author)
        user_msg = str(msg.content)
        channel = str(msg.channel)
        
        global collection_messages
        
        if server_id not in server_data:
            server_data[server_id] = {
                "user_collections": {},
                "user_current_page": {},
                "user_coins": {},
                "user_favorite_club": {},
                "user_free_claims": {},
                "user_club_name": {},
                "mentioned_user": {},
                "user_daily_wait": {},
                "user_daily_bool": {},
                "user_market": {},
                "user_market_player": {},
                "user_market_bool": {},
                "user_refund": {},
                "user_market_wait": {},
                "playerids": [],
                "usernames": [],
                "roll_reset_time": time.time(),
                "claim_reset_time": time.time(),
                "user_teams": {},
                "user_team_players": {},
                "user_upgrades": {},
                "user_team_rewards": {},
                "rolled_times": {},
                "user_max_rolls": {},
                "user_rolls": {},
                "user_can_claim": {},
                "user_tutorial": {},
                "user_tutorial_completion": {},
                "user_current_tutorial": {},
            }
        
        save_server_data(server_id, server_data[server_id])
        
        print(f"{username} said: '{user_msg}' ({channel})")
        
        
        if str(msg.author.id) not in server_data[server_id]["user_coins"]:
            server_data[server_id]["user_coins"][str(msg.author.id)] = 0
            
        if str(msg.author.id) not in server_data[server_id]["user_refund"]:
            server_data[server_id]["user_refund"][str(msg.author.id)] = 0
            
        if str(msg.author.id) not in user_refund_bool:
            user_refund_bool[str(msg.author.id)] = False
            
        if str(msg.author.id) not in user_daily:
            user_daily[str(msg.author.id)] = False
            
        print(user_refund_bool[str(msg.author.id)])
        
        if not user_refund_bool[str(msg.author.id)]:
            server_data[server_id]["user_coins"][str(msg.author.id)] += server_data[server_id]["user_refund"][str(msg.author.id)]
            server_data[server_id]["user_market_player"][str(msg.author.id)] = ""
            server_data[server_id]["user_market"][str(msg.author.id)] = 0
            server_data[server_id]["user_market_bool"][str(msg.author.id)] = False
            server_data[server_id]["user_market_wait"][str(msg.author.id)] = 0
            
            if server_data[server_id]["user_refund"][str(msg.author.id)] != 0:
                await msg.channel.send(f"{msg.author.mention} You have been refunded {server_data[server_id]['user_refund'][str(msg.author.id)]} \U0001f4a0 from the transfer market!") 
            
            server_data[server_id]["user_refund"][str(msg.author.id)] = 0
            user_refund_bool[str(msg.author.id)] = True
            print(user_refund_bool[str(msg.author.id)])
        
        if not user_daily[str(msg.author.id)]:
            server_data[server_id]["user_daily_bool"][str(msg.author.id)] = True
            user_daily[str(msg.author.id)] = True
            
        if str(msg.author.id) not in server_data[server_id]["user_tutorial_completion"]:
            server_data[server_id]["user_tutorial_completion"][str(msg.author.id)] = [[False], [False, False, False], [False, False, False, False, False, False], [False, False], [False, False, False, False, False], [False, False, False], [False, False, False, False], [False]]
        
        if str(msg.author.id) not in server_data[server_id]["user_current_tutorial"]:
            server_data[server_id]["user_current_tutorial"][str(msg.author.id)] = 0
        
        if str(msg.author.id) not in server_data[server_id]["user_upgrades"]:
            server_data[server_id]["user_upgrades"][str(msg.author.id)] = [0,0,0,0]
        
        if user_msg[0] == "?":
            user_msg = user_msg[1:]
            await send_message(msg, user_msg, is_private=True)
        elif user_msg.startswith("%c"):
            collection_messages = {}
            server_data[server_id]["mentioned_user"][str(msg.author.id)] = ""
            if len(user_msg.split()) == 1:
                await show_collection(msg.author, msg, 0, "")
                save_server_data(server_id, server_data[server_id])
            
            elif "@" in user_msg.split()[1] and len(user_msg.split()) == 2:
                server_data[server_id]["mentioned_user"][str(msg.author.id)] = user_msg.split()[1]
                await show_collection(msg.author, msg, 0, server_data[server_id]["mentioned_user"][str(msg.author.id)])
                save_server_data(server_id, server_data[server_id])
                
            elif "@" in user_msg.split()[1] and len(user_msg.split()) == 3:
                server_data[server_id]["mentioned_user"][str(msg.author.id)] = user_msg.split()[1]
                await show_collection(msg.author, msg, int(user_msg.split()[2]) - 1, server_data[server_id]["mentioned_user"][str(msg.author.id)])
                save_server_data(server_id, server_data[server_id])
                
            elif "@" in user_msg.split()[2] and len(user_msg.split()) == 3:
                server_data[server_id]["mentioned_user"][str(msg.author.id)] = user_msg.split()[2]
                await show_collection(msg.author, msg, int(user_msg.split()[1]) - 1, server_data[server_id]["mentioned_user"][str(msg.author.id)])
                save_server_data(server_id, server_data[server_id])
            
            else:
                await show_collection(msg.author, msg, int(user_msg.split()[1]) - 1, "")
                save_server_data(server_id, server_data[server_id])
                
        elif user_msg.startswith("%rm"):
            if len(user_msg.split()) == 1:
                await msg.channel.send("Please specify who you wish to remove from your collection.")
                save_server_data(server_id, server_data[server_id])
            else:
                player_name = user_msg[4:].strip()
                await remove_player(msg.author, msg, player_name)
                save_server_data(server_id, server_data[server_id])
        
        elif user_msg.startswith("%trade") or user_msg.startswith("%tr"):
            mention = user_msg.split()[1]
            player_to_trade = " ".join(user_msg.split()[2:])
            await trade_player(msg.author, msg, player_to_trade, mention)
            save_server_data(server_id, server_data[server_id])
        
        elif user_msg == "%p":
            await display_profile(msg, msg.author)
            save_server_data(server_id, server_data[server_id])
        
        elif user_msg.startswith("%sc"):
            club = user_msg.split()[1:]
            await set_favorite_club(msg, msg.author, club)
            save_server_data(server_id, server_data[server_id])
            
        elif user_msg.startswith("%tm"):
            if len(user_msg.split()) == 1:
                await transfer_market(msg, msg.author, [], "")
                save_server_data(server_id, server_data[server_id])
            else:
                player_to_list = user_msg.split()[2:]
                command = user_msg.split()[1]
                await transfer_market(msg, msg.author, player_to_list, command)
                save_server_data(server_id, server_data[server_id])
                
        elif user_msg == "%fc":
            await free_claim(msg, msg.author)
            save_server_data(server_id, server_data[server_id])
        
        elif user_msg == "%d":
            await dailies(msg, msg.author)
            save_server_data(server_id, server_data[server_id])
            
        elif user_msg == "%s":
            await sort_collection(msg, msg.author)
            save_server_data(server_id, server_data[server_id])
            
        elif user_msg.startswith("%m") and user_msg != "%match":
            position = int(user_msg.split()[1])
            player_to_move = user_msg.split()[2:]
            await move_player(msg, msg.author, player_to_move, position)
            save_server_data(server_id, server_data[server_id])
            
        elif user_msg.startswith("%n"):
            if len(user_msg.split()) == 1:
                await rename_club(msg, msg.author, [])
                save_server_data(server_id, server_data[server_id])
            else:
                name = user_msg.split()[1:]
                await rename_club(msg, msg.author, name)
                save_server_data(server_id, server_data[server_id])
        
        elif user_msg.startswith("%give"):
            print("happening")
            mention = user_msg.split()[1]
            player = " ".join(user_msg.split()[2:])
            await give_player(msg.author, msg, player, mention)
                
        elif user_msg.startswith("%tuto"):
            tutorial.tutorial_messages = {}
            if len(user_msg.split()) == 1:
                await tutorial.tutorial(msg, msg.author, server_data[server_id]["user_current_tutorial"][str(msg.author.id)])
                save_server_data(server_id, server_data[server_id])
            else:
                page_num = int(user_msg.split()[1]) - 1
                await tutorial.tutorial(msg, msg.author, page_num)
                save_server_data(server_id, server_data[server_id])
                
        elif user_msg == "%match":
            await match(msg.author, msg)
            save_server_data(server_id, server_data[server_id])
                
        elif user_msg == "%r" or user_msg.startswith("%v") or user_msg.startswith("%lc") or user_msg.startswith("%t") or user_msg.startswith("%u") or user_msg == "%index":
            await send_message(msg, user_msg, is_private=False)
            save_server_data(server_id, server_data[server_id])
            
        else:
            save_server_data(server_id, server_data[server_id])
            return
            
    client.run(TOKEN)
            
@client.event
async def on_reaction_add(reaction, user):
    user_id = str(user.id)
    
    print("Reaction added by:", user)
    print("Message author:", reaction.message.author)
    print("Emoji:", reaction.emoji)
    print("Embeds:", reaction.message.embeds)

    if user == client.user:
        print("Bot message.")
        return
    
    if user_id not in user_claim_count:
        user_claim_count[user_id] = 0
    
    if user_id not in server_data[str(user.guild.id)]["mentioned_user"]:
        server_data[str(user.guild.id)]["mentioned_user"][user_id] = ""
    
    if reaction.message.author == client.user:
        server_id = str(user.guild.id)
        
        player_embed = reaction.message.embeds[0]
        username = player_embed.description.split()[-1].strip("*")
        
        user_embed = discord.utils.get(client.get_all_members(), name=username)
        
        if user_id in server_data[server_id]["user_current_page"]:
            if reaction.emoji == "⬅️":
                
                collection_messages[user_id] = reaction.message
  
                if server_data[server_id]["user_current_page"][str(user_embed.id)] == 0:
                    server_data[server_id]["user_current_page"][str(user_embed.id)] = len(server_data[server_id]["user_collections"][str(user_embed.id)]) - 1
                else:
                    server_data[server_id]["user_current_page"][str(user_embed.id)] -= 1
                
                current_page = server_data[server_id]["user_current_page"][str(user_embed.id)]
                await show_collection(user, reaction.message, current_page, user_embed.mention)
                
                save_server_data(server_id, server_data[server_id])
                
                return
                
            elif reaction.emoji == "➡️":
                
                collection_messages[user_id] = reaction.message
                
                if server_data[server_id]["user_current_page"][str(user_embed.id)] == len(server_data[server_id]["user_collections"][str(user_embed.id)]) - 1:
                    server_data[server_id]["user_current_page"][str(user_embed.id)] = 0
                else:
                    server_data[server_id]["user_current_page"][str(user_embed.id)] += 1
                    
                current_page = server_data[server_id]["user_current_page"][str(user_embed.id)]
                await show_collection(user, reaction.message, current_page, user_embed.mention)
                
                save_server_data(server_id, server_data[server_id])
                
                return
            
            elif reaction.emoji == "\u2b05":
                print(server_data[server_id]["user_tutorial_completion"][user_id][server_data[server_id]["user_current_page"][user_id] - 1])
                if False not in server_data[server_id]["user_tutorial_completion"][user_id][server_data[server_id]["user_current_page"][user_id] - 1]: 
                    if server_data[server_id]["user_current_page"][user_id] == 0:
                        server_data[server_id]["user_current_page"][user_id] = len(server_data[server_id]["user_tutorial"][user_id]) - 1
                    else:
                        server_data[server_id]["user_current_page"][user_id] -= 1
                    
                    current_page = server_data[server_id]["user_current_page"][user_id]
                    await tutorial.tutorial(reaction.message, user, current_page)
                    
                    save_server_data(server_id, server_data[server_id])
                    
                    return
                else:
                    await reaction.message.channel.send("Please complete the current tutorial before moving onto another one.")
                    
                    save_server_data(server_id, server_data[server_id])
                    
                    return
            
            elif reaction.emoji == "\u27a1":
                print(server_data[server_id]["user_tutorial_completion"][user_id][server_data[server_id]["user_current_page"][user_id]])
                if False not in server_data[server_id]["user_tutorial_completion"][user_id][server_data[server_id]["user_current_page"][user_id]]:
                    if server_data[server_id]["user_current_page"][user_id] == len(server_data[server_id]["user_tutorial"][user_id]) - 1:
                        server_data[server_id]["user_current_page"][user_id] = 0
                    else:
                        server_data[server_id]["user_current_page"][user_id] += 1
                    
                    current_page = server_data[server_id]["user_current_page"][user_id]
                    await tutorial.tutorial(reaction.message, user, current_page)
                    
                    save_server_data(server_id, server_data[server_id])
                    
                    return
                else:
                    await reaction.message.channel.send("Please complete the current tutorial before moving onto another one.")
                    
                    save_server_data(server_id, server_data[server_id])
                    
                    return
                
    if isinstance(reaction.message.embeds[0], discord.Embed) and "Fantasy Football Draft" in reaction.message.embeds[0].footer.text:
        player_embed = reaction.message.embeds[0]
        player_id = player_embed.footer.text.split(", ")[1]
        
        current_time = time.time()
        can_claim = False
        if (current_time - server_data[server_id]["rolled_times"][player_id][0]) < 60:
            can_claim = True
        
        claimed = False 
        if player_id in server_data[server_id]["playerids"]:
            claimed = True
            
        if (not claimed) and ("**React with any emoji to claim!**" in player_embed.description) and can_claim and server_data[server_id]["user_can_claim"][user_id]:
            print("Player claimed:", player_embed.title)
            user_claim_count[user_id] += 1

            if user_id not in server_data[server_id]["user_collections"]:
                server_data[server_id]["user_collections"][user_id] = []
                
            player_embed.description = player_embed.description.replace("**React with any emoji to claim!**", f"**Claimed by {user.name}**")
            
            player_embed_data = [
                player_embed.title,
                player_embed.description,
                player_embed.color.value,
                [(field.name, field.value, field.inline) for field in player_embed.fields],
                player_embed.footer.text,
                player_embed.image.url if player_embed.image else None
            ]


            server_data[server_id]["user_collections"][user_id].append(player_embed_data)

            player_id = player_embed.footer.text.split(", ")[1]
            server_data[server_id]["playerids"].append(player_id)
            server_data[server_id]["usernames"].append(user.name)
            server_data[server_id]["user_can_claim"][user_id] = False

            await reaction.message.channel.send(f"{user.mention} has added {player_embed.title} to their collection!")
            
            if not server_data[server_id]["user_tutorial_completion"][user_id][0][0]:
                server_data[server_id]["user_tutorial_completion"][user_id][0][0] = True
                
                if user_id not in server_data[server_id]["user_free_claims"]:
                    server_data[server_id]["user_free_claims"][user_id] = 0
                    
                server_data[server_id]["user_free_claims"][user_id] += 1
                server_data[server_id]["user_current_tutorial"][user_id] = 1
                await reaction.message.channel.send("Tutorial 1 complete! You have been rewarded **1 free claim**! Type %tuto for the next steps!")
                
            if len(server_data[server_id]["user_collections"][user_id]) == 2 or user_claim_count[user_id] == 2:
                if not server_data[server_id]["user_tutorial_completion"][user_id][2][0]:
                    server_data[server_id]["user_tutorial_completion"][user_id][2][0] = True
                    
                    if user_id not in server_data[server_id]["user_max_rolls"]:
                        server_data[server_id]["user_max_rolls"][user_id] = 9
                        
                    await reaction.message.channel.send("Substep complete! Type %tuto for the next steps!")
                
                    if False not in server_data[server_id]["user_tutorial_completion"][user_id][2]:
                        server_data[server_id]["user_max_rolls"][user_id] += 1
                        server_data[server_id]["user_current_tutorial"][user_id] = 3
                        await reaction.message.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**! Type %tuto for the next steps!")
                        
            save_server_data(server_id, server_data[server_id])



    
        
    
