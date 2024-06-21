import requests
from bs4 import BeautifulSoup
import re
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk

def fetch_new_releases(artist):
    url = 'https://consequence.net/upcoming-releases/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')

        sections = soup.find('div', class_='body')
        all_songs = sections.find('div', class_='post-content')
        songs = all_songs.find_all('p')

        results = []
        for song in songs:
            if artist.lower() in song.text.lower():
                date = song.find_previous('span', style='text-decoration: underline;')
                results.append(f"{date.text}\n{song.text}\n{'-'*40}")
        return "\n".join(results)
    else:
        return f"Failed to retrieve the webpage. Status code: {response.status_code}"

def display_releases():
    artist = artist_entry.get()
    if artist:
        results = fetch_new_releases(artist)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, results)
    else:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, "Please enter an artist name.")

def fetch_hot_100():
    url = 'https://www.billboard.com/charts/hot-100/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
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
            number_values = [re.sub(r'\s+', ' ', num.text.strip()) for num in numbers[-3:]]  # Get the last three numbers

            results.append((rank, song_info, artist_info, *number_values))
        return results
    else:
        return []

def display_hot_100(search_term=""):
    results = fetch_hot_100()
    for row in hot_100_table.get_children():
        hot_100_table.delete(row)

    filtered_results = [result for result in results if search_term.lower() in result[1].lower() or search_term.lower() in result[2].lower()]
    for result in filtered_results:
        hot_100_table.insert("", "end", values=result)

def search_hot_100():
    search_term = search_entry.get()
    display_hot_100(search_term)

def open_releases_window():
    releases_window = tk.Toplevel(root)
    releases_window.title("Recent Releases")
    releases_window.configure(bg="#2c3e50")

    artist_label = tk.Label(releases_window, text="Enter artist name:", bg="#2c3e50", fg="#ecf0f1")
    artist_label.pack(pady=5)
    global artist_entry
    artist_entry = tk.Entry(releases_window, width=50, bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1")
    artist_entry.pack(pady=5)

    fetch_button = tk.Button(releases_window, text="Fetch Releases", command=display_releases, bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
    fetch_button.pack(pady=10)

    global text_area
    text_area = scrolledtext.ScrolledText(releases_window, wrap=tk.WORD, width=80, height=20, bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1")
    text_area.pack(padx=10, pady=10)

def open_hot_100_window():
    hot_100_window = tk.Toplevel(root)
    hot_100_window.title("Hot 100")
    hot_100_window.configure(bg="#2c3e50")

    search_frame = tk.Frame(hot_100_window, bg="#2c3e50")
    search_frame.pack(pady=5)
    global search_entry
    search_entry = tk.Entry(search_frame, width=50, bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1")
    search_entry.pack(side=tk.LEFT, padx=5)
    search_button = tk.Button(search_frame, text="Search", command=search_hot_100, bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
    search_button.pack(side=tk.LEFT)

    columns = ("Rank", "Song Title", "Artist", "Peak Position", "Last Week Position", "Weeks on Chart")
    global hot_100_table
    hot_100_table = ttk.Treeview(hot_100_window, columns=columns, show='headings')
    
    for col in columns:
        hot_100_table.heading(col, text=col)
        hot_100_table.column(col, minwidth=0, width=150, stretch=tk.NO)

    hot_100_table.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    display_hot_100()

root = tk.Tk()
root.title("Main Window")
root.geometry("600x400")  # dimensiunea ferestrei principale
root.configure(bg="#2c3e50")

# Buton pentru fereastra cu albumele anuntate
open_releases_button = tk.Button(root, text="New Releases", command=open_releases_window, bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
open_releases_button.pack(pady=10)

# Buton pentru top 100
open_hot_100_button = tk.Button(root, text="Hot 100", command=open_hot_100_window, bg="#3498db", fg="#ecf0f1", activebackground="#2980b9")
open_hot_100_button.pack(pady=10)

# start
root.mainloop()
