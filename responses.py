import random
import discord
import bot
import unidecode
import emoji
import asyncio
import time

user_teams = {}
user_team_players = {}
user_upgrades = {}
user_team_rewards = {}

rolled_times = {}

stadium_upgrades = [0.5, 1, 2, 4, 8]
stadium_prices = [1000, 2000, 4000, 8000, 16000]
        
board_upgrades = [5, 10, 15, 20, 25]
board_prices = [3000, 9000, 27000, 50000, 81000]
        
training_upgrades = [3, 3.5, 4, 4.5, 5]
training_prices = [500, 1000, 2000, 4000, 8000]
        
transfer_upgrades = ["3 days", "2 days", "1 day", "12 hours", "6 hours"]
transfer_prices = [2000, 5000, 8000, 12000, 24000]

async def handle_responses(msg, user_msg, user) -> discord.Embed:
    f = open('players_list.txt', 'r', encoding='utf-8')
    g = open('legends_list.txt', 'r', encoding='utf-8')
    players_list = f.readlines()
    legends_list = g.readlines()
    
    p_msg = user_msg.lower()
    
    claimed = False
    
    if p_msg == "%r":
        if user.id not in user_upgrades:
            user_upgrades[user.id] = [0,0,0,0]
            
        if user.id not in bot.user_favorite_club:
            bot.user_favorite_club[user.id] = ""
            
        num_player_club = 0
        club_upgrade_chance = 0
        normal_roll = False
        favorite_club_list = []
        
        if bot.user_favorite_club[user.id] != "":
            for line in players_list:
                if bot.user_favorite_club[user.id] in line:
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
        
        if normal_roll:
            chance = random.randint(0, 2000)
            
            if chance == 0:
                rolled_player = random.choice(legends_list)
            else:
                rolled_player = random.choice(players_list)
        
        player_info = rolled_player.strip().split(", ")
        player_name, player_positions, player_club, player_nationality, player_value, player_imageURL, player_id = player_info
        player_value += " " + emoji.emojize(":diamond_with_a_dot:")
        
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
        
        rolled_time = time.time()
        expiration_time = rolled_time + 60

        rolled_times[player_id] = (rolled_time, expiration_time)
        
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
                if all(term in normalized_line for term in normalized_search_terms):
                    player_info = line.strip().split(", ")
                    player_info.append("not legend")
                    players_found.append(player_info)
                    break
            
            for line in legends_list:
                normalized_line = unidecode.unidecode(line.lower())
                if all(term in normalized_line for term in normalized_search_terms):
                    player_info = line.strip().split(", ")
                    player_info.append("legend")
                    players_found.append(player_info)
                    break
                
            return players_found
        
        players_found = search_player(search_terms)
        
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
        for playerid in bot.playerids:
            if player_id == playerid:
                claimed = True
                claimed_user = bot.usernames[i]
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
            embed.set_footer(text="Football Roll Bot, " + player_id)
            
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
            embed.set_footer(text="Football Roll Bot, " + player_id)
            
            if claimed:
                player_status = f"**Claimed by {claimed_user}**" 
                embed.description += ("\n" + player_status)
            
            
        print(claimed)

        return embed
    
    if p_msg.startswith("%t"):
        if user.id not in user_upgrades:
            user_upgrades[user.id] = [0,0,0,0]
            
        if user.id not in user_team_players:
            user_team_players[user.id] = []
        
        if user.id not in user_team_rewards:
            user_team_rewards[user.id] = [False, False, False, False, False, False, False] 
        
        forward_pos = ["LW", "ST", "RW", "CF"]
        midfield_pos = ["CAM", "LM", "RM", "CM", "CDM"]
        defense_pos = ["LWB", "RWB", "LB", "RB", "CB", "SW"]
        
        fpos = ["f1", "f2", "f3"]
        mpos = ["m1", "m2", "m3", "m4"]
        dpos = ["d1", "d2", "d3"]
        
        if user.id not in user_teams:
            embed = discord.Embed(
                title=f"{user.name}'s Starting XI",
                description= "Type %t [position] [player_name] to add a player from your collection to your starting XI" + "\n" + "Example: %t F2 Erling Haaland" + "\n" + "\n" + "Type %t rewards to learn about starting XI rewards.",
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
            
            user_teams[user.id] = embed
        
        if len(p_msg.split()) == 1:
            new_embed = discord.Embed(
                title=user_teams[user.id].title,
                description=user_teams[user.id].description,
                color=user_teams[user.id].color
            )
            
            overall_value = 0
            player_values = []
            if len(user_team_players[user.id]) != 0:
                for player in user_team_players[user.id]:
                    for field in player.fields:
                        if "Value:" in field.name:
                            player_values.append(int(field.name.split()[1]))
                            break
                                
                overall_value = round(sum(player_values) / len(user_team_players[user.id]))
            
            if user_upgrades[user.id][2] != 0:
                overall_value = float(overall_value)
                overall_value += overall_value * (training_upgrades[user_upgrades[user.id][2] - 1] / 100)
                overall_value = int(overall_value)
            
            for field in user_teams[user.id].fields:
                if field.name.strip() == "Overall Value":
                    new_embed.add_field(name=field.name, value=overall_value, inline=field.inline)
                else:
                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline) 
            
            user_teams[user.id] = new_embed
            return user_teams[user.id]
        
        if p_msg.split()[1] == "rewards":
            ovl_value = ""
            for field in user_teams[user.id].fields:
                if field.name.strip() == "Overall Value":
                    ovl_value = field.value.strip()
                    
            reward_info = f"The overall value of your starting XI is **{ovl_value}**!\n" + "You must build a full team of 11 players to earn rewards.\n" + "\n"
            reward_info += "Build your first ever starting XI - Reward: **+1 rolls/hour**"
            if user_team_rewards[user.id][0]:
                reward_info += " \u2705"
            reward_info += "\n" + "\n" + "Build a starting XI with an overall value of 300 - Reward: **2 free claims**"
            if user_team_rewards[user.id][1]:
                reward_info += " \u2705"
            reward_info += "\n" + "\n" + "Build a starting XI with an overall value of 400 - Reward: **10 boosted rolls**"
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
            
            return embed
            
       
        search_terms = p_msg.split()[2:]
        print("Search terms:", search_terms)
            
        collection = bot.user_collections[user.id]
        correct_player = False
        correct_pos = False
        sel_player = ""
        
        if p_msg.split()[1] == "rm":
            new_embed = discord.Embed(
                title=user_teams[user.id].title,
                description=user_teams[user.id].description,
                color=user_teams[user.id].color
            )
            
            for field in user_teams[user.id].fields:
                if field.name.strip().lower() == p_msg.split()[2]:
                    new_embed.add_field(name=field.name, value="", inline=field.inline)
                elif all(term.lower() in field.value.strip().lower() for term in search_terms):
                     new_embed.add_field(name=field.name, value="", inline=field.inline)
                else:
                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline)

            user_teams[user.id] = new_embed
            
            for player in user_team_players[user.id]:
                if player.title == p_msg.split()[2]:
                    user_team_players[user.id].remove(player)
            
            return

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
                user_team_players[user.id].append(player)    
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
                if field.value.strip().lower() == sel_player.lower():
                    if field.name.strip().lower() != p_msg.split()[1]:
                        new_embed.add_field(name=field.name, value="", inline=field.inline)
                        continue 
                    
                if field.name.strip().lower() == p_msg.split()[1]:
                    new_embed.add_field(name=field.name, value=sel_player, inline=field.inline)
                else:
                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline)

            user_teams[user.id] = new_embed
        
        new_embed = discord.Embed(
                title=user_teams[user.id].title,
                description=user_teams[user.id].description,
                color=user_teams[user.id].color
        )
        
        overall_value = 0
        player_values = []
        if len(user_team_players[user.id]) != 0:
            for player in user_team_players[user.id]:
                for field in player.fields:
                    if "Value:" in field.name:
                        player_values.append(int(field.name.split()[1]))
                        break
                            
            overall_value = round(sum(player_values) / len(user_team_players[user.id]))
        
        if user_upgrades[user.id][2] != 0:
            overall_value = float(overall_value)
            overall_value += overall_value * (training_upgrades[user_upgrades[user.id][2] - 1] / 100)
            overall_value = int(overall_value)
        
        for field in user_teams[user.id].fields:
            if field.name.strip() == "Overall Value":
                new_embed.add_field(name=field.name, value=overall_value, inline=field.inline)
            else:
                new_embed.add_field(name=field.name, value=field.value, inline=field.inline) 
        
        user_teams[user.id] = new_embed
        return user_teams[user.id]
    
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
                          "• Level 4: 1000 \U0001f4a0, 20% boost.\n"
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
                            
                return embed
            
            if p_msg.split()[1] == "stadium":
                if user_upgrades[user.id][0] == 5:
                    await msg.channel.send(f"{user.mention} Your stadium is already at max level!")
                    return
                
                price_to_upgrade = stadium_prices[user_upgrades[user.id][0]]
                confirmed = await bot.purchase_confirmation(price_to_upgrade, user, msg)
                
                if confirmed:
                    bot.user_coins[user.id] -= price_to_upgrade
                    user_upgrades[user.id][0] += 1
                    await msg.channel.send(f"{user.mention} Successfully upgraded your stadium to level **{user_upgrades[user.id][0]}**!")
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
                    bot.user_coins[user.id] -= price_to_upgrade
                    user_upgrades[user.id][1] += 1
                    await msg.channel.send(f"{user.mention} Successfully upgraded your board to level **{user_upgrades[user.id][1]}**!")
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
                    bot.user_coins[user.id] -= price_to_upgrade
                    user_upgrades[user.id][2] += 1
                    await msg.channel.send(f"{user.mention} Successfully upgraded your training facility to level **{user_upgrades[user.id][2]}**!")
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
                    bot.user_coins[user.id] -= price_to_upgrade
                    user_upgrades[user.id][3] += 1
                    await msg.channel.send(f"{user.mention} Successfully upgraded your transfer market to level **{user_upgrades[user.id][3]}**!")
                    return
                else:
                    return
                            
        embed = discord.Embed(
            title=f"{user.name}'s Upgrades",
            description= f"You have **{bot.user_coins[user.id]} \U0001f4a0** !\n" + "\n" + "Use your coins to increase the level of the following upgrades.",
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
            
        return embed
        
        
        
        