# Create an empty set to store player names
player_names = set()

# List of file names
file_names = ["players_list.txt", "ultra_rare_players_list.txt", "rare_players.txt", "legends_list.txt"]

# Function to add player names from a file to the set
def add_player_names_from_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        for line in file:
            name = line.split(",")[0].strip()  # Get the player name from each line
            player_names.add(name)

# Loop through the file names and add player names to the set
for file_name in file_names:
    add_player_names_from_file(file_name)

# Create a dictionary to store duplicate player names and the number of occurrences
duplicate_names = {}

# Find and store duplicate player names
for name in player_names:
    count = sum(1 for fname in file_names if name in open(fname, 'rb').read().decode('utf-8', 'ignore'))
    if count > 1:
        duplicate_names[name] = count

# Print the duplicate player names
for name, count in duplicate_names.items():
    print(f"Player Name: {name}, Occurrences: {count}")






