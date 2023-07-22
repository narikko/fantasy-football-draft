import requests
from bs4 import BeautifulSoup

def scrape_fifa_players():
    base_url = 'https://www.fifaindex.com/players/'
    players_data = []
    rare = 0
    semi_rare = 0

    num_pages = 605

    for page_num in range(1, num_pages + 1):
        url = f'{base_url}?page={page_num}'
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            players_table = soup.find('tbody')
            rows = players_table.find_all('tr')

            for row in rows:
                try:
                    player_name_element = row.find('td', {'data-title': 'Name'}).find('a', class_='link-player')
                    player_name = player_name_element.text.strip()
                except AttributeError:
                    player_name = "N/A"   

                overall_rating_elements = row.select('td[data-title="OVR / POT"] span.badge.badge-dark.rating')
                if len(overall_rating_elements) == 2:
                    try:
                        current_overall_rating = int(overall_rating_elements[0].text.strip())
                        potential_overall_rating = int(overall_rating_elements[1].text.strip())
                    except (ValueError, IndexError):
                        current_overall_rating = 0
                        potential_overall_rating = 0
                else:
                    current_overall_rating = 0
                    potential_overall_rating = 0
                    
                overall_value = int(((0.8 * current_overall_rating) + (0.2 * potential_overall_rating)) * 10)
                
                if overall_value < 830 and overall_value >= 790:
                    overall_value -= 280
                    semi_rare += 1
                elif overall_value < 790 and overall_value >= 590:
                    overall_value -= 580
                elif overall_value < 590:
                    overall_value = 10
                else:
                    rare += 1

                try:
                    nationality_element = row.find('td', {'data-title': 'Nationality'}).find('a', class_='link-nation')
                    nationality = nationality_element['title']
                except AttributeError:
                    nationality = "N/A"

                try:
                    club_element = row.find('td', {'data-title': 'Team'}).find('a', class_='link-team')
                    club = club_element['title'].replace(' FIFA 23', '')
                except AttributeError:
                    club = "N/A"

                img_element = row.find('img', class_='player')
                image_url = img_element['src'] if img_element else "N/A"

                if player_name != "N/A" and (current_overall_rating > 0 or potential_overall_rating > 0):
                    player_data = {
                        'name': player_name,
                        'value': overall_value,
                        'club': club,
                        'nationality': nationality,
                        'imageURL': image_url
                    }
                    players_data.append(player_data)

        else:
            print(f'Failed to fetch data from page {page_num}.')

    print(f"Total players scraped: {len(players_data)}")
    print(str(rare) + " rare players.")
    print(str(semi_rare) + " semi-rare players.")
    return players_data
