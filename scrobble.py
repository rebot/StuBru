# In[0]: Importeer de environment variables uit de .env file
import os
import re
import time
from dotenv import load_dotenv

# Haal de environment variabelen op
load_dotenv()

import pylast
import requests
from jsonpath_ng import jsonpath
from jsonpath_ng.ext import parse
from apscheduler.schedulers.blocking import BlockingScheduler

# Maak een nieuwe scheduler aan
sched = BlockingScheduler()

# Activeer de logs
import logging
logging.basicConfig(level=os.getenv('LOGLEVEL', 'INFO'))

# De API key en secret maak je aan op de website:
# zie https://www.last.fm/api/account/create
LASTFM_API_KEY = os.getenv('LASTFM_API_KEY') 
LASTFM_API_SECRET = os.getenv('LASTFM_API_SECRET')

# Om te scrobblen moet je je natuurlijk ook inloggen
lastfm_username_bruut = os.getenv('LASTFM_USERNAME_BRUUT')
lastfm_password_bruut = pylast.md5(os.getenv('LASTFM_PASSWORD_BRUUT'))
lastfm_username_tijdloze = os.getenv('LASTFM_USERNAME_TIJDLOZE')
lastfm_password_tijdloze = pylast.md5(os.getenv('LASTFM_PASSWORD_TIJDLOZE'))
lastfm_username_hooray = os.getenv('LASTFM_USERNAME_HOORAY')
lastfm_password_hooray = pylast.md5(os.getenv('LASTFM_PASSWORD_HOORAY'))

# Studio Brussel Streams
status = 'http://icecast.vrtcdn.be/status-json.xsl'
streams = ['bruut', 'tijdloze', 'hooray']

def scrobble():

    network = {}
    for stream in streams:
        network[stream] = pylast.LastFMNetwork(
            api_secret = LASTFM_API_SECRET,
            username = globals()[f'lastfm_username_{stream}'], 
            password_hash = globals()[f'lastfm_password_{stream}']
        )

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
                artiest, nummer = '', ''
                # Haal de artiest en het nummer op
                for match in matches: 
                    m = re.search(r'(.*?) - (.*)', matches[0].value)
                    if m: 
                        artiest = m.group(1).lower()
                        nummer = m.group(2).lower()
                        logging.debug(f'StuBru {stream.capitalize} - Artiest: {artiest} - Nummer: {nummer}')
                        break
                # Scrobble de nummer naar last.fm
                user = network[stream].get_authenticated_user()
                current = network[stream].get_track(artiest, nummer)
                previous = user.get_recent_tracks(1, cacheable=False)[0].track
                # Scrobble het nummer als het niet het laatste nummer is
                if current.get_correction() != previous.title:
                    network[stream].scrobble(artiest, nummer, timestamp=time.time())
                    logging.debug(f'Nummer gescrobbled naar StuBru-{stream.capitalize}: {artiest.capitalize()} - {nummer.capitalize()}')
                else:
                    logging.debug(f'Geen nieuw nummer...')
                # Update now-playing
                network[stream].update_now_playing(artiest, nummer)

# In[2]: Start het clock process

@sched.scheduled_job('interval', minutes=2)
def timed_job():
    scrobble()

sched.start()
