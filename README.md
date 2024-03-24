# Spotipy Scripts

<p align="center">
  <img src="https://avatars.githubusercontent.com/u/117038620?s=200&v=4" width="125px"/></img>
</p>
<p align="center">
  <i>Made using <a href="https://github.com/spotipy-dev/spotipy">Spotipy</a></i>
</p>

## save_artist_discography.py

Useful if you prefer to save albums and whatnot in playlist format due to the improved level of organization that comes with it.

```
options:
  -h, --help     show this help message and exit
  -v, --verbose  enable verbose mode (asks for limit/offset and prints more info)
```

### Setup

1. Set up Spotify Developer Application [here](https://developer.spotify.com/dashboard)
1. Create SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET and SPOTIPY_REDIRECT_URI environment variables that match your app
2. (Optional) Create and activate a Python venv
3. Install dependencies:
    - `pip install spotipy`
    - `pip install pillow`
    - `pip install retrying`