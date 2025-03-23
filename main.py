import os
import sys
import argparse
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def tty_input(prompt=""):
    with open("/dev/tty", "r") as tty:
        print(prompt, end="", flush=True)
        return tty.readline().rstrip("\n")


def load_credentials():
    """Loads Spotify credentials from ~/.spotify_credentials."""
    credentials_path = os.path.expanduser("~/.spotify_credentials")
    credentials = {}
    if os.path.exists(credentials_path):
        with open(credentials_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    credentials[key.strip()] = value.strip()
    return credentials.get("SPOTIPY_CLIENT_ID"), credentials.get(
        "SPOTIPY_CLIENT_SECRET"
    )


def parse_filename(filename):
    """Extracts artist and song title from the given filename."""
    # Remove .mp3 extension and strip spaces
    base_name = os.path.splitext(filename.strip())[0]
    parts = base_name.split("_-_")
    if len(parts) == 2:
        artist, title = parts
        return artist.replace("_", " "), title.replace("_", " ")
    return None, None


def search_track(sp, artist, title):
    """Searches Spotify for a track and returns its URI."""
    query = f"artist:{artist} track:{title}"
    results = sp.search(q=query, type="track", limit=1)
    tracks = results.get("tracks", {}).get("items", [])
    if tracks:
        print(
            f"✅ Exact match found: {tracks[0]['artists'][0]['name']} - {tracks[0]['name']}"
        )
        return tracks[0]["uri"]
    else:
        print(f"❌ No match for '{title}' by '{artist}'")
        return None


def find_fuzzy_matches(sp, artist, title):
    """Finds fuzzy matches for a given artist and title."""
    query = f"{artist} {title}"
    results = sp.search(q=query, type="track", limit=5)
    tracks = results.get("tracks", {}).get("items", [])
    return [
        (track["uri"], track["name"], track["artists"][0]["name"]) for track in tracks
    ]


def create_playlist(sp, user_id, playlist_name):
    """Creates a new Spotify playlist and returns its ID."""
    playlist = sp.user_playlist_create(user_id, playlist_name, public=False)
    return playlist["id"]


def add_tracks_to_playlist(sp, playlist_id, track_uris):
    """Adds tracks to a playlist."""
    if track_uris:
        sp.playlist_add_items(playlist_id, track_uris)


def main():
    parser = argparse.ArgumentParser(
        description="Create a Spotify playlist from a list of songs."
    )
    parser.add_argument(
        "--playlist", required=True, help="Name of the Spotify playlist to create."
    )
    args = parser.parse_args()

    SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET = load_credentials()
    SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"

    if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
        print(
            "Error: Missing Spotify credentials. Ensure ~/.spotify_credentials is correctly set."
        )
        sys.exit(1)

    scope = "playlist-modify-private"
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope=scope,
        )
    )

    user_id = sp.current_user()["id"]
    playlist_name = args.playlist
    playlist_id = create_playlist(sp, user_id, playlist_name)

    track_uris = []
    unparsed_files = []
    unmatched_songs = []

    for line in sys.stdin:
        filename = line.strip()
        artist, title = parse_filename(filename)
        if artist and title:
            track_uri = search_track(sp, artist, title)
            if track_uri:
                track_uris.append(track_uri)
            else:
                unmatched_songs.append((filename, artist, title))
        else:
            unparsed_files.append(filename)

    add_tracks_to_playlist(sp, playlist_id, track_uris)
    print(f"Playlist created: {playlist_name}")
    track_uris = []

    still_unmatched_songs = []
    if unmatched_songs:
        for filename, artist, title in unmatched_songs:
            print(f"No exact match for {filename}. Possible matches:")
            fuzzy_matches = find_fuzzy_matches(sp, artist, title)
            for idx, (_, name, artist) in enumerate(fuzzy_matches, 1):
                print(f"{idx}. {artist} - {name}")
            choice = tty_input("Select a match number, or press Enter to skip: ")
            if choice.isdigit() and 1 <= int(choice) <= len(fuzzy_matches):
                track_uris.append(fuzzy_matches[int(choice) - 1][0])
            else:
                still_unmatched_songs.append((filename, artist, title))

    add_tracks_to_playlist(sp, playlist_id, track_uris)

    if unparsed_files:
        print("Could not parse filenames:")
        for file in unparsed_files:
            print(file)

    if still_unmatched_songs:
        print("Songs not processed after fuzzy search:")
        for filename, _, _ in unmatched_songs:
            print(filename)


if __name__ == "__main__":
    main()
