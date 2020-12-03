# In[0]: Importeer de environment variables uit de .env file
import os
import re
import time
from dotenv import load_dotenv

# Haal de environment variabelen op
load_dotenv()

import pylast
from pylast import PERIOD_1MONTH
import requests
from jsonpath_ng import jsonpath
from jsonpath_ng.ext import parse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from apscheduler.schedulers.blocking import BlockingScheduler

# Maak een nieuwe scheduler aan
sched = BlockingScheduler()

import logging
logging.basicConfig(level=os.getenv('LOGLEVEL', 'INFO'))

# In[1]: Algemene instellingen

# Studio Brussel Streams
status = 'http://icecast.vrtcdn.be/status-json.xsl'
streams = ['brussel', 'bruut', 'tijdloze', 'hooray']

LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_API_SECRET = os.getenv('LASTFM_API_SECRET')
LASTFM_USERNAME, LASTFM_PASSWORD = {}, {}

scope = 'playlist-modify-public'

# Maak het cache bestand aan - dit is het resultaat
# van auth_manager.get_access_token()
cache = os.getenv('SPOTIPY_CACHE')

if not os.path.exists('.cache'):
    with open('.cache', 'w') as f:
        f.write(cache)

for stream in streams:
    # User account
    LASTFM_USERNAME[stream] = os.getenv(f'LASTFM_USERNAME_{stream.upper()}')
    LASTFM_PASSWORD[stream] = os.getenv(f'LASTFM_PASSWORD_{stream.upper()}')

# Scope voor de API
scope = 'playlist-modify-public'

# Cache bestand voor authenticatie Spotipy client
# Resultaat van auth_manager.get_access_token()
cache = os.getenv('SPOTIPY_CACHE')

if not os.path.exists('.cache'):
    with open('.cache', 'w') as f:
        f.write(cache)

# In[2]: Functies die periodiek worden aangeroepen
def scrobble():

    network = {}
    for stream in streams:
        network[stream] = pylast.LastFMNetwork(
            api_key = LASTFM_API_KEY,
            api_secret = LASTFM_API_SECRET,
            username = LASTFM_USERNAME[stream], 
            password_hash = pylast.md5(LASTFM_PASSWORD[stream])
        )
        logging.debug(network[stream].get_authenticated_user())

    with requests.Session() as s:
        # Haal de stream op uit de status pagina    
        r = s.get(status)
        # Controleer of je een geldige response kreeg
        if r.status_code == 200:
            json_data = r.json()
            # Loop over de verschillende streams
            for stream in streams:
                jsonpath_expr = parse(f'$.icestats.source[?server_name =~ "{stream.capitalize()}"].title')
                matches = jsonpath_expr.find(json_data)
                # Definieer artiest en nummer
                artiest, nummer = None, None
                # Haal de artiest en het nummer op
                for match in matches: 
                    m = re.search(r'(.*?) - (.*)', match.value)
                    if m: 
                        artiest = m.group(1).lower()
                        nummer = m.group(2).lower()
                        logging.debug(f'StuBru {stream.capitalize()} - Artiest: {artiest} - Nummer: {nummer}')
                        break
                # Controleer of een songtitel gevonden is
                if artiest is None and nummer is None:
                    logging.debug(f'StuBru {stream.capitalize()} - Geen songtitel gevonden')
                    continue
                # Scrobble de nummer naar last.fm
                user = network[stream].get_authenticated_user()
                current = network[stream].get_track(artiest, nummer)
                try: 
                    previous = user.get_recent_tracks(1, cacheable=False)[0].track
                except IndexError:
                    network[stream].scrobble(artiest, nummer, timestamp=time.time())
                    logging.info(f'Nummer gescrobbled naar StuBru-{stream.capitalize()}: {artiest.capitalize()} - {nummer.capitalize()}')
                else:
                    # Scrobble het nummer als het niet het laatste nummer is
                    if current.get_correction() != previous.title:
                        network[stream].scrobble(artiest, nummer, timestamp=time.time())
                        logging.info(f'Nummer gescrobbled naar StuBru-{stream.capitalize()}: {artiest.capitalize()} - {nummer.capitalize()}')
                    else:
                        logging.debug(f'Geen nieuw nummer...')
                    # Update now-playing
                    network[stream].update_now_playing(artiest, nummer)

def spotify():
    # Start de Spotify client
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    playlists = {
        'bruut': 'StuBru | Bruut',
        'tijdloze': 'StuBru | De Tijdloze',
        'hooray': 'StuBru | Hooray'
    }

    # Haal de playlijsten op van de huidige gebruiker
    user_playlists = sp.current_user_playlists()
    user_playlists_titles = [p['name'] for p in user_playlists['items']]

    # Maak een nieuwe playlist als ze niet bestaat
    for _, playlist in playlists.items():
        if playlist not in user_playlists_titles:
            user_playlists['items'].append(sp.user_playlist_create(sp.me()['id'], playlist))

    # Hervorm de playlijsten
    user_playlists = {p['name']: {'id': p['id'], 'uri': p['uri'], 'href': p['href']} for p in user_playlists['items']}

    # Definieer een cleanup regex om songtitels op te kuisen
    cleanup = re.compile(r'(radio edit|\(|\)|live)')

    network = {}
    for stream in streams:
        network[stream] = pylast.LastFMNetwork(
            api_key = LASTFM_API_KEY,
            api_secret = LASTFM_API_SECRET,
            username = LASTFM_USERNAME[stream], 
            password_hash = pylast.md5(LASTFM_PASSWORD[stream])
        )
        # Haal de top 10 op van de laatste week
        tracklist = network[stream].get_authenticated_user().get_top_tracks(period=PERIOD_1MONTH, limit=15)
        # Zoek de nummer op spotify en sla hun id op
        nummers = []
        for nummer, plays in tracklist:
            # Stop bij 10 nummers
            if len(nummers) >= 10:
                break
            # Haal de titel en artiest op
            titel, _ = cleanup.subn('',nummer.title)
            artiest = nummer.artist.name
            # Zoek het liedje op spotify
            try:
                resultaat = sp.search(artiest+' '+titel, type='track', limit=1)
                spotify_id = resultaat['tracks']['items'][0]['id']
            except:
                # Sla het liedje over als het niet gevonden is
                continue
            else:
                # Voeg liedje toe aan de playlijst
                nummers.append(spotify_id)
        # Overschrijf alle nummers op de afspeellijst
        sp.playlist_replace_items(user_playlists[playlists[stream]]['id'], nummers)

# In[2]: Start het clock process

@sched.scheduled_job('interval', minutes=2)
def timed_job():
    scrobble()

@sched.scheduled_job('cron', day_of_week='mon-sun', hour=7, timezone='Europe/Brussels')
def scheduled_job():
    spotify()

sched.start(paused=False)
