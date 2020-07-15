from pathlib import Path
from difflib import get_close_matches
from mediafile import MediaFile


def generate_artist_dict(path_txt):
    # Folder structure: Library/2005-09/Artist/Album/Track
    music_lib = Path(path_txt)
    year_groups = [x for x in music_lib.iterdir() if x.is_dir()]
    artists = {}
    for folder in year_groups:
        for artist_folder in folder.iterdir():
            if artist_folder.is_dir():
                artist_name = artist_folder.parts[-1]
                try:
                    # If dict of albums already exists append to that
                    albums = artists[artist_name]
                except KeyError:
                    # if not, start with a blank dict of albums
                    albums = {}
                for album_folder in artist_folder.iterdir():
                    if album_folder.is_dir():
                        album_name = album_folder.parts[-1]
                        # Store the album folder location in the albums dict
                        albums[album_name] = album_folder
                # Store the albums dict under the artist_name
                artists[artist_name] = albums
    return artists


def artist_lookup(artist, library_path):
    artists = generate_artist_dict(library_path)
    a = get_close_matches(artist, artists.keys(), n=3, cutoff=0.5)
    print(a)
    index = int(input("Which index matches? 0/1/2: "))
    if index < len(a):
        return artists[a[index]]


def album_selector(artist, library_path):
    try:
        albums = artist_lookup(artist, library_path)
        i = 0
        keys = []
        for a in albums.keys():
            keys.append(a)
            print(i, ": ", a)
            i += 1
        ok = int(input("Fetch metadata for album :"))
        return get_album_track(albums[keys[ok]])
    except ValueError:
        # User didn't input a correct index
        return (None, None, None), None


def get_album_track(albumpath):
    for file in albumpath.iterdir():
        if file.suffix in [".mp3", ".flac"]:

            data = get_relevant_metadata(file)
            break
    cv = albumpath / "cover.jpg"
    if cv.exists():
        img = cv.read_bytes()
    return data, img


def get_relevant_metadata(path):
    track = MediaFile(path)
    return (track.albumartist, track.album, track.year)
