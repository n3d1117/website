# -*- coding: utf-8 -*-
import concurrent
import json
from concurrent.futures import ThreadPoolExecutor

import requests
from requests.adapters import HTTPAdapter
import os
import re
import sys
import time
import traceback
from os.path import exists
from urllib import parse
import base64
from dotenv import load_dotenv
import feedparser
from PIL import Image
from datetime import UTC, datetime

from unidecode import unidecode

HTTP_TIMEOUT = 30
IMAGE_WEBP_QUALITY = 82
PLEX_METADATA_WORKERS = int(os.environ.get("PLEX_METADATA_WORKERS", "16"))

SESSION = requests.Session()
SESSION.mount('https://', HTTPAdapter(pool_connections=32, pool_maxsize=32))


def main():
    data = {'movies': [], 'shows': [], 'books': [], 'spotify': [], 'github': [], 'videogames': []}
    previous_data = load_existing_data()
    content_limit = 50
    img_width = 350
    fatal_error = None
    try:
        create_img_folder()

        print('Scraping sources...')

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(timed_section, 'movies', scrape_all_movies, data, 999, img_width): 'movies',
                executor.submit(timed_section, 'shows', scrape_all_tv_shows, data, 999, img_width): 'shows',
                executor.submit(timed_section, 'books', scrape_books, data, content_limit): 'books',
                executor.submit(timed_section, 'spotify', scrape_spotify, data, content_limit): 'spotify',
                executor.submit(timed_section, 'github', scrape_github, data, content_limit): 'github',
                executor.submit(timed_section, 'videogames', scrape_videogames, data): 'videogames'
            }
            for future in concurrent.futures.as_completed(futures):
                section = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    if previous_data.get(section):
                        data[section] = previous_data[section]
                        log_warning(f'{section} failed, reused previous data: {exc}')
                    else:
                        raise RuntimeError(f'{section} failed and no previous data exists') from exc
    except Exception as exc:
        fatal_error = exc
        log_warning(f'Scraper setup failed: {exc}')

    repair_cached_images(data)
    write_data(data)
    if fatal_error:
        raise fatal_error


def scrape_all_movies(data, content_limit, img_width):
    scrape_movies(data, content_limit, img_width)
    scrape_cinema_movies(data)
    scrape_fav_movies(data)


def scrape_all_tv_shows(data, content_limit, img_width):
    scrape_tv_shows(data, content_limit, img_width)
    scrape_fav_tv_shows(data)


def scrape_movies(data, content_limit, img_width):
    plex_url: str = os.environ.get("PLEX_URL")
    plex_metadata_url: str = os.environ.get("PLEX_METADATA_URL")
    plex_user: str = os.environ.get("PLEX_USER")
    plex_proxy_img: str = os.environ.get("PLEX_PROXY_IMG")

    plex_json = get_json(plex_url)
    rows = plex_json['response']['data']['rows']

    movies = [row for row in rows if row['media_type'] == 'movie' and row['user'] == plex_user]
    seen_guids = set()
    with ThreadPoolExecutor(max_workers=PLEX_METADATA_WORKERS) as executor:
        results = executor.map(
            lambda movie: build_movie(movie, plex_metadata_url, plex_proxy_img, img_width),
            movies[:content_limit]
        )
    for movie_data in results:
        if movie_data and movie_data['guid'] not in seen_guids:
            seen_guids.add(movie_data['guid'])
            data['movies'].append(movie_data)


def build_movie(movie, plex_metadata_url, plex_proxy_img, img_width):
    j = get_json(plex_metadata_url + str(movie['rating_key']))
    if 'guids' not in j['response']['data']:
        log_warning(f'Error fetching metadata: {j}')
        return None
    guid = j['response']['data']['guids'][1].split('//')[1]
    slug = slugify(movie['title'])
    img_url = plex_proxy_img + movie['thumb'] + '&width=' + str(img_width)
    save_images('movie', slug, 'png', img_url)
    return {
        'title': movie['title'],
        'guid': guid,
        'year': movie['year'],
        'img': f'movie_{slug}.png',
        'img_webp': f'movie_{slug}.webp' if exists(f'static/img/movie_{slug}.webp') else f'movie_{slug}.png',
        'last_watch': movie['last_watch'],
        'cinema': False,
        'is_favorite': False
    }


