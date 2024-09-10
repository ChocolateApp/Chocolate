import os
import random
import re
import natsort
import datetime
import requests
import base64

from PIL import Image
from io import BytesIO
from operator import itemgetter
from m3u_parser import M3uParser
from typing import Any, Dict, List
from flask import Blueprint, request, Response, abort, send_file

from chocolate_app import get_language_file
from chocolate_app.routes.api.auth import token_required
from chocolate_app.utils.utils import generate_response, Codes, translate
from chocolate_app.tables import Users, Series, Movies, Actors, Albums, Artists, Episodes, Seasons, Tracks, Games, Books, OthersVideos, Libraries

medias_bp = Blueprint('medias', __name__, url_prefix='/medias')

LANGUAGE_FILE = get_language_file()

def episode_to_media(episode_id) -> Dict[str, Any]:
    episode = Episodes.query.filter_by(id=episode_id).first()
    main_season = Seasons.query.filter_by(tmdb_id=episode.season_id).first()
    serie = Series.query.filter_by(tmdb_id=main_season.serie_id).first()

    seasons = natsort.natsorted(Seasons.query.filter_by(serie_id=serie.tmdb_id).all(), key=lambda x: x.release)

    #TODO: Don't select the first one, select the last you watched

    banner_b64 = serie.banner_b64
    logo_b64 = serie.logo_b64
    cover_b64 = serie.cover_b64

    actors = serie.cast.split(",")
    actor_list = []

    for actor in actors:
        actor = Actors.query.filter_by(id=actor).first()
        if actor:
            actor_list.append({ "name": actor.name, "type": "actor" })

    serie_representation = []

    for season in seasons:
        episodes = natsort.natsorted(Episodes.query.filter_by(season_id=season.tmdb_id).all(), key=lambda x: x.release_date)
        eps = []

        for ep in episodes:
            eps.append({
                "id": ep.id,
                "number": ep.number,
                "title": ep.title,
                "release_date": ep.release_date,
                "file_date": datetime.datetime.fromtimestamp(os.path.getmtime(ep.slug)),
                "banner_b64": ep.cover_b64,
            })

        serie_representation.append({
            "season_id": season.id,
            "season_number": season.number,
            "episodes": eps,
        })

    media = {
        "id": episode.id,
        "title": serie.title,
        "alternatives_titles": [serie.title],
        "banner_id": serie.id,
        "description": serie.description,
        "have_logo": True if serie.logo else False,
        "type": "show",
        "note": serie.note,
        "genres": [translate(genre) for genre in serie.genre.split(",")],
        "duration": len(Episodes.query.filter_by(season_id=main_season.tmdb_id).all()),
        "release_date": datetime.datetime.strptime(serie.date, "%Y-%m-%d"),
        "file_date": datetime.datetime.fromtimestamp(os.path.getmtime(episode.slug)),
        "serie_representation": serie_representation,
        "images": {
            "banner": banner_b64,
            "logo": logo_b64,
            "cover": cover_b64,
        },
        "peoples": actor_list
    }
    return media

def serie_to_media(serie_id) -> Dict[str, Any]:
    serie = Series.query.filter_by(id=serie_id).first()
    #TODO: Don't select the first one, select the last ep you watched
    episode = natsort.natsorted(Episodes.query.filter_by(serie_id=serie.tmdb_id).all(), key=lambda x: x.release_date)[0]

    return episode_to_media(episode.id)

def movie_to_media(movie_id) -> Dict[str, Any]:
    movie = Movies.query.filter_by(id=movie_id).first()

    actors = movie.cast.split(",")
    actor_list = []

    for actor in actors:
        actor = Actors.query.filter_by(id=actor).first()
        if actor:
            actor_list.append({ "name": actor.name, "type": "actor" })

    banner_b64 = movie.banner_b64
    logo_b64 = movie.logo_b64
    cover_b64 = movie.cover_b64

    media = {
        "id": movie.id,
        "title": movie.title,
        "alternatives_titles": movie.alternatives_names.split(","),
        "banner_id": movie.id,
        "description": movie.description,
        "have_logo": True if movie.logo else False,
        "type": "movie",
        "note": movie.note,
        "genres": [translate(genre) for genre in movie.genre.split(",")],
        "duration": movie.duration,
        "release_date": datetime.datetime.strptime(movie.date, "%Y-%m-%d"),
        "file_date": datetime.datetime.fromtimestamp(movie.file_date),
        "images": {
            "banner": banner_b64,
            "logo": logo_b64,
            "cover": cover_b64,
        },
        "peoples": actor_list
    }
    return media

