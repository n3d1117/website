# -*- coding: utf-8 -*-

import requests
import json
import os
import re
from os.path import exists
from urllib import parse
import base64
from dotenv import load_dotenv
import feedparser
from PIL import Image
import csv
from datetime import datetime

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
TMDB_API_KEY=os.environ["TMDB_API_KEY"]
IGDB_COOKIE=os.environ["IGDB_COOKIE"]
IGDB_CLIENT_ID=os.environ["IGDB_CLIENT_ID"]
IGDB_CLIENT_SECRET=os.environ["IGDB_CLIENT_SECRET"]

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

# PLEX
r = requests.get(url=PLEX_URL)
j = r.json()
rows = j['response']['data']['rows']

## Movies
data['movies'] = []
movies = [row for row in rows if row['media_type'] == 'movie' and row['user'] == PLEX_USER]
for movie in movies[:LIMIT]:
    slug = slugify(movie['title'])
    img_url = PLEX_PROXY_IMG + movie['thumb'] + '&width=' + IMG_WIDTH
    save_images(slug, 'png', img_url)
    guids = requests.get(PLEX_METADATA_URL + str(movie['rating_key'])).json()['response']['data']['guids']
    data['movies'].append({
        'title': movie['title'],
        'guid': guids[1].split('//')[1],
        'year': movie['year'],
        'img': slug + '.png',
        'img_webp': slug + '.webp',
        'last_watch': movie['last_watch'],
        'cinema': 'false',
        'is_favorite': 'false'
    })

# Cinema
d = feedparser.parse('https://letterboxd.com/n3d1117/rss/')
lbxd_cinema_list = [item for item in d['entries'] if item['title'] == '🍿 Cinema'][0]
cinema_movies_raw = re.findall("<li>(.*?)</li>", lbxd_cinema_list['summary'])
cinema_movies = []
for movie in cinema_movies_raw:
    cinema_movies.append({ 'title': movie.split('">')[1].split('</a>')[0], 'link': movie.split('href="')[1].split('"')[0] })
for movie in cinema_movies:
    items = [item for item in d['entries'] if 'letterboxd_filmtitle' in item and item['letterboxd_filmtitle'] == movie['title']]
    if len(items) > 0:
        item = items[0]

        slug = slugify(item['letterboxd_filmtitle'])
        img_url = item['summary'].split('src="')[1].split('"')[0].replace('0-500-0-750', '0-230-0-345')
        save_images(slug, 'jpg', img_url)

        data['movies'].append({
            'title': item['letterboxd_filmtitle'],
            'guid': movie['link'],
            'year': item['letterboxd_filmyear'],
            'img': slug + '.jpg',
            'img_webp': slug + '.webp',
            'last_watch': int(datetime.strptime(item['letterboxd_watcheddate'], "%Y-%m-%d").timestamp()),
            'cinema': 'true',
            'is_favorite': 'false'
        })

# Fav Movies
top_movies = requests.get(url="https://api.themoviedb.org/3/list/7112446?api_key=" + TMDB_API_KEY)
top_movies_json = top_movies.json()
for movie in top_movies_json['items']:
    slug = slugify(movie['title'])
    img_url = 'https://image.tmdb.org/t/p/w300' + movie['poster_path']
    save_images(slug, 'jpg', img_url)

    data['movies'].append({
        'title': movie['title'],
        'guid': str(movie['id']),
        'year': movie['release_date'].split('-')[0],
        'img': slug + '.jpg',
        'img_webp': slug + '.webp',
        'last_watch': int(datetime.strptime(movie['release_date'], "%Y-%m-%d").timestamp()),
        'cinema': 'false',
        'is_favorite': 'true'
    })

# TV Shows
data['shows'] = []
tv_shows = [row for row in rows if row['media_type'] == 'episode' and row['user'] == PLEX_USER]
unique_shows = []
unique_show_titles = []
for show in tv_shows:
    if show['grandparent_title'] not in unique_show_titles:
        unique_show_titles.append(show['grandparent_title'])
        unique_shows.append(show)
for show in unique_shows[:LIMIT]:
    slug = slugify(show['grandparent_title'])
    img_url = PLEX_PROXY_IMG + show['thumb'] + '&width=' + IMG_WIDTH
    save_images(slug, 'png', img_url)
    guids = requests.get(PLEX_METADATA_URL + str(show['rating_key'])).json()['response']['data']['guids']

    data['shows'].append({
        'title': show['grandparent_title'],
        'guid': guids[1].split('//')[1],
        'ep': 'S' + str(show['parent_media_index']) + 'E' + str(show['media_index']),
        'img': slug + '.png',
        'img_webp': slug + '.webp',
        'is_favorite': 'false'
    })

