import discord
import responses
import asyncio
import re
import emoji
import unidecode
import time
import random
import tutorial

user_collections = {}
user_current_page = {}
collection_messages = {}
user_coins = {}
user_favorite_club = {}
user_free_claims = {}
user_club_name = {}
mentioned_user = {}

user_daily_wait = {}
user_daily_bool = {}

user_market = {}
user_market_player = {}
user_market_bool = {}
user_transfer_tasks = {}
user_market_wait = {}

playerids= []
usernames = []

roll_reset_time = time.time()
claim_reset_time = time.time()

user_coins[456861613966884866] = 1000000000

TOKEN = 'MTEzMjE3MDE4MTAxMjExNTU1Ng.GDeG1g.BDqacvjsdnOz_SHEh-OO7DFsC4_-xfwWreF4Qk'
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
def get_time_remaining():
    task = user_transfer_tasks[user.id]
    if task is not None and not task.done():
        time_remaining = user_market_wait[user.id] - time.time()
        return format_time(time_remaining)
    return ""

async def show_collection(user, msg, page_num, mention):
    if user.id not in user_current_page:
        user_current_page[user.id] = 0
        
    mention_id = 0
        
    if mention == "":
        mention_id = user.id
    else:
        mention_id = await extract_user_id(mention)

    if mention_id in user_collections:
        collection = user_collections[mention_id]
        if 0 <= page_num < len(collection):
            user_current_page[user.id] = page_num
            embed_to_show = collection[page_num]
            embed_to_show.set_footer(text=embed_to_show.footer.text.split(", ")[0] + ", " + embed_to_show.footer.text.split(", ")[1][0:5] + " --- " + f"{user_current_page[user.id] + 1}/{len(user_collections[mention_id])}")
        
            if user.id in collection_messages:
                collection_msg = collection_messages[user.id]
                await collection_msg.clear_reactions()
                await collection_msg.edit(embed=embed_to_show)
            else:
                collection_msg = await msg.channel.send(embed=embed_to_show)
                await collection_msg.clear_reactions()
                collection_messages[user.id] = collection_msg

            await collection_msg.add_reaction("⬅️")
            await collection_msg.add_reaction("➡️")
            
            if mention == "":    
                if not tutorial.user_tutorial_completion[user.id][2][1]:
                    tutorial.user_tutorial_completion[user.id][2][1] = True
                    
                    print(tutorial.user_tutorial_completion[user.id][2])
                            
                    if user.id not in responses.user_max_rolls:
                        responses.user_max_rolls[user.id] = 9
                            
                    if False not in tutorial.user_tutorial_completion[user.id][2]:
                        responses.user_max_rolls[user.id] += 1
                        tutorial.user_current_tutorial[user.id] = 3
                        await msg.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**!")
            else:
                if not tutorial.user_tutorial_completion[user.id][2][5]:
                    tutorial.user_tutorial_completion[user.id][2][5] = True
                    
                    print(tutorial.user_tutorial_completion[user.id][2])
                    
                    if user.id not in responses.user_max_rolls:
                        responses.user_max_rolls[user.id] = 9
                            
                    if False not in tutorial.user_tutorial_completion[user.id][2]:
                        responses.user_max_rolls[user.id] += 1
                        tutorial.user_current_tutorial[user.id] = 3
                        await msg.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**!")
        else:
            await msg.channel.send("Error: Page not found.")
    else:
        await msg.channel.send("Error : No players found in your collection.")

async def rename_club(msg, user, name):
    if user.id not in user_club_name:
        user_club_name[user.id] = ""
        
    if name == []:
        user_club_name[user.id] = ""
        await msg.channel.send(f"{user.mention} Your club's name has been reset to default.")
        return
    
    rename = " ".join(name)
    
    user_club_name[user.id] = rename
    
    await msg.channel.send(f"{user.mention} Your club has been renamed to **{rename}**!")
    
    if not tutorial.user_tutorial_completion[user.id][4][4]:
        tutorial.user_tutorial_completion[user.id][4][4] = True
        
        if user.id not in user_coins:
            user_coins[user.id] = 0
                
        if False not in tutorial.user_tutorial_completion[user.id][4]:
            user_coins[user.id] += 500
            tutorial.user_current_tutorial[user.id] = 5
            await msg.channel.send("Tutorial 5 complete! You have been rewarded **500 \U0001f4a0**!")

async def move_player(msg, user, player, position):
    if user.id not in user_collections:
        user_collections[user.id] = []
        
    if (position > len(user_collections[user.id])) or position < 1:
        await msg.channel.send("Error: Invalid position.")
        return
    
    collection = user_collections[user.id]
    player_to_move = None
    search_terms = player
    normalized_search_terms = [unidecode.unidecode(term.lower()) for term in search_terms]
    i = 0
    for embed in collection:
        embed_title = unidecode.unidecode(embed.title.lower().strip())
        if embed_title == " ".join(normalized_search_terms):
            player_to_move = collection.pop(i)
            break
        i += 1
        
    if player_to_move is None:
        await msg.channel.send(f"Error: {' '.join(player)} was not found in your collection.")
        return
  
    collection.insert(position - 1, player_to_move)
    await msg.channel.send(f"Succesfully moved {player_to_move.title}!")
    
    if not tutorial.user_tutorial_completion[user.id][2][3]:
        tutorial.user_tutorial_completion[user.id][2][3] = True
        
        print(tutorial.user_tutorial_completion[user.id][2])
        
        if user.id not in responses.user_max_rolls:
            responses.user_max_rolls[user.id] = 9
                
        if False not in tutorial.user_tutorial_completion[user.id][2]:
            responses.user_max_rolls[user.id] += 1
            tutorial.user_current_tutorial[user.id] = 3
            await msg.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**!")
     
