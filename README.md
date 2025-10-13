# SpotifyDL

A rudimentary Spotify Downloader based on Librespot.

## Feature
Download tracks from Spotify in OGG 320kbps with metadata.

## Usage
Requirements: Python 3.10 or newer, Spotify Premium, a [Spotify app](https://developer.spotify.com/dashboard) for API calls.
- Copy the repo and install the dependencies (use a venv as needed). 
```bash
pip install -r requirements.txt
```
- Run `.main.py` and follow the instructions.
```bash
python main.py
```
If you struggle to generate the `credentials.json` file (eg. you are running the script on a server), run the script locally, connect to the "librespot" device from a Spotify client on the same computer, then export the file to the root folder of SpotifyDL.  

Supported query: song title, Spotify URL (track, album or **public** playlist).

> [!WARNING]  
> Spotify's rate limiting is pretty strict. You might want to wait a bit after downloading about ten songs in a raw.


## To do
- Add FLAC support (bugged right now)
- Merge Spotify APIs (so the script only needs Librespot instead of the Spotipy wrapper)