import discord
import responses
import asyncio
import re
import emoji
import unidecode
import time

user_collections = {}
user_current_page = {}
collection_messages = {}
user_coins = {}
user_favorite_club = {}

user_market = {}
user_market_player = {}
user_market_bool = {}
user_transfer_tasks = {}
user_market_wait = {}

playerids= []
usernames = []


user_coins[456861613966884866] = 1000000000

TOKEN = 'MTEzMjE3MDE4MTAxMjExNTU1Ng.GDeG1g.BDqacvjsdnOz_SHEh-OO7DFsC4_-xfwWreF4Qk'
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

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
        user_market_wait = 0
    
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
                    
                    async def wait_for_sell(time_to_wait):
                        try:
                            await msg.channel.send(f"{user.mention} Successfully added {player.title} to the transfer list.")
                            task = asyncio.create_task(asyncio.sleep(time_to_wait))
                            task.starttime = time.time()
                            user_transfer_tasks[user.id] = task
                            user_market_wait[user.id] = time.time() + time_to_wait
                            
                            await task
                            
                            new_value = int(user_market[user.id] * 1.5)
                            user_coins[user.id] += new_value
                            await msg.channel.send(f"{user.mention} {player.title} has been sold for {new_value} \U0001f4a0 !")
                            user_market_player[user.id] = ""
                            user_market[user.id] = 0
                            user_market_bool[user.id] = False
                            user_market_wait[user.id] = 0
                            
                        except asyncio.CancelledError:
                            await msg.channel.send("Failed to list player.")
                            return
                        
                    if responses.user_upgrades[user.id][3] == 1:
                        wait_for_sell(30)
                        return
                    elif responses.user_upgrades[user.id][3] == 2:
                        wait_for_sell(172800)
                        return
                    elif responses.user_upgrades[user.id][3] == 3:
                        wait_for_sell(86400)
                        return
                    elif responses.user_upgrades[user.id][3] == 4:
                        wait_for_sell(43200)
                        return
                    elif responses.user_upgrades[user.id][3] == 5:
                        wait_for_sell(21600)
                        return
                    else:
                        wait_for_sell(432000)
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
            break
    
    if not found:
        for line in players_list:
            normalized_line = unidecode.unidecode(line.lower())

            if line.strip().split(", ")[2] not in clubs_found:
                for term in normalized_search_terms:
                    if term in normalized_line:
                        club_found = line.strip().split(", ")[2]
                        clubs_found.append(club_found)
        
        if len(clubs_found) == 0:
            await msg.channel.send("Club not found in our database.")
            return
    
        mult_msg = f"{len(clubs_found)} matches. Please retype the command with one of the names below.\n"
        for clubs in clubs_found:   
            mult_msg += clubs + "\n"
        
        await msg.channel.send(mult_msg)
        return
            
    

async def display_profile(msg, user):
    profile = ""
    profile += str(user_coins[user.id]) + " \U0001f4a0"
    await msg.channel.send(profile)

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

async def show_collection(user, msg, page_num):
    if user.id not in user_current_page:
        user_current_page[user.id] = 0

    if user.id in user_collections:
        collection = user_collections[user.id]
        if 0 <= page_num < len(collection):
            user_current_page[user.id] = page_num
            embed_to_show = collection[page_num]

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
        else:
            await msg.channel.send("Page not found.")
    else:
        await msg.channel.send("No players found in your collection.")

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
                
            confirmation_msg = await msg.channel.send(f"Are you sure you want to remove {found_player.title} from your collection? You will receive {found_player_value} \U0001f4a0 (y/n/yes/no)")
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
                    await responses.handle_responses(msg, f"%t rm {removed_embed.title}", msg.author)
                elif response_content == 'no' or response_content == 'n':
                    await msg.channel.send("Removal cancelled.")
            except asyncio.TimeoutError:
                await msg.channel.send("Confirmation timed out. Removal cancelled.")
        else:
            await msg.channel.send(f"{player} was not found in your collection.")
    else:
        await msg.channel.send("No players found in your collection.")
        
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
        await msg.channel.send("You do not have that player in your collection.")
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
        
        if user_msg[0] == "?":
            user_msg = user_msg[1:]
            await send_message(msg, user_msg, is_private=True)
        elif user_msg.startswith("%c"):
            collection_messages = {}
            if len(user_msg.split()) == 1:
                await show_collection(msg.author, msg, 0)
            else:
                await show_collection(msg.author, msg, int(user_msg.split()[1]))
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
            
        else:
            await send_message(msg, user_msg, is_private=False)
            
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
    
    if reaction.message.author == client.user: 
        if user.id in user_current_page: 
            if reaction.emoji == "⬅️":  
                if user_current_page[user.id] == 0:
                    user_current_page[user.id] = len(user_collections[user.id]) - 1
                else:                        
                    user_current_page[user.id] -= 1
                
                current_page = user_current_page[user.id]
                await show_collection(user, reaction.message, current_page)
                return
                
            elif reaction.emoji == "➡️":
                if user_current_page[user.id] == len(user_collections[user.id]) - 1:
                    user_current_page[user.id] = 0
                else:
                    user_current_page[user.id] += 1
                    
                current_page = user_current_page[user.id]
                await show_collection(user, reaction.message, current_page)
                return
            
    if isinstance(reaction.message.embeds[0], discord.Embed) and "Football Roll Bot" in reaction.message.embeds[0].footer.text:
        player_embed = reaction.message.embeds[0]
        player_id = player_embed.footer.text.split(", ")[1]
        
        claimed = False 
        if player_id in playerids:
            claimed = True
            
        if (not claimed) and ("**React with any emoji to claim!**" in player_embed.description):
            print("Player claimed:", player_embed.title)

            if user.id not in user_collections:
                user_collections[user.id] = []
                
            player_embed.description = player_embed.description.replace("**React with any emoji to claim!**", f"**Claimed by {user.name}**") 

            user_collections[user.id].append(player_embed)

            player_id = player_embed.footer.text.split(", ")[1]
            playerids.append(player_id)
            usernames.append(user.name)

            await reaction.message.channel.send(f"{user.mention} has added {player_embed.title} to their collection!")


    
        
    
