# Spotify Playlist Creator

Spotify app to create a playlist from MP3 filenames.

## Prerequisites

You need a spotify app client ID and client secret. You can get these by
creating an app in the [Spotify Developer
Dashboard](https://developer.spotify.com/dashboard/).

Put these credentials in `~/.spotify_credentials`, the file should look like this:

```text
SPOTIPY_CLIENT_ID=abc
SPOTIPY_CLIENT_SECRET=123
```

Recommended: use <https://github.com/astral-sh/uv> to manage dependencies and
run the script. Otherwise it's your responsibility to install the dependencies.
A virtualenv is strongly recommended.

## Usage

```shell
uv run main.py --dir some/dir/ectory --playlist "My playlist name"
```
