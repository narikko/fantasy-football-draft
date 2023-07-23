import scrape

fifa_players = scrape.scrape_fifa_players()

f = open('players_list.txt', 'w', encoding='utf-8')

id_ = 0
for player in fifa_players:
    id_ += 1
    player_id = f"{id_:05d}"
    
    f.write(f"{player['name']}, {player['club']}, {player['nationality']}, Value: {player['value']}, {player['imageURL']}, {player_id}\n")

print("Done!")            
f.close()
