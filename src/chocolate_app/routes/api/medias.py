import os
import random
import natsort
import datetime
import dateutil


from PIL import Image
from io import BytesIO
from operator import itemgetter
from typing import Any, Dict, List
from chocolate_app import get_language_file
from chocolate_app.routes.api.auth import token_required
from flask import Blueprint, request, Response, abort, send_file
from chocolate_app.utils.utils import generate_response, Codes, translate

from chocolate_app.tables import (
    TVChannels,
    TVPrograms,
    Users,
    Series,
    Movies,
    Actors,
    Albums,
    Artists,
    Episodes,
    Seasons,
    Tracks,
    Games,
    Books,
    OthersVideos,
    MediaPlayed,
)

medias_bp = Blueprint("medias", __name__, url_prefix="/medias")

LANGUAGE_FILE = get_language_file()


def extract_sibling_episodes(episode, main_season):
    previous = None
    next = None
    episodes = natsort.natsorted(
        Episodes.query.filter_by(season_id=main_season.tmdb_id).all(),
        key=lambda x: x.release_date,
    )
    for i, ep in enumerate(episodes):
        if ep.id == episode.id:
            if i != 0:
                previous = episodes[i - 1]
            else:
                previous_season = Seasons.query.filter_by(
                    tmdb_id=main_season.serie_id, number=main_season.number - 1
                ).first()
                if previous_season:
                    previous_episodes = natsort.natsorted(
                        Episodes.query.filter_by(
                            season_id=previous_season.tmdb_id
                        ).all(),
                        key=lambda x: x.release_date,
                    )
                    previous = previous_episodes[-1]
            if i != len(episodes) - 1:
                next = episodes[i + 1]
            else:
                next_season = Seasons.query.filter_by(
                    tmdb_id=main_season.serie_id, number=main_season.number + 1
                ).first()
                if next_season:
                    next_episodes = natsort.natsorted(
                        Episodes.query.filter_by(season_id=next_season.tmdb_id).all(),
                        key=lambda x: x.release_date,
                    )
                    next = next_episodes[0]
            break

    return previous, next


def episode_to_media(
    user_id, episode_id, have_serie_repr=True
) -> Dict[str, Any] | None:
    episode = Episodes.query.filter_by(id=episode_id).first()
    if not episode:
        return None
    main_season = Seasons.query.filter_by(tmdb_id=episode.season_id).first()
    if not main_season:
        return None
    serie = Series.query.filter_by(tmdb_id=main_season.serie_id).first()
    if not serie:
        return None

    seasons = natsort.natsorted(
        Seasons.query.filter_by(serie_id=serie.tmdb_id).all(), key=lambda x: x.release
    )

    # TODO: Don't select the first one, select the last you watched

    banner_b64 = episode.cover_b64
    logo_b64 = serie.logo_b64
    cover_b64 = serie.cover_b64

    actors = serie.cast.split(",")
    actor_list = []

    for actor in actors:
        actor = Actors.query.filter_by(id=actor).first()
        if actor:
            actor_list.append({"name": actor.name, "type": "actor"})

    serie_representation = []

    if have_serie_repr:
        for season in seasons:
            episodes = natsort.natsorted(
                Episodes.query.filter_by(season_id=season.tmdb_id).all(),
                key=lambda x: x.release_date,
            )
            eps = []

            for ep in episodes:
                eps.append(episode_to_media(user_id, ep.id, False))

            serie_representation.append(
                {
                    "season_id": season.id,
                    "season_number": season.number,
                    "episodes": eps,
                }
            )

    previous, next = extract_sibling_episodes(episode, main_season)

    last_duration = 0
    try:
        media_played = MediaPlayed.query.filter_by(
            user_id=user_id, media_id=episode_id, media_type="show"
        ).first()
        if media_played:
            last_duration = media_played.duration
    except Exception:
        pass

    media = {
        "id": episode_id,
        "title": episode.title,
        "serie_title": serie.title,
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
        "last_duration": last_duration,
        "number": episode.number,
        "images": {
            "banner": banner_b64,
            "logo": logo_b64,
            "cover": cover_b64,
        },
        "peoples": actor_list,
        "_previous": previous.id if previous else None,
        "_next": next.id if next else None,
    }

    return media