# Fav TV Shows
top_shows = requests.get(url="https://api.themoviedb.org/3/list/7112447?api_key=" + TMDB_API_KEY)
top_shows_json = top_shows.json()
for show in top_shows_json['items']:
    slug = slugify(show['name'])
    img_url = 'https://image.tmdb.org/t/p/w300' + show['poster_path']
    save_images(slug, 'jpg', img_url)

    data['shows'].append({
        'title': show['name'],
        'guid': str(show['id']),
        'ep': show['first_air_date'].split('-')[0],
        'img': slug + '.jpg',
        'img_webp': slug + '.webp',
        'last_watch': int(datetime.strptime(show['first_air_date'], "%Y-%m-%d").timestamp()),
        'is_favorite': 'true'
    })

# Books
data['books'] = []
OKU_URL='https://oku.club/api/collections/'
READING='yjUNL'
READ='xSQso'
TO_READ='I0Ai5'
FAVORITES='IPgqn'
f = requests.get(OKU_URL + FAVORITES).json()
d = requests.get(OKU_URL + READ).json()
d2 = requests.get(OKU_URL + READING).json()
d3 = requests.get(OKU_URL + TO_READ).json()
for fav_book in f['books']:
    slug = fav_book['slug']
    save_images(slug, 'jpg', fav_book['thumbnail'])
    data['books'].append({
        'title': fav_book['title'],
        'author': fav_book['authors'][0]['name'],
        'url': 'https://oku.club/book/' + fav_book['slug'],
        'img': slug + '.jpg',
        'img_webp': slug + '.webp',
        'is_favorite': 'true'
    })
for book in (d3['books'] + d2['books'] + d['books'])[:LIMIT]:
    slug = book['slug']
    save_images(slug, 'jpg', book['thumbnail'])
    data['books'].append({
        'title': book['title'],
        'author': book['authors'][0]['name'],
        'url': 'https://oku.club/book/' + book['slug'],
        'img': slug + '.jpg',
        'img_webp': slug + '.webp',
        'is_favorite': 'false'
    })


# Spotify
data['spotify'] = []
SPOTIFY_TOKEN_URL='https://accounts.spotify.com/api/token'
SPOTIFY_BASE_URL='https://api.spotify.com/v1/me/top/artists'
auth_header = base64.urlsafe_b64encode((SPOTIFY_CLIENT_ID + ':' + SPOTIFY_CLIENT_SECRET).encode('ascii'))
headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic {}'.format(auth_header.decode('ascii'))}
res = requests.post(url=SPOTIFY_TOKEN_URL, data={'grant_type': 'refresh_token', 'refresh_token': SPOTIFY_REFRESH_TOKEN}, headers=headers).json()
ACCESS_TOKEN = res['access_token']
URL = SPOTIFY_BASE_URL + '?{}'.format(parse.urlencode({'time_range': 'short_term', 'limit': LIMIT}))
spotify_req = requests.get(url=URL, headers={'Authorization': 'Bearer {}'.format(ACCESS_TOKEN)})
print(spotify_req)
j = spotify_req.json()
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


# GitHub
data['github'] = []
GITHUB_URL = 'https://api.github.com/users/{}/repos?per_page=50'.format('n3d1117')
exclude = ['CrackBot']
j = requests.get(GITHUB_URL).json()
d = sorted(j, key=lambda item: item['stargazers_count'], reverse=True)
for project in [p for p in d if p['name'] not in exclude][:LIMIT]:
    data['github'].append({
        'name': project['name'],
        'html_url': project['html_url'],
        'description': project['description'],
        'language': project['language'],
        'stargazers_count': project['stargazers_count'],
        'forks_count': project['forks_count'],
    })

# Videogames
data['videogames'] = []
params = (
    ('client_id', IGDB_CLIENT_ID),
    ('client_secret', IGDB_CLIENT_SECRET),
    ('grant_type', 'client_credentials'),
)
response = requests.post('https://id.twitch.tv/oauth2/token', params=params)
access_token = response.json()['access_token']
headers = {
    'Client-ID': IGDB_CLIENT_ID,
    'Authorization': 'Bearer ' + access_token,
    'Accept': 'application/json',
}
response = requests.get('https://www.igdb.com/users/nedda/lists/games-i-play.csv', cookies={ '_server_session': IGDB_COOKIE })
reader = csv.DictReader(response.content.decode('utf-8').splitlines(), delimiter=',')
for row in reader:
    d = 'fields first_release_date, cover.url; where id = ' + row['id'] + ';'
    cover = requests.post('https://api.igdb.com/v4/games', headers=headers, data=d)
    cover_url = cover.json()[0]['cover']['url'].replace('t_thumb', 't_cover_big').replace('//', 'https://')
    slug = slugify(row['game'])
    save_images(slug, 'jpg', cover_url)
    data['videogames'].append({
        'name': row['game'],
        'url': row['url'],
        'year': datetime.utcfromtimestamp(int(cover.json()[0]['first_release_date'])).strftime('%Y'),
        'img': slug + '.jpg',
        'img_webp': slug + '.webp'
    })

# Write data
with open('data/scraper.json', 'w') as f:
    json.dump(data, f)
  