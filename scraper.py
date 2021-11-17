# -*- coding: utf-8 -*-

import requests
import json
import os
import re
from os.path import exists
from urllib import parse
import base64
from dotenv import load_dotenv
import datetime
import feedparser
from PIL import Image
import csv

print('Scraping sources...')

load_dotenv()

if not os.path.exists('static/img'):
    os.mkdir('static/img')

PLEX_URL = os.environ["PLEX_URL"]
PLEX_METADATA_URL = os.environ["PLEX_METADATA_URL"]
PLEX_USER = os.environ["PLEX_USER"]
PLEX_PROXY_IMG = os.environ["PLEX_PROXY_IMG"]
SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
SPOTIFY_REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]
TMDB_API_KEY = os.environ["TMDB_API_KEY"]
IGDB_COOKIE = os.environ["IGDB_COOKIE"]
IGDB_CLIENT_ID = os.environ["IGDB_CLIENT_ID"]
IGDB_CLIENT_SECRET = os.environ["IGDB_CLIENT_SECRET"]

LIMIT = 20
IMG_WIDTH = '350'

data = {}

non_url_safe = ['"', '#', '$', '%', '&', '+', ',', '/', ':', ';', '=',
                '?', '@', '[', '\\', ']', '^', '`', '{', '|', '}', '~', "'", "(", ")"]
non_url_safe_regex = re.compile(r'[{}]'.format(
    ''.join(re.escape(x) for x in non_url_safe)))

def slugify(text):
    text = non_url_safe_regex.sub('', text).strip()
    text = u'_'.join(re.split(r'\s+', text))
    return text.lower()

def save_images(slug, ext, url, square=False):
    if not exists('static/img/' + slug + '.' + ext):
        img_data = requests.get(url).content
        with open('static/img/' + slug + '.' + ext, 'wb') as f:
            f.write(img_data)
        if square:
            with open('static/img/' + slug + '.' + ext, 'r+b') as f:
                with Image.open(f) as image:
                    square_image(image, 320).save('static/img/' + slug + '.' + ext, image.format)
        os.system('cd static/img && cwebp ' + slug + '.' + ext + ' -o ' + slug + '.webp')

# https://stackoverflow.com/a/65977483/6022481
def square_image(image: Image, length: int) -> Image:
    if image.size[0] == image.size[1]:
        return image
    elif image.size[0] < image.size[1]:
        resized_image = image.resize((length, int(image.size[1] * (length / image.size[0]))))
        required_loss = (resized_image.size[1] - length)
        resized_image = resized_image.crop(
            box=(0, required_loss / 2, length, resized_image.size[1] - required_loss / 2))
        return resized_image
    else:
        resized_image = image.resize((int(image.size[0] * (length / image.size[1])), length))
        required_loss = resized_image.size[0] - length
        resized_image = resized_image.crop(
            box=(required_loss / 2, 0, resized_image.size[0] - required_loss / 2, length))
        return resized_image

# Spotify
data['spotify'] = []
SPOTIFY_TOKEN_URL='https://accounts.spotify.com/api/token'
SPOTIFY_BASE_URL='https://api.spotify.com/v1/me/top/artists'
auth_header = base64.urlsafe_b64encode((SPOTIFY_CLIENT_ID + ':' + SPOTIFY_CLIENT_SECRET).encode('ascii'))
headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic {}'.format(auth_header.decode('ascii'))}
res = requests.post(url=SPOTIFY_TOKEN_URL, data={'grant_type': 'refresh_token', 'refresh_token': SPOTIFY_REFRESH_TOKEN}, headers=headers).json()
ACCESS_TOKEN = res['access_token']
URL = SPOTIFY_BASE_URL + '?{}'.format(parse.urlencode({'time_range': 'short_term', 'limit': LIMIT}))
j = requests.get(url=URL, headers={'Authorization': 'Bearer {}'.format(ACCESS_TOKEN)}).json()
for item in j['items']:
    slug = slugify(item['name'])
    save_images(slug, 'jpeg', item['images'][1]['url'], square=True)
    data['spotify'].append({
        'name': item['name'],
        'url': item['external_urls']['spotify'],
        'followers': str(item['followers']['total']),
        'img': slug + '.jpeg',
        'img_webp': slug + '.webp'
    })

# Write data
with open('data/scraper.json', 'w') as f:
    json.dump(data, f)
  