def serie_to_media(user_id, serie_id) -> Dict[str, Any] | None:
    serie = Series.query.filter_by(id=serie_id).first()
    if not serie:
        return None

    serie_media_played = MediaPlayed.query.filter_by(
        user_id=user_id, serie_id=serie_id, media_type="show"
    ).all()

    episode_exists = Episodes.query.filter_by(serie_id=serie.tmdb_id).first()

    if not serie_media_played or not episode_exists:
        if not episode_exists:
            for media in serie_media_played:
                MediaPlayed.query.filter_by(id=media.id).delete()
        return episode_to_media(
            user_id,
            natsort.natsorted(
                Episodes.query.filter_by(serie_id=serie.tmdb_id).all(),
                key=lambda x: x.release_date,
            )[0].id,
            False,
        )

    serie_media_played = [media.__dict__ for media in serie_media_played]

    serie_media_played = natsort.natsorted(
        serie_media_played, key=itemgetter(*["datetime"]), reverse=True
    )

    episode_id = serie_media_played[0]["media_id"]
    episode_exists = Episodes.query.filter_by(id=episode_id).first()

    if not episode_exists:
        for media in serie_media_played:
            MediaPlayed.query.filter_by(id=media["id"]).delete()
        return episode_to_media(
            user_id,
            natsort.natsorted(
                Episodes.query.filter_by(serie_id=serie.tmdb_id).all(),
                key=lambda x: x.release_date,
            )[0].id,
            False,
        )

    return episode_to_media(user_id, episode_id, False)


def movie_to_media(user_id, movie_id) -> Dict[str, Any] | None:
    movie = Movies.query.filter_by(id=movie_id).first()
    if not movie:
        return None
    actors = movie.cast.split(",")
    actor_list = []

    for actor in actors:
        actor = Actors.query.filter_by(id=actor).first()
        if actor:
            actor_list.append({"name": actor.name, "type": "actor"})

    banner_b64 = movie.banner_b64
    logo_b64 = movie.logo_b64
    cover_b64 = movie.cover_b64

    last_duration = 0
    try:
        media_played = MediaPlayed.query.filter_by(
            user_id=user_id, media_id=movie_id, media_type="movie"
        ).first()
        if media_played:
            last_duration = media_played.duration
    except Exception:
        pass

    media = {
        "id": movie.id,
        "title": movie.title,
        "alternatives_titles": movie.alternative_title.split(","),
        "banner_id": movie.id,
        "description": movie.description,
        "have_logo": True if movie.logo else False,
        "type": "movie",
        "note": movie.note,
        "genres": [translate(genre) for genre in movie.genre.split(",")],
        "duration": movie.duration,
        "release_date": datetime.datetime.strptime(movie.date, "%Y-%m-%d"),
        "file_date": datetime.datetime.fromtimestamp(movie.file_date),
        "last_duration": last_duration,
        "images": {
            "banner": banner_b64,
            "logo": logo_b64,
            "cover": cover_b64,
        },
        "peoples": actor_list,
    }
    return media


def other_to_media(user_id, other_id) -> Dict[str, Any] | None:
    other = OthersVideos.query.filter_by(id=other_id).first()
    if not other:
        return None
    banner_b64 = other.banner_b64
    logo_b64 = banner_b64
    cover_b64 = banner_b64

    last_duration = 0
    media_played = MediaPlayed.query.filter_by(
        user_id=user_id, media_id=other_id, media_type="other"
    ).first()
    if media_played:
        last_duration = media_played.duration

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
        "last_duration": last_duration,
        "images": {
            "banner": banner_b64,
            "logo": logo_b64,
            "cover": cover_b64,
        },
        "peoples": [],
    }
    return media


