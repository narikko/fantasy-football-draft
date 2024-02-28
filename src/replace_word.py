word_to_remove = " FIFA 24"

# Open the file in read-write mode
with open("D:\\Soccer Discord Bot\\data\\new_players_list.txt", 'r+', encoding='utf-8') as f:
    # Read the content
    content = f.read()

    # Replace all occurrences of the word with an empty string
    modified_content = content.replace(word_to_remove, '')

    # Move the file pointer to the beginning of the file
    f.seek(0)

    # Truncate the file (remove any content after the current position)
    f.truncate()

    # Write the modified content back to the file
    f.write(modified_content)
    
print("Done")