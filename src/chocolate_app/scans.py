# Copyright (C) 2024 Impre_visible
import re
import io
import os
import ast
import zlib
import uuid
import fitz
import rarfile
import zipfile
import datetime
import requests
import subprocess
import sqlalchemy
import deezer as deezer_main

from PIL import Image
from tinytag import TinyTag
from guessit import guessit
from tmdbv3api.as_obj import AsObj
from typing import Any, Tuple, Dict
from Levenshtein import distance as lev
from deep_translator import GoogleTranslator
from tmdbv3api.exceptions import TMDbException
from tmdbv3api import TV, Episode, Movie, Person, Search, Group


from chocolate_app import DB, get_dir_path, config, IMAGES_PATH
from chocolate_app.tables import (
    Libraries,
    Movies,
    Series,
    Artists,
    Albums,
    Tracks,
    Episodes,
    Seasons,
    Actors,
    Games,
    OthersVideos,
    Books,
)

from chocolate_app.utils.utils import (
    path_join,
    save_image,
    is_video_file,
    is_music_file,
    is_book_file,
    is_image_file,
    is_directory,
    log,
    generate_b64_image
)
from chocolate_app.plugins_loader import events, overrides

dir_path = get_dir_path()

deezer = deezer_main.Client()

image_requests = requests.Session()

"""
genre_list = {
    12: "Aventure",
    14: "Fantastique",
    16: "Animation",
    18: "Drama",
    27: "Horreur",
    28: "Action",
    35: "Comédie",
    36: "Histoire",
    37: "Western",
    53: "Thriller",
    80: "Crime",
    99: "Documentaire",
    878: "Science-fiction",
    9648: "Mystère",
    10402: "Musique",
    10749: "Romance",
    10751: "Famille",
    10752: "War",
    10759: "Action & Adventure",
    10762: "Kids",
    10763: "News",
    10764: "Reality",
    10765: "Sci-Fi & Fantasy",
    10766: "Soap",
    10767: "Talk",
    10768: "War & Politics",
    10769: "Western",
    10770: "TV Movie",
}
"""

websites_trailers = {
    "YouTube": "https://www.youtube.com/embed/",
    "Dailymotion": "https://www.dailymotion.com/video/",
    "Vimeo": "https://vimeo.com/",
}


def transformToDict(obj: AsObj | list) -> dict | list:
    """
    Transform an AsObj to a dict

    Args:
        obj (AsObj | list): The object to transform

    Returns:
        dict: The transformed object
    """
    if isinstance(obj, list):
        return obj
    if isinstance(obj, AsObj):
        obj = str(obj)
        obj = ast.literal_eval(obj)
        return obj
    return obj


def transformToList(obj: AsObj | list) -> list:
    """
    Transform an AsObj to a list

    Args:
        obj (AsObj | list): The object to transform

    Returns:
        list: The transformed object
    """
    if isinstance(obj, AsObj):
        return list(obj)
    if isinstance(obj, list):
        return obj
    return obj.replace('"', '\\"')


def length_video(path: str) -> float:
    seconds = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        return float(seconds.stdout)
    except Exception as e:
        log_message = f"Error while getting the length of the video {path}: {e}"
        log("ERROR", "LENGTH VIDEO", log_message)
        return 0


def createArtist(artistName: str, lib: str) -> int:
    exists = Artists.query.filter_by(name=artistName).first() is not None
    if exists:
        return Artists.query.filter_by(name=artistName).first().id

    artists = deezer.search_artists(artistName)
    artist = artists[0]
    artist_id = artist.id

    exists = Artists.query.filter_by(id=artist_id).first() is not None
    if exists:
        return artist_id

    cover = save_image(artist.picture_big, f"{IMAGES_PATH}/Artist_{artist_id}")

    artist = Artists(id=artist_id, name=artistName, cover=cover, library_name=lib)
    DB.session.add(artist)
    DB.session.commit()

    events.execute_event(events.NEW_ARTIST, artist)

    return artist_id


def createAlbum(
    name: str, artist_id: int, tracks: list = [], library: str = ""
) -> Albums | None:
    exists = (
        Albums.query.filter_by(dir_name=name, artist_id=artist_id).first() is not None
    )
    if exists:
        Albums.query.filter_by(dir_name=name, artist_id=artist_id).first().tracks = (
            ",".join(tracks)
        )
        DB.session.commit()
        return Albums.query.filter_by(dir_name=name, artist_id=artist_id).first()

    albums = deezer.search_albums(
        f"{Artists.query.filter_by(id=artist_id).first().name} - {name}"
    )

    if len(albums) == 0:
        return None
    best_match = albums[0]

    for album in albums:
        if lev(name, album.title) < lev(name, best_match.title):
            best_match = album
        elif lev(name, album.title) == lev(name, best_match.title):
            best_match = best_match
        if lev(name, best_match.title) == 0:
            break

    album = best_match

    album_id = album.id
    exist = Albums.query.filter_by(id=album_id, artist_id=artist_id).first() is not None
    if exist:
        return Albums.query.filter_by(id=album_id, artist_id=artist_id).first()
    
    album_name = album.title
    cover = save_image(album.cover_big, f"{IMAGES_PATH}/Album_{album_id}")

    tracks_list = ",".join(tracks)

    album = Albums(
        id=album_id,
        title=album_name,
        dir_name=name,
        artist_id=artist_id,
        cover=cover,
        cover_b64=generate_b64_image(cover, width=300),
        tracks=tracks_list,
        library_name=library,
        release_date=album.release_date,
    )
    DB.session.add(album)
    DB.session.commit()

    events.execute_event(events.NEW_ALBUM, album)

    return album


def getAlbumImage(album_name: str, path: str) -> str | None:
    album = deezer.search_albums(album_name)
    if len(album) == 0:
        return None
    album = album[0]
    cover = save_image(album.cover_big, path)
    return cover


def getArtistImage(artist_name: str, path: str) -> str:
    artist = deezer.search_artists(artist_name)[0]
    cover = save_image(artist.picture_big, path)
    return cover


