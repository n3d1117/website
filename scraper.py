# -*- coding: utf-8 -*-
import concurrent
import json
from concurrent.futures import ThreadPoolExecutor

import requests
import os
import re
import subprocess
import threading
import time
import traceback
from os.path import exists
from urllib import parse
import base64
from dotenv import load_dotenv
import feedparser
from PIL import Image
from datetime import datetime

from storage3.utils import StorageException
from supabase import create_client, Client, ClientOptions
from unidecode import unidecode

HTTP_TIMEOUT = 30
STORAGE_TIMEOUT = 120
UPLOAD_RETRIES = 3
UPLOAD_CONCURRENCY = 3
UPLOAD_SEMAPHORE = threading.BoundedSemaphore(UPLOAD_CONCURRENCY)
BUCKET_FILES_LOCK = threading.Lock()


def main():
    data = {'movies': [], 'shows': [], 'books': [], 'spotify': [], 'github': [], 'videogames': []}
    content_limit = 50
    img_width = 350
    try:
        bucket = get_supabase_bucket()
        bucket_list = {f['name'] for f in bucket.list(options={'limit': 999999})}
        create_img_folder()

        print('Scraping sources...')

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(scrape_all_movies, data, 999, img_width, bucket, bucket_list),
                executor.submit(scrape_all_tv_shows, data, 999, img_width, bucket, bucket_list),
                executor.submit(scrape_books, data, content_limit, bucket, bucket_list),
                executor.submit(scrape_spotify, data, content_limit, bucket, bucket_list),
                executor.submit(scrape_github, data, content_limit),
                executor.submit(scrape_videogames, data, bucket, bucket_list)
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    log_warning(f'Source task failed: {exc}')
    except Exception as exc:
        log_warning(f'Scraper setup failed: {exc}')

    write_data(data)


def scrape_all_movies(data, content_limit, img_width, bucket, bucket_list):
    scrape_movies(data, content_limit, img_width, bucket, bucket_list)
    scrape_cinema_movies(data, bucket, bucket_list)
    scrape_fav_movies(data, bucket, bucket_list)


def scrape_all_tv_shows(data, content_limit, img_width, bucket, bucket_list):
    scrape_tv_shows(data, content_limit, img_width, bucket, bucket_list)
    scrape_fav_tv_shows(data, bucket, bucket_list)


def scrape_movies(data, content_limit, img_width, bucket, bucket_list):
    plex_url: str = os.environ.get("PLEX_URL")
    plex_metadata_url: str = os.environ.get("PLEX_METADATA_URL")
    plex_user: str = os.environ.get("PLEX_USER")
    plex_proxy_img: str = os.environ.get("PLEX_PROXY_IMG")

    plex_json = requests.get(url=plex_url).json()
    rows = plex_json['response']['data']['rows']

    movies = [row for row in rows if row['media_type'] == 'movie' and row['user'] == plex_user]
    for movie in movies[:content_limit]:
        j = requests.get(plex_metadata_url + str(movie['rating_key'])).json()
        if 'guids' in j['response']['data']:
            guid = j['response']['data']['guids'][1].split('//')[1]
            if not any(m['guid'] == guid for m in data['movies']):
                slug = slugify(movie['title'])
                img_url = plex_proxy_img + movie['thumb'] + '&width=' + str(img_width)
                save_images(bucket, bucket_list, 'movie', slug, 'png', img_url)
                data['movies'].append({
                    'title': movie['title'],
                    'guid': guid,
                    'year': movie['year'],
                    'img': f'movie_{slug}.png',
                    'img_webp': f'movie_{slug}.webp' if exists(
                        f'static/img/movie_{slug}.webp') else f'movie_{slug}.png',
                    'last_watch': movie['last_watch'],
                    'cinema': False,
                    'is_favorite': False
                })
        else:
            log_warning(f'Error fetching metadata: {j}')


