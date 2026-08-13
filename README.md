# Audio Library Browser

A lightweight Windows-friendly audio browser for large game-audio collections.

## Features

- Recursively scans a whole audio collection
- Search by filename/path
- Automatic top-level folder categories
- Instant preview
- Previous / next playback
- Keyboard navigation
- Volume control
- Supports WAV, MP3, OGG, FLAC, AAC, M4A and WMA (actual codec support depends on pygame/SDL)

## Run

1. Install Python 3.11+.
2. Open a terminal in this folder.
3. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

4. Start:

```bash
python main.py
```

5. Click **Choose Library** and select the folder containing your audio collection.

## Controls

- Double-click a sound: play
- Space: play
- Enter: play
- Up / Down: previous / next
- Esc: stop

## Future upgrades

The app is intentionally kept simple so it is easy to extend with:

- waveform previews
- favorites
- tags
- recently played
- drag-and-drop into Godot/Unity
- file duration
- playback speed
- global hotkeys
- audio normalization