def scrape_cinema_movies(data):
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
                        save_images('movie', slug, 'jpg', img_url)
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


def scrape_fav_movies(data):
    tmdb_api_key: str = os.environ.get("TMDB_API_KEY")
    top_movies_json = get_json("https://api.themoviedb.org/3/list/7112446?api_key=" + tmdb_api_key)
    for movie in top_movies_json['items']:
        slug = slugify(movie['title'])
        img_url = 'https://image.tmdb.org/t/p/w300' + movie['poster_path']
        save_images('movie', slug, 'jpg', img_url)
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


def scrape_tv_shows(data, content_limit, img_width):
    plex_url: str = os.environ.get("PLEX_URL")
    plex_metadata_url: str = os.environ.get("PLEX_METADATA_URL")
    plex_user: str = os.environ.get("PLEX_USER")
    plex_proxy_img: str = os.environ.get("PLEX_PROXY_IMG")

    plex_json = get_json(plex_url)
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
    with ThreadPoolExecutor(max_workers=PLEX_METADATA_WORKERS) as executor:
        results = executor.map(
            lambda show: build_show(show, episodes, plex_metadata_url, plex_proxy_img, img_width),
            unique_shows[:content_limit]
        )
    data['shows'].extend(show_data for show_data in results if show_data)


def build_show(show, episodes, plex_metadata_url, plex_proxy_img, img_width):
    j = get_json(plex_metadata_url + str(show['rating_key']))
    if 'grandparent_guids' not in j['response']['data']:
        return None
    slug = slugify(show['grandparent_title'])
    img_url = plex_proxy_img + show['thumb'] + '&width=' + str(img_width)
    save_images('show', slug, 'png', img_url)
    guid = j['response']['data']['grandparent_guids'][1].split('//')[1]
    eps = episodes[str(show['grandparent_rating_key'])]
    for ep in eps:
        ep['parent_show_id'] = guid
    return {
        'title': show['grandparent_title'],
        'guid': guid,
        'ep': 'S' + str(show['parent_media_index']) + 'E' + str(show['media_index']),
        'last_watch': show['last_watch'],
        'img': f'show_{slug}.png',
        'img_webp': f'show_{slug}.webp' if exists(f'static/img/show_{slug}.webp') else f'show_{slug}.png',
        'episodes': eps,
        'is_favorite': False
    }


def scrape_fav_tv_shows(data):
    tmdb_api_key: str = os.environ.get("TMDB_API_KEY")
    top_shows_json = get_json("https://api.themoviedb.org/3/list/7112447?api_key=" + tmdb_api_key)
    for show in top_shows_json['items']:
        slug = slugify(show['name'])
        img_url = 'https://image.tmdb.org/t/p/w300' + show['poster_path']
        save_images('show', slug, 'jpg', img_url)
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


def scrape_books(data, content_limit):
    oku_url = 'https://oku.club/api/collections/'
    reading = 'yjUNL'
    read = 'xSQso'
    # to_read='I0Ai5'
    favorites = 'IPgqn'
    f = get_json(oku_url + favorites)
    d = get_json(oku_url + read)
    d2 = get_json(oku_url + reading)
    # d3 = requests.get(oku_url + to_read).json()
    for fav_book in f['books']:
        slug = fav_book['slug']
        save_images('book', slug, 'jpg', fav_book['thumbnail'])
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
        save_images('book', slug, 'jpg', book['thumbnail'])
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
        save_images('book', slug, 'jpg', book['thumbnail'])
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