async def sort_collection(msg, user):
    if user.id not in user_collections:
        user_collections[user.id] = []
        
    def get_embed_value(embed):
        for field in embed.fields:
            if "Value:" in field.name:
                return int(field.name.split()[1])
                                  
    collection = user_collections[user.id]
    collection.sort(key=get_embed_value, reverse=True)
    
    await msg.channel.send("Your collection has been successfully sorted from highest to lowest value.")
    
    if not tutorial.user_tutorial_completion[user.id][2][2]:
        tutorial.user_tutorial_completion[user.id][2][2] = True
        
        print(tutorial.user_tutorial_completion[user.id][2])
        
        if user.id not in responses.user_max_rolls:
            responses.user_max_rolls[user.id] = 9
                
        if False not in tutorial.user_tutorial_completion[user.id][2]:
            responses.user_max_rolls[user.id] += 1
            tutorial.user_current_tutorial[user.id] = 3
            await msg.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**!")

async def dailies(msg, user):
    if user.id not in user_daily_bool:
        user_daily_bool[user.id] = True
        
    if user.id not in user_daily_wait:
        user_daily_wait[user.id] = 0
        
    if user_daily_bool[user.id]:
        chance = random.randint(0, 100)
        daily_reward = 0
        
        if chance < 4:
            daily_reward = float(random.randint(700, 950))
        else:
            daily_reward = float(random.randint(100, 300))
            
        if responses.user_upgrades[user.id][1] != 0:
            daily_reward += daily_reward * (responses.board_upgrades[responses.user_upgrades[user.id][1] - 1] / 100)
            
        await msg.channel.send(f"{user.mention} You have been given **+{int(daily_reward)}**!")
        user_coins[user.id] += int(daily_reward)
        user_daily_bool[user.id] = False
        user_daily_wait[user.id] = time.time() + 86400
        
        if not tutorial.user_tutorial_completion[user.id][1][2]:
            tutorial.user_tutorial_completion[user.id][1][2] = True
            
            if user.id not in user_coins:
                user_coins[user.id] = 0
        
            if False not in tutorial.user_tutorial_completion[user.id][1]:
                user_coins[user.id] += 250
                tutorial.user_current_tutorial[user.id] = 2
                await msg.channel.send("Tutorial 2 complete! You have been rewarded **250 \U0001f4a0**!")
        
        await asyncio.sleep(86400)
        user_daily_bool[user.id] = True
    else:
        time_left = format_time(user_daily_wait[user.id] - time.time())
        await msg.channel.send(f"Your daily reward is not available yet. Please wait **{time_left}**.")

async def team_rewards(msg, user, value):
    if value == 700:
        f = open('players_list.txt', 'r', encoding='utf-8')
        players_list = f.readlines()
        
        rare_players = []
        for line in players_list:
            if int(line.split(", ")[4].split()[1]) >= 830:
                rare_players.append(line)
                
        reward = random.choice(rare_players)
        
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
        embed.set_footer(text="Football Roll Bot, " + player_id)
            
        player_status = f"**Claimed by {user.name}**"
        embed.description += ("\n" + player_status)
        
        user_collections[user.id].append(embed)

        player_id = embed.footer.text.split(", ")[1]
        playerids.append(player_id)
        usernames.append(user.name)
        
        await msg.channel.send(embed=embed)
        
    elif value == 800:
        f = open('legends_list.txt', 'r', encoding='utf-8')
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
        embed.set_footer(text="Football Roll Bot, " + player_id)
            
        player_status = f"**Claimed by {user.name}**"
        embed.description += ("\n" + player_status)
        
        user_collections[user.id].append(embed)

        player_id = embed.footer.text.split(", ")[1]
        playerids.append(player_id)
        usernames.append(user.name)
        
        await msg.channel.send(embed=embed)
        
async def free_claim(msg, user):
    if user.id not in user_free_claims:
        user_free_claims[user.id] = 0
        
    if user_free_claims[user.id] != 0:
        confirmation_msg = await msg.channel.send(f"You have **{user_free_claims[user.id]}** free claim(s). Are you sure you want to use a free claim? Make sure you don't already have claim ready. (y/n/yes/no)")
        try:
            response = await client.wait_for('message', timeout=30, check=lambda m: m.author == msg.author and m.channel == msg.channel)
            response_content = response.content.lower()
            if response_content == 'yes' or response_content == 'y':
                responses.user_can_claim[user.id] = True
                user_free_claims[user.id] -= 1
                await msg.channel.send(f"{user.mention} Successfully used a free claim!")
            elif response_content == 'no' or response_content == 'n':
                await msg.channel.send("Process cancelled.")
        except asyncio.TimeoutError:
            await msg.channel.send("Confirmation timed out. Process cancelled.")
    else:
        await msg.channel.send(f"{user.mention} You do not have any free claims.")

async def claim_timer():
    while True:
        global claim_reset_time
        claim_reset_time = time.time()
            
        for key in responses.user_can_claim:
            responses.user_can_claim[key] = True
            
        await asyncio.sleep(1)

async def roll_timer():
    while True:
        global roll_reset_time
        roll_reset_time = time.time()
            
        for key in responses.user_rolls:
            responses.user_rolls[key] = responses.user_max_rolls[key]
            
        await asyncio.sleep(3600)
        

async def clean_up_rolled_times():
    while True:
        current_time = time.time()
        expired_players = []

        for player_id, (rolled_time, expiration_time) in responses.rolled_times.items():
            if current_time > expiration_time:
                expired_players.append(player_id)

        for player_id in expired_players:
            del responses.rolled_times[player_id]

        await asyncio.sleep(60)