def other_to_media(other_id) -> Dict[str, Any]:
    other = OthersVideos.query.filter_by(id=other_id).first()

    banner_b64 = other.banner_b64
    logo_b64 = banner_b64
    cover_b64 = banner_b64

    media = {
        "id": other.video_hash,
        "title": other.title,
        "alternatives_titles": [other.title],
        "banner_id": other.video_hash,
        "description": "",
        "have_logo": False,
        "type": "other",
        "note": 0,
        "genres": [],
        "duration": other.duration,
        "release_date": "N/A",
        "file_date": datetime.datetime.fromtimestamp(os.path.getmtime(other.slug)),
        "images": {
            "banner": banner_b64,
            "logo": logo_b64,
            "cover": cover_b64,
        },
        "peoples": []
    }
    return media

def album_to_media(album_id) -> Dict[str, Any]:
    album = Albums.query.filter_by(id=album_id).first()
    artist = Artists.query.filter_by(id=album.artist_id).first()
    track = Tracks.query.filter_by(album_id=album_id).first()

    cover_b64 = album.cover_b64
    banner_b64 = cover_b64

    media = {
        "id": album.id,
        "title": album.title,
        "alternatives_titles": [],
        "banner_id": album.id,
        "description": "",
        "have_logo": False,
        "type": "album",
        "note": 0,
        "genres": [translate(10402)],
        "duration": len(Tracks.query.filter_by(album_id=album_id).all()),
        "release_date": datetime.datetime.strptime(album.release_date, "%Y-%m-%d"),
        "file_date": datetime.datetime.fromtimestamp(track.file_date),
        "images": {
            "banner": banner_b64,
            "logo": None,
            "cover": cover_b64,
        },
        "peoples": [{ "name": artist.name, "type": "artist" }]
    }
    return media

def tv_to_media(tv_path, channel) -> Dict[str, Any]:
    logo_url = channel["logo"]

    logo = requests.get(logo_url).content

    banner_b64 = None

    image = Image.open(logo)
    width, height = image.size
    new_width = 300
    new_height = int((new_width / width) * height)
    image = image.resize((new_width, new_height))
    image.save(logo, "webp")

    with open(logo, "rb") as image_file:
        banner_b64 = base64.b64encode(image_file.read()).decode("utf-8")    

    media = {
        "id": channel["tvg"]["id"],
        "title": channel["name"],
        "alternatives_titles": [channel["tvg"]["name"]],
        "banner_id": channel["tvg"]["id"],
        "description": "",
        "have_logo": True,
        "type": "live-tv",
        "note": 0,
        "genres": [],
        "duration": 0,
        "release_date": "N/A",
        "file_date": "N/A",
        "images": {
            "banner": banner_b64,
            "logo": None,
            "cover": banner_b64,
        },
        "peoples": []
    }
    

    return {"temp":"todo"}

def parse_tv_folder(tv_path) -> Any:
    #it's a m3u file, either on http or local
    raw_file = None
    if tv_path.startswith("http"):
        raw_file = requests.get(tv_path).text
    else:
        if not os.path.exists(tv_path):
            return []
        with open(tv_path, "r") as file:
            raw_file = file.read()

    channels = []
    parser = M3uParser()
    file = parser.parse(raw_file)
    channels = file._streams_info

    return channels


def get_continue_watching(user: Users) -> List[Dict[str, Any]]:
    #TODO: Implement real continue watching system, for Movies, Series and Others
    user_id = user.id
    return []
    #TODO: Impletement continue watching 
    # continue_watching =.query.filter_by(user_id=user_id).all()
    continue_watching_list = [watching.__dict__ for watching in continue_watching]

    for watching in continue_watching_list:
        del watching["_sa_instance_state"]
    
    continue_watching_list = [episode_to_media(episode["episode_id"]) for episode in continue_watching_list]

    return continue_watching_list

def get_all_medias_without_albums() -> Dict[str, List[Dict[str, Any]]]:
    all_movies = [movie_to_media(movie.id) for movie in Movies.query.all()]
    all_series = [serie_to_media(serie.id) for serie in Series.query.all()]
    
    all_medias = all_movies + all_series
    
    return all_medias

def get_all_medias() -> Dict[str, List[Dict[str, Any]]]:
    return get_all_medias_without_albums() + [album_to_media(album.id) for album in Albums.query.all()]