def scrape_cinema_movies(data, bucket, bucket_list):
    d = feedparser.parse('https://letterboxd.com/n3d1117/rss/')
    for lbx_list in ['🍿 Cinema', '🍿 Cinema 2', '🍿 Cinema 3']:  # due to rss limit. waiting for letterboxd apis to be available...
        lbxd_cinema_lists = [item for item in d['entries'] if item['title'] == lbx_list]
        if len(lbxd_cinema_lists) > 0:
            lbxd_cinema_list = lbxd_cinema_lists[0]
            cinema_movies_raw = re.findall("<li>(.*?)</li>", lbxd_cinema_list['summary'])
            cinema_movies = []
            for movie in cinema_movies_raw:
                cinema_movies.append(
                    {'title': movie.split('">')[1].split('</a>')[0], 'link': movie.split('href="')[1].split('"')[0]})
            for movie in cinema_movies:
                items = [item for item in d['entries'] if
                         'letterboxd_filmtitle' in item and item['letterboxd_filmtitle'] == movie['title']]
                if len(items) > 0:
                    item = items[0]

                    if not any(m['guid'] == movie['link'] for m in data['movies']):
                        slug = slugify(item['letterboxd_filmtitle'])
                        img_url = item['summary'].split('src="')[1].split('"')[0].replace('0-500-0-750', '0-230-0-345')
                        save_images(bucket, bucket_list, 'movie', slug, 'jpg', img_url)
                        data['movies'].append({
                            'title': item['letterboxd_filmtitle'],
                            'guid': movie['link'],
                            'year': int(item['letterboxd_filmyear']),
                            'img': f'movie_{slug}.jpg',
                            'img_webp': f'movie_{slug}.webp' if exists(
                                f'static/img/movie_{slug}.webp') else f'movie_{slug}.jpg',
                            'last_watch': int(
                                datetime.strptime(item['letterboxd_watcheddate'], "%Y-%m-%d").timestamp()),
                            'cinema': True,
                            'is_favorite': False
                        })


def scrape_fav_movies(data, bucket, bucket_list):
    tmdb_api_key: str = os.environ.get("TMDB_API_KEY")
    top_movies = requests.get(url="https://api.themoviedb.org/3/list/7112446?api_key=" + tmdb_api_key)
    top_movies_json = top_movies.json()
    for movie in top_movies_json['items']:
        slug = slugify(movie['title'])
        img_url = 'https://image.tmdb.org/t/p/w300' + movie['poster_path']
        save_images(bucket, bucket_list, 'movie', slug, 'jpg', img_url)
        data['movies'].append({
            'title': movie['title'],
            'guid': str(movie['id']),
            'year': int(movie['release_date'].split('-')[0]),
            'img': f'movie_{slug}.jpg',
            'img_webp': f'movie_{slug}.webp' if exists(f'static/img/movie_{slug}.webp') else f'movie_{slug}.jpg',
            'last_watch': int(datetime.strptime(movie['release_date'], "%Y-%m-%d").timestamp()),
            'cinema': False,
            'is_favorite': True
        })


def scrape_tv_shows(data, content_limit, img_width, bucket, bucket_list):
    plex_url: str = os.environ.get("PLEX_URL")
    plex_metadata_url: str = os.environ.get("PLEX_METADATA_URL")
    plex_user: str = os.environ.get("PLEX_USER")
    plex_proxy_img: str = os.environ.get("PLEX_PROXY_IMG")

    plex_json = requests.get(url=plex_url).json()
    rows = plex_json['response']['data']['rows']

    tv_shows = [row for row in rows if row['media_type'] == 'episode' and row['user'] == plex_user]
    unique_shows = []
    unique_show_titles = []
    episodes = {}
    for show in tv_shows:
        key = str(show['grandparent_rating_key'])

        if show['grandparent_title'] not in unique_show_titles:
            unique_show_titles.append(show['grandparent_title'])
            unique_shows.append(show)
            episodes[key] = []
            episodes[key].append({
                'episode': 'S' + str(show['parent_media_index']) + 'E' + str(show['media_index']),
                'name': show['grandchild_title'],
                'watched_on': show['last_watch']
            })
        else:
            episodes[key].append({
                'episode': 'S' + str(show['parent_media_index']) + 'E' + str(show['media_index']),
                'name': show['grandchild_title'],
                'watched_on': show['last_watch']
            })
    for show in unique_shows[:content_limit]:
        j = requests.get(plex_metadata_url + str(show['rating_key'])).json()
        if 'grandparent_guids' in j['response']['data']:
            slug = slugify(show['grandparent_title'])
            img_url = plex_proxy_img + show['thumb'] + '&width=' + str(img_width)
            save_images(bucket, bucket_list, 'show', slug, 'png', img_url)
            guid = j['response']['data']['grandparent_guids'][1].split('//')[1]
            eps = episodes[str(show['grandparent_rating_key'])]
            for ep in eps:
                ep['parent_show_id'] = guid
            data['shows'].append({
                'title': show['grandparent_title'],
                'guid': guid,
                'ep': 'S' + str(show['parent_media_index']) + 'E' + str(show['media_index']),
                'last_watch': show['last_watch'],
                'img': f'show_{slug}.png',
                'img_webp': f'show_{slug}.webp' if exists(f'static/img/show_{slug}.webp') else f'show_{slug}.png',
                'episodes': eps,
                'is_favorite': False
            })


