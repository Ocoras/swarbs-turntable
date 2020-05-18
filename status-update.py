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


def update_status_soundcloud_mix(
    url, artist=None, title=None, year=None, artist_title=False
):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")

    foundtitle, foundartist = soup.find("h1").find_all("a")
    if title is None:
        title = foundtitle.string.strip()
    if artist is None:
        artist = foundartist.string.strip()
    if artist_title:
        artist, title = title.split(" - ")
    if year is None:
        year = soup.find("time").string[:4]
    filled_template = template.format(artist=artist, title=title, year=year, url=url)

    print("About to Tweet: ", filled_template)
    ok = input("Does this look right? (y/n) ")

    if ok == "y":
        img_link = soup.find("img")["src"]
        imagedata = requests.get(img_link).content
        print("Tweeting: ", filled_template)
        _update_status(filled_template, imagedata)


def _nts_template_filler(
    results, channel, artist=None, title=None, time="now", swap=False
):
    """Handle NTS Shows that don't have a title"""
    bt = results[channel - 1][time]["broadcast_title"]
    # Remove ampersand issues
    bt = bt.replace("amp;", "")

    if bt.find("(R)") > 0:
        # ToDo: Handle Re-records, and remove (R) symbol
        print("This is a re-record, fetching original time.")
        year = results[channel - 1][time]["embeds"]["details"]["broadcast"][:4]
        bt = bt.replace(" (R)", "")
    else:
        year = "LIVE"

    if bt.find("W/") > 0:
        # If a big W in there, split on that
        broadcast_title = bt.split("W/")
    else:
        # Otherwise try and split on little w
        broadcast_title = bt.split("w/")

    if len(broadcast_title) == 2:
        # A W was there somewhere - reformat to match templateamp
        if title is None:
            title = broadcast_title[0].strip()
        if artist is None:
            artist = broadcast_title[1].strip()

        if swap:
            # Assuming deep copy not needed
            s = title
            title = artist
            artist = s
    elif len(broadcast_title) == 1:
        # Single dj title, so set the title to NTS + date
        if artist is None:
            artist = broadcast_title[0].strip()
        if title is None:
            if year == "LIVE":
                t = results[channel - 1][time]["start_timestamp"]
            else:
                # Re record
                t = results[channel - 1][time]["embeds"]["details"]["broadcast"]
            yr = t[2:4]
            month = t[5:7]
            day = t[8:10]
            title = "NTS " + day + "/" + month + "/" + yr

    return template.format(
        artist=artist,
        title=title,
        year=year,
        url="https://www.nts.live/" + str(channel),
    )


def _nts_check(filled_template, prev_answers=(False, False, False)):
    print("About to Tweet: ", filled_template)
    ok = input("Does this look right? ([y]es/[n]ext/[s]wap) ")

    if ok == "y":
        return (True, False, False)
    elif ok == "n":
        return (prev_answers[0], not prev_answers[1], prev_answers[2])
    elif ok == "s":
        return (prev_answers[0], prev_answers[1], not prev_answers[2])
    else:
        return (False, False, False)


def update_status_ntslive(channel, artist=None, title=None):
    r = requests.get("https://www.nts.live/api/v2/live")
    results = r.json()["results"]
    print("Data for Channel ", results[channel - 1]["channel_name"])

    filled_template = _nts_template_filler(results, channel, artist, title)
    flags = _nts_check(filled_template)
    time = "now"
    # 0 = y, 1 = next show, 2 = swap order of show/artist
    while flags[0] or flags[1] or flags[2]:
        if flags[0]:
            img_link = results[channel - 1][time]["embeds"]["details"]["media"][
                "picture_large"
            ]
            imagedata = requests.get(img_link).content
            _update_status(filled_template, imagedata)
            flags = [False, False, False]  # Exit loop
        else:
            if flags[1]:
                time = "next"
            else:
                time = "now"
            swap = flags[2]
            filled_template = _nts_template_filler(
                results, channel, artist, title, time, swap
            )
            flags = _nts_check(filled_template, flags)


parser = argparse.ArgumentParser()
parser.add_argument("url", help="URL to grab data from. (Soundcloud/NTS)")
parser.add_argument("-a", "--artist", default=None, help="Artist override for tweet")
parser.add_argument("-t", "--title", default=None, help="Title override for tweet")
parser.add_argument(
    "-at",
    "--artist_title",
    action="store_true",
    help="Title contains ARTIST - TITLE already",
)
parser.add_argument("-y", "--year", default=None, help="Year override for tweet")
parser.add_argument("-n", "--nts", default=1, help="NTS Channel (1/2)")
args = parser.parse_args()

if "soundcloud" in args.url:
    print("Source: Soundcloud")
    update_status_soundcloud_mix(
        args.url, args.artist, args.title, args.year, args.artist_title
    )
elif "nts.live" in args.url:
    print("Source: NTS Live")
    update_status_ntslive(int(args.nts), args.artist, args.title)
