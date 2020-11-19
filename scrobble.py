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

# Studio Brussel Streams
status = 'http://icecast.vrtcdn.be/status-json.xsl'
streams = ['bruut', 'tijdloze', 'hooray']

LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_API_SECRET = os.getenv('LASTFM_API_SECRET')
LASTFM_USERNAME, LASTFM_PASSWORD = {}, {}

for stream in streams:
    # User account
    LASTFM_USERNAME[stream] = os.getenv(f'LASTFM_USERNAME_{stream.upper()}')
    LASTFM_PASSWORD[stream] = os.getenv(f'LASTFM_PASSWORD_{stream.upper()}')

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

# In[2]: Start het clock process

@sched.scheduled_job('interval', minutes=2)
def timed_job():
    scrobble()

sched.start()
