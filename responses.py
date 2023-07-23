import random
import discord

def handle_responses(msg) -> discord.Embed:
    f = open('players_list.txt', 'r', encoding='utf-8')
    players_list = f.readlines()
    
    p_msg = msg.lower()
    
    if p_msg == "%r":
        rolled_player = random.choice(players_list)
        player_info = rolled_player.strip().split(", ")
        player_name, player_club, player_nationality, player_value, player_imageURL, player_id = player_info
        
        embed = discord.Embed(
            title=player_name,
            description=player_club + "\n" + player_nationality,
            color=0xAF0000
        )
        
        embed.add_field(name= player_value, value="", inline=False)
        embed.set_image(url=player_imageURL)
        embed.set_footer("Football Roll Bot, " + player_id)

        return embed