def album_to_media(user_id, album_id) -> Dict[str, Any] | None:
    album = Albums.query.filter_by(id=album_id).first()
    if not album:
        return None
    artist = Artists.query.filter_by(id=album.artist_id).first()
    if not artist:
        return None
    track = Tracks.query.filter_by(album_id=album_id).first()
    if not track:
        return None

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
        "peoples": [{"name": artist.name, "type": "artist"}],
    }
    return media


def get_current_program(channel_id) -> Any | None:
    now = datetime.datetime.now(datetime.timezone.utc)
    programs = TVPrograms.query.filter_by(channel_id=channel_id).all()
    for program in programs:
        start = dateutil.parser.parse(program.start_time)
        end = dateutil.parser.parse(program.end_time)
        program = program.__dict__
        del program["_sa_instance_state"]
        if start <= now <= end:
            return program
    return None


def get_sibling_channels(channel_id) -> Any:
    channel = TVChannels.query.filter_by(id=channel_id).first()
    if not channel:
        return None, None

    # get the first channel with an id lower than the current channel
    previous = (
        TVChannels.query.filter(TVChannels.id < channel_id)
        .order_by(TVChannels.id.desc())
        .first()
    )

    # get the first channel with an id higher than the current channel
    next = (
        TVChannels.query.filter(TVChannels.id > channel_id)
        .order_by(TVChannels.id.asc())
        .first()
    )

    return previous, next


def tv_to_media(channel_id) -> Dict[str, Any] | None:
    channel = TVChannels.query.filter_by(id=channel_id).first()

    if not channel:
        return None

    previous, next = get_sibling_channels(channel_id)

    media = {
        "id": f"{channel.id}",
        "_source": channel.slug,
        "_epg": get_current_program(channel_id),
        "title": channel.name,
        "alternatives_titles": [channel.name],
        "banner_id": channel.id,
        "description": "",
        "have_logo": True,
        "type": "live-tv",
        "note": 0,
        "genres": [],
        "duration": 0,
        "release_date": "N/A",
        "file_date": "N/A",
        "images": {
            "banner": channel.logo,
            "logo": channel.logo,
            "cover": channel.logo,
        },
        "peoples": [],
        "_previous": previous.id if previous else None,
        "_next": next.id if next else None,
    }

    return media


def check_usability(media_list: List[Dict[str, Any]]) -> None:
    # for all media, check if the id is in the database
    for media in media_list:
        if media["media_type"] == "movie":
            movie = Movies.query.filter_by(id=media["id"]).first()
            if not movie:
                media_list.remove(media)
        elif media["media_type"] == "show":
            serie = Series.query.filter_by(id=media["id"]).first()
            if not serie:
                media_list.remove(media)
        elif media["media_type"] == "album":
            album = Albums.query.filter_by(id=media["id"]).first()
            if not album:
                media_list.remove(media)
        elif media["media_type"] == "other":
            other = OthersVideos.query.filter_by(video_hash=media["id"]).first()
            if not other:
                media_list.remove(media)


def get_continue_watching(user: Users, media_type) -> List[Dict[str, Any]]:
    user_id = user.id
    if media_type == "all":
        continue_watching = MediaPlayed.query.filter_by(user_id=user_id).all()
    else:
        continue_watching = MediaPlayed.query.filter_by(
            user_id=user_id, media_type=media_type
        ).all()
    continue_watching_list = [media.__dict__ for media in continue_watching]

    check_usability(continue_watching_list)

    for watching in continue_watching_list:
        del watching["_sa_instance_state"]

    serie_ids_in_continue = []

    # sort by date, and then by time
    continue_watching_list = natsort.natsorted(
        continue_watching_list, key=itemgetter(*["datetime"]), reverse=True
    )
    continue_watching_list_to_return = []

    type_to_function = {
        "movie": movie_to_media,
        "show": episode_to_media,
        "album": album_to_media,
        "other": other_to_media,
    }

    for watching in continue_watching_list:
        if (
            watching["media_type"] == "show"
            and watching["serie_id"] in serie_ids_in_continue
        ):
            continue
        if watching["media_type"] == "show":
            serie_ids_in_continue.append(watching["serie_id"])
        media_type = watching["media_type"]
        if media_type == "show":
            continue_watching_list_to_return.append(
                episode_to_media(user_id, watching["media_id"], False)
            )
        else:
            continue_watching_list_to_return.append(
                type_to_function[watching["media_type"]](user_id, watching["media_id"])
            )

    return continue_watching_list_to_return