async def transfer_market(msg, user, player_to_list, command):
    if user.id not in responses.user_upgrades:
        responses.user_upgrades[user.id] = [0,0,0,0]
        
    if user.id not in user_market:
        user_market[user.id] = 0
        
    if user.id not in user_market_bool:
        user_market_bool[user.id] = False
        
    if user.id not in user_market_player:
        user_market_player[user.id] = ""
        
    if user.id not in user_transfer_tasks:
        user_transfer_tasks[user.id] = None
        
    if user.id not in user_market_wait:
        user_market_wait[user.id] = 0
    
    task = None
    if command == "add":
        if not user_market_bool[user.id]:
            search_terms = player_to_list
            normalized_search_terms = [unidecode.unidecode(term.lower()) for term in search_terms]
            collection = user_collections[user.id]
            
            for player in collection:
                normalized_title = unidecode.unidecode(player.title.lower())
                if all(term.lower() in normalized_title for term in normalized_search_terms):
                    for field in player.fields:
                        if "Value:" in field.name:
                            user_market[user.id] = int(field.name.split()[1])
                            break
                    
                    user_market_player[user.id] = player.title
                    user_market_bool[user.id] = True
                    
                    if not tutorial.user_tutorial_completion[user.id][6][2]:
                        tutorial.user_tutorial_completion[user.id][6][2] = True
                            
                        if user.id not in user_coins:
                                    user_coins[user.id] = 0
                                    
                        if False not in tutorial.user_tutorial_completion[user.id][6]:
                            tutorial.user_tutorial_completion[user.id][7][0] = True
                            user_coins[user.id] += 750
                            tutorial.user_current_tutorial[user.id] = 7
                            await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**!")
                    
                    if responses.user_upgrades[user.id][3] == 1:
                        try:
                            await msg.channel.send(f"{user.mention} Successfully added {player.title} to the transfer list.")
                            task = asyncio.create_task(asyncio.sleep(30))
                            task.starttime = time.time()
                            user_transfer_tasks[user.id] = task
                            user_market_wait[user.id] = time.time() + 30
                            
                            await task
                            
                            new_value = float(user_market[user.id] * 1.5)
                            if responses.user_upgrades[user.id][1] != 0:
                                new_value += new_value * (responses.board_upgrades[responses.user_upgrades[user.id][1] - 1] / 100)
                                
                            user_coins[user.id] += int(new_value)
                            await msg.channel.send(f"{user.mention} {player.title} has been sold for {new_value} \U0001f4a0 !")
                            user_market_player[user.id] = ""
                            user_market[user.id] = 0
                            user_market_bool[user.id] = False
                            user_market_wait[user.id] = 0
                            
                            if not tutorial.user_tutorial_completion[user.id][6][3]:
                                tutorial.user_tutorial_completion[user.id][6][3] = True
                                    
                                if user.id not in user_coins:
                                    user_coins[user.id] = 0
                                    
                                if False not in tutorial.user_tutorial_completion[user.id][6]:
                                    tutorial.user_tutorial_completion[user.id][7][0] = True
                                    user_coins[user.id] += 750
                                    tutorial.user_current_tutorial[user.id] = 7
                                    await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**!")
                            
                        except asyncio.CancelledError:
                            await msg.channel.send("Failed to list player.")
                            return
                            
                    elif responses.user_upgrades[user.id][3] == 2:
                        try:
                            await msg.channel.send(f"{user.mention} Successfully added {player.title} to the transfer list.")
                            task = asyncio.create_task(asyncio.sleep(172800))
                            task.starttime = time.time()
                            user_transfer_tasks[user.id] = task
                            user_market_wait[user.id] = time.time() + 172800

                            await task
                            
                            new_value = float(user_market[user.id] * 1.5)
                            if responses.user_upgrades[user.id][1] != 0:
                                new_value += new_value * (responses.board_upgrades[responses.user_upgrades[user.id][1] - 1] / 100)
                                
                            user_coins[user.id] += int(new_value)
                            await msg.channel.send(f"{user.mention} {player.title} has been sold for {new_value} \U0001f4a0 !")
                            user_market_player[user.id] = ""
                            user_market[user.id] = 0
                            user_market_bool[user.id] = False
                            user_market_wait[user.id] = 0
                            
                            if not tutorial.user_tutorial_completion[user.id][6][3]:
                                tutorial.user_tutorial_completion[user.id][6][3] = True
                                    
                                if user.id not in user_coins:
                                    user_coins[user.id] = 0
                                    
                                if False not in tutorial.user_tutorial_completion[user.id][6]:
                                    tutorial.user_tutorial_completion[user.id][7][0] = True
                                    user_coins[user.id] += 750
                                    tutorial.user_current_tutorial[user.id] = 7
                                    await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**!")
                            
                        except asyncio.CancelledError:
                            await msg.channel.send("Failed to list player.")
                            return
                    
                    elif responses.user_upgrades[user.id][3] == 3:
                        try:
                            await msg.channel.send(f"{user.mention} Successfully added {player.title} to the transfer list.")
                            task = asyncio.create_task(asyncio.sleep(86400))
                            user_transfer_tasks[user.id] = task
                            user_market_wait[user.id] = time.time() + 86400
                            
                            await task
                            
                            new_value = float(user_market[user.id] * 1.5)
                            if responses.user_upgrades[user.id][1] != 0:
                                new_value += new_value * (responses.board_upgrades[responses.user_upgrades[user.id][1] - 1] / 100)
                                
                            user_coins[user.id] += int(new_value)
                            await msg.channel.send(f"{user.mention} {player.title} has been sold for {new_value} \U0001f4a0 !")
                            user_market_player[user.id] = ""
                            user_market[user.id] = 0
                            user_market_bool[user.id] = False
                            user_market_wait[user.id] = 0
                            
                            if not tutorial.user_tutorial_completion[user.id][6][3]:
                                tutorial.user_tutorial_completion[user.id][6][3] = True
                                    
                                if user.id not in user_coins:
                                    user_coins[user.id] = 0
                                    
                                if False not in tutorial.user_tutorial_completion[user.id][6]:
                                    tutorial.user_tutorial_completion[user.id][7][0] = True
                                    user_coins[user.id] += 750
                                    tutorial.user_current_tutorial[user.id] = 7
                                    await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**!")
                            
                        except asyncio.CancelledError:
                            await msg.channel.send("Failed to list player.")
                            return
                        
                    elif responses.user_upgrades[user.id][3] == 4:
                        try:
                            await msg.channel.send(f"{user.mention} Successfully added {player.title} to the transfer list.")
                            task = asyncio.create_task(asyncio.sleep(43200))
                            task.starttime = time.time()
                            user_transfer_tasks[user.id] = task
                            user_market_wait[user.id] = time.time() + 43200
                            
                            await task
                            
                            new_value = float(user_market[user.id] * 1.5)
                            if responses.user_upgrades[user.id][1] != 0:
                                new_value += new_value * (responses.board_upgrades[responses.user_upgrades[user.id][1] - 1] / 100)
                                
                            user_coins[user.id] += int(new_value)
                            await msg.channel.send(f"{user.mention} {player.title} has been sold for {new_value} \U0001f4a0 !")
                            user_market_player[user.id] = ""
                            user_market[user.id] = 0
                            user_market_bool[user.id] = False
                            user_market_wait[user.id] = 0
                            
                            if not tutorial.user_tutorial_completion[user.id][6][3]:
                                tutorial.user_tutorial_completion[user.id][6][3] = True
                                    
                                if user.id not in user_coins:
                                    user_coins[user.id] = 0
                                    
                                if False not in tutorial.user_tutorial_completion[user.id][6]:
                                    tutorial.user_tutorial_completion[user.id][7][0] = True
                                    user_coins[user.id] += 750
                                    tutorial.user_current_tutorial[user.id] = 7
                                    await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**!")
                            
                        except asyncio.CancelledError:
                            await msg.channel.send("Failed to list player.")
                            return
                    
                    elif responses.user_upgrades[user.id][3] == 5:
                        try:
                            await msg.channel.send(f"{user.mention} Successfully added {player.title} to the transfer list.")
                            task = asyncio.create_task(asyncio.sleep(21600))
                            task.starttime = time.time()
                            user_transfer_tasks[user.id] = task
                            user_market_wait[user.id] = time.time() + 21600
                            
                            await task
                            
                            new_value = float(user_market[user.id] * 1.5)
                            if responses.user_upgrades[user.id][1] != 0:
                                new_value += new_value * (responses.board_upgrades[responses.user_upgrades[user.id][1] - 1] / 100)
                                
                            user_coins[user.id] += int(new_value)
                            await msg.channel.send(f"{user.mention} {player.title} has been sold for {new_value} \U0001f4a0 !")
                            user_market_player[user.id] = ""
                            user_market[user.id] = 0
                            user_market_bool[user.id] = False
                            user_market_wait[user.id] = 0
                            
                            if not tutorial.user_tutorial_completion[user.id][6][3]:
                                tutorial.user_tutorial_completion[user.id][6][3] = True
                                
                                if user.id not in user_coins:
                                    user_coins[user.id] = 0
                                    
                                if False not in tutorial.user_tutorial_completion[user.id][6]:
                                    tutorial.user_tutorial_completion[user.id][7][0] = True
                                    user_coins[user.id] += 750
                                    await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**!")
                            
                        except asyncio.CancelledError:
                            await msg.channel.send("Failed to list player.")
                            return
                    
                    else:
                        try:
                            await msg.channel.send(f"{user.mention} Successfully added {player.title} to the transfer list.")
                            task = asyncio.create_task(asyncio.sleep(432000))
                            task.starttime = time.time()
                            user_transfer_tasks[user.id] = task
                            user_market_wait[user.id] = time.time() + 432000
                            
                            await task
                            
                            new_value = float(user_market[user.id] * 1.5)
                            if responses.user_upgrades[user.id][1] != 0:
                                new_value += new_value * (responses.board_upgrades[responses.user_upgrades[user.id][1] - 1] / 100)
                                
                            user_coins[user.id] += int(new_value)
                            await msg.channel.send(f"{user.mention} {player.title} has been sold for {new_value} \U0001f4a0 !")
                            user_market_player[user.id] = ""
                            user_market[user.id] = 0
                            user_market_bool[user.id] = False
                            user_market_wait[user.id] = 0
                            
                            if not tutorial.user_tutorial_completion[user.id][6][3]:
                                tutorial.user_tutorial_completion[user.id][6][3] = True
                                
                                if user.id not in user_coins:
                                    user_coins[user.id] = 0
                                    
                                if False not in tutorial.user_tutorial_completion[user.id][6]:
                                    tutorial.user_tutorial_completion[user.id][7][0] = True
                                    user_coins[user.id] += 750
                                    tutorial.user_current_tutorial[user.id] = 7
                                    await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**!")
                            
                        except asyncio.CancelledError:
                            await msg.channel.send("Failed to list player.")
                            return
        
        else:
            await msg.channel.send(f"Error. You already have a player listed in the transfer market.")
            return
        
    if command == "rm":
        if user_market_bool[user.id]:
            user_market_player[user.id] = ""
            user_market[user.id] = 0
            user_market_bool[user.id] = False
            try:
                task.cancel()
                try:
                    await task
                except:
                    await msg.channel.send("Failed to remove player from transfer list.")
                    return
                        
            except asyncio.CancelledError:
                await msg.channel.send("Failed to remove player from transfer list.")
                return
            
        else:
            await msg.channel.send("Error. You have no player listed on the transfer market.")
        
    if command == "":
        menu = "**Welcome to the Transfer Market \U0001f4dc !**\n"
        if responses.user_upgrades[user.id][3] != 0:
            menu += f"Here you can add a player from your collection to the transfer list, and in **{responses.transfer_upgrades[responses.user_upgrades[user.id][3] - 1]}**, you will receive 150% of the value of the player you sold!\n" + "\n"
        else:
            menu += f"Here you can add a player from your collection to the transfer list, and in **5 days**, you will receive 150% of the value of the player you sold!\n" + "\n"
            
        menu += "To add a player to the transfer list, type %tm add [player_name]. You may only add one player at a time. Example: %tm add Erling Haaland\n"
        menu += "To remove a player from your transfer list, type %tm rm [player_name]. Example: %tm rm Erling Haaland\n" + "\n"
        menu += "**Transfer List:**\n"
        if user_market_bool[user.id]:
            menu += user_market_player[user.id] + f" - Player will be sold in **{get_time_remaining()}**"
        else:
            menu += "Ready to add a player from your collection!"
            
        print("Sending menu...")
        await msg.channel.send(menu)
        
        if not tutorial.user_tutorial_completion[user.id][6][1]:
            tutorial.user_tutorial_completion[user.id][6][1] = True
            
            if user.id not in user_coins[user.id]:
                user_coins[user.id] = 0
                                    
            if False not in tutorial.user_tutorial_completion[user.id][6]:
                tutorial.user_tutorial_completion[user.id][7][0] = True
                user_coins[user.id] += 750
                tutorial.user_current_tutorial[user.id] = 7
                await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**!")
                
