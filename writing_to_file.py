import scrape

fifa_players = scrape.scrape_fifa_players()

f = open('players_list.txt', 'w', encoding='utf-8')

for player in fifa_players:
    f.write(f"{player['name']}, {player['club']}, {player['nationality']}, Value: {player['value']}, {player['imageURL']}\n")

print("Done!")            
f.close()