def get_all_medias_without_albums(user_id) -> List[Dict[str, Any]]:
    all_movies = [movie_to_media(user_id, movie.id) for movie in Movies.query.all()]

    all_series_db = Series.query.all()
    all_series = []

    for serie in all_series_db:
        try:
            media = serie_to_media(user_id, serie.id)
        except Exception:
            continue
        if media:
            all_series.append(media)

    all_medias = all_movies + all_series

    return all_medias  # type: ignore


def get_all_medias(user_id) -> Dict[str, List[Dict[str, Any]]]:
    all_medias_without_albums = get_all_medias_without_albums(user_id)
    all_albums = [album_to_media(user_id, album.id) for album in Albums.query.all()]
    all_albums = [album for album in all_albums if album is not None]
    return all_medias_without_albums + all_albums  # type: ignore


def get_medias_for_key(key: str, all_medias: List[Dict[str, Any]]) -> List[str]:
    medias = [media for media in all_medias if media is not None]
    medias = natsort.natsorted(medias, key=itemgetter(*[key]), reverse=True)
    return medias[:15]  # type: ignore


def get_latest_scanned_medias(all_medias: List[Dict[str, Any]]) -> List[str]:
    return get_medias_for_key("file_date", all_medias)


def get_latest_medias(all_medias: List[Dict[str, Any]]) -> List[str]:
    return get_medias_for_key("release_date", all_medias)


def get_top_rated_medias(all_medias: List[Dict[str, Any]]) -> List[str]:
    return get_medias_for_key("note", all_medias)


def get_best_of_year(all_medias: List[Dict[str, Any]]) -> List[str]:
    current_year = datetime.datetime.now().year

    medias = [media for media in all_medias if media is not None]
    medias = [
        media for media in medias if media["release_date"].year == current_year  # type: ignore
    ]

    medias = natsort.natsorted(medias, key=itemgetter(*["note"]), reverse=True)

    return medias[:15]  # type: ignore


def get_media_for_genre(genre: int, all_medias: list[Dict[str, Any]]) -> List[str]:
    medias = [media for media in all_medias if media is not None]
    medias = [media for media in medias if int(genre) in media["genres"]]  # type: ignore
    medias = natsort.natsorted(medias, key=itemgetter(*["release_date"]))
    return medias[:15]  # type: ignore


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

    all_medias: Any = get_all_medias_without_albums(current_user.id)
    albums = [album_to_media(current_user.id, album.id) for album in Albums.query.all()]
    albums = [album for album in albums if album is not None]

    continue_watching = get_continue_watching(current_user, "all")
    data["continue_watching"] = continue_watching

    latest = get_latest_medias(all_medias + albums)  # type: ignore
    data["latest"] = latest

    recently_added = get_latest_scanned_medias(all_medias + albums)  # type: ignore
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
        data["main_media"] = random.choice(all_medias)  # type: ignore
    else:
        all_medias = get_all_medias_without_albums(current_user.id)
        if len(all_medias) == 0:
            return generate_response(Codes.MEDIA_NOT_FOUND, True)
        data["main_media"] = all_medias[0]  # type: ignore

    return generate_response(Codes.SUCCESS, False, data)


