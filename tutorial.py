import discord
import bot

tutorial_messages = {}

async def tutorial(msg, user, page_num):
    server_data = bot.server_data.get(str(msg.guild.id), {})
    user_id = str(user.id)
    
    user_tutorial = server_data.get('user_tutorial', {})
    user_tutorial_completion = server_data.get('user_tutorial_completion', {})
    user_current_page = server_data.get('user_current_page', {})
    user_current_tutorial = server_data.get('user_current_tutorial', {})
    
    if user_id not in user_tutorial:
        tutorial_list = []
        
        tuto_1 = discord.Embed(
            title="Tutorial 1: The Basics",
            description="**Reward: 1 free claim**",
            color=0xFFA500 
        )
        
        tuto_1.add_field(
            name="Roll for a player and claim a player for the first time:",
            value="To roll for a player, simply type %r. The bot will promptly select a player at random and send the player card. To claim the player, react to the player card with any emoji. The bot will indicate if the player has already been claimed by someone else. If the player is already claimed, you cannot claim the player. Instead, you will receive in coins the value of that duplicate player. Note that there is a maximum limit to the number of rolls you can make in an hour. It's also worth noting that you can only make a claim once every 3 hours, so choose your moments wisely to craft a diverse and formidable player collection!",
            inline=False
        )
        
        tuto_2 = discord.Embed(
            title="Tutorial 2: Profile",
            description="**Reward: 250 \U0001f4a0**",
            color=0xFFA500 
        )
        
        tuto_2.add_field(
            name="Display your profile:",
            value="To view your profile, type %p. The menu will display essential information such as your remaining rolls, claim status, and other pertinent details.",
            inline=False   
        )
        
        tuto_2.add_field(
            name="Set your favorite club:",
            value="Type %sc [club_name] to set your favorite club. Example: %sc Manchester Utd",
            inline=False
        )
        
        tuto_2.add_field(
            name="Claim your daily reward:",
            value="Type %d to claim your daily reward of coins.",
            inline=False
        )
        
        tuto_3 = discord.Embed(
            title="Tutorial 3: Collection",
            description= "**Reward: +1 roll/hour**", 
            color=0xFFA500 
        )
        
        tuto_3.add_field(
            name="Claim a second player:",
            value="Remember you can react to the player card with any emoji to claim a player. Additionally, you can claim any player card even if it's not your roll. You can use the free claim you earned previously by typing %fc to claim a new player.",
            inline=False
        )
        
        tuto_3.add_field(
            name="View your collection:",
            value="To view your collection, type %c. You can use the reaction arrows to scroll through your collection. You can also type %c [page_number] to directly go to a page of your collection. Example: %c 4",
            inline=False
        )
        
        tuto_3.add_field(
            name="Sort your collection:",
            value="Type %s to sort your collection from highest to lowest value.",
            inline=False   
        )
        
        tuto_3.add_field(
            name="Move a player in your collection:",
            value="To manually move a player to a specific page in your collection, type %m [page_number] [player_name]. Example: %m 1 Mohamed Salah",
            inline=False
        )
        
        tuto_3.add_field(
            name="Remove a player from your collection:",
            value="To remove a player from your collection, type %rm [player_name]. You will receive in coins the value of the removed player. Example: %rm Kevin De Bruyne",
            inline=False
        )
        
        tuto_3.add_field(
            name="View another player's collection:",
            value="To view another player's collection, type %c [user_mention]. Example: %c @joe325. You can also go to a specific page. Example: %c @joe325 5",
            inline=False
        )
        
        tuto_4 = discord.Embed(
            title="Tutorial 4: Viewing",
            description="**Reward: 500 \U0001f4a0**",
            color=0xFFA500 
        )
        
        tuto_4.add_field(
            name="View any player:",
            value="Type %v [player_name] to view a player. The bot will send a non-claimable card of that player. Example: %v Lionel Messi (Prime)",
            inline=False
        )
        
        tuto_4.add_field(
            name="List the players from a club:",
            value="To view all the players from a specific club, type %lc [club]. Claimed players will have green checkmark next to their name. Example: %lc Real Madrid",
            inline=False
        )
        
        tuto_5 = discord.Embed(
            title="Tutorial 5: Team Building",
            description="**Reward: 500 \U0001f4a0**",
            color=0xFFA500 
        )
        
        tuto_5.add_field(
            name="View your starting XI:",
            value="Type %t to view your starting XI.",
            inline=False
        )
        
        tuto_5.add_field(
            name="Add a player to your starting XI:",
            value="Type %t [position] [player_name] to add a player from your collection to your starting XI. Example: %t F2 Erling Haaland",
            inline=False
        )
        
        tuto_5.add_field(
            name="Remove a player from your starting XI:",
            value="Type %t rm [player_name] to remove a player from your starting XI. Example: %t rm Kylian Mbappé",
            inline=False
        )
        
        tuto_5.add_field(
            name="View the team building rewards:",
            value="Type %t rewards to learn about starting XI rewards.",
            inline=False
        )
        
        tuto_5.add_field(
            name="Rename your club:",
            value="To rename your club, type %n [new_name]. If you want to reset your club name to default, simply type %n.",
            inline=False
        )
        
        tuto_6 = discord.Embed(
            title="Tutorial 6: Upgrades",
            description="**Reward: 1 free claim**",
            color=0xFFA500 
        )
        
        tuto_6.add_field(
            name="Open the upgrades menu:",
            value="Type %u to open the upgrades menu.",
            inline=False
        )
        
        tuto_6.add_field(
            name="Open the upgrades info menu:",
            value="For more info about the upgrades and its prices, type %u info.",
            inline=False
        )
        
        tuto_6.add_field(
            name="Level up an upgrade:",
            value="To level up an upgrade, type %u [upgrade_name]. Example: %u Board.",
            inline=False
        )
        
        tuto_7 = discord.Embed(
            title="Tutorial 7: Trading and the Transfer Market",
            description="**Reward: 750 \U0001f4a0**",
            color=0xFFA500 
        )
        
        tuto_7.add_field(
            name="Complete a trade:",
            value="To trade a player from your collection with another user's player, type %tr (or %trade) [user_mention] [your_player_name]. Example: %tr @joe325 Harry Kane",
            inline=False
        )
        
        tuto_7.add_field(
            name="Open the transfer market menu:",
            value="Type %tm to open the transfer market menu.",
            inline=False
        )
        
        tuto_7.add_field(
            name="Add a player to the transfer list:",
            value="To add a player to the transfer list, type %tm add [player_name]. You may only add one player at a time. Example: %tm add Erling Haaland. To remove a player from your transfer list, type %tm rm [player_name]. Example: %tm rm Erling Haaland",
            inline=False
        )
        
        tuto_7.add_field(
            name="Complete a transfer:",
            value="Wait for your transfer to be completed and receive the transfer fee. ",
            inline=False
        )
        
        tuto_8 = discord.Embed(
            title="Congrats! You have completed the tutorial!",
            description="Type %index for a summary of all the commands." + "\n" + "Type %tuto [page_number] to go back on a specific tutorial.",
            color=0xFFA500 
        )
        
        tuto_1_data = [
            tuto_1.title,
            tuto_1.description,
            tuto_1.color.value,
            [(field.name, field.value, field.inline) for field in tuto_1.fields],
        ]
        
        tuto_2_data = [
            tuto_2.title,
            tuto_2.description,
            tuto_2.color.value,
            [(field.name, field.value, field.inline) for field in tuto_2.fields],
        ]
        
        tuto_3_data = [
            tuto_3.title,
            tuto_3.description,
            tuto_3.color.value,
            [(field.name, field.value, field.inline) for field in tuto_3.fields],
        ]
        
        tuto_4_data = [
            tuto_4.title,
            tuto_4.description,
            tuto_4.color.value,
            [(field.name, field.value, field.inline) for field in tuto_4.fields],
        ]
        
        tuto_5_data = [
            tuto_5.title,
            tuto_5.description,
            tuto_5.color.value,
            [(field.name, field.value, field.inline) for field in tuto_5.fields],
        ]
        
        tuto_6_data = [
            tuto_6.title,
            tuto_6.description,
            tuto_6.color.value,
            [(field.name, field.value, field.inline) for field in tuto_6.fields],
        ]
        
        tuto_7_data = [
            tuto_7.title,
            tuto_7.description,
            tuto_7.color.value,
            [(field.name, field.value, field.inline) for field in tuto_7.fields],
        ]
        
        tuto_8_data = [
            tuto_8.title,
            tuto_8.description,
            tuto_8.color.value,
            [(field.name, field.value, field.inline) for field in tuto_8.fields],
        ]
                
        tutorial_list.append(tuto_1_data)
        tutorial_list.append(tuto_2_data)
        tutorial_list.append(tuto_3_data)
        tutorial_list.append(tuto_4_data)
        tutorial_list.append(tuto_5_data)
        tutorial_list.append(tuto_6_data)
        tutorial_list.append(tuto_7_data)
        tutorial_list.append(tuto_8_data)
        
        user_tutorial[user_id] = tutorial_list
        
    i = 0
    for page in user_tutorial[user_id]:
        if i == 7:
            break
        
        j = 0
        new_page = discord.Embed(
            title=page[0],
            description=page[1],
            color=page[2]
            )
        for field in page[3]:
            if user_tutorial_completion[user_id][i][j]:
                new_page.add_field(name=field[0].split(":")[0] + ": " + "\u2705", value=field[1], inline=field[2])
            else:
                new_page.add_field(name=field[0], value= field[1], inline=field[2])
                
            j += 1
        
        new_page_data = [
            new_page.title,
            new_page.description,
            new_page.color.value,
            [(field.name, field.value, field.inline) for field in new_page.fields],
        ]
        
        user_tutorial[user_id][i] = new_page_data
        i += 1

    if page_num > user_current_tutorial[user_id]:
        print(user_tutorial_completion[user_id][page_num])
        if False in user_tutorial_completion[user_id][page_num]:
            await msg.channel.send("Please complete the current tutorial before moving onto another one.")
            return
        
    tutorials = user_tutorial[user_id]
   
    if 0 <= page_num < len(tutorials):
        user_current_page[user_id] = page_num
        embed_to_show_data = tutorials[page_num]
        
        embed_to_show = discord.Embed(
            title=embed_to_show_data[0],
            description=embed_to_show_data[1],
            color=embed_to_show_data[2]
        )
        
        for field in embed_to_show_data[3]:
            embed_to_show.add_field(name=field[0], value=field[1], inline=field[2])
        
        embed_to_show.set_footer(text=f"{user_current_page[user_id] + 1}/{len(tutorials)}")
       
        if user_id in tutorial_messages:
            tutorial_msg = tutorial_messages[user_id]
            await tutorial_msg.clear_reactions()
            await tutorial_msg.edit(embed=embed_to_show)
        else:
            tutorial_msg = await msg.channel.send(embed=embed_to_show)
            await tutorial_msg.clear_reactions()
            tutorial_messages[user_id] = tutorial_msg
        
        await tutorial_msg.add_reaction("\u2b05")
        await tutorial_msg.add_reaction("\u27a1")
    else:
        await msg.channel.send("Error: Page not found.")
        

            
        