def generateImage(title: str, librairie: str, banner: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    largeur = 1280
    hauteur = 720
    image = Image.new("RGB", (largeur, hauteur), color="#1d1d1d")

    draw = ImageDraw.Draw(image)

    font_path = f"{dir_path}/static/fonts/Poppins-Medium.ttf"
    font_title = ImageFont.truetype(font_path, size=70)
    font_librairie = ImageFont.truetype(font_path, size=50)

    titre_larg, titre_haut = draw.textsize(title, font=font_title)
    librairie_larg, librairie_haut = draw.textsize(librairie, font=font_librairie)
    x_title = int((largeur - titre_larg) / 2)
    y_title = int((hauteur - titre_haut - librairie_haut - 50) / 2)
    x_librairie = int((largeur - librairie_larg) / 2)
    y_librairie = y_title + titre_haut + 50

    # Ajouter le texte du titre
    draw.text((x_title, y_title), title, font=font_title, fill="white", align="center")

    # Ajouter le texte de la librairie
    draw.text(
        (x_librairie, y_librairie),
        librairie,
        font=font_librairie,
        fill="white",
        align="center",
    )

    # Enregistrer l'image
    os.remove(banner)
    image.save(banner, "webp")


def is_connected() -> bool:
    try:
        requests.get("https://ww.google.com/").status_code
        return True
    except Exception:
        return False


def print_loading(filesList: list, index: int, title: str) -> None:
    try:
        os.get_terminal_size().columns
    except OSError:
        return
    terminal_size = os.get_terminal_size().columns - 1
    percentage = index * 100 / len(filesList)

    loading_first_part = ("•" * int(percentage * 0.2))[:-1]
    loading_first_part = f"{loading_first_part}➤"
    loading_second_part = "•" * (20 - int(percentage * 0.2))

    loading_start = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loading_first_part}\33[31m{loading_second_part}\33[0m]"
    loading_middle = f"{title}"
    loading_end = f"{index}/{len(filesList)}"

    if len(loading_start) + len(loading_middle) + len(loading_end) > terminal_size:
        loading_middle = (
            loading_middle[: terminal_size - len(loading_start) - len(loading_end) - 3]
            + "..."
        )

    free_space = (
        terminal_size - len(loading_start) - len(loading_middle) - len(loading_end)
    ) // 2
    loading_middle = (
        " " * free_space
        + loading_middle
        + " " * free_space
        + " "
        * (
            (
                terminal_size
                - len(loading_start)
                - len(loading_middle)
                - len(loading_end)
            )
            % 2
        )
    )

    loading = f"{loading_start} | {loading_middle} | {loading_end}"
    print("\033[?25l", end="")
    print(loading, end="\r", flush=True)


def searchGame(game: str, console: str) -> dict | None:
    url = f"https://www.igdb.com/search_autocomplete_all?q={game.replace(' ', '%20')}"
    return IGDBRequest(url, console)


def translate(string: str) -> str:
    language = config["ChocolateSettings"]["language"]
    if language == "EN":
        return string
    translated = GoogleTranslator(source="english", target=language.lower()).translate(
        string
    )
    return translated


def IGDBRequest(url: str, console: str) -> Dict | None:
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (X11; UwUntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": url,
        "DNT": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Referer": url,
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    response = requests.request("GET", url, headers=custom_headers)

    client_id = config.get("APIKeys", "IGDBID")
    client_secret = config.get("APIKeys", "IGDBSECRET")

    if response.status_code == 200 and client_id and client_secret:
        grant_type = "client_credentials"
        get_access_token = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type={grant_type}"
        token_req = requests.request("POST", get_access_token)
        token = token_req.json()
        if "message" in token and token["message"] == "invalid client secret":
            print("Invalid client secret")
            return None
        if "access_token" not in token:
            return None
        token = token["access_token"]

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Client-ID": client_id,
        }

        games = response.json()["game_suggest"]

        for i in games:
            game = i
            game_id = game["id"]
            url = "https://api.igdb.com/v4/games"
            body = f"fields name, cover.*, summary, total_rating, first_release_date, genres.*, platforms.*; where id = {game_id};"
            response = requests.request("POST", url, headers=headers, data=body)
            if len(response.json()) == 0:
                break
            game = response.json()[0]
            if "platforms" in game:
                game_platforms = game["platforms"]
                try:
                    platforms = []

                    for i in game_platforms:
                        if "abbreviation" not in i:
                            platforms.append(i["alternative_name"])
                        else:
                            platforms.append(i["abbreviation"])

                    real_console_name = {
                        "GB": "Game Boy",
                        "GBA": "Game Boy Advance",
                        "GBC": "Game Boy Color",
                        "N64": "Nintendo 64",
                        "NES": "Nintendo Entertainment System",
                        "NDS": "Nintendo DS",
                        "SNES": "Super Nintendo Entertainment System",
                        "Sega Master System": "Sega Master System",
                        "Sega Mega Drive": "Sega Mega Drive",
                        "PS1": "PS1",
                    }

                    if (
                        real_console_name[console] not in platforms
                        and console not in platforms
                    ):
                        continue
                    if "total_rating" not in game:
                        game["total_rating"] = "Unknown"
                    if "genres" not in game:
                        game["genres"] = [{"name": "Unknown"}]
                    if "summary" not in game:
                        game["summary"] = "Unknown"
                    if "first_release_date" not in game:
                        game["first_release_date"] = "Unknown"
                    if "cover" not in game:
                        game["cover"] = {
                            "url": "//images.igdb.com/igdb/image/upload/t_cover_big/nocover.png"
                        }

                    game["summary"] = translate(game["summary"])
                    game["genres"][0]["name"] = translate(game["genres"][0]["name"])

                    genres = []
                    for genre in game["genres"]:
                        genres.append(genre["name"])
                    genres_list = ", ".join(genres)

                    game_data = {
                        "title": game["name"],
                        "cover": game["cover"]["url"].replace("//", "https://"),
                        "description": game["summary"],
                        "note": game["total_rating"],
                        "date": game["first_release_date"],
                        "genre": genres_list,
                        "id": game["id"],
                    }
                    return game_data
                except Exception:
                    log_message = (
                        f"Error while getting the game {game['name']} from IGDB"
                    )
                    log("ERROR", "GAME SCAN", log_message)
                    continue
        return None
    return None


def getMovies(library_name: str) -> None:
    path = Libraries.query.filter_by(name=library_name).first().folder

    if overrides.have_override("scan_movie"):
        return overrides.execute_override("scan_movie", path, library_name)

    all_movies_not_sorted = []

    movie_files = Movies.query.filter_by(library_name=library_name).all()
    for movie in movie_files:
        slug = movie.slug
        if not os.path.exists(slug):
            DB.session.delete(movie)
            DB.session.commit()

    film_file_list = []
    if not os.path.exists(path):
        return

    movie_files = os.listdir(path)

    for movie_file in movie_files:
        if is_video_file(movie_file) or is_directory(path_join(path, movie_file)):
            film_file_list.append(movie_file)

    if not is_connected():
        return

    movie = Movie()
    index = 0
    for searchedFilm in film_file_list:
        index += 1
        movieTitle = searchedFilm
        if os.path.isdir(path_join(path, searchedFilm)):
            the_path = path_join(path, searchedFilm)
            try:
                searchedFilm = path_join(searchedFilm, os.listdir(the_path)[0])
            except Exception as e:
                log_message = f"Error while getting the movie {movieTitle}: {e}"
                log("ERROR", "MOVIE SCAN", log_message)
                continue
        else:
            movieTitle, extension = os.path.splitext(movieTitle)
        originalMovieTitle = movieTitle

        print_loading(film_file_list, index, movieTitle)

        slug = searchedFilm
        video_path = f"{path}/{slug}"
        exists = Movies.query.filter_by(slug=video_path).first() is not None

        if not exists:
            guessedData = guessit(originalMovieTitle)
            guessedTitle = ""
            year = None
            if "title" not in guessedData:
                guessedTitle = originalMovieTitle
            else:
                guessedTitle = guessedData["title"]
                if "episode" in guessedData:
                    guessedTitle = f"{guessedData['episode']} {guessedTitle}"
                if "alternative_title" in guessedData:
                    guessedTitle = (
                        f"{guessedData['alternative_title']} - {guessedTitle}"
                    )
                if "part" in guessedData:
                    guessedTitle = f"{guessedTitle} Part {guessedData['part']}"
                if "year" in guessedData:
                    year = guessedData["year"]

            try:
                search = Search().movies(guessedTitle, year=year, adult=True)
            except Exception:
                search = Search().movies(guessedTitle, year=year)

            search = transformToDict(search)
            if not search or not search["results"]:
                all_movies_not_sorted.append(originalMovieTitle)
                continue

            search = search["results"]
            bestMatch = search[0]
            if (
                config["ChocolateSettings"]["askwhichmovie"] == "false"
                or len(search) == 1
            ):
                for i in range(len(search)):
                    if (
                        lev(guessedTitle, search[i]["title"])
                        < lev(guessedTitle, bestMatch["title"])
                        and bestMatch["title"] not in film_file_list
                    ):
                        bestMatch = search[i]
                    elif (
                        lev(guessedTitle, search[i]["title"])
                        == lev(guessedTitle, bestMatch["title"])
                        and bestMatch["title"] not in film_file_list
                    ):
                        bestMatch = bestMatch
                    if (
                        lev(guessedTitle, bestMatch["title"]) == 0
                        and bestMatch["title"] not in film_file_list
                    ):
                        break

            res = bestMatch
            try:
                name = res["title"]
            except AttributeError:
                name = res["original_title"]
            movie_id = res["id"]
            details = movie.details(movie_id)

            logo_download_url = None
            logo_url = None

            all_images = movie.images(movie_id, include_image_language="null")
            all_images_text = movie.images(movie_id)

            if len(all_images["posters"]) > 0:
                cover = save_image(
                    f"https://image.tmdb.org/t/p/original{all_images['posters'][0]['file_path']}",
                    f"{IMAGES_PATH}/{movie_id}_Movie_Cover",
                )
            else:
                cover = save_image(
                    f"https://image.tmdb.org/t/p/original{res['poster_path']}",
                    f"{IMAGES_PATH}/{movie_id}_Movie_Cover",
                )

            if len(all_images["backdrops"]) > 0:
                banner = save_image(
                    f"https://image.tmdb.org/t/p/original{all_images['backdrops'][0]['file_path']}",
                    f"{IMAGES_PATH}/{movie_id}_Movie_Banner",
                )
            else:
                banner = save_image(
                    f"https://image.tmdb.org/t/p/original{res['backdrop_path']}",
                    f"{IMAGES_PATH}/{movie_id}_Movie_Banner",
                )

            banner_text = None
            if len(all_images_text["backdrops"]) > 0:
                banner_text = all_images_text["backdrops"][0]["file_path"]

            if len(all_images["logos"]) > 0:
                logo_download_url = f"https://image.tmdb.org/t/p/original{all_images['logos'][0]['file_path']}"
                logo_url = f"{IMAGES_PATH}/{movie_id}_Movie_Logo"
            else:
                all_images = movie.images(movie_id, include_image_language="en")
                if len(all_images["logos"]) > 0:
                    logo_download_url = f"https://image.tmdb.org/t/p/original{all_images['logos'][0]['file_path']}"
                    logo_url = f"{IMAGES_PATH}/{movie_id}_Movie_Logo"

            if logo_download_url is not None:
                logo_url = save_image(logo_download_url, logo_url)

            description = res["overview"]
            note = res["vote_average"]
            try:
                date = res["release_date"]
            except AttributeError:
                date = "Unknown"
            casts = list(details.casts.cast)[:5]
            theCast = []
            for cast in casts:

                actor_id = cast.id
                actorImage = save_image(
                    f"https://www.themovieDB.org/t/p/w600_and_h900_bestv2{cast.profile_path}",
                    f"{IMAGES_PATH}/Actor_{actor_id}",
                )
                image_b64 = generate_b64_image(actorImage, width=300)
                if actor_id not in theCast:
                    theCast.append(actor_id)
                else:
                    break
                person = Person()
                p = person.details(cast.id)
                exists = Actors.query.filter_by(tmdb_id=cast.id).first() is not None
                if not exists:
                    actor = Actors(
                        name=cast.name,
                        image=actorImage,
                        image_b64=image_b64,
                        description=p.biography,
                        birth_date=p.birthday,
                        birth_place=p.place_of_birth,
                        programs=f"{movie_id}",
                        tmdb_id=cast.id
                    )
                    DB.session.add(actor)
                    DB.session.commit()
                else:
                    actor = Actors.query.filter_by(tmdb_id=cast.id).first()
                    actor.programs = f"{actor.programs} {movie_id}"
                    DB.session.commit()
            theCastStr = ",".join([str(i) for i in theCast])
            
            genre = res["genre_ids"]
            length: str
            list_length: list = []
            try:
                list_length = str(
                    datetime.timedelta(seconds=length_video(video_path))
                ).split(":")
            except Exception:
                list_length = []

            if len(list_length) == 3:
                hours = list_length[0]
                minutes = list_length[1]
                seconds = str(round(float(list_length[2])))
                if int(seconds) < 10:
                    seconds = f"0{seconds}"
                length = f"{hours}:{minutes}:{seconds}"
            elif len(list_length) == 2:
                minutes = list_length[0]
                seconds = str(round(float(list_length[1])))
                if int(seconds) < 10:
                    seconds = f"0{seconds}"
                length = f"{minutes}:{seconds}"
            elif len(list_length) == 1:
                seconds = str(round(float(list_length[0])))
                if int(seconds) < 10:
                    seconds = f"0{seconds}"
                length = f"00:{seconds}"
            else:
                length = "0"

            duration = length

            genre_ids = ",".join([str(i) for i in genre])

            bandeAnnonce = details.videos.results
            trailer_url = ""
            if len(bandeAnnonce) > 0:
                for video in bandeAnnonce:
                    bandeAnnonceType = video.type
                    bandeAnnonceHost = video.site
                    bandeAnnonceKey = video.key
                    if bandeAnnonceType == "Trailer":
                        try:
                            trailer_url = (
                                websites_trailers[bandeAnnonceHost] + bandeAnnonceKey
                            )
                            break
                        except KeyError:
                            trailer_url = "Unknown"

            alternatives_names = []
            actualTitle = movieTitle
            characters = [" ", "-", "_", ":", ".", ",", "!", "'", "`", '"']
            empty = ""
            for character in characters:
                for character2 in characters:
                    if character != character2:
                        stringTest = actualTitle.replace(character, character2)
                        alternatives_names.append(stringTest)
                        stringTest = actualTitle.replace(character2, character)
                        alternatives_names.append(stringTest)
                        stringTest = actualTitle.replace(character, empty)
                        alternatives_names.append(stringTest)
                        stringTest = actualTitle.replace(character2, empty)
                        alternatives_names.append(stringTest)

            officialAlternativeNames = movie.alternative_titles(
                movie_id=movie_id
            ).titles
            if officialAlternativeNames is not None:
                for officialAlternativeName in officialAlternativeNames:
                    alternatives_names.append(officialAlternativeName.title)

            alternatives_names = list(dict.fromkeys(alternatives_names))

            filmData = Movies(
                tmdb_id=movie_id,
                title=name,
                cover=cover,
                banner=banner,
                logo=logo_url,
                cover_b64=generate_b64_image(cover, width=300),
                banner_b64=generate_b64_image(banner, height=300),
                logo_b64=generate_b64_image(logo_url, height=300),
                slug=video_path,
                description=description,
                note=note,
                date=date,
                genre=genre_ids,
                duration=str(duration),
                cast=theCastStr,
                trailer_url=trailer_url,
                adult=str(res["adult"]),
                library_name=library_name,
                alternatives_names=",".join(alternatives_names),
                file_date=os.path.getmtime(video_path),
            )
            DB.session.add(filmData)
            DB.session.commit()
            events.execute_event(events.NEW_MOVIE, filmData)


def getSeries(library_name: str) -> None:
    allSeriesPath = Libraries.query.filter_by(name=library_name).first().folder

    if overrides.have_override("scan_serie"):
        return overrides.execute_override("scan_serie", allSeriesPath, library_name)

    if not os.path.exists(allSeriesPath):
        return

    allSeries = os.listdir(allSeriesPath)
    allSeriesName = []
    for dir in allSeries:
        if os.path.isdir(f"{allSeriesPath}/{dir}"):
            allSeriesName.append(f"{allSeriesPath}/{dir}")

    if not is_connected():
        return

    show = TV()
    index = 0
    for serie in allSeriesName:
        index += 1
        if not isinstance(serie, str):
            continue

        seriePath = serie
        serieTitle = serie.split("/")[-1]
        originalSerieTitle = serieTitle

        print_loading(allSeriesName, index, originalSerieTitle)

        try:
            serie_modified_time = os.path.getmtime(seriePath)
        except FileNotFoundError as e:
            log_message = f"File {seriePath} not found: {e}"
            log("ERROR", "SERIE SCAN", log_message)

        serie_guess = guessit(originalSerieTitle)
        if "title" in serie_guess:
            serieTitle = serie_guess["title"]

        if "alternative_title" in serie_guess:
            serieTitle = f"{serieTitle} - {serie_guess['alternative_title']}"

        try:
            if "year" in serie_guess:
                search = Search().tv_shows(serieTitle, release_year=serie_guess["year"])
            else:
                search = Search().tv_shows(serieTitle)
        except TMDbException as e:
            log_message = f"Error while searching serie {serieTitle}: {e}"
            log("ERROR", "SERIE SEARCH", log_message)
            break

        search = search.results
        search = transformToDict(search)

        if search == {}:
            continue

        askForGoodSerie = config["ChocolateSettings"]["askWhichSerie"]
        bestMatch = search[0]
        if askForGoodSerie == "false" or len(search) == 1:
            for i in range(len(search)):
                if (
                    lev(serieTitle, search[i]["name"])
                    < lev(serieTitle, bestMatch["name"])
                    and bestMatch["name"] not in allSeriesName
                ):
                    bestMatch = search[i]
                elif (
                    lev(serieTitle, search[i]["name"])
                    == lev(serieTitle, bestMatch["name"])
                    and bestMatch["name"] not in allSeriesName
                ):
                    bestMatch = bestMatch
                if (
                    lev(serieTitle, bestMatch["name"]) == 0
                    and bestMatch["name"] not in allSeriesName
                ):
                    break

        res = bestMatch
        serie_id = str(res["id"])

        exists = Series.query.filter_by(path=seriePath).first() is not None

        details = show.details(serie_id)
        defaultNbOfSeasons = details.number_of_seasons
        defaultNbOfEpisodes = details.number_of_episodes
        seasonsInfo = details.seasons

        seasonsNumber = []
        seasons = os.listdir(seriePath)
        for seasonFolder in seasons:
            if os.path.isdir(f"{seriePath}/{seasonFolder}") and seasonFolder != "":
                seasonFolder = re.sub(r"\D", "", seasonFolder)
                if seasonFolder == "":
                    continue
                seasonsNumber.append(int(seasonFolder))

        episodes = []
        for seasonFolder in seasons:
            allEpisodes = os.listdir(f"{seriePath}/{seasonFolder}")
            for episode in allEpisodes:
                if os.path.isfile(f"{seriePath}/{seasonFolder}/{episode}"):
                    episodes.append(episode)

        nbEpisodes = len(episodes)
        nbSeasons = len(seasons)

        episodeGroups = show.episode_groups(serie_id).results

        if (
            len(episodeGroups) > 0
            and nbEpisodes > defaultNbOfEpisodes
            and nbSeasons > defaultNbOfSeasons
        ):
            seasonsInfo = None
            groupNbEpisodes = 0
            groupNbSeasons = 0
            for group in episodeGroups:
                groupNbEpisodes = group.episode_count
                groupNbSeasons = group.group_count

                if nbEpisodes >= groupNbEpisodes * 0.95 and nbSeasons == groupNbSeasons:
                    theGroup = Group()
                    seasonsInfo = theGroup.details(group.id).groups
                    for seasonDict in seasonsInfo:
                        season = seasonDict.__dict__
                        if len(season["episodes"]) > 0:
                            season["season_number"] = season["order"]
                            season["episode_count"] = len(season["episodes"])
                            season["air_date"] = season["episodes"][0]["air_date"]
                            season["overview"] = ""
                            season["poster_path"] = season["episodes"][0]["still_path"]
            if seasonsInfo is None:
                for group in episodeGroups:
                    if nbEpisodes <= groupNbEpisodes and nbSeasons <= groupNbSeasons:
                        groupNbEpisodes = group.episode_count
                        groupNbSeasons = group.group_count

                        if (
                            nbEpisodes == groupNbEpisodes
                            and nbSeasons == groupNbSeasons
                        ):
                            theGroup = Group()
                            seasonsInfo = theGroup.details(group.id).groups
                            for season in seasonsInfo:
                                season["season_number"] = season["order"]
                                season["episode_count"] = len(season["episodes"])
                                season["air_date"] = season["episodes"][0]["air_date"]
                                season["overview"] = ""
                                season["poster_path"] = season["episodes"][0][
                                    "still_path"
                                ]
                            break

            if seasonsInfo is None or seasonsInfo == {}:
                group = episodeGroups[0]
                theGroup = Group()
                seasonsInfo = theGroup.details(group.id).groups
                for season in seasonsInfo:
                    season["season_number"] = season["order"]
                    season["episode_count"] = len(season["episodes"])
                    season["air_date"] = season["episodes"][0]["air_date"]
                    season["overview"] = ""
                    season["poster_path"] = season["episodes"][0]["still_path"]

        name = res["name"]
        if not exists:            
            all_images = show.images(serie_id)

            if len(all_images["posters"]) > 0:
                cover = save_image(
                    f"https://image.tmdb.org/t/p/original{all_images['posters'][0]['file_path']}",
                    f"{IMAGES_PATH}/{serie_id}_Serie_Cover",
                )
            else:
                cover = save_image(
                    f"https://image.tmdb.org/t/p/original{res['poster_path']}",
                    f"{IMAGES_PATH}/{serie_id}_Serie_Cover",
                )

            if len(all_images["backdrops"]) > 0:
                banner = save_image(
                    f"https://image.tmdb.org/t/p/original{all_images['backdrops'][0]['file_path']}",
                    f"{IMAGES_PATH}/{serie_id}_Serie_Banner",
                )
            else:
                banner = save_image(
                    f"https://image.tmdb.org/t/p/original{res['backdrop_path']}",
                    f"{IMAGES_PATH}/{serie_id}_Serie_Banner",
                )
            
            logo_download_url = None
            logo_url = None

            if len(all_images["logos"]) > 0:
                logo_download_url = f"https://image.tmdb.org/t/p/original{all_images['logos'][0]['file_path']}"
                logo_url = f"{IMAGES_PATH}/{serie_id}_Serie_Logo"
            else:
                all_images = show.images(serie_id, include_image_language="en")
                if len(all_images["logos"]) > 0:
                    logo_download_url = f"https://image.tmdb.org/t/p/original{all_images['logos'][0]['file_path']}"
                    logo_url = f"{IMAGES_PATH}/{serie_id}_Serie_Logo"

            if logo_download_url is not None:
                logo_url = save_image(logo_download_url, logo_url)

            description = res["overview"]
            note = res["vote_average"]
            date = res["first_air_date"]
            cast = details.credits.cast
            runTime = details.episode_run_time
            duration = ""
            for i in range(len(runTime)):
                if i != len(runTime) - 1:
                    duration += f"{str(runTime[i])}:"
                else:
                    duration += f"{str(runTime[i])}"
            serieGenre = details.genres
            bandeAnnonce = details.videos.results
            trailer_url = ""
            if len(bandeAnnonce) > 0:
                for video in bandeAnnonce:
                    bandeAnnonceType = video.type
                    bandeAnnonceHost = video.site
                    bandeAnnonceKey = video.key
                    if bandeAnnonceType == "Trailer" or len(bandeAnnonce) == 1:
                        try:
                            trailer_url = (
                                websites_trailers[bandeAnnonceHost] + bandeAnnonceKey
                            )
                            break
                        except KeyError as e:
                            log_message = f"Error while getting trailer for serie {serieTitle}: {e}"
                            log("ERROR", "SERIE SCAN", log_message)
                            trailer_url = "Unknown"

            genre_list = ",".join([str(i["id"]) for i in serieGenre])
            newCast = []
            cast = list(cast)[:5]
            for actor in cast:
                actor_id = actor.id
                actorImage = save_image(
                    f"https://image.tmdb.org/t/p/original{actor.profile_path}",
                    f"{IMAGES_PATH}/Actor_{actor_id}",
                )
                actor.profile_path = str(actorImage)
                newCast.append(actor_id)

                person = Person()
                p = person.details(actor.id)
                exists = Actors.query.filter_by(id=actor.id).first() is not None
                if not exists:
                    actor = Actors(
                        name=actor.name,
                        id=actor.id,
                        image=actorImage,
                        description=p.biography,
                        birth_date=p.birthday,
                        birth_place=p.place_of_birth,
                        programs=f"{serie_id}",
                    )
                    DB.session.add(actor)
                    DB.session.commit()
                else:
                    actor = Actors.query.filter_by(id=actor.id).first()
                    if serie_id not in actor.programs:
                        actor.programs = f"{actor.programs} {serie_id}"
                    DB.session.commit()

            newCast = newCast[:5]
            cast = ",".join([str(i) for i in newCast])
            isAdult = str(details["adult"])
            serieObject = Series(
                tmdb_id=serie_id,
                title=name,
                genre=genre_list,
                duration=duration,
                description=description,
                cast=cast,
                trailer_url=trailer_url,
                cover=cover,
                banner=banner,
                logo=logo_url,
                cover_b64=generate_b64_image(cover, width=300),
                banner_b64=generate_b64_image(banner, height=300),
                logo_b64=generate_b64_image(logo_url, height=300),
                note=note,
                date=date,
                serie_modified_time=serie_modified_time,
                adult=isAdult,
                library_name=library_name,
                path=seriePath,
            )
            DB.session.add(serieObject)
            DB.session.commit()
            events.execute_event(events.NEW_SERIE, serieObject)

        for season in seasonsInfo:
            season = transformToDict(season)
            allSeasons = os.listdir(seriePath)
            url = None
            for season_dir in allSeasons:
                season_dir_number = re.sub(r"\D", "", season_dir)
                if season_dir_number != "" and int(season_dir_number) == int(
                    season["season_number"]
                ):
                    url = f"{seriePath}/{season_dir}"
                    break
            if not url:
                # print(f"\nCan't find {serieTitle} season {season['season_number']}")
                continue
            season_dir = url
            # print(f"\nSeason {season['season_number']} of {serieTitle} found: {season_dir}")
            seasonInDB = Seasons.query.filter_by(tmdb_id=season["id"]).first()
            if seasonInDB:
                modified_date = seasonInDB.modified_date
                try:
                    actualSeasonModifiedTime = os.path.getmtime(url)
                except FileNotFoundError as e:
                    log_message = f"File {url} not found: {e}"
                    log("ERROR", "SERIE SCAN", log_message)
            if seasonInDB is None or modified_date != actualSeasonModifiedTime:
                try:
                    allEpisodes = [
                        f
                        for f in os.listdir(season_dir)
                        if os.path.isfile(path_join(season_dir, f))
                    ]
                except FileNotFoundError as e:
                    log_message = f"File {season_dir} not found: {e}"
                    log("ERROR", "SERIE SCAN", log_message)

                if seasonInDB:
                    seasonInDB.modified_date = modified_date
                    DB.session.commit()
                bigSeason = season
                releaseDate = season["air_date"]
                episodes_number = season["episode_count"]
                season_number = season["season_number"]
                season_id = season["id"]
                season_name = season["name"]
                season_description = season["overview"]
                seasonPoster = season["poster_path"]

                try:
                    seasonModifiedTime = os.path.getmtime(season_dir)
                    savedModifiedTime = (
                        Seasons.query.filter_by(tmdb_id=season_id)
                        .first()
                        .seasonModifiedTime
                    )
                except AttributeError:
                    seasonModifiedTime = os.path.getmtime(season_dir)

                if len(allEpisodes) > 0 or (seasonModifiedTime != savedModifiedTime):
                    try:
                        exists = (
                            Seasons.query.filter_by(tmdb_id=season_id).first()
                            is not None
                        )
                    except sqlalchemy.exc.PendingRollbackError:
                        DB.session.rollback()
                        exists = (
                            Seasons.query.filter_by(tmdb_id=season_id).first()
                            is not None
                        )
                    # number of episodes in the season
                    savedModifiedTime = 0
                    if not exists or (seasonModifiedTime != savedModifiedTime):
                        season_cover_path = save_image(
                            f"https://image.tmdb.org/t/p/original{seasonPoster}",
                            f"{IMAGES_PATH}/{season_id}_Cover",
                        )

                        allSeasons = os.listdir(seriePath)

                        try:
                            modified_date = os.path.getmtime(season_dir)
                        except FileNotFoundError:
                            modified_date = 0

                    allEpisodesInDB = Episodes.query.filter_by(
                        season_id=season_id
                    ).all()
                    allEpisodesInDB = [
                        episode.title for episode in allEpisodesInDB
                    ]

                    exists = (
                        Seasons.query.filter_by(tmdb_id=season_id).first() is not None
                    )
                    if not exists:
                        thisSeason = Seasons(
                            tmdb_id=season_id,
                            serie_id=serie_id,
                            release=releaseDate,
                            episodes_number=episodes_number,
                            number=season_number,
                            title=season_name,
                            description=season_description,
                            cover=season_cover_path,
                            modified_date=modified_date,
                            number_of_episode_in_folder=len(allEpisodes),
                        )

                        try:
                            DB.session.add(thisSeason)
                            DB.session.commit()
                        except sqlalchemy.exc.PendingRollbackError:
                            DB.session.rollback()
                            DB.session.add(thisSeason)
                            DB.session.commit()
                        events.execute_event(events.NEW_SEASON, thisSeason)
                    if len(allEpisodes) != len(allEpisodesInDB):
                        for episode in allEpisodes:
                            slug = f"{season_dir}/{episode}"
                            episodeName = slug.split("/")[-1]
                            guess = guessit(episodeName)
                            if "episode" in guess:
                                episodeIndex = guess["episode"]
                            elif "episode_title" in guess:
                                episodeIndex = guess["episode_title"]
                            elif (
                                "season" in guess
                                and isinstance(guess["season"], list)
                                and len(guess["season"]) == 2
                            ):
                                episodeIndex = guess["season"][1]
                            elif "season" in guess:
                                episodeIndex = guess["season"]
                            elif "title" in guess:
                                episodeIndex = guess["title"]
                            else:
                                print(
                                    f"Can't find the episode index of {episodeName}, data: {guess}, slug: {slug}"
                                )
                                continue

                            if isinstance(episodeIndex, list):
                                for i in range(len(episodeIndex)):
                                    if isinstance(episodeIndex[i], int):
                                        episodeIndex[i] = str(episodeIndex[i])
                                episodeIndex = "".join(episodeIndex)

                            if (
                                not isinstance(episodeIndex, int)
                                and not episodeIndex.isnumeric()
                            ):
                                print(f"Episode index {episodeIndex} is not a number")
                                log(
                                    "ERROR",
                                    "SERIE SCAN",
                                    f"Episode index {episodeIndex} is not a number",
                                )
                                continue

                            exists = (
                                Episodes.query.filter_by(
                                    number=int(episodeIndex),
                                    season_id=season_id,
                                ).first()
                                is not None
                            )

                            if not exists:
                                # print(f"Episode {episodeIndex} of {serieTitle} for the Season {season_id} not found")
                                if isinstance(season_id, int) or season_id.isnumeric():
                                    showEpisode = Episode()
                                    # print(f"Get episodeInfo of : E{episodeIndex} S{season_number} of {serieTitle}")
                                    try:
                                        episodeDetails = showEpisode.details(
                                            serie_id, season_number, episodeIndex
                                        )
                                    except TMDbException as e:
                                        log_message = f"Error while getting episode {episodeIndex} of season {season_number} of serie {serieTitle}: {e}"
                                        log("ERROR", "SERIE SCAN", log_message)
                                        continue
                                    realEpisodeName = episodeDetails.name
                                    episodeInfo = showEpisode.details(
                                        serie_id, season_number, episodeIndex
                                    )
                                    episode_id = episodeInfo["id"]
                                else:
                                    episodeInfo = bigSeason["episodes"][
                                        int(episodeIndex) - 1
                                    ]
                                    episode_id = episodeInfo["id"]
                                    realEpisodeName = episodeInfo["name"]

                                coverEpisode = save_image(
                                    f"https://image.tmdb.org/t/p/original{episodeInfo['still_path']}",
                                    f"{IMAGES_PATH}/{season_id}_{episode_id}_Episode_Banner",
                                )

                                try:
                                    exists = (
                                        Episodes.query.filter_by(
                                            tmdb_id=episode_id
                                        ).first()
                                        is not None
                                    )
                                except sqlalchemy.exc.PendingRollbackError:
                                    DB.session.rollback()
                                    exists = (
                                        Episodes.query.filter_by(
                                            tmdb_id=episode_id
                                        ).first()
                                        is not None
                                    )
                                if not exists:
                                    episodeData = Episodes(
                                        serie_id = serie_id,
                                        tmdb_id=episode_id,
                                        title=realEpisodeName,
                                        season_id=season_id,
                                        number=episodeIndex,
                                        description=episodeInfo["overview"],
                                        cover_path=coverEpisode,
                                        cover_b64=generate_b64_image(coverEpisode, width=300),
                                        release_date=episodeInfo["air_date"],
                                        slug=slug,
                                    )
                                    thisSeason = Seasons.query.filter_by(
                                        tmdb_id=season_id
                                    ).first()
                                    thisSeason.number_of_episode_in_folder += 1
                                    try:
                                        DB.session.add(episodeData)
                                        DB.session.commit()
                                    except Exception:
                                        DB.session.rollback()
                                        DB.session.add(episodeData)
                                        DB.session.commit()
                                    events.execute_event(
                                        events.NEW_EPISODE, episodeData
                                    )
                        else:
                            pass

    allFiles = [
        name
        for name in os.listdir(allSeriesPath)
        if os.path.isfile(path_join(allSeriesPath, name)) and is_video_file(name)
    ]
    index = 0
    for file in allFiles:
        index += 1
        print_loading(allFiles, index, file)

        slug = path_join(allSeriesPath, file)
        exists = Episodes.query.filter_by(slug=slug).first() is not None
        if not exists:
            guess = guessit(file)
            # print(f"\n {guess}")
            title = guess["title"]
            if "episode" not in guess:
                season = guess["season"]
                if isinstance(guess["season"], list):
                    season, episode = guess["season"]
                else:
                    season = guess["season"]
                    episode = str(int(guess["episode_title"]))
            else:
                season = guess["season"]
                episode = guess["episode"]

            seasonIndex = season
            originalFile = file
            episodeIndex = episode
            originalSerieTitle = title
            serie_modified_time = 0
            series = TV()
            show = Search().tv_shows(title)
            res = show[0]
            serie = res.name
            serie_id = res.id
            details = series.details(serie_id)
            episodeGroups = series.episode_groups(serie_id).results
            serieEpisodes = []
            serieSeasons = []

            for file in allFiles:
                guess = guessit(file)
                serie = guess["title"]
                season = guess["season"]
                if isinstance(season, list):
                    season, episode = guess["season"]
                season = int(season)
                if serie == originalSerieTitle:
                    serieEpisodes.append(file)
                    if season not in serieSeasons:
                        serieSeasons.append(season)

            file = originalFile

            defaultNbOfSeasons = details.number_of_seasons
            defaultNbOfEpisodes = details.number_of_episodes

            nbSeasons = len(serieSeasons)
            nbEpisodes = len(serieEpisodes)

            season_api = None
            season_id = None

            if nbEpisodes <= defaultNbOfEpisodes and nbSeasons <= defaultNbOfSeasons:
                for seasontmdb in details.seasons:
                    if str(seasontmdb.season_number) == str(seasonIndex):
                        season_id = seasontmdb.id
                        season_api = seasontmdb
                        break
            elif len(episodeGroups) > 0:
                for group in episodeGroups:
                    groupNbEpisodes = group.episode_count
                    groupNbSeasons = group.group_count
                    if nbEpisodes <= groupNbEpisodes and nbSeasons <= groupNbSeasons:
                        theGroup = Group()
                        seasonsInfo = theGroup.details(group.id).groups
                        for season in seasonsInfo:
                            season["season_number"] = season["order"]
                            season["episode_count"] = len(season["episodes"])
                            season["air_date"] = season["episodes"][0]["air_date"]
                            season["overview"] = ""
                            season["poster_path"] = season["episodes"][0]["still_path"]

                        season_api = seasonsInfo[seasonIndex - 1]
                        season_id = season_api["id"]
            else:
                for seasontmdb in details.seasons:
                    if str(seasontmdb.season_number) == str(seasonIndex):
                        season_id = seasontmdb.id
                        season_api = seasontmdb
                        break

            serieExists = Series.query.filter_by(tmdb_id=serie_id).first() is not None
            if not serieExists:
                name = res.name

                all_images = series.images(serie_id, "null")

                if len(all_images["posters"]) > 0:
                    cover = save_image(
                        f"https://image.tmdb.org/t/p/original{all_images['posters'][0]['file_path']}",
                        f"{IMAGES_PATH}/{serie_id}_Serie_Cover",
                    )
                else:
                    cover = save_image(
                        f"https://image.tmdb.org/t/p/original{res['poster_path']}",
                        f"{IMAGES_PATH}/{serie_id}_Serie_Cover",
                    )

                if len(all_images["backdrops"]) > 0:
                    banner = save_image(
                        f"https://image.tmdb.org/t/p/original{all_images['backdrops'][0]['file_path']}",
                        f"{IMAGES_PATH}/{serie_id}_Serie_Banner",
                    )
                else:
                    banner = save_image(
                        f"https://image.tmdb.org/t/p/original{res['backdrop_path']}",
                        f"{IMAGES_PATH}/{serie_id}_Serie_Banner",
                    )

                
                logo_download_url = None
                logo_url = None

                if len(all_images["logos"]) > 0:
                    logo_download_url = f"https://image.tmdb.org/t/p/original{all_images['logos'][0]['file_path']}"
                    logo_url = f"{IMAGES_PATH}/{serie_id}_Serie_Logo"
                else:
                    all_images = series.images(serie_id, include_image_language="en")
                    if len(all_images["logos"]) > 0:
                        logo_download_url = f"https://image.tmdb.org/t/p/original{all_images['logos'][0]['file_path']}"
                        logo_url = f"{IMAGES_PATH}/{serie_id}_Serie_Logo"

                if logo_download_url is not None:
                    logo_url = save_image(logo_download_url, logo_url)

                description = res["overview"]
                note = res.vote_average
                date = res.first_air_date
                cast = details.credits.cast
                runTime = details.episode_run_time
                duration = ""
                for i in range(len(runTime)):
                    if i != len(runTime) - 1:
                        duration += f"{str(runTime[i])}:"
                    else:
                        duration += f"{str(runTime[i])}"
                serieGenre = details.genres
                bandeAnnonce = details.videos.results
                trailer_url = ""
                if len(bandeAnnonce) > 0:
                    for video in bandeAnnonce:
                        bandeAnnonceType = video.type
                        bandeAnnonceHost = video.site
                        bandeAnnonceKey = video.key
                        if bandeAnnonceType == "Trailer" or len(bandeAnnonce) == 1:
                            try:
                                trailer_url = (
                                    websites_trailers[bandeAnnonceHost]
                                    + bandeAnnonceKey
                                )
                                break
                            except KeyError:
                                trailer_url = "Unknown"

                genre_list = ",".join([str(i["id"]) for i in serieGenre])
                newCast = []
                cast = list(cast)[:5]
                for actor in cast:
                    actor_id = actor.id
                    actorImage = save_image(
                        f"https://image.tmdb.org/t/p/original{actor.profile_path}",
                        f"{IMAGES_PATH}/Actor_{actor_id}",
                    )
                    actor.profile_path = str(actorImage)
                    thisActor = actor_id
                    newCast.append(thisActor)

                    person = Person()
                    p = person.details(actor.id)
                    exists = (
                        Actors.query.filter_by(id=actor.id).first() is not None
                    )
                    if not exists:
                        actor = Actors(
                            name=actor.name,
                            id=actor.id,
                            image=actorImage,
                            description=p.biography,
                            birth_date=p.birthday,
                            birth_place=p.place_of_birth,
                            programs=f"{serie_id}",
                        )
                        DB.session.add(actor)
                        DB.session.commit()
                    else:
                        actor = Actors.query.filter_by(id=actor.id).first()
                        actor.programs = f"{actor.programs} {serie_id}"
                        DB.session.commit()

                newCast = newCast[:5]
                cast = ",".join([str(i) for i in newCast])
                isAdult = str(details["adult"])
                serieObject = Series(
                    tmdb_id=serie_id,
                    title=name,
                    path=allSeriesPath,
                    genre=genre_list,
                    duration=duration,
                    description=description,
                    cast=cast,
                    trailer_url=trailer_url,
                    cover=cover,
                    banner=banner,
                    logo=logo_url,
                    cover_b64=generate_b64_image(cover, width=300),
                    banner_b64=generate_b64_image(banner, height=300),
                    logo_b64=generate_b64_image(logo_url, height=300),
                    note=note,
                    date=date,
                    serie_modified_time=serie_modified_time,
                    adult=isAdult,
                    library_name=library_name,
                )
                DB.session.add(serieObject)
                DB.session.commit()
                events.execute_event(events.NEW_SERIE, serieObject)

            # print(f"Pour {file}, serie_id = {serie_id} et season_id = {season_id}")

            seasonExists = (
                Seasons.query.filter_by(serie_id=serie_id, tmdb_id=season_id).first()
                is not None
            )

            if season_api and not seasonExists:
                season = season_api
                releaseDate = season.air_date
                episodes_number = season.episode_count
                season_number = season.season_number
                season_name = season.name
                season_description = season.overview
                seasonPoster = season.poster_path

                savedModifiedTime = 0

                season_cover_path = save_image(
                    "https://image.tmdb.org/t/p/original{seasonPoster}",
                    f"{IMAGES_PATH}/{season_id}_Cover",
                )

                try:
                    modified_date = os.path.getmtime(f"{allSeriesPath}{slug}")
                except Exception:
                    modified_date = 0

                seasonObject = Seasons(
                    serie_id=serie_id,
                    tmdb_id=season_id,
                    title=season_name,
                    description=season_description,
                    cover=season_cover_path,
                    number=season_number,
                    episodes_number=episodes_number,
                    release=releaseDate,
                    modified_date=modified_date,
                    number_of_episode_in_folder=0,
                )

                DB.session.add(seasonObject)
                DB.session.commit()
                events.execute_event(events.NEW_SEASON, seasonObject)

            bigSeason = season_api

            showEpisode = Episode()
            season_number = seasonIndex
            serie_id, season_number, episodeIndex = (
                str(serie_id),
                str(season_number),
                str(episodeIndex),
            )

            try:
                exists = (
                    Episodes.query.filter_by(
                        number=episodeIndex, season_id=season_id
                    ).first()
                    is not None
                )
            except sqlalchemy.exc.PendingRollbackError:
                DB.session.rollback()
                exists = (
                    Episodes.query.filter_by(
                        number=episodeIndex, season_id=season_id
                    ).first()
                    is not None
                )
            if not exists:
                if season_id and (isinstance(season_id, int) or season_id.isnumeric()):
                    showEpisode = Episode()
                    episodeDetails = showEpisode.details(
                        serie_id, season_number, episodeIndex
                    )
                    realEpisodeName = episodeDetails.name
                    episodeInfo = showEpisode.details(
                        serie_id, season_number, episodeIndex
                    )
                    episode_id = episodeInfo.id
                elif bigSeason is not None:
                    episodeInfo = bigSeason["episodes"][int(episodeIndex) - 1]
                    episode_id = episodeInfo["id"]
                    realEpisodeName = episodeInfo["name"]

                coverEpisode = save_image(
                    f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}",
                    f"{IMAGES_PATH}/{season_id}_{episode_id}_Episode_Banner",
                )

                try:
                    exists = (
                        Episodes.query.filter_by(tmdb_id=episode_id).first()
                        is not None
                    )
                except sqlalchemy.exc.PendingRollbackError:
                    DB.session.rollback()
                    exists = (
                        Episodes.query.filter_by(tmdb_id=episode_id).first()
                        is not None
                    )
                if not exists:
                    # Mprint(f"Pour le fichier {file}, j'ai trouvé : \n  -  episode_number: {episodeIndex} \n  -  season_id: {season_id} \n  -  Serie: {serie_id} \n  -  Episode ID: {episode_id}")

                    episodeData = Episodes(
                        tmdb_id=episode_id,
                        serie_id=serie_id,
                        title=realEpisodeName,
                        season_id=season_id,
                        number=episodeIndex,
                        description=episodeInfo.overview,
                        cover_path=coverEpisode,
                        cover_b64=generate_b64_image(coverEpisode, width=300),
                        release_date=episodeInfo.air_date,
                        slug=slug,
                    )
                    thisSeason = Seasons.query.filter_by(tmdb_id=season_id).first()
                    thisSeason.number_of_episode_in_folder += 1
                    try:
                        DB.session.add(episodeData)
                        DB.session.commit()
                    except Exception:
                        DB.session.rollback()
                        DB.session.add(episodeData)
                        DB.session.commit()
                    events.execute_event(events.NEW_EPISODE, episodeData)

    allSeriesInDB = Series.query.all()
    allSeriesInDB = [
        serie.path
        for serie in allSeriesInDB
        if serie.library_name == library_name
    ]

    for serie in allSeriesInDB:
        if serie == allSeriesPath:
            continue 
        serie_id = Series.query.filter_by(path=serie).first().tmdb_id
        allSeasons = Seasons.query.filter_by(serie_id=serie_id).all()
        if serie not in allSeriesName:
            for season in allSeasons:
                season_id = season.id
                allEpisodes = Episodes.query.filter_by(id=season_id).all()
                for episode_data in allEpisodes:
                    if not os.path.exists(episode_data.slug):
                        try:
                            DB.session.delete(episode_data)
                            DB.session.commit()
                        except Exception:
                            DB.session.rollback()
                            DB.session.delete(episode_data)
                            DB.session.commit()

        for season in allSeasons:
            season_id = season.tmdb_id
            allEpisodes = Episodes.query.filter_by(season_id=season_id).all()
            if len(allEpisodes) == 0:
                try:
                    DB.session.delete(season)
                    DB.session.commit()
                except Exception:
                    DB.session.rollback()
                    DB.session.delete(season)
                    DB.session.commit()
        allSeasons = Seasons.query.filter_by(serie_id=serie_id).all()
        if len(allSeasons) == 0:
            try:
                DB.session.delete(Series.query.filter_by(tmdb_id=serie_id).first())
                DB.session.commit()
            except Exception:
                DB.session.rollback()
                DB.session.delete(Series.query.filter_by(tmdb_id=serie_id).first())
                DB.session.commit()


