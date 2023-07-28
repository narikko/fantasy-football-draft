import random
import discord
import bot

user_teams = {}

def handle_responses(msg, user) -> discord.Embed:
    f = open('players_list.txt', 'r', encoding='utf-8')
    players_list = f.readlines()
    
    p_msg = msg.lower()
    
    claimed = False
    
    if p_msg == "%r":
        rolled_player = random.choice(players_list)
        player_info = rolled_player.strip().split(", ")
        player_name, player_positions, player_club, player_nationality, player_value, player_imageURL, player_id = player_info
        
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
        
        embed.add_field(name=player_positions, value="", inline=False)
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
        
        embed.add_field(name=player_positions, value="", inline=False)
        embed.add_field(name=player_value, value="", inline=False)
        embed.set_image(url=player_imageURL)
        embed.set_footer(text="Football Roll Bot, " + player_id)
        
        if claimed:
            player_status = f"**Claimed by {claimed_user}**" 
            embed.description += ("\n" + player_status)
            
        print(claimed)

        return embed
    
    if p_msg.startswith("%t"):
        forward_pos = ["LW", "ST", "RW", "CF"]
        midfield_pos = ["CAM", "LM", "RM", "CM", "CDM"]
        defense_pos = ["LWB", "RWB", "LB", "RB", "CB", "SW"]
        
        fpos = ["f1", "f2", "f3"]
        mpos = ["m1", "m2", "m3", "m4"]
        dpos = ["d1", "d2", "d3"]
        
        if user.id not in user_teams:
            embed = discord.Embed(
                title=f"{user}'s Starting XI",
                description= "Type %t [position] [player_name] to add a player from your collection to your starting XI" + "\n" + "Example: %t F2 Erling Haaland",
                color=0xAF0000
            )
            
            embed.add_field(name="F1", value ="", inline=True)
            embed.add_field(name="F2", value ="", inline=True)
            embed.add_field(name="F3", value ="", inline=True)
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(name="M1", value ="", inline=True)
            embed.add_field(name="M2", value ="", inline=True)
            embed.add_field(name="M3", value ="", inline=True)
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="M3", value ="", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(name="D1", value ="", inline=True)
            embed.add_field(name="D2", value ="", inline=True)
            embed.add_field(name="D3", value ="", inline=True)
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="GK", value="", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            
            user_teams[user.id] = embed
        
        if len(p_msg.split()) == 1:
            return user_teams[user.id]
       
        search_terms = p_msg.split()[2:]
        print("Search terms:", search_terms)
            
        collection = bot.user_collections[user.id]
        correct_player = False
        correct_pos = False
        sel_player = ""
            
        for player in collection:
            if all(term.lower() in player.title.lower() for term in search_terms):
                correct_player = True
                sel_player = player.title
                for field in player.fields:
                    positions = field.name.split("/")
                    for pos in positions:
                        if (pos in forward_pos) and (p_msg.split()[1] in fpos):
                            correct_pos = True
                            break
                        elif (pos in midfield_pos) and (p_msg.split()[1] in mpos):
                            correct_pos = True
                            break
                        elif (pos in defense_pos) and (p_msg.split()[1] in dpos):
                            correct_pos = True
                            break
                        elif (pos == "GK") and (p_msg.split()[1] == "gk"):
                            correct_pos = True
                            break
                        
                    if correct_pos:
                        break
                    else:
                        return discord.Embed(title="Error", description=f"You cannot add {player.title} to {p_msg.split()[1]}", color=0xFF0000)
            
            if correct_player:
                break

        if not correct_player:
            return discord.Embed(title="Error", description="Player not found in your collection.", color=0xFF0000)
        
        if correct_player and correct_pos:
            new_embed = discord.Embed(
                title=user_teams[user.id].title,
                description=user_teams[user.id].description,
                color=user_teams[user.id].color
            )

            for field in user_teams[user.id].fields:
                if field.name.strip().lower() == p_msg.split()[1]:
                    new_embed.add_field(name=field.name, value=sel_player, inline=field.inline)
                else:
                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline)

            user_teams[user.id] = new_embed
            return user_teams[user.id]