async def purchase_confirmation(price_to_upgrade, user, msg):
    if user_coins[user.id] >= price_to_upgrade:
        confirmation_msg = await msg.channel.send(f"Are you sure you want to spend {price_to_upgrade} \U0001f4a0 on this upgrade? You will have {user_coins[user.id] - price_to_upgrade} \U0001f4a0 left after this purchase. (y/n/yes/no)")
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
    if user.id not in user_favorite_club:
        user_favorite_club[user.id] = ""
    
    f = open('players_list.txt', 'r', encoding='utf-8')
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
            user_favorite_club[user.id] = favorite_club
            found = True
            await msg.channel.send(f"{user.mention} Your favorite club has been set to {favorite_club}")
            
            if not tutorial.user_tutorial_completion[user.id][1][1]:
                tutorial.user_tutorial_completion[user.id][1][1] = True
                
                if user.id not in user.coins[user.id]:
                    user.coins[user.id] = 0
            
                if False not in tutorial.user_tutorial_completion[user.id][1]:
                    user_coins[user.id] += 250
                    tutorial.user_current_tutorial[user.id] = 2
                    await msg.channel.send("Tutorial 2 complete! You have been rewarded **250 \U0001f4a0**!")
            
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
            await msg.channel.send("Error has occured. Too many matches.")
        return
    
            
