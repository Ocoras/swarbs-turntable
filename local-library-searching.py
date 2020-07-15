from pathlib import Path
from difflib import get_close_matches

# Folder structure: Library/2005-09/Artist/Album/Track
# Root of library
music_lib = Path("/home/david/Music/Library")


year_groups = [x for x in music_lib.iterdir() if x.is_dir()]
artists = {}
for folder in year_groups:
    for artist_folder in folder.iterdir():
        artist_name = artist_folder.parts[-1]
        try:
            # If dict of albums already exists append to that
            albums = artists[artist_name]
        except KeyError:
            # if not, start with a blank dict of albums
            albums = {}

        for album_folder in artist_folder.iterdir():
            album_name = album_folder.parts[-1]
            # Store the album folder location in the albums dict
            albums[album_name] = album_folder
        # Store the albums dict under the artist_name
        artists[artist_name] = albums


def artist_lookup(artist):
    a = get_close_matches(artist, artists.keys(), n=3, cutoff=0.5)
    print(a)
    ok = input("Which index matches? 0/1/2: ")
    try:
        index = int(ok)
        if index < len(a):
            return artists[a[index]]
    except ValueError:
        # Not an integer
        pass
