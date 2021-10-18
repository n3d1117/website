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

load_dotenv()

PLEX_URL = os.environ["PLEX_URL"]
PLEX_USER = os.environ["PLEX_USER"]
PLEX_PROXY_IMG = os.environ["PLEX_PROXY_IMG"]
SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
SPOTIFY_REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]

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

def save_images(slug, ext, url):
    if not exists('static/img/' + slug + '.' + ext):
        img_data = requests.get(url).content
        with open('static/img/' + slug + '.' + ext, 'wb') as f:
            f.write(img_data)
        os.system('cd static/img && cwebp ' + slug + '.' + ext + ' -o ' + slug + '.webp')

# PLEX
r = requests.get(url=PLEX_URL)
j = r.json()
rows = j['response']['data']['rows']

## Movies
data['movies'] = []
movies = [row for row in rows if row['media_type'] == 'movie' and row['user'] == PLEX_USER]
for movie in movies[:20]:
    slug = slugify(movie['title'])
    img_url = PLEX_PROXY_IMG + movie['thumb'] + '&width=' + IMG_WIDTH
    save_images(slug, 'png', img_url)
    data['movies'].append({
        'title': movie['title'],
        'guid': movie['guid'].split('//')[1].split('?')[0],
        'year': movie['year'],
        'img': slug + '.png',
        'img_webp': slug + '.webp',
        'last_watch': movie['last_watch'],
        'cinema': 'false'
    })

# Cinema
d = feedparser.parse('https://letterboxd.com/n3d1117/rss/')
lbxd_cinema_list = [item for item in d['entries'] if item['title'] == '🍿 Cinema'][0]
cinema_movies_raw = re.findall("<li>(.*?)</li>", lbxd_cinema_list['summary'])
cinema_movies = [movie.split('">')[1].split('</a>')[0] for movie in cinema_movies_raw]
for title in cinema_movies:
    items = [item for item in d['entries'] if 'letterboxd_filmtitle' in item and item['letterboxd_filmtitle'] == title]
    if len(items) > 0:
        item = items[0]

        slug = slugify(item['letterboxd_filmtitle'])
        img_url = item['summary'].split('src="')[1].split('"')[0].replace('0-500-0-750', '0-230-0-345')
        save_images(slug, 'jpg', img_url)

        data['movies'].append({
            'title': item['letterboxd_filmtitle'],
            'guid': item['link'].replace('/n3d1117', ''),
            'year': item['letterboxd_filmyear'],
            'img': slug + '.jpg',
            'img_webp': slug + '.webp',
            'last_watch': int(datetime.datetime.strptime(item['letterboxd_watcheddate'], "%Y-%m-%d").timestamp()),
            'cinema': 'true'
        })


## TV Shows
data['shows'] = []
tv_shows = [row for row in rows if row['media_type'] == 'episode' and row['user'] == PLEX_USER]
unique_shows = []
unique_show_titles = []
for show in tv_shows:
    if show['grandparent_title'] not in unique_show_titles:
        unique_show_titles.append(show['grandparent_title'])
        unique_shows.append(show)
for show in unique_shows[:20]:
    slug = slugify(show['grandparent_title'])
    img_url = PLEX_PROXY_IMG + show['thumb'] + '&width=' + IMG_WIDTH
    save_images(slug, 'png', img_url)

    data['shows'].append({
        'title': show['grandparent_title'],
        'guid': show['guid'].split('//')[1].split('/')[0],
        'ep': 'S' + str(show['parent_media_index']) + 'E' + str(show['media_index']),
        'img': slug + '.png',
        'img_webp': slug + '.webp'
    })


# Books
data['books'] = []
OKU_URL='https://oku.club/api/collections/'
READING='yjUNL'
READ='xSQso'
TO_READ='I0Ai5'
d = requests.get(OKU_URL + READ).json()
d2 = requests.get(OKU_URL + READING).json()
d3 = requests.get(OKU_URL + TO_READ).json()
for book in (d3['books'] + d2['books'] + d['books'])[:20]:
    slug = book['slug']
    save_images(slug, 'jpg', book['thumbnail'])
    data['books'].append({
        'title': book['title'],
        'author': book['authors'][0]['name'],
        'url': 'https://oku.club/book/' + book['slug'],
        'img': slug + '.jpg',
        'img_webp': slug + '.webp'
    })


# Spotify
data['spotify'] = []
SPOTIFY_TOKEN_URL='https://accounts.spotify.com/api/token'
SPOTIFY_BASE_URL='https://api.spotify.com/v1/me/top/artists'
auth_header = base64.urlsafe_b64encode((SPOTIFY_CLIENT_ID + ':' + SPOTIFY_CLIENT_SECRET).encode('ascii'))
headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic {}'.format(auth_header.decode('ascii'))}
res = requests.post(url=SPOTIFY_TOKEN_URL, data={'grant_type': 'refresh_token', 'refresh_token': SPOTIFY_REFRESH_TOKEN}, headers=headers).json()
ACCESS_TOKEN = res['access_token']
URL = SPOTIFY_BASE_URL + '?{}'.format(parse.urlencode({'time_range': 'short_term', 'limit': '20'}))
j = requests.get(url=URL, headers={'Authorization': 'Bearer {}'.format(ACCESS_TOKEN)}).json()
for item in j['items']:
    slug = slugify(item['name'])
    save_images(slug, 'jpeg', item['images'][1]['url'])
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
  