import os
import re
import sys
import time
import logging

import pylast
import requests
from jsonpath_ng.ext import parse

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger()

hnd = logging.StreamHandler(sys.stdout)
frm = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hnd.setFormatter(frm)

logger.addHandler(hnd)
logger.setLevel(logging.DEBUG)

# In[1]: Algemene instellingen

# Studio Brussel Streams
status = 'http://icecast.vrtcdn.be/status-json.xsl'

LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_API_SECRET = os.getenv('LASTFM_API_SECRET')
LASTFM_USERNAME = os.getenv('LASTFM_USERNAME')
LASTFM_PASSWORD = os.getenv('LASTFM_PASSWORD')

# Scope voor de API
scope = 'playlist-modify-public'

# In[2]: Functies die periodiek worden aangeroepen
def scrobble():
    network = pylast.LastFMNetwork(
        api_key = LASTFM_API_KEY,
        api_secret = LASTFM_API_SECRET,
        username = LASTFM_USERNAME, 
        password_hash = pylast.md5(LASTFM_PASSWORD)
    )
    logger.debug(network.get_authenticated_user())

    with requests.Session() as s:
        # Haal de stream op uit de status pagina    
        r = s.get(status)
        # Controleer of je een geldige response kreeg
        if r.status_code == 200:
            json_data = r.json()
            # Loop over de verschillende streams
            jsonpath_expr = parse('$.icestats.source[?server_name =~ "Studio Brussel"].title')
            matches = jsonpath_expr.find(json_data)
            # Definieer artiest en nummer
            artiest, nummer = None, None
            # Haal de artiest en het nummer op
            for match in matches: 
                m = re.search(r'(.*?) - (.*)', match.value)
                if m: 
                    artiest = m.group(1).lower()
                    nummer = m.group(2).lower()
                    logger.debug(f'Studio Brusssel - Artiest: {artiest} - Nummer: {nummer}')
                    break
            # Controleer of een songtitel gevonden is
            if artiest is None and nummer is None:
                logger.debug('Studio Brussel - Geen songtitel gevonden')
                sys.exit()
            # Scrobble de nummer naar last.fm
            user = network.get_authenticated_user()
            current = network.get_track(artiest, nummer)
            try: 
                previous = user.get_recent_tracks(1, cacheable=False)[0].track
            except IndexError:
                network.scrobble(artiest, nummer, timestamp=time.time())
                logger.info(f'Nummer gescrobbled naar Studio Brussel: {artiest.capitalize()} - {nummer.capitalize()}')
            else:
                # Scrobble het nummer als het niet het laatste nummer is
                if current.get_correction() != previous.title:
                    network.scrobble(artiest, nummer, timestamp=time.time())
                    logger.info(f'Nummer gescrobbled naar Studio Brussel: {artiest.capitalize()} - {nummer.capitalize()}')
                else:
                    logger.debug(f'Geen nieuw nummer...')
                # Update now-playing
                network.update_now_playing(artiest, nummer)

if __name__ == '__main__':
    scrobble()
