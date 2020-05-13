from twitter import *
import requests
from bs4 import BeautifulSoup
import argparse
import yaml

with open("swarbs-turntable-login.yaml", "r") as stream:
    try:
        config = yaml.safe_load(stream)
        auth = OAuth(
            config["access_token"],
            config["access_token_secret"],
            config["api_key"],
            config["api_secret_key"],
        )
    except yaml.YAMLError as exc:
        print("Could not load configuration file")
        raise
    except KeyError:
        print("Could not load OAuth correctly")
        raise

try:
    template = config["template"]
except KeyError:
    print("Using Default Config")
    template = "{artist} - {title} ({year}) \n{url}"


def _update_status(filled_template, imagedata):
    t = Twitter(auth=auth)
    t_upload = Twitter(domain="upload.twitter.com", auth=auth)
    img_id = t_upload.media.upload(media=imagedata)["media_id_string"]
    t.statuses.update(
        status=filled_template, media_ids=img_id,
    )


def update_status_soundcloud_mix(url, auth, artist=None, title=None, debug=False):
    # template =

    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")

    foundtitle, foundartist = soup.find("h1").find_all("a")
    if title is None:
        title = foundtitle.string
    if artist is None:
        artist = foundartist.string

    year = soup.find("time").string[:4]
    img_link = soup.find("img")["src"]

    imagedata = requests.get(img_link).content
    filled_template = template.format(artist=artist, title=title, year=year, url=url)

    if debug:
        print(filled_template)
    else:
        _update_status(filled_template, imagedata)


parser = argparse.ArgumentParser()
parser.add_argument("url", help="url for Soundcloud mix")
parser.add_argument("-a", "--artist", default=None, help="Artist override for tweet")
parser.add_argument("-t", "--title", default=None, help="Title override for tweet")
parser.add_argument("-d", "--debug", action="store_true", help="Debug - Don't print")
args = parser.parse_args()

if "soundcloud" in args.url:
    print("Soundcloud Link Selected")
    update_status_soundcloud_mix(args.url, auth, args.artist, args.title, args.debug)
