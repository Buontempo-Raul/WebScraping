import requests
from bs4 import BeautifulSoup
import re
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk

import time
from winotify import Notification, audio

from twilio.rest import Client
import keys 

import schedule
from datetime import time, timedelta, datetime

def fetch_chart(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')
        top_100 = soup.find('div', class_='chart-results-list')
        songs = top_100.find_all('div', class_='o-chart-results-list-row-container')
        results = []
        for song in songs:
            rank = song.find('span', class_='c-label').text.strip()
            song_info = song.find('h3', id='title-of-a-story').text.strip()
            artist_info = song.find('span', class_='c-label').find_next('span').text.strip()
            numbers = song.find_all('li', class_='o-chart-results-list__item')
            number_values = [re.sub(r'\s+', ' ', num.text.strip()) for num in numbers[-3:]]  
            results.append((rank, song_info, artist_info, *number_values))
        return results
    except requests.RequestException as e:
        print(f"Error fetching chart data: {e}")
        return []

def display_chart(url, table, search_term=""):
    results = fetch_chart(url)
    for row in table.get_children():
        table.delete(row)
    filtered_results = [result for result in results if search_term.lower() in result[1].lower() or search_term.lower() in result[2].lower()]
    for result in filtered_results:
        table.insert("", "end", values=result)

def search_chart(url, table, entry):
    search_term = entry.get()
    display_chart(url, table, search_term)

def open_chart_window(title, url):
    chart_window = tk.Toplevel(root)
    chart_window.title(title)
    chart_window.configure(bg="#2c3e50")

    search_frame = tk.Frame(chart_window, bg="#2c3e50")
    search_frame.pack(pady=5)
    search_entry = tk.Entry(search_frame, width=50, bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1")
    search_entry.pack(side=tk.LEFT, padx=5)
    search_button = tk.Button(search_frame, text="Search", command=lambda: search_chart(url, chart_table, search_entry), bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
    search_button.pack(side=tk.LEFT)

    columns = ("Rank", "Song Title", "Artist", "Peak Position", "Last Week Position", "Weeks on Chart")
    chart_table = ttk.Treeview(chart_window, columns=columns, show='headings')
    for col in columns:
        chart_table.heading(col, text=col)
        chart_table.column(col, minwidth=0, width=150, stretch=tk.NO)
    chart_table.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    display_chart(url, chart_table)

def open_releases_window():

    releases_window = tk.Toplevel(root)
    releases_window.title("Recent Releases")
    releases_window.configure(bg="#2c3e50")

    search_label = tk.Label(releases_window, text="Search for a specific artist:", bg="#2c3e50", fg="#ecf0f1")
    search_label.pack(pady=5)
    search_entry = tk.Entry(releases_window, width=50, bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1")
    search_entry.pack(pady=5)
    search_button = tk.Button(releases_window, text="Search", command=lambda: search_releases(search_entry), bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
    search_button.pack(pady=10)

    global text_area
    text_area = scrolledtext.ScrolledText(releases_window, wrap=tk.WORD, width=80, height=20, bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1")
    text_area.pack(padx=10, pady=10)

    artist_label = tk.Label(releases_window, text="Enter artist name:", bg="#2c3e50", fg="#ecf0f1")
    artist_label.pack(pady=5)
    artist_entry = tk.Entry(releases_window, width=50, bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1")
    artist_entry.pack(pady=5)
    add_artist_button = tk.Button(releases_window, text="Add Artist", command=lambda: add_artist(artist_entry), bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
    add_artist_button.pack(pady=10)

    delete_artist_button = tk.Button(releases_window, text="Delete Selected Artist", command=delete_artist, bg="#e74c3c", fg="#ecf0f1", activebackground="#c0392b")
    delete_artist_button.pack(pady=10)

    fetch_button = tk.Button(releases_window, text="Fetch Releases for Favorites", command=display_releases, bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
    fetch_button.pack(pady=10)

    global favorite_artists
    favorite_artists = []

    global artist_listbox
    artist_listbox = tk.Listbox(releases_window, bg="#34495e", fg="#ecf0f1")
    artist_listbox.pack(padx=10, pady=10)

    try:
        with open('fav_artists.txt') as file:
            lines = file.readline()
            
            while lines:
                line = lines[:-1]
                favorite_artists.append(line)
                artist_listbox.insert(tk.END, line)
                lines = file.readline()
    except FileNotFoundError:
        pass

    display_releases()

def add_artist(artist_entry):
    artist = artist_entry.get()
    if artist and artist not in favorite_artists:
        with open('fav_artists.txt','a') as file:
            file.write(artist)
            file.write('\n')

        favorite_artists.append(artist)
        artist_listbox.insert(tk.END, artist)
        artist_entry.delete(0, tk.END)

def delete_artist():
    selected_artist_index = artist_listbox.curselection()
    if selected_artist_index:
        selected_artist = artist_listbox.get(selected_artist_index)
        favorite_artists.remove(selected_artist)
        artist_listbox.delete(selected_artist_index)

        with open('fav_artists.txt', 'w') as file:
            for artist in favorite_artists:
                file.write(artist + '\n')

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

def fetch_new_releases_for_artist(artist):
    return fetch_new_releases([artist])

def display_releases():
    if favorite_artists:
        new_results = fetch_new_releases(favorite_artists)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, new_results)

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

            print(message.body)

        with open('old_list.txt','w') as file:
            file.write(new_results)
    else:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, "Please add at least one artist to the list.")

def search_releases(search_entry):
    artist = search_entry.get()
    if artist:
        results = fetch_new_releases_for_artist(artist)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, results)
    else:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, "Please enter an artist name.")

def on_country_select(event, url_dict, chart_table, search_entry):
    selected_country = country_combo.get()
    if selected_country:
        display_chart(url_dict[selected_country], chart_table, search_entry.get())

def open_hot_100_window():
    country_urls = {
        'Italy': 'https://www.billboard.com/charts/billboard-italy-hot-100/',
        'Romania': 'https://www.billboard.com/charts/romania-songs-hotw/',
        'France': 'https://www.billboard.com/charts/france-songs-hotw/',
        'USA': 'https://www.billboard.com/charts/hot-100/',
        'UK': 'https://www.billboard.com/charts/official-uk-songs/',
        'Belgium': 'https://www.billboard.com/charts/belgium-songs-hotw/',
        'Norway': 'https://www.billboard.com/charts/norway-songs-hotw/',
        'Spain': 'https://www.billboard.com/charts/spain-songs-hotw/',
        'Sweden': 'https://www.billboard.com/charts/sweden-songs-hotw/',
        'Portugal': 'https://www.billboard.com/charts/portugal-songs-hotw/',
        'Hungary': 'https://www.billboard.com/charts/hungary-songs-hotw/',
    }

    hot_100_window = tk.Toplevel(root)
    hot_100_window.title("Hot 100")
    hot_100_window.configure(bg="#2c3e50")

    country_frame = tk.Frame(hot_100_window, bg="#2c3e50")
    country_frame.pack(pady=5)
    country_label = tk.Label(country_frame, text="Select Country:", bg="#2c3e50", fg="#ecf0f1")
    country_label.pack(side=tk.LEFT, padx=5)
    
    global country_combo
    country_combo = ttk.Combobox(country_frame, values=list(country_urls.keys()), state="readonly")
    country_combo.pack(side=tk.LEFT, padx=5)
    
    search_frame = tk.Frame(hot_100_window, bg="#2c3e50")
    search_frame.pack(pady=5)
    search_entry = tk.Entry(search_frame, width=50, bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1")
    search_entry.pack(side=tk.LEFT, padx=5)
    search_button = tk.Button(search_frame, text="Search", command=lambda: search_chart(country_urls[country_combo.get()], chart_table, search_entry), bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
    search_button.pack(side=tk.LEFT)

    columns = ("Rank", "Song Title", "Artist", "Peak Position", "Last Week Position", "Weeks on Chart")
    chart_table = ttk.Treeview(hot_100_window, columns=columns, show='headings')
    for col in columns:
        chart_table.heading(col, text=col)
        chart_table.column(col, minwidth=0, width=150, stretch=tk.NO)
    chart_table.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    country_combo.bind("<<ComboboxSelected>>", lambda event: on_country_select(event, country_urls, chart_table, search_entry))


root = tk.Tk()
root.title("Main Window")
root.geometry("600x400")
root.configure(bg="#2c3e50")

open_releases_button = tk.Button(root, text="New Releases", command=open_releases_window, bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
open_releases_button.pack(pady=10)

open_hot_100_button = tk.Button(root, text="Hot 100", command=open_hot_100_window, bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
open_hot_100_button.pack(pady=10)

root.mainloop()