@medias_bp.route("movies", methods=["GET"])
@token_required
def get_movies_media(current_user) -> Response:
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

    all_medias = [
        movie_to_media(current_user.id, movie.id) for movie in Movies.query.all()
    ]
    all_medias: Any = [media for media in all_medias if media is not None]

    continue_watching = get_continue_watching(current_user, "movie")
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
        medias = get_all_medias_without_albums(current_user.id)
        if len(medias) > 0:
            data["main_media"] = medias[0]
        else:
            data["main_media"] = None

    return generate_response(Codes.SUCCESS, False, data)


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

    all_medias = [
        serie_to_media(current_user.id, serie.id) for serie in Series.query.all()
    ]
    all_medias = [media for media in all_medias if media is not None]

    continue_watching = get_continue_watching(current_user, "show")
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
        medias = get_all_medias_without_albums(current_user.id)
        if len(medias) > 0:
            data["main_media"] = medias[0]
        else:
            data["main_media"] = None

    return generate_response(Codes.SUCCESS, False, data)


@medias_bp.route("tv", methods=["GET"])
@token_required
def get_tv_media(current_user) -> Response:
    data = {"medias": []}

    data["medias"] = [tv_to_media(channel.id) for channel in TVChannels.query.all()]

    # on trie par ordre alphabétique
    data["medias"] = natsort.natsorted(data["medias"], key=lambda x: x["title"])

    return generate_response(Codes.SUCCESS, False, data)


@medias_bp.route("/images/<image_type>/<media_type>/<media_id>", methods=["GET"])
def get_image(image_type: str, media_type: str, media_id: int) -> Response:
    image = None
    if image_type == "banner":
        if media_type == "movie":
            movie = Movies.query.filter_by(id=media_id).first()
            if not movie:
                abort(404)
            image = movie.banner
        elif media_type == "show":
            serie = Series.query.filter_by(id=media_id).first()
            if not serie:
                abort(404)
            image = serie.banner
        elif media_type == "episode":
            ep = Episodes.query.filter_by(episode_id=media_id).first()
            if not ep:
                abort(404)
            serie = Series.query.filter_by(tmdb_id=ep.serie_id).first()
            if not serie:
                abort(404)
            image = serie.banner
        elif media_type == "album":
            album = Albums.query.filter_by(id=media_id).first()
            if not album:
                abort(404)
            image = album.cover
        elif media_type == "game":
            game = Games.query.filter_by(id=media_id).first()
            if not game:
                abort(404)
        elif media_type == "books":
            book = Books.query.filter_by(id=media_id).first()
            if not book:
                abort(404)
            image = book.cover
        else:
            abort(404)
    elif image_type == "cover":
        if media_type == "movie":
            movie = Movies.query.filter_by(id=media_id).first()
            if not movie:
                abort(404)
            image = movie.cover
        elif media_type == "show":
            serie = Series.query.filter_by(id=media_id).first()
            if not serie:
                abort(404)
            image = serie.cover
        elif media_type == "episode":
            ep = Episodes.query.filter_by(episode_id=media_id).first()
            if not ep:
                abort(404)
            serie = Series.query.filter_by(tmdb_id=ep.serie_id).first()
            if not serie:
                abort(404)
            image = serie.cover
        elif media_type == "album":
            album = Albums.query.filter_by(id=media_id).first()
            if not album:
                abort(404)
            image = album.cover
        elif media_type == "game":
            game = Games.query.filter_by(id=media_id).first()
            if not game:
                abort(404)
            image = game.cover
        elif media_type == "books":
            book = Books.query.filter_by(id=media_id).first()
            if not book:
                abort(404)
            image = book.cover
        else:
            abort(404)
    elif image_type == "logo":
        if media_type == "show" or media_type == "episode":
            serie = Series.query.filter_by(id=media_id).first()
            if not serie:
                abort(404)
            image = serie.logo
        elif media_type == "movie":
            movie = Movies.query.filter_by(id=media_id).first()
            if not movie:
                abort(404)
            image = movie.logo
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
        wpercent = int(width) / float(image.size[0])
        hsize = int((float(image.size[1]) * float(wpercent)))
        image = image.resize((int(width), hsize), Image.ANTIALIAS)  # type: ignore
        img_io = BytesIO()
        image.save(img_io, "WEBP")
        img_io.seek(0)
        return send_file(img_io, mimetype=mime_type.get(extension, "image/webp"))

    height = request.args.get("height")
    if height:
        image = Image.open(image)
        hpercent = int(height) / float(image.size[1])
        wsize = int((float(image.size[0]) * float(hpercent)))
        image = image.resize((wsize, int(height)), Image.ANTIALIAS)  # type: ignore
        img_io = BytesIO()
        image.save(img_io, "WEBP")
        img_io.seek(0)
        return send_file(img_io, mimetype=mime_type.get(extension, "image/webp"))

    try:
        return send_file(image, mimetype=mime_type.get(extension, "image/jpeg"))
    except FileNotFoundError:
        return send_file(
            f"static/img/broken{ 'Banner' if image_type == 'banner' else '' }.webp",
            mimetype="image/webp",
        )


