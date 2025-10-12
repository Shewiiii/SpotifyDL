# SpotifyDL

A rudimentary Spotify Downloader based on Librespot.

## Feature
Download tracks from Spotify in OGG 320kbps with metadata.

## Usage
Requirements: Python 3.10 or newer, Spotify Premium.
- Copy the repo and install the dependencies (use a venv as needed). 
```bash
pip install -r requirements.txt
```
- Run `.main.py` and follow the instructions.
```bash
python main.py
```
If you struggle to generate the `credentials.json` file (eg. you are running the script on a server), run the script locally, then export the file in the root folder.


## To do
- Add FLAC support (bugged right now)
- Organize albums and playlists
- Add auto-retry on key fetch error