async def display_profile(msg, user):
    if user.id not in user_coins:
        user_coins[user.id] = 0
        
    if user.id not in responses.user_max_rolls:
        responses.user_max_rolls[user.id] = 9
            
    if user.id not in responses.user_rolls:
        responses.user_rolls[user.id] = responses.user_max_rolls[user.id]
            
    if user.id not in responses.user_can_claim:
        responses.user_can_claim[user.id] = True
        
    if user.id not in user_favorite_club:
        user_favorite_club[user.id] = ""
        
    if user.id not in user_daily_bool:
        user_daily_bool[user.id] = True
        
    if user.id not in user_daily_wait:
        user_daily_wait[user.id] = 0
        
    if user.id not in user_collections:
        user_collections[user.id] = []
        
    profile = f"**{user.name}'s Profile**\n"
    curr_time = time.time()
    
    time_left_claim = format_time(1 - (curr_time - claim_reset_time))
    if responses.user_can_claim[user.id]:
        profile += f"You can __claim__ now! Claim reset is in **{time_left_claim}**.\n"
    else:
        profile += f"You can't claim for another **{time_left_claim}**.\n"
    
    time_left_rolls = format_time(3600 - (curr_time - roll_reset_time))
    profile += f"You have **{responses.user_rolls[user.id]}** rolls left. Rolls will replenish in **{time_left_rolls}**.\n" + "\n"
    
    time_left_daily = format_time(user_daily_wait[user.id] - curr_time)
    if user_daily_bool[user.id]:
        profile += "__Your daily reward is ready!__\n" + "\n"
    else:
        profile += f"Your daily reward will be ready in **{time_left_daily}**.\n" + "\n"
    
    if user_favorite_club[user.id] != "":
        profile += f"Your favorite club is set to **{user_favorite_club[user.id]}**.\n"
        
    profile += f"You have **{len(user_collections[user.id])}** player(s) in your collection.\n" + "\n"
    
    profile += "You have " + str(user_coins[user.id]) + " \U0001f4a0"
    
    await msg.channel.send(profile)
    
    if not tutorial.user_tutorial_completion[user.id][1][0]:
        tutorial.user_tutorial_completion[user.id][1][0] = True
        
        if user.id not in user_coins:
            user_coins[user.id] = 0
    
        if False not in tutorial.user_tutorial_completion[user.id][1]:
            user_coins[user.id] += 250
            tutorial.user_current_tutorial[user.id] = 2
            await msg.channel.send("Tutorial 2 complete! You have been rewarded **250 \U0001f4a0**!")
        

