import requests
from bs4 import BeautifulSoup
import re
from winotify import Notification, audio
from twilio.rest import Client
import keys
from datetime import datetime

def fetch_new_releases(artist_list):
    url = 'https://consequence.net/upcoming-releases/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')

        sections = soup.find('div', class_='body')
        all_songs = sections.find('div', class_='post-content')
        songs = all_songs.find_all('p')

        results = []
        for song in songs:
            for artist in artist_list:
                if artist.lower() in song.text.lower():
                    date = song.find_previous('span', style='text-decoration: underline;')
                    results.append(f"{date.text}\n{song.text}\n{' '*40}")
        return "\n".join(results)
    except requests.RequestException as e:
        return f"Failed to retrieve the webpage. Error: {e}"

def display_releases():
    try:
        with open('fav_artists.txt') as file:
            favorite_artists = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        favorite_artists = []

    if favorite_artists:
        new_results = fetch_new_releases(favorite_artists)
        
        try:
            with open('old_list.txt', 'r') as file:
                old_results = file.read()
        except FileNotFoundError:
            old_results = ""

        if old_results != new_results:
            toast = Notification(app_id="SPOPIFY",
                                 title="NEW MUSIC ANNOUNCED",
                                 msg="A new album has been announced",
                                 duration="long",
                                 icon=r"D:\Practica\image.webp")
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            
            client = Client(keys.account_sid, keys.auth_token)
            message = client.messages.create(
                body = "\nNEW MUSIC\n\n" + new_results,
                from_ = keys.twilio_number,
                to = keys.my_phone_number
            )
            print("SMS sent:", message.body)

        with open('old_list.txt','w') as file:
            file.write(new_results)
    else:
        print("Please add at least one artist to the fav_artists.txt file.")

# Run the function once and stop
if __name__ == "__main__":
    display_releases()