def getGames(library_name: str) -> None:
    allGamesPath = Libraries.query.filter_by(name=library_name).first().folder

    if overrides.have_override("scan_game"):
        return overrides.execute_override("scan_game", allGamesPath, library_name)

    try:
        allConsoles = [
            name
            for name in os.listdir(allGamesPath)
            if os.path.isdir(path_join(allGamesPath, name)) and is_video_file(name)
        ]
    except Exception as e:
        log_message = f"Error while getting games in {allGamesPath} : {e}"
        log("ERROR", "GAME SCAN", log_message)
        return

    for console in allConsoles:
        if os.listdir(f"{allGamesPath}/{console}") == []:
            allConsoles.remove(console)
    saidPS1 = False
    supportedConsoles = [
        "3DO",
        "Amiga",
        "Atari 2600",
        "Atari 5200",
        "Atari 7800",
        "Atari Jaguar",
        "Atari Lynx",
        "GB",
        "GBA",
        "GBC",
        "N64",
        "NDS",
        "NES",
        "SNES",
        "Neo Geo Pocket",
        "PSX",
        "Sega 32X",
        "Sega CD",
        "Sega Game Gear",
        "Sega Master System",
        "Sega Mega Drive",
        "Sega Saturn",
        "PS1",
    ]
    supportedFileTypes = [
        ".zip",
        ".adf",
        ".adz",
        ".dms",
        ".fdi",
        ".ipf",
        ".hdf",
        ".lha",
        ".slave",
        ".info",
        ".cdd",
        ".nrg",
        ".mds",
        ".chd",
        ".uae",
        ".m3u",
        ".a26",
        ".a52",
        ".a78",
        ".j64",
        ".lnx",
        ".gb",
        ".gba",
        ".gbc",
        ".n64",
        ".nds",
        ".nes",
        ".ngp",
        ".psx",
        ".sfc",
        ".smc",
        ".smd",
        ".32x",
        ".cd",
        ".gg",
        ".md",
        ".sat",
        ".sms",
    ]
    index = 0
    for console in allConsoles:
        index += 1
        if console not in supportedConsoles:
            print(
                f"{console} is not supported or the console name is not correct, here is the list of supported consoles: \n{', '.join(supportedConsoles)} rename the folder to one of these names if it's the correct console"
            )
            break

        print_loading(allConsoles, index, console)

        allFiles = os.listdir(f"{allGamesPath}/{console}")
        index = 0
        for file in allFiles:
            index += 1
            # get all games in the db
            allGamesInDB = Games.query.filter_by(
                library_name=library_name, console=console
            ).all()
            allGamesInDB = [game.slug for game in allGamesInDB]
            numberOfGamesInDB = len(allGamesInDB)
            numberOfGamesInFolder = len(allFiles)
            if numberOfGamesInDB < numberOfGamesInFolder:
                gameSlug = f"{allGamesPath}/{console}/{file}"
                exists = Games.query.filter_by(slug=gameSlug).first() is not None
                if file.endswith(tuple(supportedFileTypes)) and not exists:
                    newFileName = file
                    newFileName = re.sub(r"\d{5} - ", "", newFileName)
                    newFileName = re.sub(r"\d{4} - ", "", newFileName)
                    newFileName = re.sub(r"\d{3} - ", "", newFileName)
                    newFileName, extension = os.path.splitext(newFileName)
                    newFileName = newFileName.rstrip()
                    newFileName = f"{newFileName}{extension}"
                    os.rename(
                        f"{allGamesPath}/{console}/{file}",
                        f"{allGamesPath}/{console}/{newFileName}",
                    )

                    print_loading(allFiles, index, newFileName)

                    file = newFileName

                    file, extension = os.path.splitext(file)

                    gameIGDB = searchGame(file, console)

                    if gameIGDB is not None and gameIGDB != {} and not exists:
                        gameName = gameIGDB["title"]
                        gameCover = gameIGDB["cover"]
                        gameDescription = gameIGDB["description"]
                        gameNote = gameIGDB["note"]
                        gameDate = gameIGDB["date"]
                        gameGenre = gameIGDB["genre"]
                        game_id = gameIGDB["id"]
                    else:
                        gameName = file
                        gameCover = "/static/img/broken.webp"
                        gameDescription = ""
                        gameNote = 0
                        gameDate = ""
                        gameGenre = ""
                        game_id = str(uuid.uuid4())

                    gameRealTitle = newFileName
                    gameConsole = console

                    game = Games(
                        console=gameConsole,
                        id=game_id,
                        title=gameName,
                        real_title=gameRealTitle,
                        cover=gameCover,
                        description=gameDescription,
                        note=gameNote,
                        date=gameDate,
                        genre=gameGenre,
                        slug=gameSlug,
                        library_name=library_name,
                    )
                    DB.session.add(game)
                    DB.session.commit()

                    events.execute_event(events.NEW_GAME, game)

                elif console == "PS1" and file.endswith(".cue") and not exists:
                    if not saidPS1:
                        print(
                            "You need to zip all our .bin files and the .cue file in one .zip file to being able to play it"
                        )
                        saidPS1 = True

                    value = config["ChocolateSettings"]["compressPS1Games"]
                    if value.lower() == "true":
                        index = allFiles.index(file) - 1

                        allBins = []
                        while allFiles[index].endswith(".bin"):
                            allBins.append(allFiles[index])
                            index -= 1

                        fileName, extension = os.path.splitext(file)
                        with zipfile.ZipFile(
                            f"{allGamesPath}/{console}/{fileName}.zip", "w"
                        ) as zipObj:
                            for binFiles in allBins:
                                zipObj.write(
                                    f"{allGamesPath}/{console}/{binFiles}", binFiles
                                )
                            zipObj.write(f"{allGamesPath}/{console}/{file}", file)
                        for binFiles in allBins:
                            os.remove(f"{allGamesPath}/{console}/{binFiles}")
                        os.remove(f"{allGamesPath}/{console}/{file}")
                        file = f"{fileName}.zip"
                        newFileName = file
                        newFileName = re.sub(r"\d{5} - ", "", newFileName)
                        newFileName = re.sub(r"\d{4} - ", "", newFileName)
                        newFileName = re.sub(r"\d{3} - ", "", newFileName)
                        newFileName, extension = os.path.splitext(newFileName)
                        newFileName = newFileName.rstrip()
                        newFileName = f"{newFileName}{extension}"
                        os.rename(
                            f"{allGamesPath}/{console}/{file}",
                            f"{allGamesPath}/{console}/{newFileName}",
                        )
                        file = newFileName
                        while ".." in newFileName:
                            newFileName = newFileName.replace("..", ".")
                        try:
                            os.rename(
                                f"{allGamesPath}/{console}/{file}",
                                f"{allGamesPath}/{console}/{newFileName}",
                            )
                        except FileExistsError:
                            os.remove(f"{allGamesPath}/{console}/{file}")
                        file, extension = os.path.splitext(file)

                        gameIGDB = searchGame(file, console)
                        if gameIGDB is not None and gameIGDB != {}:
                            gameName = gameIGDB["title"]
                            gameRealTitle = newFileName
                            gameCover = gameIGDB["cover"]
                            gameCover = save_image(
                                gameCover, f"{IMAGES_PATH}/{console}_{gameRealTitle}"
                            )

                            gameDescription = gameIGDB["description"]
                            gameNote = gameIGDB["note"]
                            gameDate = gameIGDB["date"]
                            gameGenre = gameIGDB["genre"]
                            game_id = gameIGDB["id"]
                            gameConsole = console
                            gameSlug = f"{allGamesPath}/{console}/{newFileName}"
                            game = Games.query.filter_by(slug=gameSlug).first()
                            print(game)
                            if not game:
                                game = Games(
                                    console=gameConsole,
                                    id=game_id,
                                    title=gameName,
                                    real_title=gameRealTitle,
                                    cover=gameCover,
                                    description=gameDescription,
                                    note=gameNote,
                                    date=gameDate,
                                    genre=gameGenre,
                                    slug=gameSlug,
                                )
                                DB.session.add(game)
                                DB.session.commit()

                                events.execute_event(events.NEW_GAME, game)
                elif not file.endswith(".bin") and not exists:
                    print(
                        f"{file} is not supported, here's the list of supported files : \n{','.join(supportedFileTypes)}"
                    )
        gamesInDb = Games.query.filter_by(console=console).all()
        gamesInDb = [game.real_title for game in gamesInDb]
        for game in gamesInDb:
            if game not in allFiles:
                game = Games.query.filter_by(console=console, real_title=game).first()
                DB.session.delete(game)
                DB.session.commit()