def genre_id_to_name(genre_id: int) -> str:
    return translate(genre_id)


def search_medias(
    medias: List[Dict[str, Any]], search_terms: List[str], user_id
) -> Dict[str, List[Dict[str, Any]]]:
    results = {}
    for media in medias:
        if not media:
            continue
        count = 0.0

        title = media["title"].lower()
        alternative_titles = media["alternatives_titles"]
        description = media["description"].lower().split(" ")
        genres = media["genres"]
        people = media["peoples"]

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

    return results  # type: ignore


def search_movies(user_id, search_terms: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    movies = [movie_to_media(user_id, movie.id) for movie in Movies.query.all()]

    results = search_medias(movies, search_terms, user_id)  # type: ignore

    return results


def search_series(user_id, search_terms: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    series = [serie_to_media(user_id, serie.id) for serie in Series.query.all()]

    results = search_medias(series, search_terms, user_id)  # type: ignore

    return results


def search_musics(user_id, search_terms: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    albums = [album_to_media(user_id, album.id) for album in Albums.query.all()]

    results = search_medias(albums, search_terms, user_id)  # type: ignore

    return results


@medias_bp.route("/search/<type>", methods=["GET"])
@token_required
def search_medias_route(current_user, type: str) -> Response:
    if type not in ["home", "movies", "shows", "musics"]:
        abort(404)

    search = request.args.get("search")

    if not search:
        abort(400, "Missing search")
    search_results = []
    search_terms = search.split(" ")

    if type == "home":
        search_results = search_medias(get_all_medias(current_user.id), search_terms, current_user.id)  # type: ignore
    elif type == "movies":
        search_results = search_movies(current_user.id, search_terms)
    elif type == "shows":
        search_results = search_series(current_user.id, search_terms)
    elif type == "musics":
        search_results = search_musics(current_user.id, search_terms)

    if len(search_results) == 0:
        return generate_response(Codes.NO_RETURN_DATA, False)

    if len(search_results) > 1:
        data = {
            "main_media": search_results[0],  # type: ignore
            "medias": search_results[1:],  # type: ignore
        }
    elif len(search_results) == 1:
        data = {"main_media": search_results[0], "medias": []}  # type: ignore
    else:
        data = {"main_media": None, "medias": []}

    return generate_response(Codes.SUCCESS, False, data)


@medias_bp.route("/media/<media_type>/<media_id>", methods=["GET"])
@token_required
def get_media(current_user, media_type: str, media_id: int) -> Response:
    media = None
    if media_type == "movie":
        media = movie_to_media(current_user.id, media_id)
    elif media_type == "show":
        media = episode_to_media(current_user.id, media_id)
    elif media_type == "album":
        media = album_to_media(current_user.id, media_id)
    elif media_type == "other":
        media = other_to_media(current_user.id, media_id)
    elif media_type == "live-tv":
        media = tv_to_media(media_id)
    else:
        abort(404)

    if not media:
        abort(404)

    return generate_response(Codes.SUCCESS, False, media)
