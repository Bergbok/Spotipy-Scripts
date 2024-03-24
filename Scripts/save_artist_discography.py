from io import BytesIO
from PIL import Image
from retrying import retry
from spotipy.oauth2 import SpotifyOAuth
from urllib.parse import urlparse
import argparse
import base64
import os
import re
import requests
import spotipy

scope = " ugc-image-upload playlist-modify-public"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

def get_artist_name(artist_input):
    parsed_url = urlparse(artist_input)
    if parsed_url.netloc == 'open.spotify.com':
        path_parts = parsed_url.path.split('/')
        if len(path_parts) > 2 and path_parts[1] == 'artist':
            artist_id = path_parts[2]
            artist = sp.artist(artist_id)
            return artist['name']
    return artist_input

def get_artist_id(artist_input, args):
    parsed_url = urlparse(artist_input)
    if parsed_url.netloc == 'open.spotify.com':
        path_parts = parsed_url.path.split('/')
        if len(path_parts) > 2 and path_parts[1] == 'artist':
            return path_parts[2]
    else:
        results = sp.search(q='artist:' + artist_input, type='artist')
        items = results['artists']['items']
        if len(items) == 0:
            print(f"No artist found with name '{artist_input}'")
            main(args)
        return items[0]['id']

def get_albums(artist_id, action, limit, offset):
    album_type = ['single', 'album', 'compilation'][int(action) - 1]
    return sp.artist_albums(artist_id, album_type=album_type, limit=limit, offset=offset)

def create_playlist(album_or_tracks, verbose, playlist_name='undefined'):
    if isinstance(album_or_tracks, dict):
        album = album_or_tracks
        album_name = re.sub(r'\(.*Soundtrack.*\)', '', album['name'], flags=re.IGNORECASE)
        album_images = album['images']
        album_year = album['release_date']
        track_ids = [track['id'] for track in sp.album(album['id'])['tracks']['items']]
    else:
        album_name = playlist_name
        album_images = [] 
        album_year = ''
        track_ids = album_or_tracks

    playlist_name = album_name
    playlist_description = f"{album_year}"

    encoded_playlist_image_data = None

    if album_images:
        playlist_image_url = album_images[0]['url']
        playlist_image_data = requests.get(playlist_image_url).content
        encoded_playlist_image_data = base64.b64encode(playlist_image_data)

        jpeg_quality=100
        while len(encoded_playlist_image_data) > 256000:
            playlist_image = Image.open(BytesIO(playlist_image_data))
            playlist_image = playlist_image.convert('RGB')
            playlist_image.save('temp.jpg', format='JPEG', quality=jpeg_quality)
            with open('temp.jpg', 'rb') as image_data:
                encoded_playlist_image_data = base64.b64encode(image_data.read())
            os.remove('temp.jpg')
            jpeg_quality -= 5

        if verbose:
            print(f"Used JPEG quality of: {jpeg_quality}% for {playlist_name} | Size: ", len(encoded_playlist_image_data))

    playlist = sp.user_playlist_create(user=sp.current_user()['id'], name=playlist_name, public=True, description=playlist_description)

    sp.playlist_add_items(playlist['id'], track_ids)

    if encoded_playlist_image_data:
        @retry(stop_max_attempt_number=3, wait_fixed=2000)
        def upload_cover_image(playlist_id, image_data):
            sp.playlist_upload_cover_image(playlist_id, image_data)

        try:
            upload_cover_image(playlist['id'], encoded_playlist_image_data)
        except:
            print(f"Failed to upload cover image for playlist '{playlist_name}'")

    print(f"Playlist '{playlist_name}' created.")

def main(args):
    artist_input = input("Enter an artist name or URL: ")
    artist_name = get_artist_name(artist_input)
    artist_id = get_artist_id(artist_input, args)

    action = input("1. Save singles\n2. Save albums\n3. Save compilations\nEnter an action: ")

    if args.verbose:
        if action == '1':
            one_or_many = input("\n1. Save singles to one playlist\n2. Save singles many playlists\nEnter an action: ")
        offset = int(input("\nEnter an offset (default: 0): ") or 0)
        limit = int(input("Enter a limit (default: 50): ") or 50)
    else:
        offset = 0
        limit = 50
        one_or_many = '2'

    albums = get_albums(artist_id, action, limit, offset)

    if one_or_many == '1':
        track_ids = []
        for album in albums['items']:
            track_ids += [track['id'] for track in sp.album(album['id'])['tracks']['items']]
        create_playlist(track_ids, args.verbose, artist_name + ' Singles')
    else:
        for album in albums['items']:
            create_playlist(album, args.verbose)
        
    main(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Save artist discographies as Spotify playlists.')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose mode (asks for limit/offset and prints more info)')

    args = parser.parse_args()
    main(args)