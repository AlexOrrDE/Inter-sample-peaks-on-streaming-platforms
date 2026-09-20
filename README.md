# Inter-sample-peaks-on-streaming-platforms

## Installation

Install requirements:
```
pip install requirements.txt
```

The following should be installed (macOS):

- [BlackHole loopback device](https://github.com/ExistentialAudio/BlackHole)
- [Spotify application](https://open.spotify.com/download)
- [Tidal application](https://offer.tidal.com/download?lang=en)

Spotify and Tidal subscriptions are also required to run the code as intended. There are free trials for both of these.

The EBU validation tests should be downloaded and placed in the `ebu_tests/` directory:

- https://tech.ebu.ch/publications/ebu_loudness_test_set

## Audio device setup

Set BlackHole as your default output device. When validating true peak tests, set it to 48 kHz. When capturing streaming platform audio, set it to 44.1 kHz.

## Validating the toolchain

To check the toolchain against the LUFS tests, from the project parent directory run:

```
python -m measurement.lufs_validator
```

To check the toolchain against the True Peak tests, from the project parent directory run:

```
python -m measurement.tp_validator
```

Then follow the instructions in the terminal, making sure to start playing the test file after recording has started. I used VLC media player for this (check audio normalisation is not on).

## API keys

To run the Spotify capture, a [Spotify API key](https://developer.spotify.com/documentation/web-api) is required.

To build a corpus of randomly sampled tracks, a [Last.fm API key](https://www.last.fm/api/account/create) is required.

In a `.env` file in the root folder, set the following with your API settings:

```
SPOTIPY_CLIENT_ID=
SPOTIPY_CLIENT_SECRET=
SPOTIPY_REDIRECT_URI=
LASTFM_API_KEY=
LASTFM_API_SECRET=
```

## Building a corpus

To build a corpus, run:

```
python -m corpus.build_corpus
```

This will only create files for genres that do not already have an associated `.csv` in `cadidates/`. To use these for capture, you must add a duration in seconds value (`duration_s`) for them manually, using Tidal durations of these tracks as reference.

## Capturing audio

To initiate Tidal capture, run:

```
python main.py tidal --quality {normal,high} --normalisation {on,off} --track-list candidates/{genre}.csv
```

Selecting only one option for each of the arguments. Then follow the instructions in the terminal and play from the Tidal app. Each track's capture must be initiated manually in this case.

To initiate Spotify capture, run:

```
python main.py tidal --quality {low,normal,high,very_high} --normalisation {on,off} --genre {genre} --n-tracks {int}
```

Selecting only one option for each of the arguments. Then play songs from the Spotify app. Capture will continue for as many tracks as specified.

## Playlists used for project capture

**Jazz**
- https://tidal.com/playlist/405c52ba-99fe-466e-bfe4-5b525086b299
- https://open.spotify.com/playlist/6qON9qJKosHIUVPRXeeHOq?si=d12d8f1fd4ac4903

**Pop**
- https://tidal.com/playlist/eaaf4bc5-0dba-404c-94f0-aa24bdbf13aa
- https://open.spotify.com/playlist/1bMTeX9brXTvXZRciEoJIv?si=727a92515c89451b&pt=e0a29d2fcd3aa7fb580a0468b0e353ce

**Electronic**
- https://tidal.com/playlist/8dbdf125-e1d0-4dc2-8bab-ec99f67a1737
- https://open.spotify.com/playlist/0UJYeKDqJEOxAH3sgCGcou?si=87667794df8d4a7c&pt=a0abfaa9d5690ca9257ced185f35eb26

**Rock**
- https://tidal.com/playlist/573ad5ab-adc6-4800-bf2e-956476438e04
- https://open.spotify.com/playlist/2uizSw884s1eQvmFsRZoyh?si=d86788e2262d43d1&pt=cfabc1fada6e6564c6ca1a24a2d72104

**Hip-hop**
- https://tidal.com/playlist/ea84ed6d-73e5-477e-9112-6be97d0ab9ff
- https://open.spotify.com/playlist/3G5EsF5ZOubwX8XSEOdeVM?si=258489638bf44390&pt=e0b864e1699b71330ccb13754ee992e8


## Analysis 
Analysis is done in analyse.ipynb with corpus.db uploaded as a temporary file in Google Colab.