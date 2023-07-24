import random
import discord
import bot

def handle_responses(msg) -> discord.Embed:
    f = open('players_list.txt', 'r', encoding='utf-8')
    players_list = f.readlines()
    
    p_msg = msg.lower()
    
    claimed = False
    
    if p_msg == "%r":
        rolled_player = random.choice(players_list)
        player_info = rolled_player.strip().split(", ")
        player_name, player_club, player_nationality, player_value, player_imageURL, player_id = player_info
        
        i = 0
        claimed_user = ""
        for playerid in bot.playerids:
            if player_id == playerid:
                claimed = True
                claimed_user = bot.usernames[i]
                break
            i += 1
        
        embed = discord.Embed(
            title=player_name,
            description=player_club + "\n" + player_nationality,
            color=0xAF0000
        )
        
        embed.add_field(name= player_value, value="", inline=False)
        embed.set_image(url=player_imageURL)
        embed.set_footer(text="Football Roll Bot, " + player_id)
        
        player_status = f"**Claimed by {claimed_user}**" if claimed else "**React with any emoji to claim!**"
        embed.description += ("\n" + player_status) 

        return embed
    
    if p_msg.startswith("%v"):
        search_terms = p_msg.split()[1:]
        print("Search terms:", search_terms)
        
        if not search_terms:
            return discord.Embed(title="Error", description="Please provide search terms.", color=0xFF0000)

        for line in players_list:
            if all(term in line.lower() for term in search_terms):
                player_info = line.strip().split(", ")
                player_name, player_club, player_nationality, player_value, player_imageURL, player_id = player_info
                print("Player found:", player_name)
                break
            
        claimed = False
        
        i = 0
        claimed_user = ""
        for playerid in bot.playerids:
            if player_id == playerid:
                claimed = True
                claimed_user = bot.usernames[i]
                break
            i += 1
        
        embed = discord.Embed(
            title=player_name,
            description=player_club + "\n" + player_nationality,
            color=0xAF0000
        )

        embed.add_field(name=player_value, value="", inline=False)
        embed.set_image(url=player_imageURL)
        embed.set_footer(text="Football Roll Bot, " + player_id)
        
        if claimed:
            player_status = f"**Claimed by {claimed_user}**" 
            embed.description += ("\n" + player_status)
            
        print(claimed)

        return embed
