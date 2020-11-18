# In[0]: Importeer de environment variables uit de .env file
import os
import dotenv import load_dotenv
load_dotenv()

# In[1: Importeer pylast en authenticeer je
import pylast

# De API key en secret maak je aan op de website:
# zie https://www.last.fm/api/account/create
LASTFM_API_KEY = os.getenv('LASTFM_API_KEY') 
LASTFM_API_SECRET = os.getenv('LASTFM_API_SECRET')

# Om te scrobblen moet je je natuurlijk ook inloggen
lastfm_username = os.getenv('LASTFM_USERNAME')
lastfm_password = pylast.md5('LASTFM_PASSWORD')

network = pylast.LastFMNetwork(
    api_key = LASTFM_API_KEY, 
    api_secret = LASTFM_API_SECRET,
    username = lastfm_username, 
    password_hash = lastfm_password
)

# In[2]: Haal de audio stream van Studio Brussel op

stream = 'http://icecast.vrtcdn.be/stubru_bruut-mid.mp3'



# Now you can use that object everywhere
artist = network.get_artist("System of a Down")
artist.shout("<3")


track = network.get_track("Iron Maiden", "The Nomad")
track.love()
track.add_tags(("awesome", "favorite"))

# Type help(pylast.LastFMNetwork) or help(pylast) in a Python interpreter
# to get more help about anything and see examples of how it works