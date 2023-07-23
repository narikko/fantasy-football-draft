import discord
import responses

user_collections = {}

async def send_message(msg, user_msg, is_private):
    try:
        response = responses.handle_responses(user_msg)
        await msg.author.send(embed=response) if is_private else await msg.channel.send(embed=response)
            
    except Exception as e:
        print(e)
        
def run_discord_bot():
    TOKEN = 'MTEzMjE3MDE4MTAxMjExNTU1Ng.GDeG1g.BDqacvjsdnOz_SHEh-OO7DFsC4_-xfwWreF4Qk'
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    
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
        else:
            await send_message(msg, user_msg, is_private=False)
            
    @client.event
    async def on_reaction_add(reaction, user):
        if reaction.message.author == client.user:
            return

        if isinstance(reaction.message.embeds[0], discord.Embed) and "Football Roll Bot" in reaction.message.embeds[0].footer.text:
            player_embed = reaction.message.embeds[0]

            if user.id not in user_collections:
                user_collections[user.id] = []

            user_collections[user.id].append(player_embed)

            await reaction.message.channel.send(f"{user.mention} has added {player_embed.title} to their collection!")
    
        
    client.run(TOKEN)
