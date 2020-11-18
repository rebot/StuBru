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
lastfm_username = os.getenv('LASTFM_USERNAME')
lastfm_password = pylast.md5(os.getenv('LASTFM_PASSWORD'))

# Studio Brussel Streams
status = 'http://icecast.vrtcdn.be/status-json.xsl'
stream = 'http://icecast.vrtcdn.be/stubru_bruut-mid.mp3'

def scrobble():

    network = pylast.LastFMNetwork(
        api_key = LASTFM_API_KEY, 
        api_secret = LASTFM_API_SECRET,
        username = lastfm_username, 
        password_hash = lastfm_password
    )

    with requests.Session() as s:
        # Voeg header toe om ook de metadata te bevragen
        s.headers.update({
            'Icy-MetaData': '1'
        })
        # Start de stream op
        r = s.get(stream, stream=True)
        # Controleer de encoding
        if r.encoding is None:
            r.encoding = 'utf-8'
        # Loop over de data en zoek voor de songtitel
        # De chunk_size is de grootte van het datablock
        # Informatie te achterhalen via http://icecast.vrtcdn.be/status-json.xsl
        for line in r.iter_content(chunk_size=19600, decode_unicode=True):
            m = re.search(r'StreamTitle=\'(.*?) - (.*?)\';', line)
            if m: 
                artiest = m.group(1).lower()
                nummer = m.group(2).lower()
                logging.debug(f'Artiest: {artiest} - Nummer: {nummer}')
                break
        
        # Haal de stream op uit de status pagina
        r = s.get(status)
        # Controleer of je een geldige response kreeg
        if r.status_code == 200:
            json_data = r.json()
            jsonpath_expr = parse('$.icestats.source[?server_name = "StuBru Bruut"].title')
            matches = jsonpath_expr.find(json_data)
            # Haal de artiest en het nummer op
            for match in matches: 
                m = re.search(r'(.*?) - (.*)', matches[0].value)
                if m: 
                    artiest = m.group(1).lower()
                    nummer = m.group(2).lower()
                    logging.debug(f'Artiest: {artiest} - Nummer: {nummer}')
                    break

    # Scrobble het nummer naar last.fm
    user = network.get_authenticated_user()
    current = network.get_track(artiest, nummer)
    previous = user.get_recent_tracks(1, cacheable=False)[0].track

    if current.get_mbid() != previous.get_mbid():
        network.scrobble(artiest, nummer, timestamp=time.time())
        logging.debug(f'Nummer gescrobbled: {artiest.capitalize()} - {nummer.capitalize()}')
    else:
        logging.debug(f'Geen nieuw nummer...')

    network.update_now_playing(artiest, nummer)

# In[2]: Start het clock process

@sched.scheduled_job('interval', minutes=2)
def timed_job():
    scrobble()

sched.start()