def getOthersVideos(library: str, allVideosPath: str | None = None) -> None:
    if not allVideosPath:
        allVideosPath = Libraries.query.filter_by(name=library).first().folder
        try:
            allVideos = os.listdir(allVideosPath)
        except Exception as e:
            log_message = f"Error while getting others videos in {allVideosPath} : {e}"
            log("ERROR", "OTHER SCAN", log_message)
            return
    else:
        allVideos = os.listdir(allVideosPath)

    allDirectories = [
        video for video in allVideos if os.path.isdir(f"{allVideosPath}/{video}")
    ]
    allVideos = [video for video in allVideos if is_video_file(video)]

    for directory in allDirectories:
        directoryPath = f"{allVideosPath}/{directory}"
        getOthersVideos(library, directoryPath)
    index = 0
    for video in allVideos:
        index += 1
        title, extension = os.path.splitext(video)

        print_loading(allVideos, index, title)

        slug = f"{allVideosPath}/{video}"
        exists = OthersVideos.query.filter_by(slug=slug).first() is not None
        if not exists:
            with open(slug, "rb") as f:
                video_hash = zlib.crc32(f.read())

            # Conversion du hash en chaîne hexadécimale
            video_hash_hex = hex(video_hash)[2:]

            # Récupération des 10 premiers caractères
            hash = video_hash_hex[:10]
            videoDuration = length_video(slug)
            middle = videoDuration // 2
            banner = f"{IMAGES_PATH}/Other_Banner_{library}_{hash}.webp"
            command = [
                "ffmpeg",
                "-i",
                slug,
                "-vf",
                f"select='eq(n,{middle})'",
                "-vframes",
                "1",
                f"{banner}",
                "-y",
            ]
            try:
                subprocess.run(
                    command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                if os.path.getsize(f"{banner}") == 0:
                    generateImage(title, library, f"{banner}")
                banner = f"{IMAGES_PATH}/Other_Banner_{library}_{hash}.webp"
            except Exception:
                banner = "/static/img/broken.webp"
            video = OthersVideos(
                title=title,
                slug=slug,
                banner=banner,
                duration=videoDuration,
                library_name=library,
            )
            DB.session.add(video)
            DB.session.commit()

    for videoObj in OthersVideos.query.filter_by(library_name=library).all():
        path = videoObj.slug
        if not os.path.exists(path):
            DB.session.delete(video)
            DB.session.commit()


def getMusics(library: str) -> None:
    allMusicsPath = Libraries.query.filter_by(name=library).first().folder

    if overrides.have_override("scan_music"):
        return overrides.execute_override("scan_music", allMusicsPath, library)

    allMusics = os.listdir(allMusicsPath)

    allArtists = [
        music for music in allMusics if os.path.isdir(f"{allMusicsPath}/{music}")
    ]

    for artist in allArtists:
        filesAndDirs = os.listdir(f"{allMusicsPath}/{artist}")
        allAlbums = [
            dire
            for dire in filesAndDirs
            if os.path.isdir(f"{allMusicsPath}/{artist}/{dire}")
        ]
        allFiles = [
            file
            for file in filesAndDirs
            if os.path.isfile(f"{allMusicsPath}/{artist}/{file}")
            and is_music_file(file)
        ]
        artist_id = createArtist(artist, library)
        artistName = artist
        albumsInDB = Albums.query.filter_by(artist_id=artist_id).all()
        tracksInDB = Tracks.query.filter_by(artist_id=artist_id).all()
        albumsInDB = len([album for album in albumsInDB])
        tracksInDB = len([track for track in tracksInDB])
        if albumsInDB == len(allAlbums) and tracksInDB == len(allFiles):
            continue

        startPath = f"{allMusicsPath}/{artist}"
        index = 0
        for album in allAlbums:
            index += 1
            albumGuessedData = guessit(album)
            if "title" in albumGuessedData:
                albumName = albumGuessedData["title"]
            else:
                albumName, extension = os.path.splitext(album)

            allTracks = os.listdir(f"{startPath}/{album}")
            allTracks = [track for track in allTracks if is_music_file(track)]
            try:
                album_data = createAlbum(albumName, artist_id, allTracks, library)
            except deezer_main.exceptions.DeezerErrorResponse as e:
                continue

            album_id = album_data.id

            for track in allTracks:
                slug = f"{startPath}/{album}/{track}"

                exists = Tracks.query.filter_by(slug=slug).first() is not None
                if exists:
                    continue

                title, extension = os.path.splitext(track)
                print_loading(allTracks, index, title)

                tags = TinyTag.get(slug, image=True)

                image = tags.get_image()
                imagePath = f"{IMAGES_PATH}/Album_{album_id}.webp"
                if image is not None:
                    if not os.path.exists(imagePath):
                        img = Image.open(io.BytesIO(image))
                        img.save(imagePath, "webp")
                        img.close()
                elif not os.path.exists(imagePath):
                    getAlbumImage(album, imagePath)

                if tags.title is not None and tags.title != "" and tags.title != " ":
                    title = tags.title
                else:
                    guessedData = guessit(title)

                    title = ""

                    if "title" in guessedData:
                        title = guessedData["title"]
                        if title.isdigit():
                            title = guessedData["alternative_title"]
                    else:
                        if isinstance("episode", list) and "season" in guessedData:
                            title = f"{guessedData['season']}{' '.join(guessedData['episode'][1])}"
                        elif "episode" in guessedData and "season" in guessedData:
                            title = f"{guessedData['season']}{guessedData['episode']}"

                    if "release_group" in guessedData:
                        title += f" ({guessedData['release_group']}"

                imagePath = imagePath.replace(dir_path, "")

                track = Tracks(
                    name=title,
                    slug=slug,
                    album_id=album_id,
                    artist_id=artist_id,
                    duration=tags.duration,
                    cover=imagePath,
                    cover_b64=generate_b64_image(imagePath, width=300),
                    library_name=library,
                    file_date=os.path.getmtime(slug),
                    release_date=album_data.release_date,
                )
                DB.session.add(track)
                DB.session.commit()
                events.execute_event(events.NEW_TRACK, track)
        index = 0
        for track in allFiles:
            index += 1
            slug = f"{startPath}/{track}"

            exists = Tracks.query.filter_by(slug=slug).first() is not None
            if exists:
                continue

            title, extension = os.path.splitext(track)
            print_loading(allFiles, index, title)

            tags = TinyTag.get(slug, image=True)

            image = tags.get_image()
            imagePath = f"{IMAGES_PATH}/Album_{artist_id}.webp"
            if image is not None:
                if not os.path.exists(imagePath):
                    img = Image.open(io.BytesIO(image))
                    img.save(imagePath, "webp")
                    img.close()
            elif not os.path.exists(imagePath):
                getArtistImage(artistName, imagePath)

            if tags.title is not None and tags.title != "" and tags.title != " ":
                title = tags.title
            else:
                guessedData = guessit(title)

                title = ""

                if "title" in guessedData:
                    title = guessedData["title"]
                    if title.isdigit():
                        title = guessedData["alternative_title"]
                else:
                    if isinstance("episode", list) and "season" in guessedData:
                        title = f"{guessedData['season']}{' '.join(guessedData['episode'][1])}"
                    elif "episode" in guessedData and "season" in guessedData:
                        title = f"{guessedData['season']}{guessedData['episode']}"

                if "release_group" in guessedData:
                    title += f" ({guessedData['release_group']}"

            imagePath = imagePath.replace(dir_path, "")

            track = Tracks(
                name=title,
                slug=slug,
                album_id=0,
                artist_id=artist_id,
                duration=tags.duration,
                cover=imagePath,
                cover_b64=None,
                library_name=library,
            )
            DB.session.add(track)
            DB.session.commit()
            events.execute_event(events.NEW_TRACK, track)

    allTracks = Tracks.query.filter_by(library_name=library).all()
    for trackData in allTracks:
        path = trackData.slug
        if not os.path.exists(path):
            DB.session.delete(trackData)
            DB.session.commit()

    allAlbums = Albums.query.filter_by(library_name=library).all()
    for albumData in allAlbums:
        tracks = albumData.tracks
        if tracks == "":
            DB.session.delete(albumData)
            DB.session.commit()
            continue

    allArtists = Artists.query.filter_by(library_name=library).all()
    for artist in allArtists:
        artist_id = artist.id
        albums = Albums.query.filter_by(artist_id=artist_id).all()
        tracks = Tracks.query.filter_by(artist_id=artist_id).all()
        if len(albums) == 0 and len(tracks) == 0:
            DB.session.delete(artist)
            DB.session.commit()
            continue


def getBooks(library: str) -> None:
    allBooksPath = Libraries.query.filter_by(name=library).first().folder

    if overrides.have_override("scan_book"):
        return overrides.execute_override("scan_book", allBooksPath, library)

    allBooks = os.walk(allBooksPath)
    books = []

    for root, dirs, files in allBooks:
        for file in files:
            path = f"{root}/{file}".replace("\\", "/")

            if is_book_file(file):
                books.append(path)

    imageFunctions = {
        ".pdf": getPDFCover,
        ".epub": getEPUBCover,
        ".cbz": getCBZCover,
        ".cbr": getCBRCover,
    }

    index = 0
    for book in books:
        index += 1
        name, extension = os.path.splitext(book)
        name = name.split("/")[-1]

        print_loading(books, index, name)

        slug = f"{book}"

        exists = Books.query.filter_by(slug=slug).first() is not None
        if not exists and not os.path.isdir(slug):
            if extension in imageFunctions.keys():
                book_cover, book_type = "temp", "temp"
                book = Books(
                    title=name,
                    slug=slug,
                    book_type=book_type,
                    cover=book_cover,
                    cover_b64=generate_b64_image(book_cover, width=300),
                    library_name=library,
                )
                DB.session.add(book)
                DB.session.commit()
                book_id = book.id
                book_cover, book_type = imageFunctions[extension](slug, name, book_id)
                book.cover = book_cover
                book.book_type = book_type
                DB.session.commit()

                events.execute_event(events.NEW_BOOK, book)

    allBooksInDb = Books.query.filter_by(library_name=library).all()
    for book in allBooksInDb:
        if not os.path.exists(book.slug):
            DB.session.delete(book)
            DB.session.commit()


def getPDFCover(path: str, name: str, id: int) -> Tuple[str, str]:
    pdfDoc = fitz.open(path)

    page = pdfDoc[0]

    pix = page.get_pixmap()

    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    if os.path.exists(f"{IMAGES_PATH}/Books_Banner_{id}.webp"):
        os.remove(f"{IMAGES_PATH}/Books_Banner_{id}.webp")

    img.save(f"{IMAGES_PATH}/Books_Banner_{id}.webp", "webp")
    path = f"{IMAGES_PATH}/Books_Banner_{id}.webp"
    return path, "PDF"


def getEPUBCover(path, name, id):
    pdfDoc = fitz.open(path)
    page = pdfDoc[0]
    pix = page.get_pixmap()

    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    if os.path.exists(f"{IMAGES_PATH}/Books_Banner_{id}.webp"):
        os.remove(f"{IMAGES_PATH}/Books_Banner_{id}.webp")

    img.save(f"{IMAGES_PATH}/Books_Banner_{id}.webp", "webp")
    img.close()
    pdfDoc.close()
    path = f"{IMAGES_PATH}/Books_Banner_{id}.webp"

    return path, "EPUB"


def getCBZCover(path, name, id):
    try:
        with zipfile.ZipFile(path, "r") as zip_ref:
            for file in zip_ref.filelist:
                if is_image_file(file.filename):
                    with zip_ref.open(file) as image_file:
                        img = Image.open(io.BytesIO(image_file.read()))
                        img.save(f"{IMAGES_PATH}/Books_Banner_{id}.webp", "webp")
                        img.close()
                        break
                elif file.filename.endswith("/"):
                    with zip_ref.open(file) as image_file:
                        for file in zip_ref.filelist:
                            if is_image_file(file.filename):
                                with zip_ref.open(file) as image_file:
                                    img = Image.open(io.BytesIO(image_file.read()))
                                    img.save(
                                        f"{IMAGES_PATH}/Books_Banner_{id}.webp", "webp"
                                    )
                                    img.close()
                                    break
        return f"{IMAGES_PATH}/Books_Banner_{id}.webp", "CBZ"
    except Exception:
        return getCBRCover(path, name, id)


def getCBRCover(path, name, id):
    name = name.replace(" ", "_").replace("#", "")
    try:
        with rarfile.RarFile(path, "r") as rar_ref:
            for file in rar_ref.infolist():
                if is_image_file(file.filename):
                    with rar_ref.open(file) as image_file:
                        img = Image.open(io.BytesIO(image_file.read()))
                        img.save(f"{IMAGES_PATH}/Books_Banner_{id}.webp", "webp")
                        img.close()
                        break
                elif file.filename.endswith("/"):
                    with rar_ref.open(file) as image_file:
                        img = Image.open(io.BytesIO(image_file.read()))
                        img.save(f"{IMAGES_PATH}/Books_Banner_{id}.webp", "webp")
                        img.close()
                        break

            return f"{IMAGES_PATH}/Books_Banner_{id}.webp", "CBR"
    except rarfile.NotRarFile:
        return getCBZCover(path, name, id)