async def extract_user_id(mention):
    pattern = r"<@!?(\d+)>"
    match = re.match(pattern, mention)
    if match:
        user_id = match.group(1)
        return int(user_id)
    else:
        return None

async def send_message(msg, user_msg, is_private):
    try:
        response = await responses.handle_responses(msg, user_msg, msg.author)
        await msg.author.send(embed=response) if is_private else await msg.channel.send(embed=response)
            
    except Exception as e:
        print(e)

async def remove_player(user, msg, player):
    if user.id not in responses.user_upgrades:
        responses.user_upgrades[user.id] = [0,0,0,0]
        
    if user.id not in user_coins:
        user_coins[user.id] = 0
    
    if user.id in user_collections:
        collection = user_collections[user.id]
        i = 0
        found_player = None
        found_player_value = 0
        
        for embed in collection:
            if embed.title == player:
                found_player = embed
                break
            i += 1
            
        if found_player:
            for field in found_player.fields:
                if "Value:" in field.name:
                    found_player_value = float(field.name.split()[1])
            
            if responses.user_upgrades[user.id][1] != 0:
                found_player_value += found_player_value * (responses.board_upgrades[responses.user_upgrades[user.id][1] - 1] / 100)
                found_player_value = int(found_player_value)
                
            confirmation_msg = await msg.channel.send(f"Are you sure you want to remove {found_player.title} from your collection? You will receive {int(found_player_value)} \U0001f4a0 (y/n/yes/no)")
            try:
                response = await client.wait_for('message', timeout=30, check=lambda m: m.author == msg.author and m.channel == msg.channel)
                response_content = response.content.lower()
                if response_content == 'yes' or response_content == 'y':
                    removed_embed = collection.pop(i)
                    
                    removed_player_id = removed_embed.footer.text.split(", ")[1]
                    j = 0
                    for playerid in playerids:
                        if removed_player_id == playerid:
                            playerids.pop(j)
                            usernames.pop(j)
                        j += 1
                    
                    user_coins[user.id] += int(found_player_value)
                    await msg.channel.send(f"{removed_embed.title} was removed from {user.mention}'s collection.")
                    
                    if user.id not in responses.user_team_players:
                        responses.user_team_players[user.id] = []
                    
                    for player in responses.user_team_players:
                        if player.title == removed_embed.title:
                            await responses.handle_responses(msg, f"%t rm {removed_embed.title}", msg.author)
                    
                    if not tutorial.user_tutorial_completion[user.id][2][4]:
                        tutorial.user_tutorial_completion[user.id][2][4] = True
                        
                        print(tutorial.user_tutorial_completion[user.id][2])
                        
                        if user.id not in responses.user_max_rolls:
                            responses.user_max_rolls[user.id] = 9
                    
                        if False not in tutorial.user_tutorial_completion[user.id][2]:
                            responses.user_max_rolls[user.id] += 1
                            tutorial.user_current_tutorial[user.id] = 3
                            await msg.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**!")
                    
                elif response_content == 'no' or response_content == 'n':
                    await msg.channel.send("Removal cancelled.")
            except asyncio.TimeoutError:
                await msg.channel.send("Confirmation timed out. Removal cancelled.")
        else:
            await msg.channel.send(f"Error: {player} was not found in your collection.")
    else:
        await msg.channel.send("Error: No players found in your collection.")
        
async def trade_player(user, msg, player, mention):
    user_id = user.id
    other_id = await extract_user_id(mention)
    
    other_user = client.get_user(other_id)
    
    user_collection = user_collections[user_id]
    other_collection = user_collections[other_id]
    
    user_embed_trade = None
    other_embed_trade = None
    
    user_i = 0
    other_i = 0
    
    for embed in user_collection:
        if embed.title == player:
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
            return m.author.id == other_id and m.channel == msg.channel
        
        try:
            response = await client.wait_for('message', timeout=180, check=check_response)
            response_content = response.content.lower()
            
            if response_content == "n" or response_content == "no":
                await msg.channel.send("Trade cancelled.")
                repeat = False
            else:
                for embed in other_collection:
                    if embed.title.lower() == response_content:
                        other_embed_trade = embed
                        repeat = False
                        break
                    else:
                        await msg.channel.send(f"<@{other_id} Could not find that player in your collection. Please try again.")
                    other_i += 1
                          
        except asyncio.TimeoutError:
            await msg.channel.send(f"<@{other_id}> You took too long to respond. Trade cancelled.")
            return
        
        user_confirm = False
        
        if other_embed_trade:
            confirmation_msg = await msg.channel.send(f"{user.mention} You are trading {user_embed_trade.title} for {other_embed_trade.title}. Do you confirm this trade? (y/n/yes/no)")
            
            def check_user_response(m):
                    return m.author.id == user_id and m.channel == msg.channel
            
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
            confirmation_msg = await msg.channel.send(f"<@{other_id}> You are trading {other_embed_trade.title} for {user_embed_trade.title}. Do you confirm this trade? (y/n/yes/no)")
            
            def check_response(m):
                return m.author.id == other_id and m.channel == msg.channel
        
            try:
                response = await client.wait_for('message', timeout=100, check=check_response)
                response_content = response.content.lower()
                
                if response_content == 'yes' or response_content == 'y':
                    j = 0
                    
                    user_removed = user_collection.pop(user_i)
                    other_removed = other_collection.pop(other_i)
                    
                    user_removed_playerid = user_removed.footer.text.split(", ")[1]
                    other_removed_playerid = other_removed.footer.text.split(", ")[1]
                    
                    for playerid in playerids:
                        if user_removed_playerid == playerid:
                            playerids.pop(j)
                            usernames.pop(j)
                        if other_removed_playerid == playerid:
                            playerids.pop(j)
                            usernames.pop(j)
                        j += 1
                    
                    
                    user_removed.description = user_removed.description.replace(f"**Claimed by {user.name}**", f"**Claimed by {other_user.name}**") 
                    other_removed.description = other_removed.description.replace(f"**Claimed by {other_user.name}**", f"**Claimed by {user.name}**")
                    
                    user_collections[user_id].append(other_removed)
                    user_collections[other_id].append(user_removed)
                    
                    await msg.channel.send("Trade successful!")
                    
                    if not tutorial.user_tutorial_completion[user.id][6][0]:
                        tutorial.user_tutorial_completion[user.id][6][0] = True
                        
                        if user.id not in user_coins:
                            user_coins[user.id] = 0
                            
                        if False not in tutorial.user_tutorial_completion[user.id][6]:
                            tutorial.user_tutorial_completion[user.id][7][0] = True
                            user_coins[user.id] += 750
                            tutorial.user_current_tutorial[user.id] = 7
                            await msg.channel.send("Tutorial 7 complete! You have been rewarded **750 \U0001f4a0**!")
                    
                elif response_content == 'no' or response_content == 'n':
                    await msg.channel.send("Trade cancelled.")
            
            except asyncio.TimeoutError:
                await msg.channel.send("Confirmation timed out. Trade cancelled.")
                