def scrape_spotify(data, content_limit):
    spotify_client_id: str = os.environ.get("SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = os.environ.get("SPOTIFY_CLIENT_SECRET")
    spotify_refresh_token: str = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    spotify_token_url = 'https://accounts.spotify.com/api/token'
    spotify_base_url = 'https://api.spotify.com/v1/me/top/artists'
    auth_header = base64.urlsafe_b64encode((spotify_client_id + ':' + spotify_client_secret).encode('ascii'))
    headers = {'Content-Type': 'application/x-www-form-urlencoded',
               'Authorization': 'Basic {}'.format(auth_header.decode('ascii'))}
    res = post_json(spotify_token_url,
                    data={'grant_type': 'refresh_token', 'refresh_token': spotify_refresh_token},
                    headers=headers)
    if 'access_token' not in res:
        log_warning(f'Error refreshing Spotify token: {res}')
        return
    access_token = res['access_token']
    url = spotify_base_url + '?{}'.format(parse.urlencode({'time_range': 'short_term', 'limit': content_limit}))
    j = get_json(url, headers={'Authorization': 'Bearer {}'.format(access_token)})
    for item in j['items']:
        slug = slugify(item['name'])
        image_url = item['images'][1]['url'] if len(item['images']) > 1 else 'https://upload.wikimedia.org/wikipedia/commons/5/50/Black_Wallpaper.jpg'
        save_images('artist', slug, 'jpeg', image_url, square=True)
        data['spotify'].append({
            'name': item['name'],
            'url': item['external_urls']['spotify'],
            'followers': str(item['followers']['total']),
            'img': f'artist_{slug}.jpeg',
            'img_webp': f'artist_{slug}.webp' if exists(f'static/img/artist_{slug}.webp') else f'artist_{slug}.jpeg',
        })


def scrape_github(data, content_limit):
    github_url = 'https://api.github.com/users/{}/repos?per_page=500'.format('n3d1117')
    github_token = os.environ.get("GITHUB_TOKEN")
    headers = {'Authorization': f'Bearer {github_token}'} if github_token else None
    include = ['chatgpt-telegram-bot', 'appdb', 'stats-ios', 'InstaSane', 'BracketView', 'hackernews-ios']
    j = get_json(github_url, headers=headers)
    if not isinstance(j, list):
        raise RuntimeError(f'Unexpected GitHub response: {j}')
    for i in include:
        matches = [p for p in j if p['name'] == i]
        if not matches:
            log_warning(f'Included GitHub project not found: {i}')
            continue
        project = matches[0]
        data['github'].append({
            'name': project['name'],
            'html_url': project['html_url'],
            'description': project['description'],
            'language': project['language'],
            'stargazers_count': project['stargazers_count'],
            'forks_count': project['forks_count'],
        })


def scrape_videogames(data):
    igdb_client_id: str = os.environ.get("IGDB_CLIENT_ID")
    igdb_client_secret: str = os.environ.get("IGDB_CLIENT_SECRET")
    params = (
        ('client_id', igdb_client_id),
        ('client_secret', igdb_client_secret),
        ('grant_type', 'client_credentials'),
    )
    access_token = post_json('https://id.twitch.tv/oauth2/token', params=params)['access_token']
    headers = {
        'Client-ID': igdb_client_id,
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
    }
    # if same year, most recent first
    ids = ['154986', '43335', '732', '27081', '96209', '114287', '134101', '114285', '1020', '7331', '8837',
           '4647', '4649', '4648', '10662', '96', '3136', '19560', '6036', '157446', '112875', '205780']
    d = 'fields id, first_release_date, cover.url, name, url; where id = ({}); limit {};'.format(
        ','.join(ids), len(ids)
    )
    responses = post_json('https://api.igdb.com/v4/games', headers=headers, data=d)
    games_by_id = {str(game['id']): game for game in responses}
    for id in ids:
        response = games_by_id.get(id)
        if response:
            cover_url = response['cover']['url'].replace('t_thumb', 't_cover_big').replace('//', 'https://')
            year = int(datetime.fromtimestamp(int(response['first_release_date']), UTC).strftime('%Y'))
            slug = slugify(response['name'])
            save_images('game', slug, 'jpg', cover_url)
            data['videogames'].append({
                'name': response['name'],
                'url': response['url'],
                'year': year,
                'img': f'game_{slug}.jpg',
                'img_webp': f'game_{slug}.webp' if exists(f'static/img/game_{slug}.webp') else f'game_{slug}.jpg',
            })


def create_img_folder():
    if not exists('static/img'):
        os.makedirs('static/img')


def timed_section(name, func, *args):
    start = time.perf_counter()
    func(*args)
    print(f'{name}: {time.perf_counter() - start:.1f}s')


def load_existing_data():
    for path in ('data/scraper.json', 'static/data.json'):
        if exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception as exc:
                log_warning(f'Failed to load previous scraper data from {path}: {exc}')
    return {}


def write_data(data):
    try:
        with open('data/scraper.json', 'w') as f:
            json.dump(data, f)
        with open('static/data.json', 'w', encoding='utf8') as f:
            json.dump(data, f)
    except Exception as exc:
        log_warning(f'Failed to write scraper output: {exc}')


def get_json(url, headers=None):
    try:
        response = SESSION.get(url=url, headers=headers, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f'GET {safe_url(url)} failed: {exc.__class__.__name__}') from exc


def post_json(url, data=None, headers=None, params=None):
    try:
        response = SESSION.post(url=url, data=data, headers=headers, params=params, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f'POST {safe_url(url)} failed: {exc.__class__.__name__}') from exc


def download_file(url, path, retries=3, timeout=HTTP_TIMEOUT):
    tmp_path = f'{path}.part'

    for attempt in range(1, retries + 1):
        try:
            response = SESSION.get(url, timeout=timeout)
            response.raise_for_status()
            with open(tmp_path, 'wb') as f:
                f.write(response.content)
            validate_downloaded_image(tmp_path)
            os.replace(tmp_path, path)
            return
        except (requests.exceptions.RequestException, Image.UnidentifiedImageError) as exc:
            if exists(tmp_path):
                os.remove(tmp_path)
            if attempt == retries:
                raise RuntimeError(f'Failed to download {safe_url(url)} after {retries} attempts') from exc
            print(f'Download failed for {safe_url(url)} (attempt {attempt}/{retries}): {exc}. Retrying...')
            time.sleep(attempt)


def save_images(media_type, slug, ext, url, square=False):
    img_folder = 'static/img'
    orig_filename = f'{media_type}_{slug}.{ext}'
    webp_filename = f'{media_type}_{slug}.webp'
    orig_path = f'{img_folder}/{orig_filename}'
    webp_path = f'{img_folder}/{webp_filename}'

    for filename, path in {orig_filename: orig_path, webp_filename: webp_path}.items():
        if is_zero_byte_file(path):
            print(f'Removing empty {filename}...')
            os.remove(path)

    if not valid_local_file(orig_path):
        print(f'Saving {orig_filename} locally...')
        download_file(url, orig_path)
        if square:
            with Image.open(orig_path) as image:
                square_image(image, 320).save(orig_path, image.format)

    if not valid_local_file(webp_path):
        print(f'Saving {webp_filename} locally...')
        convert_to_webp(orig_path, webp_path)


def valid_local_file(path):
    return exists(path) and not is_zero_byte_file(path)


def is_zero_byte_file(path):
    return exists(path) and os.path.getsize(path) == 0


def convert_to_webp(input_path, output_path):
    tmp_path = f'{output_path}.part'
    if exists(tmp_path):
        os.remove(tmp_path)
    with Image.open(input_path) as image:
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        image.save(tmp_path, 'WEBP', quality=IMAGE_WEBP_QUALITY, method=6)
    os.replace(tmp_path, output_path)


def validate_downloaded_image(path):
    with Image.open(path) as image:
        image.verify()


def repair_cached_images(data):
    for items in data.values():
        for item in items:
            original = item.get('img')
            webp = item.get('img_webp')
            if not original or not webp or not webp.endswith('.webp'):
                continue
            original_path = f'static/img/{original}'
            webp_path = f'static/img/{webp}'
            if valid_local_file(original_path) and not valid_local_file(webp_path):
                if is_zero_byte_file(webp_path):
                    os.remove(webp_path)
                print(f'Repairing {webp} from {original}...')
                convert_to_webp(original_path, webp_path)


def safe_url(url):
    parsed = parse.urlsplit(url)
    return parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))


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
        sys.exit(1)