def scrape_fav_tv_shows(data, bucket, bucket_list):
    tmdb_api_key: str = os.environ.get("TMDB_API_KEY")
    top_shows = requests.get(url="https://api.themoviedb.org/3/list/7112447?api_key=" + tmdb_api_key)
    top_shows_json = top_shows.json()
    for show in top_shows_json['items']:
        slug = slugify(show['name'])
        img_url = 'https://image.tmdb.org/t/p/w300' + show['poster_path']
        save_images(bucket, bucket_list, 'show', slug, 'jpg', img_url)
        data['shows'].append({
            'title': show['name'],
            'guid': str(show['id']),
            'ep': show['first_air_date'].split('-')[0],
            'img': f'show_{slug}.jpg',
            'img_webp': f'show_{slug}.webp' if exists(f'static/img/show_{slug}.webp') else f'show_{slug}.jpg',
            'last_watch': int(datetime.strptime(show['first_air_date'], "%Y-%m-%d").timestamp()),
            'episodes': [],
            'is_favorite': True
        })


def scrape_books(data, content_limit, bucket, bucket_list):
    oku_url = 'https://oku.club/api/collections/'
    reading = 'yjUNL'
    read = 'xSQso'
    # to_read='I0Ai5'
    favorites = 'IPgqn'
    f = requests.get(oku_url + favorites).json()
    d = requests.get(oku_url + read).json()
    d2 = requests.get(oku_url + reading).json()
    # d3 = requests.get(oku_url + to_read).json()
    for fav_book in f['books']:
        slug = fav_book['slug']
        save_images(bucket, bucket_list, 'book', slug, 'jpg', fav_book['thumbnail'])
        data['books'].append({
            'title': fav_book['title'],
            'author': fav_book['authors'][0]['name'],
            'url': 'https://oku.club/book/' + fav_book['slug'],
            'img': f'book_{slug}.jpg',
            'img_webp': f'book_{slug}.webp' if exists(f'static/img/book_{slug}.webp') else f'book_{slug}.jpg',
            'added_at': int(datetime.strptime(fav_book['addedAt'], "%Y-%m-%d").timestamp()),
            'is_favorite': True,
            'reading': False
        })
    for book in (d['books'])[:content_limit]:
        slug = book['slug']
        save_images(bucket, bucket_list, 'book', slug, 'jpg', book['thumbnail'])
        data['books'].append({
            'title': book['title'],
            'author': book['authors'][0]['name'],
            'url': 'https://oku.club/book/' + book['slug'],
            'img': f'book_{slug}.jpg',
            'img_webp': f'book_{slug}.webp' if exists(f'static/img/book_{slug}.webp') else f'book_{slug}.jpg',
            'added_at': int(datetime.strptime(book['addedAt'], "%Y-%m-%d").timestamp()),
            'is_favorite': False,
            'reading': False
        })
    for book in (d2['books'])[:content_limit]:
        slug = book['slug']
        save_images(bucket, bucket_list, 'book', slug, 'jpg', book['thumbnail'])
        data['books'].append({
            'title': book['title'],
            'author': book['authors'][0]['name'],
            'url': 'https://oku.club/book/' + book['slug'],
            'img': f'book_{slug}.jpg',
            'img_webp': f'book_{slug}.webp' if exists(f'static/img/book_{slug}.webp') else f'book_{slug}.jpg',
            'added_at': int(datetime.strptime(book['addedAt'], "%Y-%m-%d").timestamp()),
            'is_favorite': False,
            'reading': True
        })