def run_discord_bot():
    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')
        
    @client.event
    async def on_message(msg):
        if msg.author == client.user:
            return
        
        username = str(msg.author)
        user_msg = str(msg.content)
        channel = str(msg.channel)
        
        print(f"{username} said: '{user_msg}' ({channel})")
        
        global collection_messages
        
        if msg.author.id not in tutorial.user_tutorial_completion:
            tutorial.user_tutorial_completion[msg.author.id] = [[False], [False, False, False], [False, False, False, False, False, False], [False, False], [False, False, False, False, False], [False, False, False], [False, False, False, False], [False]]
        
        if msg.author.id not in tutorial.user_current_tutorial:
            tutorial.user_current_tutorial[msg.author.id] = 0
        
        if user_msg[0] == "?":
            user_msg = user_msg[1:]
            await send_message(msg, user_msg, is_private=True)
        elif user_msg.startswith("%c"):
            collection_messages = {}
            mentioned_user[msg.author.id] = ""
            if len(user_msg.split()) == 1:
                await show_collection(msg.author, msg, 0, "")
            
            elif "@" in user_msg.split()[1] and len(user_msg.split()) == 2:
                mentioned_user[msg.author.id] = user_msg.split()[1]
                await show_collection(msg.author, msg, 0, mentioned_user[msg.author.id])
                
            elif "@" in user_msg.split()[1] and len(user_msg.split()) == 3:
                mentioned_user[msg.author.id] = user_msg.split()[1]
                await show_collection(msg.author, msg, int(user_msg.split()[2]) - 1, mentioned_user[msg.author.id])
                
            elif "@" in user_msg.split()[2] and len(user_msg.split()) == 3:
                mentioned_user[msg.author.id] = user_msg.split()[2]
                await show_collection(msg.author, msg, int(user_msg.split()[1]) - 1, mentioned_user[msg.author.id])
            
            else:
                await show_collection(msg.author, msg, int(user_msg.split()[1]) - 1, "")
        elif user_msg.startswith("%rm"):
            if len(user_msg.split()) == 1:
                await msg.channel.send("Please specify who you wish to remove from your collection.")
            else:
                player_name = user_msg[4:].strip()
                await remove_player(msg.author, msg, player_name)
        
        elif user_msg.startswith("%trade") or user_msg.startswith("%tr"):
            mention = user_msg.split()[1]
            player_to_trade = " ".join(user_msg.split()[2:])
            await trade_player(msg.author, msg, player_to_trade, mention)
        
        elif user_msg == "%p":
            await display_profile(msg, msg.author)
        
        elif user_msg.startswith("%sc"):
            club = user_msg.split()[1:]
            await set_favorite_club(msg, msg.author, club)
            
        elif user_msg.startswith("%tm"):
            if len(user_msg.split()) == 1:
                await transfer_market(msg, msg.author, [], "")
            else:
                player_to_list = user_msg.split()[2:]
                command = user_msg.split()[1]
                await transfer_market(msg, msg.author, player_to_list, command)
                
        elif user_msg == "%fc":
            await free_claim(msg, msg.author)
        
        elif user_msg == "%d":
            await dailies(msg, msg.author)
            
        elif user_msg == "%s":
            await sort_collection(msg, msg.author)
            
        elif user_msg.startswith("%m"):
            position = int(user_msg.split()[1])
            player_to_move = user_msg.split()[2:]
            await move_player(msg, msg.author, player_to_move, position)
            
        elif user_msg.startswith("%n"):
            if len(user_msg.split()) == 1:
                await rename_club(msg, msg.author, [])
            else:
                name = user_msg.split()[1:]
                await rename_club(msg, msg.author, name)
                
        elif user_msg.startswith("%tuto"):
            tutorial.tutorial_messages = {}
            if len(user_msg.split()) == 1:
                await tutorial.tutorial(msg, msg.author, tutorial.user_current_tutorial[msg.author.id])
            else:
                page_num = user_msg.split()[1]
                await tutorial.tutorial(msg, msg.author, page_num)
                
        elif user_msg == "%r" or user_msg.startswith("%v") or user_msg.startswith("%lc") or user_msg.startswith("%t") or user_msg.startswith("%u"):
            await send_message(msg, user_msg, is_private=False)
            
        else:
            return
            
    client.loop.create_task(clean_up_rolled_times())
    client.loop.create_task(roll_timer())
    client.loop.create_task(claim_timer())
            
    client.run(TOKEN)
            
