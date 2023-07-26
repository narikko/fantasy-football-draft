import discord
import responses

user_collections = {}
user_current_page = {}
collection_messages = {}

playerids= []
usernames = []


TOKEN = 'MTEzMjE3MDE4MTAxMjExNTU1Ng.GDeG1g.BDqacvjsdnOz_SHEh-OO7DFsC4_-xfwWreF4Qk'
intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def send_message(msg, user_msg, is_private):
    try:
        response = responses.handle_responses(user_msg)
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
        removed = False
        for embed in collection:
            if embed.title == player:
                removed_embed = collection.pop(i)
                removed = True
                await msg.channel.send(f"{removed_embed.title} was removed from {user.mention}'s collection.")
                break
            i += 1
        if not removed:
            await msg.channel.send(f"{player} was not found in your collection.")
    else:
        await msg.channel.send("No players found in your collection.")
        
                

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
                player_name = user_msg[4:].split()
                await remove_player(msg.author, msg, player_name)
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


    
        
    
