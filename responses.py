import random
import discord
import bot
import unidecode
import emoji
import asyncio
import time
import unicodedata
import tutorial

stadium_upgrades = [0.5, 1, 2, 4, 8]
stadium_prices = [1000, 2000, 4000, 8000, 16000]
        
board_upgrades = [5, 10, 15, 20, 25]
board_prices = [3000, 9000, 27000, 50000, 81000]
        
training_upgrades = [3, 3.5, 4, 4.5, 5]
training_prices = [500, 1000, 2000, 4000, 8000]
        
transfer_upgrades = ["3 days", "2 days", "1 day", "12 hours", "6 hours"]
transfer_prices = [2000, 5000, 8000, 12000, 24000]

async def handle_responses(msg, user_msg, user) -> discord.Embed:
    
    server_data = bot.server_data.get(str(msg.guild.id), {})
        
    user_upgrades = server_data.get('user_upgrades', {})
    user_favorite_club = server_data.get('user_favorite_club', {})
    user_max_rolls = server_data.get('user_max_rolls', {})
    user_rolls = server_data.get('user_rolls', {})
    user_can_claim = server_data.get('user_can_claim', {})
    playerids = server_data.get('playerids', [])
    usernames = server_data.get('usernames', [])
    rolled_times = server_data.get('rolled_times', {})
    user_tutorial_completion = server_data.get('user_tutorial_completion', {})
    user_coins = server_data.get('user_coins', {})
    user_current_tutorial = server_data.get('user_current_tutorial', {})
    user_team_players = server_data.get('user_team_players', {})
    user_team_rewards = server_data.get('user_team_rewards', {})
    user_club_name = server_data.get('user_club_name', {})
    user_teams = server_data.get('user_teams', {})
    user_collections = server_data.get('user_collections', {})
    user_free_claims = server_data.get('user_free_claims', {})
    roll_reset_time = server_data.get('roll_reset_time', time.time())
    
    f = open('players_list.txt', 'r', encoding='utf-8')
    g = open('legends_list.txt', 'r', encoding='utf-8')
    players_list = f.readlines()
    legends_list = g.readlines()
    
    p_msg = user_msg.lower()
    print(p_msg)
    
    claimed = False
    legend = False
    
    if p_msg == "%r":
        if user.id not in user_upgrades:
            user_upgrades[user.id] = [0,0,0,0]
            
        if user.id not in user_favorite_club:
            user_favorite_club[user.id] = ""
            
        if user.id not in user_max_rolls:
            user_max_rolls[user.id] = 9
            
        if user.id not in user_rolls:
            user_rolls[user.id] = user_max_rolls[user.id]
            
        if user.id not in user_can_claim:
            user_can_claim[user.id] = True
            
        if user_rolls[user.id] == 0:
            curr_time = time.time()
            print("Current time:", curr_time)
            print("Roll reset time:", roll_reset_time)
            time_left = bot.format_time(90 - (curr_time - roll_reset_time))
            print("Time left:", time_left)
            await msg.channel.send(f"{user.mention} You have no rolls remaining. Your rolls will replenish in **{time_left}**.")
                  
            return
        
        num_player_club = 0
        club_upgrade_chance = 0
        normal_roll = False
        favorite_club_list = []
        rolled_player = ""
        
        if user_favorite_club[user.id] != "":
            for line in players_list:
                if user_favorite_club[user.id] in line:
                    num_player_club += 1
                    favorite_club_list.append(line)
            
            if user_upgrades[user.id][0] != 0:
                club_upgrade_chance = round(((num_player_club / 18141) * 10000) + (stadium_upgrades[user_upgrades[user.id][0] - 1] * 100))
                club_chance = random.randint(0, 10000)

                if club_chance < club_upgrade_chance:
                    rolled_player = random.choice(favorite_club_list)
                else:
                    normal_roll = True
            else:
                normal_roll = True
        else:
            normal_roll = True
        
        if normal_roll:
            chance = random.randint(0, 2000)
            
            if chance == 0:
                rolled_player = random.choice(legends_list)
                legend = True
            else:
                rolled_player = random.choice(players_list)
        
        player_info = rolled_player.strip().split(", ")
        player_name, player_positions, player_club, player_nationality, player_value, player_imageURL, player_id = player_info
        player_value += " " + emoji.emojize(":diamond_with_a_dot:")
        
        i = 0
        claimed_user = ""
        for playerid in playerids:
            if player_id == playerid:
                claimed = True
                claimed_user = usernames[i]
                break
            i += 1
        
        embed = discord.Embed(
            title=player_name,
            description=player_club + "\n" + player_nationality,
            color=0xAF0000 if not legend else 0xFFD700
        )
        
        embed.add_field(name=player_positions, value="", inline=False)
        embed.add_field(name= player_value, value="", inline=False)
        embed.set_image(url=player_imageURL)
        embed.set_footer(text="Fantasy Football Draft, " + player_id)
        
        player_status = f"**Claimed by {claimed_user}**" if claimed else "**React with any emoji to claim!**"
        embed.description += ("\n" + player_status)
        
        if claimed:
            dup_coins = float(player_value.split()[1].strip())
            
            if user_upgrades[user.id][1] != 0:
                dup_coins += dup_coins * (board_upgrades[user_upgrades[user.id][1] - 1] / 100)
            
            user_coins[user.id] += int(dup_coins)
            await msg.channel.send(f"You have been given **+{int(dup_coins)}** \U0001f4a0 for the duplicate player!")
        
        rolled_time = time.time()
        expiration_time = rolled_time + 60

        rolled_times[player_id] = (rolled_time, expiration_time)
        
        print(rolled_times[player_id])
        print(bot.server_data[str(msg.guild.id)]["rolled_times"][player_id])
        
        user_rolls[user.id] -= 1
        
        return embed
   
    if p_msg.startswith("%v"):
        if user.id not in user_upgrades:
            user_upgrades[user.id] = [0,0,0,0]
            
        search_terms = p_msg.split()[1:]
        print("Search terms:", search_terms)
        
        if not search_terms:
            return discord.Embed(title="Error", description="Please provide search terms.", color=0xFF0000)
        
        def search_player(search_terms):
            normalized_search_terms = [unidecode.unidecode(term.lower()) for term in search_terms]
            players_found = []

            for line in players_list:
                normalized_line = unidecode.unidecode(line.lower())
                if all(term in normalized_line.split(", ")[0] for term in normalized_search_terms):
                    player_info = line.strip().split(", ")
                    player_info.append("not legend")
                    players_found.append(player_info)
                    break
            
            for line in legends_list:
                normalized_line = unidecode.unidecode(line.lower())
                if all(term in normalized_line.split(", ")[0] for term in normalized_search_terms):
                    player_info = line.strip().split(", ")
                    player_info.append("legend")
                    players_found.append(player_info)
                    break
                
            return players_found
        
        players_found = search_player(search_terms)
        print("Players found:", players_found)
        
        if len(players_found) == 1:
            player_info = players_found[0]
            player_name, player_positions, player_club, player_nationality, player_value, player_imageURL, player_id, player_legend = player_info
            player_value += " " + emoji.emojize(":diamond_with_a_dot:")
        else:
            players_found_msg = f"{len(players_found)} matches:\n"
            for players in players_found:
                players_found_msg += players[0] + " " + players[4] + "\n"
            
            await msg.channel.send(players_found_msg)
            return
        
        claimed = False
        
        i = 0
        claimed_user = ""
        for playerid in playerids:
            if player_id == playerid:
                claimed = True
                claimed_user = usernames[i]
                break
            i += 1
        
        if player_legend == "not legend":
            embed = discord.Embed(
                title=player_name,
                description=player_club + "\n" + player_nationality,
                color=0xAF0000
            )
            
            embed.add_field(name=player_positions, value="", inline=False)
            embed.add_field(name=player_value, value="", inline=False)
            embed.set_image(url=player_imageURL)
            embed.set_footer(text="Fantasy Football Draft, " + player_id)
            
            if claimed:
                player_status = f"**Claimed by {claimed_user}**" 
                embed.description += ("\n" + player_status)
        else:
            embed = discord.Embed(
                title=player_name,
                description=player_club + "\n" + player_nationality,
                color=0xFFD700
            )
            
            embed.add_field(name=player_positions, value="", inline=False)
            embed.add_field(name=player_value, value="", inline=False)
            embed.set_image(url=player_imageURL)
            embed.set_footer(text="Fantasy Football Draft, " + player_id)
            
            if claimed:
                player_status = f"**Claimed by {claimed_user}**" 
                embed.description += ("\n" + player_status)
                
        if not user_tutorial_completion[user.id][3][0]:
            user_tutorial_completion[user.id][3][0] = True
            
            if user.id not in user_coins:
                user_coins[user.id] = 0
                
            await msg.channel.send("Substep complete! Type %tuto for the next steps!")
            
            if False not in user_tutorial_completion[user.id][3]:
                user_coins[user.id] += 500
                user_current_tutorial[user.id] = 4
                await msg.channel.send("Tutorial 4 complete! You have been rewarded **500 \U0001f4a0**! Type %tuto for the next steps!")
            
        return embed
    
    if p_msg.split()[0] == "%lc":
        club = p_msg.split()[1:]
        
        if not club:
            return discord.Embed(title="Error", description="Please provide search terms.", color=0xFF0000)
        
        clubs_found = []
        found = False
        normalized_search_terms = [unidecode.unidecode(term.lower()) for term in club]
        
        for line in players_list:
            normalized_line = unidecode.unidecode(line.lower())
            club_search = " ".join(normalized_search_terms)
            if club_search.lower() == normalized_line.split(", ")[2]:
                clubs_found.append(line.strip().split(", ")[2])
                found = True
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
        
        def search_club(search_terms):
            normalized_search_terms = [unidecode.unidecode(term.lower()) for term in search_terms]
            found = []
            players_found = []
            ids_found = []

            for line in players_list:
                normalized_line = unidecode.unidecode(line.lower())
                if all(term in normalized_line.split(", ")[2] for term in normalized_search_terms):
                    player_name = line.strip().split(", ")[0]
                    id_found = line.strip().split(", ")[6]
                    players_found.append(player_name)
                    ids_found.append(id_found)
                        
            for line in legends_list:
                normalized_line = unidecode.unidecode(line.lower())
                if all(term in normalized_line.split(", ")[2] for term in normalized_search_terms):
                    player_name = line.strip().split(", ")[0]
                    id_found = line.strip().split(", ")[6]
                    players_found.append(player_name)
                    ids_found.append(id_found)
                        
            found.append(players_found)
            found.append(ids_found)
            return found
            
        found = search_club(club)
        normalized_search_terms = [unidecode.unidecode(term.lower()) for term in club]
        club_title = ""
        for line in players_list:
            normalized_line = unidecode.unidecode(line.lower())
            if all(term in normalized_line.split(", ")[2] for term in normalized_search_terms):
                club_title = line.split(", ")[2]
            
        players_desc = ""
        i = 0
        for player in found[0]:
            if found[1][i] in playerids:
                players_desc += player + " \u2705" + "\n"
            else:
                players_desc += player + "\n"
            
            i += 1
                
        embed = discord.Embed(
            title=club_title,
            description=players_desc,
            color=0xADD8E6
            )
        
        if not user_tutorial_completion[user.id][3][1]:
            user_tutorial_completion[user.id][3][1] = True
            
            if user.id not in user_coins:
                user_coins[user.id] = 0
            
            await msg.channel.send("Substep complete! Type %tuto for the next steps!")
            
            if False not in user_tutorial_completion[user.id][3]:
                user_coins[user.id] += 500
                user_current_tutorial[user.id] = 4
                await msg.channel.send("Tutorial 4 complete! You have been rewarded **500 \U0001f4a0**! Type %tuto for the next steps!")
            
        return embed
    
    if p_msg.startswith("%t"):
        if user.id not in user_upgrades:
            user_upgrades[user.id] = [0,0,0,0]
            
        if user.id not in user_team_players:
            user_team_players[user.id] = []
        
        if user.id not in user_team_rewards:
            user_team_rewards[user.id] = [False, False, False, False, False, False, False]
            
        if user.id not in user_club_name:
            print("intializing name")
            user_club_name[user.id] = ""

        forward_pos = ["LW", "ST", "RW", "CF"]
        midfield_pos = ["CAM", "LM", "RM", "CM", "CDM"]
        defense_pos = ["LWB", "RWB", "LB", "RB", "CB", "SW"]
        
        fpos = ["f1", "f2", "f3"]
        mpos = ["m1", "m2", "m3", "m4"]
        dpos = ["d1", "d2", "d3"]
        
        print(user_club_name[user.id])
        if user.id not in user_teams:
            embed = discord.Embed(
                title=f"{user.name}'s Starting XI" if user_club_name[user.id] == "" else user_club_name[user.id],
                description= "Type %t [position] [player_name] to add a player from your collection to your starting XI" + "\n" + "Example: %t F2 Erling Haaland" + "\n" + "\n" + "Type %t rewards to learn about starting XI rewards.",
                color=0x7CFC00
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
            embed.add_field(name="M4", value ="", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(name="D1", value ="", inline=True)
            embed.add_field(name="D2", value ="", inline=True)
            embed.add_field(name="D3", value ="", inline=True)
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="GK", value="", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            
            embed.add_field(name="Overall Value", value="0", inline=False)
            
            embed_data = [
                embed.title,
                embed.description,
                embed.color.value,
                [(field.name, field.value, field.inline) for field in embed.fields]
            ]
            
            user_teams[user.id] = embed_data
        
        if len(p_msg.split()) == 1:
            new_embed = discord.Embed(
                title=f"{user.name}'s Starting XI" if user_club_name[user.id] == "" else user_club_name[user.id],
                description=user_teams[user.id][1],
                color=discord.Colour(int(user_teams[user.id][2]))
            )
            
            overall_value = 0
            player_values = []
            if len(user_team_players[user.id]) != 0:
                for player in user_team_players[user.id]:
                    for field in player[3]:
                        if "Value:" in field[0]:
                            player_values.append(int(field[0].split()[1]))
                            break
                                
                overall_value = round(sum(player_values) / len(user_team_players[user.id]))
            
            if user_upgrades[user.id][2] != 0:
                overall_value = float(overall_value)
                overall_value += overall_value * (training_upgrades[user_upgrades[user.id][2] - 1] / 100)
                overall_value = int(overall_value)
            
            for field in user_teams[user.id][3]:
                if field[0].strip() == "Overall Value":
                    new_embed.add_field(name=field[0], value=overall_value, inline=field[2])
                else:
                    new_embed.add_field(name=field[0], value=field[1], inline=field[2])
                    
            embed_data = [
                new_embed.title,
                new_embed.description,
                new_embed.color.value,
                [(field.name, field.value, field.inline) for field in new_embed.fields]
            ]
            
            user_teams[user.id] = embed_data
            
            if not user_tutorial_completion[user.id][4][0]:
                user_tutorial_completion[user.id][4][0] = True
                
                if user.id not in user_coins:
                    user_coins[user.id] = 0
                
                await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                
                if False not in user_tutorial_completion[user.id][4]:
                    user_coins[user.id] += 500
                    
                    await msg.channel.send("Tutorial 5 complete! You have been rewarded **500 \U0001f4a0**! Type %tuto for the next steps!")
            
            return new_embed
        
        if p_msg.split()[1] == "rewards":
            ovl_value = ""
            for field in user_teams[user.id][3]:
                if field[0].strip() == "Overall Value":
                    ovl_value = field[1].strip()
                    
            reward_info = f"The overall value of your starting XI is **{ovl_value}**!\n" + "You must build a full team of 11 players to earn rewards.\n" + "\n"
            reward_info += "Build your first ever starting XI - Reward: **1000 \U0001f4a0**"
            if user_team_rewards[user.id][0]:
                reward_info += " \u2705"
            reward_info += "\n" + "\n" + "Build a starting XI with an overall value of 300 - Reward: **2 free claims**"
            if user_team_rewards[user.id][1]:
                reward_info += " \u2705"
            reward_info += "\n" + "\n" + "Build a starting XI with an overall value of 400 - Reward: **2000 \U0001f4a0**"
            if user_team_rewards[user.id][2]:
                reward_info += " \u2705"
            reward_info += "\n" + "\n" + "Build a starting XI with an overall value of 500 - Reward: **+2 rolls/hour**"    
            if user_team_rewards[user.id][3]:
                reward_info += " \u2705"
            reward_info += "\n" + "\n" + "Build a starting XI with an overall value of 600 - Reward: **+3 rolls/hour**"     
            if user_team_rewards[user.id][4]:
                reward_info += " \u2705"
            reward_info += "\n" + "\n" + "Build a starting XI with an overall value of 700 - Reward: **Acquire a random 830+ value card**"    
            if user_team_rewards[user.id][5]:
                reward_info += " \u2705"
            reward_info += "\n" + "\n" + "Build a starting XI with an overall value of 800 - Reward: **Acquire a random legend card**" 
            if user_team_rewards[user.id][6]:
                reward_info += " \u2705"
            
            embed = discord.Embed(
                title=f"Starting XI Rewards Info",
                description=reward_info,
                color=0x00008B
            )
            
            if not user_tutorial_completion[user.id][4][3]:
                user_tutorial_completion[user.id][4][3] = True
                
                if user.id not in user_coins:
                    user_coins[user.id] = 0
                    
                await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                
                if False not in user_tutorial_completion[user.id][4]:
                    user_coins[user.id] += 500
                    user_current_tutorial[user.id] = 5
                    await msg.channel.send("Tutorial 5 complete! You have been rewarded **500 \U0001f4a0**! Type %tuto for the next steps!")
            
            return embed
            
       
        search_terms = p_msg.split()[2:]
        print("Search terms:", search_terms)
            
        collection = user_collections[user.id]
        correct_player = False
        correct_pos = False
        sel_player = ""
        
        if p_msg.split()[1] == "rm":
            print("this happened")
            new_embed = discord.Embed(
                title=user_teams[user.id][0],
                description=user_teams[user.id][1],
                color=discord.Colour(int(user_teams[user.id][2]))
            )
            
            for field in user_teams[user.id][3]:
                if field[0].strip().lower() == p_msg.split()[2]:
                    new_embed.add_field(name=field[0], value="", inline=field[2])
                elif all(term.lower() in field[1].strip().lower() for term in search_terms):
                     new_embed.add_field(name=field[0], value="", inline=field[2])
                else:
                    new_embed.add_field(name=field[0], value=field[1], inline=field[2])
                    
            embed_data = [
                new_embed.title,
                new_embed.description,
                new_embed.color.value,
                [(field.name, field.value, field.inline) for field in new_embed.fields]
            ]
                    
            user_teams[user.id] = embed_data
            
            removed_player = ""
            for player in user_team_players[user.id]:
                if player[0].lower() == " ".join(p_msg.split()[2:]):
                    print("this is happening")
                    user_team_players[user.id].remove(player)
                    removed_player = player[0]
            
            newer_embed = discord.Embed(
                title=user_teams[user.id][0],
                description=user_teams[user.id][1],
                color=discord.Colour(int(user_teams[user.id][2]))
            )
            
            overall_value = 0
            player_values = []
            if len(user_team_players[user.id]) != 0:
                for player in user_team_players[user.id]:
                    for field in player[3]:
                        if "Value:" in field[0]:
                            print(int(field[0].split()[1]))
                            player_values.append(int(field[0].split()[1]))
                            break
                                
                overall_value = round(sum(player_values) / len(user_team_players[user.id]))
            
            if user_upgrades[user.id][2] != 0:
                overall_value = float(overall_value)
                overall_value += overall_value * (training_upgrades[user_upgrades[user.id][2] - 1] / 100)
                overall_value = int(overall_value)
            
            for field in user_teams[user.id][3]:
                if field[0].strip() == "Overall Value":
                    newer_embed.add_field(name=field[0], value=overall_value, inline=field[2])
                else:
                    newer_embed.add_field(name=field[0], value=field[1], inline=field[2])
                    
            embed_data = [
                newer_embed.title,
                newer_embed.description,
                newer_embed.color.value,
                [(field.name, field.value, field.inline) for field in newer_embed.fields]
            ]

            user_teams[user.id] = embed_data
            
            await msg.channel.send(f"{removed_player} was removed from your starting XI.")
            
            if not user_tutorial_completion[user.id][4][2]:
                user_tutorial_completion[user.id][4][2] = True
                
                if user.id not in user_coins:
                    user_coins[user.id] = 0
                    
                await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                
                if False not in user_tutorial_completion[user.id][4]:
                    user_coins[user.id] += 500
                    user_current_tutorial[user.id] = 5
                    await msg.channel.send("Tutorial 5 complete! You have been rewarded **500 \U0001f4a0**! Type %tuto for the next steps!")
            return

        for player in collection:
            if all(term.lower() in player[0].lower() for term in search_terms):
                correct_player = True
                sel_player = player[0]
                for field in player[3]:
                    positions = field[0].split("/")
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
                user_team_players[user.id].append(player)    
                break

        if not correct_player:
            return discord.Embed(title="Error", description="Player not found in your collection.", color=0xFF0000)
        
        if correct_player and correct_pos:
            new_embed = discord.Embed(
                title=f"{user.name}'s Starting XI" if user_club_name[user.id] == "" else user_club_name[user.id],
                description=user_teams[user.id][1],
                color=discord.Colour(int(user_teams[user.id][2]))
            )

            for field in user_teams[user.id][3]:
                if field[1].strip().lower() == sel_player.lower():
                    if field[0].strip().lower() != p_msg.split()[1]:
                        new_embed.add_field(name=field[0], value="", inline=field[2])
                        continue 
                    
                if field[0].strip().lower() == p_msg.split()[1]:
                    new_embed.add_field(name=field[0], value=sel_player, inline=field[2])
                else:
                    new_embed.add_field(name=field[0], value=field[1], inline=field[2])
                    
            embed_data = [
                new_embed.title,
                new_embed.description,
                new_embed.color.value,
                [(field.name, field.value, field.inline) for field in new_embed.fields]
            ]

            user_teams[user.id] = embed_data
        
        new_embed = discord.Embed(
            title=user_teams[user.id][0],
            description=user_teams[user.id][1],
            color=0x7CFC00
        )
        
        overall_value = 0
        player_values = []
        if len(user_team_players[user.id]) != 0:
            for player in user_team_players[user.id]:
                for field in player[3]:
                    if "Value:" in field[0]:
                        player_values.append(int(field[0].split()[1]))
                        break
                            
            overall_value = round(sum(player_values) / len(user_team_players[user.id]))
        
        if user_upgrades[user.id][2] != 0:
            overall_value = float(overall_value)
            overall_value += overall_value * (training_upgrades[user_upgrades[user.id][2] - 1] / 100)
            overall_value = int(overall_value)
        
        for field in user_teams[user.id][3]:
            if field[0].strip() == "Overall Value":
                new_embed.add_field(name=field[0], value=overall_value, inline=field[2])
            else:
                new_embed.add_field(name=field[0], value=field[1], inline=field[2])
        
        num_players = 0
        for field in new_embed.fields:
            cleaned_name = unicodedata.normalize('NFKD', field.name).encode('ascii', 'ignore').decode('utf-8')
            cleaned_value = unicodedata.normalize('NFKD', field.value).encode('ascii', 'ignore').decode('utf-8')
            if cleaned_value.strip() != "" and cleaned_name.strip() != "Overall Value":
                num_players += 1

        if num_players == 11:
            print("11 players")
            if not user_team_rewards[user.id][0]:
                print("1st reward")
                user_team_rewards[user.id][0] = True
                 
                if user.id not in user_coins:
                    user_coins[user.id] = 0
                    
                user_coins[user.id] += 1000
                await msg.channel.send(f"Congratulations {user.mention}! You have built your first ever starting XI. You have been rewarded **1000 \U0001f4a0**!")
                
            if overall_value >= 300 and not user_team_rewards[user.id][1]:
                print("2nd reward")
                user_team_rewards[user.id][1] = True
                
                if user.id not in user_free_claims:
                    user_free_claims[user.id] = 0
                    
                user_free_claims[user.id] += 2
                await msg.channel.send(f"Congratulations {user.mention}! You have built a starting XI with an overall value of at least 300. You have been rewarded **2 free claims**!")
                
            if overall_value >= 400 and not user_team_rewards[user.id][2]:
                print("3rd reward")
                user_team_rewards[user.id][2] = True
                
                if user.id not in user_coins:
                    user_coins[user.id] = 0
                    
                user_coins[user.id] += 2000
                await msg.channel.send(f"Congratulations {user.mention}! You have built a starting XI with an overall value of at least 4000. You have been rewarded **2000 \U0001f4a0** !")
            
            if overall_value >= 500 and not user_team_rewards[user.id][3]:
                print("4th reward")
                user_team_rewards[user.id][3] = True
                user_max_rolls[user.id] += 2
                await msg.channel.send(f"Congratulations {user.mention}! You have built a starting XI with an overall value of at least 500. You have been rewarded **+2 rolls/hour**!")
            
            if overall_value >= 600 and not user_team_rewards[user.id][4]:
                print("5th reward")
                user_team_rewards[user.id][4] = True
                user_max_rolls[user.id] += 3
                await msg.channel.send(f"Congratulations {user.mention}! You have built a starting XI with an overall value of at least 600. You have been rewarded **+3 rolls/hour**!")
                
            if overall_value >= 700 and not user_team_rewards[user.id][5]:
                print("6th reward")
                user_team_rewards[user.id][5] = True

                await msg.channel.send(f"Congratulations {user.mention}! You have built a starting XI with an overall value of at least 700. You have been rewarded a random **830+ player**!")
                await team_rewards(msg, user, 700)
                
            if overall_value >= 800 and not user_team_rewards[user.id][6]:
                print("7th reward")
                user_team_rewards[user.id][6] = True

                await msg.channel.send(f"Congratulations {user.mention}! You have built a starting XI with an overall value of at least 800. You have been rewarded a random **legend player**!")
                await team_rewards(msg, user, 800)
                
        embed_data = [
            new_embed.title,
            new_embed.description,
            new_embed.color.value,
            [(field.name, field.value, field.inline) for field in new_embed.fields]
        ]
        
        user_teams[user.id] = embed_data
        
        if not user_tutorial_completion[user.id][4][1]:
            user_tutorial_completion[user.id][4][1] = True
                
            if user.id not in user_coins:
                user_coins[user.id] = 0
                
            await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                
            if False not in user_tutorial_completion[user.id][4]:
                user_coins[user.id] += 500
                user_current_tutorial[user.id] = 5
                await msg.channel.send("Tutorial 5 complete! You have been rewarded **500 \U0001f4a0**! Type %tuto for the next steps!")
                
        return new_embed
    
    if p_msg.startswith("%u"):
        if user.id not in user_upgrades:
            user_upgrades[user.id] = [0,0,0,0]
            
        if len(p_msg.split()) != 1:
            if p_msg.split()[1] == "info":              
                embed = discord.Embed(
                title=f"Upgrade Info",
                color=0x00008B
                )
                
                embed.add_field(
                    name="Stadium \U0001f3df",
                    value="Increases the chances of getting a player from your favorite club (excluding Legend cards).\n"
                          "• Level 1: 1000 \U0001f4a0, 0.5% increase.\n"
                          "• Level 2: 2000 \U0001f4a0, 1% increase.\n"
                          "• Level 3: 4000 \U0001f4a0, 2% increase.\n"
                          "• Level 4: 8000 \U0001f4a0, 4% increase.\n"
                          "• Level 5 (MAX): 16000 \U0001f4a0, 8% increase.",
                    inline=False
                )
                embed.add_field(
                    name="Board \U0001f454",
                    value="Boosts overall income. Whenever you collect coins (dailies, selling players, getting duplicates, transfer market), you will receive an extra bonus from what you would usually get.\n"
                          "• Level 1: 3000 \U0001f4a0, 5% boost.\n"
                          "• Level 2: 9000 \U0001f4a0, 10% boost.\n"
                          "• Level 3: 27000 \U0001f4a0, 15% boost.\n"
                          "• Level 4: 50000 \U0001f4a0, 20% boost.\n"
                          "• Level 5 (MAX): 81000 \U0001f4a0, 25% boost.",
                    inline=False
                )
                embed.add_field(
                    name="Training Facility \U0001f3cb\u200d\u2642\ufe0f",
                    value="Boosts the overall value of your starting XI.\n"
                          "• Level 1: 500 \U0001f4a0, 3% boost.\n"
                          "• Level 2: 1000 \U0001f4a0, 3.5% boost.\n"
                          "• Level 1: 2000 \U0001f4a0, 4% boost.\n"
                          "• Level 4: 4000 \U0001f4a0, 4.5% boost.\n"
                          "• Level 5 (MAX): 8000 \U0001f4a0, 5% boost.",
                    inline=False
                )
                embed.add_field(
                    name="Transfer Market \U0001f4dc",
                    value="Reduces the time you need to wait for a transfer to be completed.\n"
                          "• Level 1: 2000 \U0001f4a0, reduced to 3 days.\n"
                          "• Level 2: 5000 \U0001f4a0, reduced to 2 days.\n"
                          "• Level 3: 8000 \U0001f4a0, reduced to 1 day.\n"
                          "• Level 4: 12000 \U0001f4a0, reduced to 12 hours.\n"
                          "• Level 5 (MAX): 24000 \U0001f4a0, reduced to 6 hours.",
                    inline=False
                )
                
                if not user_tutorial_completion[user.id][5][1]:
                    user_tutorial_completion[user.id][5][1] = True
                    
                    if user.id not in user_free_claims:
                        user_free_claims[user.id] = 0
                        
                    await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                        
                    if False not in user_tutorial_completion[user.id][5]:
                        user_free_claims[user.id] += 1
                        user_current_tutorial[user.id] = 6
                        await msg.channel.send("Tutorial 6 complete! You have been rewarded **1 free claim**! Type %tuto for the next steps!")
                            
                return embed
            
            if p_msg.split()[1] == "stadium":
                if user_upgrades[user.id][0] == 5:
                    await msg.channel.send(f"{user.mention} Your stadium is already at max level!")
                    return
                
                price_to_upgrade = stadium_prices[user_upgrades[user.id][0]]
                confirmed = await bot.purchase_confirmation(price_to_upgrade, user, msg)
                
                if confirmed:
                    user_coins[user.id] -= price_to_upgrade
                    user_upgrades[user.id][0] += 1
                    await msg.channel.send(f"{user.mention} Successfully upgraded your stadium to level **{user_upgrades[user.id][0]}**!")
                    
                    if not user_tutorial_completion[user.id][5][2]:
                        user_tutorial_completion[user.id][5][2] = True
                            
                        if user.id not in user_free_claims:
                            user_free_claims[user.id] = 0
                            
                        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                            
                        if False not in user_tutorial_completion[user.id][5]:
                            user_free_claims[user.id] += 1
                            user_current_tutorial[user.id] = 6
                            await msg.channel.send("Tutorial 6 complete! You have been rewarded **1 free claim**! Type %tuto for the next steps!")
                    
                    return
                else:
                    return
            
            if p_msg.split()[1] == "board":
                if user_upgrades[user.id][1] == 5:
                    await msg.channel.send(f"{user.mention} Your board is already at max level!")
                    return
                
                price_to_upgrade = board_prices[user_upgrades[user.id][1]]
                confirmed = await bot.purchase_confirmation(price_to_upgrade, user, msg)
                
                if confirmed:
                    user_coins[user.id] -= price_to_upgrade
                    user_upgrades[user.id][1] += 1
                    await msg.channel.send(f"{user.mention} Successfully upgraded your board to level **{user_upgrades[user.id][1]}**!")
                    
                    if not user_tutorial_completion[user.id][5][2]:
                        user_tutorial_completion[user.id][5][2] = True
                            
                        if user.id not in user_free_claims:
                            user_free_claims[user.id] = 0
                            
                        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                            
                        if False not in user_tutorial_completion[user.id][5]:
                            user_free_claims[user.id] += 1
                            user_current_tutorial[user.id] = 6
                            await msg.channel.send("Tutorial 6 complete! You have been rewarded **1 free claim**! Type %tuto for the next steps!")
                            
                    return
                else:
                    return
            
            if p_msg.split()[1] == "training":
                if user_upgrades[user.id][2] == 5:
                    await msg.channel.send(f"{user.mention} Your training facility is already at max level!")
                    return
                
                price_to_upgrade = training_prices[user_upgrades[user.id][2]]
                confirmed = await bot.purchase_confirmation(price_to_upgrade, user, msg)
                
                if confirmed:
                    user_coins[user.id] -= price_to_upgrade
                    user_upgrades[user.id][2] += 1
                    await msg.channel.send(f"{user.mention} Successfully upgraded your training facility to level **{user_upgrades[user.id][2]}**!")
                    
                    if not user_tutorial_completion[user.id][5][2]:
                        user_tutorial_completion[user.id][5][2] = True
                            
                        if user.id not in user_free_claims:
                            user_free_claims[user.id] = 0
                            
                        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                            
                        if False not in user_tutorial_completion[user.id][5]:
                            user_free_claims[user.id] += 1
                            user_current_tutorial[user.id] = 6
                            await msg.channel.send("Tutorial 6 complete! You have been rewarded **1 free claim**! Type %tuto for the next steps!")                            
                    return
                else:
                    return
            
            if p_msg.split()[1] == "transfer":
                if user_upgrades[user.id][3] == 5:
                    await msg.channel.send(f"{user.mention} Your training facility is already at max level!")
                    return
                
                price_to_upgrade = transfer_prices[user_upgrades[user.id][3]]
                confirmed = await bot.purchase_confirmation(price_to_upgrade, user, msg)
                
                if confirmed:
                    user_coins[user.id] -= price_to_upgrade
                    user_upgrades[user.id][3] += 1
                    await msg.channel.send(f"{user.mention} Successfully upgraded your transfer market to level **{user_upgrades[user.id][3]}**!")
                    
                    if not user_tutorial_completion[user.id][5][2]:
                        user_tutorial_completion[user.id][5][2] = True
                            
                        if user.id not in user_free_claims:
                            user_free_claims[user.id] = 0
                            
                        await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                            
                        if False not in user_tutorial_completion[user.id][5]:
                            user_free_claims[user.id] += 1
                            user_current_tutorial[user.id] = 6
                            await msg.channel.send("Tutorial 6 complete! You have been rewarded **1 free claim**! Type %tuto for the next steps!")
                            
                    return
                else:
                    return
                            
        embed = discord.Embed(
            title=f"{user.name}'s Upgrades",
            description= f"You have **{user_coins[user.id]} \U0001f4a0** !\n" + "\n" + "Use your coins to increase the level of the following upgrades.",
            color=0x00008B
        )
        
        embed.add_field(
        name="Stadium \U0001f3df",
        value=f"Your current level is {user_upgrades[user.id][0]}. Next level: **{stadium_prices[user_upgrades[user.id][0]]} \U0001f4a0** "
              f"- The chances of rolling a player from your favorite team will increase by **{stadium_upgrades[user_upgrades[user.id][0]]}%**.",
        inline=False
        )
        embed.add_field(
            name="Board \U0001f454",
            value=f"Your current level is {user_upgrades[user.id][1]}. Next level: **{board_prices[user_upgrades[user.id][1]]} \U0001f4a0** "
                  f"- Your overall income will be boosted by **{board_upgrades[user_upgrades[user.id][1]]}%**.",
            inline=False
        )
        embed.add_field(
            name="Training Facility \U0001f3cb\u200d\u2642\ufe0f",
            value=f"Your current level is {user_upgrades[user.id][2]}. Next level: **{training_prices[user_upgrades[user.id][2]]} \U0001f4a0** "
                  f"- Your starting XI's overall value will be boosted by **{training_upgrades[user_upgrades[user.id][2]]}%**.",
            inline=False
        )
        embed.add_field(
            name="Transfer Market \U0001f4dc",
            value=f"Your current level is {user_upgrades[user.id][3]}. Next level: **{transfer_prices[user_upgrades[user.id][3]]} \U0001f4a0** "
                  f"- You will be able to complete a transfer every **{transfer_upgrades[user_upgrades[user.id][3]]}**.",
            inline=False
        )
        embed.add_field(
            name="",
            value="For more info about the upgrades and its prices, type %u info.\n"
                  "To level up an upgrade, type %u [upgrade_name]. Example: %u Board.",
            inline=False
        )
        
        if not user_tutorial_completion[user.id][5][0]:
            user_tutorial_completion[user.id][5][0] = True
                
            if user.id not in user_free_claims:
                user_free_claims[user.id] = 0
                
            await msg.channel.send("Substep complete! Type %tuto for the next steps!")
                            
            if False not in user_tutorial_completion[user.id][5]:
                user_free_claims[user.id] += 1
                user_current_tutorial[user.id] = 6
                await msg.channel.send("Tutorial 6 complete! You have been rewarded **1 free claim**! Type %tuto for the next steps!")
            
        return embed
    
    if p_msg == "%index":
        index_description = "__%c__: View your collection.\n" + "__%c [page_number]__: View your collection at a specific page.\n"
        index_description += "__%c [mention]__: View another user's collection.\n" + "__%c [mention] [page_number]__: View another user's collection at a specific page.\n"
        index_description += "__%d__: Claim your daily reward.\n"
        index_description += "__%fc__: Use a free claim.\n"
        index_description += "__%index__: Summary of all commands.\m"
        index_description += "__%lc__: List all players from a club.\n"
        index_description += "__%m [page_number] [player_name]__: Move a player in your collection.\n"
        index_description += "__%n__: Reset your club name to default.\n"
        index_description += "__%n [name]__: Rename your club.\n"
        index_description += "__%p__: View your profile.\n"
        index_description += "__%r__: Roll for a player.\n"
        index_description += "__%rm [player_name]__: Remove a player from your collection.\n"
        index_description += "__%s__: Sort your collection from highest to lowest value.\n"
        index_description += "__%sc__: Select your favorite club.\n"
        index_description += "__%t__: View your starting XI.\n"
        index_description += "__%t [position] [player_name]__: Add a player to your starting XI.\n"
        index_description += "__%t rewards__: View starting XI rewards.\n"
        index_description += "__%t rm [player_name]__: Remove a player from your starting XI.\n"
        index_description += "__%tr (or %trade) [mention] [player_name]__: Trade a player to another user.\n"
        index_description += "__%tm__: View the transfer market.\n"
        index_description += "__%tm add [player_name]__: Add a player from your collection to the transfer list.\n"
        index_description += "__%tm rm [player_name]__: Remove player from transfer list.\n"
        index_description += "__%tuto__: View your current tutorial.\n"
        index_description += "__%tuto [page_number]__: View a specific unlocked tutorial.\n"
        index_description += "__%u__: View your upgrades.\n"
        index_description += "__%u [upgrade]__: Level up an upgrade.\n"
        index_description += "__%u info__: Info about upgrades.\n"
        index_description += "__%v [player_name]__: View a player.\n"
        
        embed = discord.Embed(
            title="Index",
            description=index_description,
            color=0xB2BEB5
        )
        
        return embed
    
    
        
        
        
        