@client.event
async def on_reaction_add(reaction, user):
    print("Reaction added by:", user)
    print("Message author:", reaction.message.author)
    print("Emoji:", reaction.emoji)
    print("Embeds:", reaction.message.embeds)

    if user == client.user:
        print("Bot message.")
        return
    
    if user.id not in mentioned_user:
        mentioned_user[user.id] = ""
    
    if reaction.message.author == client.user: 
        if user.id in user_current_page: 
            if reaction.emoji == "⬅️":
                if mentioned_user[user.id] != "":
                    mention_id = await extract_user_id(mentioned_user[user.id])
                    if user_current_page[user.id] == 0:
                        user_current_page[user.id] = len(user_collections[user.id]) - 1
                    else:
                        user_current_page[user.id] -= 1
                    
                else:   
                    if user_current_page[user.id] == 0:
                        user_current_page[user.id] = len(user_collections[user.id]) - 1
                    else:                        
                        user_current_page[user.id] -= 1
                
                current_page = user_current_page[user.id]
                await show_collection(user, reaction.message, current_page, mentioned_user[user.id])
                return
                
            elif reaction.emoji == "➡️":
                if mentioned_user[user.id] != "":
                    mention_id = await extract_user_id(mentioned_user[user.id])
                    if user_current_page[user.id] == len(user_collections[mention_id]) - 1:
                        user_current_page[user.id] = 0
                    else:
                        user_current_page[user.id] += 1
                else:
                    if user_current_page[user.id] == len(user_collections[user.id]) - 1:
                        user_current_page[user.id] = 0
                    else:
                        user_current_page[user.id] += 1
                    
                current_page = user_current_page[user.id]
                await show_collection(user, reaction.message, current_page, mentioned_user[user.id])
                return
            
            elif reaction.emoji == "\u2b05":
                if False not in tutorial.user_tutorial_completion[user.id][user_current_page[user.id] - 1]: 
                    if user_current_page[user.id] == 0:
                        user_current_page[user.id] = len(tutorial.user_tutorial[user.id]) - 1
                    else:                        
                        user_current_page[user.id] -= 1
                    
                    current_page = user_current_page[user.id]
                    await tutorial.tutorial(reaction.message, user, current_page) 
                    return
                else:
                    await reaction.message.channel.send("Please complete the current tutorial before moving onto another one.")
                    return
            
            elif reaction.emoji == "\u27a1":
                if False not in tutorial.user_tutorial_completion[user.id][user_current_page[user.id]]:
                    if user_current_page[user.id] == len(tutorial.user_tutorial[user.id]) - 1:
                        user_current_page[user.id] = 0
                    else:
                        user_current_page[user.id] += 1
                    
                    current_page = user_current_page[user.id]
                    await tutorial.tutorial(reaction.message, user, current_page) 
                    return
                else:
                    await reaction.message.channel.send("Please complete the current tutorial before moving onto another one.")
                    return
            
            
    if isinstance(reaction.message.embeds[0], discord.Embed) and "Football Roll Bot" in reaction.message.embeds[0].footer.text:
        player_embed = reaction.message.embeds[0]
        player_id = player_embed.footer.text.split(", ")[1]
        
        current_time = time.time()
        can_claim = False
        if (current_time - responses.rolled_times[player_id][0]) < 60:
            can_claim = True
        
        claimed = False 
        if player_id in playerids:
            claimed = True
            
        if (not claimed) and ("**React with any emoji to claim!**" in player_embed.description) and can_claim and responses.user_can_claim[user.id]:
            print("Player claimed:", player_embed.title)

            if user.id not in user_collections:
                user_collections[user.id] = []
                
            player_embed.description = player_embed.description.replace("**React with any emoji to claim!**", f"**Claimed by {user.name}**") 

            user_collections[user.id].append(player_embed)

            player_id = player_embed.footer.text.split(", ")[1]
            playerids.append(player_id)
            usernames.append(user.name)
            responses.user_can_claim[user.id] = False

            await reaction.message.channel.send(f"{user.mention} has added {player_embed.title} to their collection!")
            
            if not tutorial.user_tutorial_completion[user.id][0][0]:
                tutorial.user_tutorial_completion[user.id][0][0] = True
                
                if user.id not in user_free_claims:
                    user_free_claims[user.id] = 0
                    
                user_free_claims[user.id] += 1
                tutorial.user_current_tutorial[user.id] = 1
                await reaction.message.channel.send("Tutorial 1 complete! You have been rewarded **1 free claim**!")
                
            if len(user_collections[user.id]) == 2:
                if not tutorial.user_tutorial_completion[user.id][2][0]:
                    tutorial.user_tutorial_completion[user.id][2][0] = True
                    
                    print(tutorial.user_tutorial_completion[user.id][2])
                    
                    if user.id not in responses.user_max_rolls:
                        responses.user_max_rolls[user.id] = 9
                
                    if False not in tutorial.user_tutorial_completion[user.id][2]:
                        responses.user_max_rolls[user.id] += 1
                        tutorial.user_current_tutorial[user.id] = 3
                        await reaction.message.channel.send("Tutorial 3 complete! You have been rewarded **+1 roll/hour**!")


    
        
    