def get_latest_scanned_medias(all_medias: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    all_medias = natsort.natsorted(all_medias, key=itemgetter(*["file_date"]), reverse=True)
    return all_medias[:15]

def get_latest_medias(all_medias: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    all_medias = natsort.natsorted(all_medias, key=itemgetter(*["release_date"]), reverse=True)
    return all_medias[:15]

def get_top_rated_medias(all_medias: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    all_medias = natsort.natsorted(all_medias, key=itemgetter(*["note"]), reverse=True)
    return all_medias[:15]

def get_best_of_year(all_medias: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    current_year = datetime.datetime.now().year

    all_medias = [media for media in all_medias if media["release_date"].year == current_year]

    all_medias = natsort.natsorted(all_medias, key=itemgetter(*["note"]), reverse=True)

    return all_medias[:15]

def get_media_for_genre(genre: int, all_medias: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    all_medias = [media for media in all_medias if int(genre) in media["genres"]]
    all_medias = natsort.natsorted(all_medias, key=itemgetter(*["release_date"]))
    return all_medias[:15]

@medias_bp.route("home", methods=["GET"])
@token_required
def get_home_medias(current_user) -> Response:
    data = {
        "main_media": None,
        "continue_watching": [],
        "latest": [],
        "recently_added": [],
        "top_rated": [],
        "best_of_year": [],
        "family": [],
        "comedy": [],
        "animated": [],
        "action": [],
        "thriller": [],
        "horror": [],
        "drama": [],
        "western": [],
    }

    all_medias = get_all_medias_without_albums()
    albums = [album_to_media(album.id) for album in Albums.query.all()]
    
    continue_watching = get_continue_watching(current_user)
    data["continue_watching"] = continue_watching

    latest = get_latest_medias(all_medias + albums)
    data["latest"] = latest

    recently_added = get_latest_scanned_medias(all_medias + albums)
    data["recently_added"] = recently_added

    top_rated = get_top_rated_medias(all_medias)
    data["top_rated"] = top_rated

    best_of_year = get_best_of_year(all_medias)
    data["best_of_year"] = best_of_year

    family = get_media_for_genre(10751, all_medias)
    data["family"] = family

    comedy = get_media_for_genre(35, all_medias)
    data["comedy"] = comedy

    animated = get_media_for_genre(16, all_medias)
    data["animated"] = animated

    action = get_media_for_genre(28, all_medias)
    data["action"] = action

    thriller = get_media_for_genre(53, all_medias)
    data["thriller"] = thriller

    horror = get_media_for_genre(27, all_medias)
    data["horror"] = horror

    drama = get_media_for_genre(18, all_medias)
    data["drama"] = drama

    western = get_media_for_genre(37, all_medias)
    data["western"] = western
        
    keys = list(data.keys())
    keys.pop(0)

    for key in keys:
        medias = data[key]
        for media in medias:
            if "alternatives_titles" in media:
                del media["alternatives_titles"]
            if media in all_medias:
                all_medias.remove(media)
    
    if len(all_medias) > 0:
        data["main_media"] = random.choice(all_medias)
    else:
        data["main_media"] = get_all_medias_without_albums()[0]
    
    return (generate_response(Codes.SUCCESS, False, data))


@medias_bp.route("movies", methods=["GET"])
@token_required
def get_movies_media() -> Response:
    data = {
        "main_media": None,
        "continue_watching": [],
        "latest": [],
        "recently_added": [],
        "top_rated": [],
        "best_of_year": [],
        "family": [],
        "comedy": [],
        "animated": [],
        "action": [],
        "thriller": [],
        "horror": [],
        "drama": [],
        "western": [],
    }

    all_medias = [movie_to_media(movie.id) for movie in Movies.query.all()]
    
    latest = get_latest_medias(all_medias)
    data["latest"] = latest

    recently_added = get_latest_scanned_medias(all_medias)
    data["recently_added"] = recently_added

    top_rated = get_top_rated_medias(all_medias)
    data["top_rated"] = top_rated

    best_of_year = get_best_of_year(all_medias)
    data["best_of_year"] = best_of_year

    family = get_media_for_genre(10751, all_medias)
    data["family"] = family

    comedy = get_media_for_genre(35, all_medias)
    data["comedy"] = comedy

    animated = get_media_for_genre(16, all_medias)
    data["animated"] = animated

    action = get_media_for_genre(28, all_medias)
    data["action"] = action

    thriller = get_media_for_genre(53, all_medias)
    data["thriller"] = thriller

    horror = get_media_for_genre(27, all_medias)
    data["horror"] = horror

    drama = get_media_for_genre(18, all_medias)
    data["drama"] = drama

    western = get_media_for_genre(37, all_medias)
    data["western"] = western
        
    keys = list(data.keys())
    keys.pop(0)

    for key in keys:
        medias = data[key]
        for media in medias:
            if media in all_medias:
                all_medias.remove(media)
    
    if len(all_medias) > 0:
        data["main_media"] = random.choice(all_medias)
    else:
        data["main_media"] = get_all_medias_without_albums()[0]
    
    return (generate_response(Codes.SUCCESS, False, data))


@medias_bp.route("shows", methods=["GET"])
@token_required
def get_shows_media(current_user) -> Response:
    data = {
        "main_media": None,
        "continue_watching": [],
        "latest": [],
        "recently_added": [],
        "top_rated": [],
        "best_of_year": [],
        "family": [],
        "comedy": [],
        "animated": [],
        "action": [],
        "thriller": [],
        "horror": [],
        "drama": [],
        "western": [],
    }

    all_medias = [serie_to_media(serie.id) for serie in Series.query.all()]
    
    continue_watching = get_continue_watching(current_user)
    data["continue_watching"] = continue_watching

    latest = get_latest_medias(all_medias)
    data["latest"] = latest

    recently_added = get_latest_scanned_medias(all_medias)
    data["recently_added"] = recently_added

    top_rated = get_top_rated_medias(all_medias)
    data["top_rated"] = top_rated

    best_of_year = get_best_of_year(all_medias)
    data["best_of_year"] = best_of_year

    family = get_media_for_genre(10751, all_medias)
    data["family"] = family

    comedy = get_media_for_genre(35, all_medias)
    data["comedy"] = comedy

    animated = get_media_for_genre(16, all_medias)
    data["animated"] = animated

    action = get_media_for_genre(28, all_medias)
    data["action"] = action

    thriller = get_media_for_genre(53, all_medias)
    data["thriller"] = thriller

    horror = get_media_for_genre(27, all_medias)
    data["horror"] = horror

    drama = get_media_for_genre(18, all_medias)
    data["drama"] = drama

    western = get_media_for_genre(37, all_medias)
    data["western"] = western
        
    keys = list(data.keys())
    keys.pop(0)

    for key in keys:
        medias = data[key]
        for media in medias:
            if media in all_medias:
                all_medias.remove(media)
    
    if len(all_medias) > 0:
        data["main_media"] = random.choice(all_medias)
    else:
        data["main_media"] = get_all_medias_without_albums()[0]
    
    return (generate_response(Codes.SUCCESS, False, data))

def get_tv_media(current_user) -> Response:
    data = {
        "medias": []
    }

    all_tv_path = [lib.folder for lib in Libraries.query.filter_by(type="tv").all()]

    channels = []

    for tv_path in all_tv_path:
        channels = channels + parse_tv_folder(tv_path)

    all_medias = [tv_to_media(tv_path, channel) for channel in channels]

@medias_bp.route("/images/<image_type>/<media_type>/<media_id>", methods=["GET"])
def get_image(image_type: str, media_type: str, media_id: int) -> Response:
    image = None
    if image_type == "banner":
        if media_type == "movie":
            image = Movies.query.filter_by(id=media_id).first().banner
        elif media_type == "show":
            image = Series.query.filter_by(id=media_id).first().banner
        elif media_type == "episode":
            ep = Episodes.query.filter_by(episode_id=media_id).first()
            season = Seasons.query.filter_by(season_id=ep.season_id).first()
            image = Series.query.filter_by(id=season.serie).first().banner
        elif media_type == "album":
            image = Albums.query.filter_by(id=media_id).first().cover
        elif media_type == "album":
            image = Games.query.filter_by(id=media_id).first().cover
        elif media_type == "books":
            image = Books.query.filter_by(id=media_id).first().cover
        else:
            abort(404)
    elif image_type == "cover":
        if media_type == "movie":
            image = Movies.query.filter_by(id=media_id).first().cover
        elif media_type == "show":
            image = Series.query.filter_by(id=media_id).first().cover
        elif media_type == "episode":
            ep = Episodes.query.filter_by(episode_id=media_id).first()
            season = Seasons.query.filter_by(season_id=ep.season_id).first()
            image = Series.query.filter_by(id=season.serie).first().cover
        elif media_type == "album":
            image = Albums.query.filter_by(id=media_id).first().cover
        elif media_type == "album":
            image = Games.query.filter_by(id=media_id).first().cover
        elif media_type == "books": 
            image = Books.query.filter_by(id=media_id).first().cover
        else:
            abort(404)
    elif image_type == "logo":
        if media_type == "show" or media_type == "episode":
            image = Series.query.filter_by(id=media_id).first().logo
        elif media_type == "movie":
            image = Movies.query.filter_by(id=media_id).first().logo
        else:
            abort(404)

    if not image:
        abort(404)

    extension = os.path.splitext(image)[1]
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    width = request.args.get("width")
    if width:
        image = Image.open(image)
        wpercent = (int(width) / float(image.size[0]))
        hsize = int((float(image.size[1]) * float(wpercent)))
        image = image.resize((int(width), hsize), Image.ANTIALIAS)
        img_io = BytesIO()
        image.save(img_io, 'WEBP')
        img_io.seek(0)
        return send_file(img_io, mimetype=mime_type.get(extension, "image/webp"))
    
    height = request.args.get("height")
    if height:
        image = Image.open(image)
        hpercent = (int(height) / float(image.size[1]))
        wsize = int((float(image.size[0]) * float(hpercent)))
        image = image.resize((wsize, int(height)), Image.ANTIALIAS)
        img_io = BytesIO()
        image.save(img_io, 'WEBP')
        img_io.seek(0)
        return send_file(img_io, mimetype=mime_type.get(extension, "image/webp"))

    try:
        return send_file(image, mimetype=mime_type.get(extension, "image/jpeg"))
    except FileNotFoundError:
        return send_file(f"static/img/broken{ 'Banner' if image_type == 'banner' else '' }.webp", mimetype="image/webp")

def genre_id_to_name(genre_id: int) -> str:
    return translate(genre_id)


def search_medias(medias: List[Dict[str, Any]], search_terms: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    results = {}
    for media in medias:
        if not media:
            continue
        count = 0.0
        try:
            title = media["title"].lower()
            alternative_titles = media["alternatives_titles"]
            description = media["description"].lower().split(" ")
            genres = [genre_id_to_name(genre) for genre in media["genres"]]
            people = media["peoples"]
        except:
            continue

        for term in search_terms:
            term = term.lower()
            if term in title:
                count += 2
            for alt_title in alternative_titles:
                if term in alt_title.lower():
                    count += 1
            for word in description:
                if term == word.lower():
                    count += 0.1
            for genre in genres:
                if term == genre.lower():
                    count += 0.5
            for person in people:
                if term == person["name"].lower():
                    count += 1
        if count > 0:
            results[f"{media['id']} - {media['title']}"] = count

    temp_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

    results = []
    for result in temp_results:
        for media in medias:
            if f"{media['id']} - {media['title']}" == result[0]:
                results.append(media)
                break

    return results


def search_movies(search_terms: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    movies = [movie_to_media(movie.id) for movie in Movies.query.all()]
    
    results = search_medias(movies, search_terms)

    return results

def search_series(search_terms: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    series = [serie_to_media(serie.id) for serie in Series.query.all()]
    
    results = search_medias(series, search_terms)

    return results

def search_musics(search_terms: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    albums = [album_to_media(album.id) for album in Albums.query.all()]
    
    results = search_medias(albums, search_terms)

    return results


@medias_bp.route("/search/<type>", methods=["GET"])
@token_required
def search_medias_route(type: str) -> Response:
    if type not in ["home", "movies", "shows", "musics"]:
        abort(404)

    search = request.args.get("search")

    if not search:
        abort(400, "Missing search")

    search_terms = search.split(" ")
    
    if type == "home":
        search_results = search_medias(get_all_medias(), search_terms)
    elif type == "movies":
        search_results = search_movies(search_terms)
    elif type == "shows":
        search_results = search_series(search_terms)
    elif type == "musics":
        search_results = search_musics(search_terms)

    if len(search_results) == 0:
        return (generate_response(Codes.NO_RETURN_DATA, False))

    data = {
        "main_media": search_results[0],
        "medias": search_results[1:],
    }

    print(data)

    return (generate_response(Codes.SUCCESS, False, data))

@medias_bp.route("/media/<media_type>/<media_id>", methods=["GET"])
@token_required
def get_media(media_type: str, media_id: int) -> Response:
    if media_type == "movie":
        media = movie_to_media(media_id)
    elif media_type == "show":
        media = episode_to_media(media_id)
    elif media_type == "album":
        media = album_to_media(media_id)
    elif media_type == "other":
        media = other_to_media(media_id)
    else:
        abort(404)

    if not media:
        abort(404)

    return (generate_response(Codes.SUCCESS, False, media))