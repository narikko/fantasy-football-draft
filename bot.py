import discord
import responses

user_collections = {}
playerids= []
usernames = []
user_current_page = {}

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
            collection_msg = await msg.channel.send(embed=embed_to_show)
            await collection_msg.add_reaction("⬅️")  
            await collection_msg.add_reaction("➡️")
        else:
            await user.send("Page not found.")
    else:
        await user.send("No players found in your collection.")
            
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
        
        if user_msg[0] == "?":
            user_msg = user_msg[1:]
            await send_message(msg, user_msg, is_private=True)
        elif user_msg.startswith("%c"):
            if len(user_msg.split()) == 1:
                await show_collection(msg.author, msg, 0)
            else:
                await show_collection(msg.author, msg, int(user_msg.split()[1]))
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

            user_collections[user.id].append(player_embed)

            player_id = player_embed.footer.text.split(", ")[1]
            playerids.append(player_id)
            usernames.append(user.name)

            await reaction.message.channel.send(f"{user.mention} has added {player_embed.title} to their collection!")


    
        
    