def scrape_spotify(data, content_limit, bucket, bucket_list):
    spotify_client_id: str = os.environ.get("SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = os.environ.get("SPOTIFY_CLIENT_SECRET")
    spotify_refresh_token: str = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    spotify_token_url = 'https://accounts.spotify.com/api/token'
    spotify_base_url = 'https://api.spotify.com/v1/me/top/artists'
    auth_header = base64.urlsafe_b64encode((spotify_client_id + ':' + spotify_client_secret).encode('ascii'))
    headers = {'Content-Type': 'application/x-www-form-urlencoded',
               'Authorization': 'Basic {}'.format(auth_header.decode('ascii'))}
    res = requests.post(url=spotify_token_url,
                        data={'grant_type': 'refresh_token', 'refresh_token': spotify_refresh_token},
                        headers=headers).json()
    if 'access_token' not in res:
        log_warning(f'Error refreshing Spotify token: {res}')
        return
    access_token = res['access_token']
    url = spotify_base_url + '?{}'.format(parse.urlencode({'time_range': 'short_term', 'limit': content_limit}))
    spotify_req = requests.get(url=url, headers={'Authorization': 'Bearer {}'.format(access_token)})
    j = spotify_req.json()
    for item in j['items']:
        slug = slugify(item['name'])
        image_url = item['images'][1]['url'] if len(item['images']) > 1 else 'https://upload.wikimedia.org/wikipedia/commons/5/50/Black_Wallpaper.jpg'
        save_images(bucket, bucket_list, 'artist', slug, 'jpeg', image_url, square=True)
        data['spotify'].append({
            'name': item['name'],
            'url': item['external_urls']['spotify'],
            'followers': str(item['followers']['total']),
            'img': f'artist_{slug}.jpeg',
            'img_webp': f'artist_{slug}.webp' if exists(f'static/img/artist_{slug}.webp') else f'artist_{slug}.jpeg',
        })


def scrape_github(data, content_limit):
    github_url = 'https://api.github.com/users/{}/repos?per_page=500'.format('n3d1117')
    include = ['chatgpt-telegram-bot', 'appdb', 'stats-ios', 'cook']
    exclude = ['CrackBot']
    j = requests.get(github_url).json()
    for i in include:
        project = [p for p in j if p['name'] == i][0]
        data['github'].append({
            'name': project['name'],
            'html_url': project['html_url'],
            'description': project['description'],
            'language': project['language'],
            'stargazers_count': project['stargazers_count'],
            'forks_count': project['forks_count'],
        })
    d = sorted(j, key=lambda item: item['stargazers_count'], reverse=True)
    for project in [p for p in d if p['name'] not in exclude and p['name'] not in include][:content_limit]:
        data['github'].append({
            'name': project['name'],
            'html_url': project['html_url'],
            'description': project['description'],
            'language': project['language'],
            'stargazers_count': project['stargazers_count'],
            'forks_count': project['forks_count'],
        })


def scrape_videogames(data, bucket, bucket_list):
    igdb_client_id: str = os.environ.get("IGDB_CLIENT_ID")
    igdb_client_secret: str = os.environ.get("IGDB_CLIENT_SECRET")
    params = (
        ('client_id', igdb_client_id),
        ('client_secret', igdb_client_secret),
        ('grant_type', 'client_credentials'),
    )
    response = requests.post('https://id.twitch.tv/oauth2/token', params=params)
    access_token = response.json()['access_token']
    headers = {
        'Client-ID': igdb_client_id,
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
    }
    # if same year, most recent first
    ids = ['154986', '43335', '732', '27081', '96209', '114287', '134101', '114285', '1020', '7331', '8837',
           '4647', '4649', '4648', '10662', '96', '3136', '19560', '6036', '157446', '112875', '205780']
    for id in ids:
        d = 'fields first_release_date, cover.url, name, url; where id = ' + id + ';'
        response = requests.post('https://api.igdb.com/v4/games', headers=headers, data=d).json()
        if len(response) > 0:
            response = response[0]
            cover_url = response['cover']['url'].replace('t_thumb', 't_cover_big').replace('//', 'https://')
            year = int(datetime.utcfromtimestamp(int(response['first_release_date'])).strftime('%Y'))
            slug = slugify(response['name'])
            save_images(bucket, bucket_list, 'game', slug, 'jpg', cover_url)
            data['videogames'].append({
                'name': response['name'],
                'url': response['url'],
                'year': year,
                'img': f'game_{slug}.jpg',
                'img_webp': f'game_{slug}.webp' if exists(f'static/img/game_{slug}.webp') else f'game_{slug}.jpg',
            })


def get_supabase_bucket():
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    bucket_name: str = os.environ.get("SUPABASE_BUCKET_NAME")
    supabase: Client = create_client(url, key, options=ClientOptions(storage_client_timeout=STORAGE_TIMEOUT))
    bucket = supabase.storage.from_(bucket_name)
    return bucket


def create_img_folder():
    if not exists('static/img'):
        os.makedirs('static/img')


def write_data(data):
    try:
        with open('data/scraper.json', 'w') as f:
            json.dump(data, f)
        with open('static/data.json', 'w', encoding='utf8') as f:
            json.dump(data, f)
    except Exception as exc:
        log_warning(f'Failed to write scraper output: {exc}')


def download_file(url, path, retries=3, timeout=HTTP_TIMEOUT):
    tmp_path = f'{path}.part'

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            with open(tmp_path, 'wb') as f:
                f.write(response.content)
            os.replace(tmp_path, path)
            return
        except requests.exceptions.RequestException as exc:
            if exists(tmp_path):
                os.remove(tmp_path)
            if attempt == retries:
                raise RuntimeError(f'Failed to download {url} after {retries} attempts') from exc
            print(f'Download failed for {url} (attempt {attempt}/{retries}): {exc}. Retrying...')
            time.sleep(attempt)


def upload_file(bucket, filename, path, bucket_list, retries=UPLOAD_RETRIES):
    file_options = {'content-type': get_content_type(path), 'upsert': 'false'}

    for attempt in range(1, retries + 1):
        try:
            with UPLOAD_SEMAPHORE:
                bucket.upload(filename, os.path.abspath(path), file_options=file_options)
            remember_bucket_file(bucket_list, filename)
            return
        except StorageException as exc:
            if is_duplicate_storage_error(exc):
                remember_bucket_file(bucket_list, filename)
                return
            if bucket_file_exists(bucket, filename):
                remember_bucket_file(bucket_list, filename)
                return
            if attempt == retries:
                raise RuntimeError(f'Failed to upload {filename} after {retries} attempts') from exc
            print(f'Upload failed for {filename} (attempt {attempt}/{retries}): {exc}. Retrying...')
            time.sleep(attempt)
        except Exception as exc:
            if bucket_file_exists(bucket, filename):
                remember_bucket_file(bucket_list, filename)
                return
            if attempt == retries:
                raise RuntimeError(f'Failed to upload {filename} after {retries} attempts') from exc
            print(f'Upload failed for {filename} (attempt {attempt}/{retries}): {exc}. Retrying...')
            time.sleep(attempt)


def save_images(bucket, bucket_list, media_type, slug, ext, url, square=False):
    img_folder = 'static/img'
    orig_filename = f'{media_type}_{slug}.{ext}'
    webp_filename = f'{media_type}_{slug}.webp'
    orig_path = f'{img_folder}/{orig_filename}'
    webp_path = f'{img_folder}/{webp_filename}'

    try:
        for filename, path in {orig_filename: orig_path, webp_filename: webp_path}.items():
            if bucket_has_file(bucket_list, filename) and not exists(path):
                print(f'Downloading {filename}...')
                with open(path, 'wb+') as f:
                    try:
                        f.write(bucket.download(filename))
                    except StorageException:
                        pass

        if not exists(orig_path):
            print(f'Saving {orig_filename} locally...')
            download_file(url, orig_path)
            if square:
                with open(orig_path, 'r+b') as f:
                    with Image.open(f) as image:
                        square_image(image, 320).save(orig_path, image.format)

        if not exists(webp_path):
            print(f'Saving {webp_filename} locally...')
            subprocess.run(
                ['cwebp', '-quiet', orig_filename, '-o', webp_filename],
                cwd=img_folder,
                check=True
            )

        for filename, path in {orig_filename: orig_path, webp_filename: webp_path}.items():
            if exists(path) and not bucket_has_file(bucket_list, filename):
                print(f'Uploading {filename}...')
                upload_file(bucket, filename, path, bucket_list=bucket_list)
    except Exception as exc:
        log_warning(f'Image processing failed for {orig_filename}: {exc}')


def get_content_type(path):
    ext = os.path.splitext(path)[1].lower()
    return {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
    }.get(ext, 'application/octet-stream')


def is_duplicate_storage_error(exc):
    message = str(exc)
    return 'Duplicate' in message or '409' in message


def bucket_has_file(bucket_list, filename):
    with BUCKET_FILES_LOCK:
        return filename in bucket_list


def remember_bucket_file(bucket_list, filename):
    if bucket_list is None:
        return
    with BUCKET_FILES_LOCK:
        bucket_list.add(filename)


def bucket_file_exists(bucket, filename):
    try:
        return bucket.exists(filename)
    except Exception:
        return False


def log_warning(message):
    print(f'Warning: {message}')


def slugify(text):
    non_url_safe = ['"', '#', '$', '%', '&', '+', ',', '/', ':', ';', '=',
                    '?', '@', '[', '\\', ']', '^', '`', '{', '|', '}', '~', "'", "(", ")"]
    non_url_safe_regex = re.compile(r'[{}]'.format(''.join(re.escape(x) for x in non_url_safe)))
    text = non_url_safe_regex.sub('', text).strip()
    text = u'_'.join(re.split(r'\s+', text))
    return unidecode(text.lower())


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


if __name__ == '__main__':
    load_dotenv()
    try:
        main()
    except Exception:
        log_warning(f'Unexpected top-level failure:\n{traceback.format_exc()}')
