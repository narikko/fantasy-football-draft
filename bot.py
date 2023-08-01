import discord
import responses
import asyncio
import re

user_collections = {}
user_current_page = {}
collection_messages = {}

playerids= []
usernames = []


TOKEN = 'MTEzMjE3MDE4MTAxMjExNTU1Ng.GDeG1g.BDqacvjsdnOz_SHEh-OO7DFsC4_-xfwWreF4Qk'
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

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
    if user.id in user_collections:
        collection = user_collections[user.id]
        i = 0
        found_player = None
        
        for embed in collection:
            if embed.title == player:
                found_player = embed
                break
            i += 1
            
        if found_player:
            confirmation_msg = await msg.channel.send(f"Are you sure you want to remove {found_player.title} from your collection? (y/n/yes/no)")
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
        
        elif user_msg.startswith("%trade"):
            mention = user_msg.split()[1]
            player_to_trade = " ".join(user_msg.split()[2:])
            await trade_player(msg.author, msg, player_to_trade, mention)
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


    
        
    
