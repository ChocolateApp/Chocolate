import deezer
import requests
import os
import rarfile
import zipfile
import zlib
import ast
import datetime
import sqlalchemy
import re
import subprocess
import io
import uuid
import fitz

from guessit import guessit
from Levenshtein import distance as lev
from tmdbv3api import TV, Episode, Movie, Person, Search, Group
from tmdbv3api.as_obj import AsObj
from tmdbv3api.exceptions import TMDbException
from PIL import Image
from tinytag import TinyTag
from deep_translator import GoogleTranslator

from . import DB, get_dir_path, config, IMAGES_PATH
from .tables import (
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


from .utils.utils import path_join, save_image, is_video_file, is_music_file, is_book_file, is_image_file, is_directory, log

dir_path = get_dir_path()

deezer = deezer.Client()

image_requests = requests.Session()

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

websites_trailers = {
    "YouTube": "https://www.youtube.com/embed/",
    "Dailymotion": "https://www.dailymotion.com/video/",
    "Vimeo": "https://vimeo.com/",
}


def transformToDict(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, AsObj):
        obj = str(obj)
        obj = ast.literal_eval(obj)
        return obj
    return obj


def transformToList(obj):
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


def createArtist(artistName, lib):
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

    return artist_id


def createAlbum(name, artist_id, tracks=[], library=""):
    exists = (
        Albums.query.filter_by(dir_name=name, artist_id=artist_id).first() is not None
    )
    if exists:
        Albums.query.filter_by(
            dir_name=name, artist_id=artist_id
        ).first().tracks = ",".join(tracks)
        DB.session.commit()
        return Albums.query.filter_by(dir_name=name, artist_id=artist_id).first().id

    albums = deezer.search_albums(
        f"{Artists.query.filter_by(id=artist_id).first().name} - {name}"
    )

    # pour chaque album trouvé, on vérifie si le nom de est proche du nom de l'album qu'on cherche
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
        return album_id
    album_name = album.title
    cover = save_image(album.cover_big, f"{IMAGES_PATH}/Album_{album_id}")

    tracks = ",".join(tracks)

    album = Albums(
        id=album_id,
        name=album_name,
        dir_name=name,
        artist_id=artist_id,
        cover=cover,
        tracks=tracks,
        library_name=library,
    )
    DB.session.add(album)
    DB.session.commit()

    return album_id

def getAlbumImage(album_name, path):
    album = deezer.search_albums(album_name)
    if len(album) == 0:
        return None
    album = album[0]
    cover = save_image(album.cover_big, path)
    return cover


def getArtistImage(artist_name, path):
    artist = deezer.search_artists(artist_name)[0]
    cover = save_image(artist.picture_big, path)
    return cover


def generateImage(title, librairie, banner):
    from PIL import Image, ImageDraw, ImageFont

    largeur = 1280
    hauteur = 720
    image = Image.new("RGB", (largeur, hauteur), color="#1d1d1d")

    # Ajouter les textes au centre de l'image
    draw = ImageDraw.Draw(image)

    # Charger la police Poppins
    font_path = f"{dir_path}/static/fonts/Poppins-Medium.ttf"
    font_title = ImageFont.truetype(font_path, size=70)
    font_librairie = ImageFont.truetype(font_path, size=50)

    # Positionner les textes au centre de l'image
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


def is_connected():
    try:
        requests.get("https://ww.google.com/").status_code
        return True
    except Exception:
        return False


def print_loading(filesList, index, title):
    terminal_size = os.get_terminal_size().columns - 1
    percentage = index * 100 / len(filesList)

    loading_first_part = ("•" * int(percentage * 0.2))[:-1]
    loading_first_part = f"{loading_first_part}➤"
    loading_second_part = "•" * (20 - int(percentage * 0.2))

    loading_start = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loading_first_part}\33[31m{loading_second_part}\33[0m]"
    loading_middle = f"{title}"
    loading_end = f"{index}/{len(filesList)}"

    if len(loading_start) + len(loading_middle) + len(loading_end) > terminal_size:
        loading_middle = loading_middle[: terminal_size - len(loading_start) - len(loading_end) - 3] + "..."

    free_space = (terminal_size - len(loading_start) - len(loading_middle) - len(loading_end)) // 2
    loading_middle = " " * free_space + loading_middle + " " * free_space + " " * ((terminal_size - len(loading_start) - len(loading_middle) - len(loading_end)) % 2)

    loading = f"{loading_start} | {loading_middle} | {loading_end}"
    print("\033[?25l", end="")
    print(loading, end="\r", flush=True)


def searchGame(game, console):
    url = f"https://www.igdb.com/search_autocomplete_all?q={game.replace(' ', '%20')}"
    return IGDBRequest(url, console)


def translate(string):
    language = config["ChocolateSettings"]["language"]
    if language == "EN":
        return string
    translated = GoogleTranslator(source="english", target=language.lower()).translate(
        string
    )
    return translated


def IGDBRequest(url, console):
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
        token = requests.request("POST", get_access_token)
        token = token.json()
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
                    genres = ", ".join(genres)

                    game_data = {
                        "title": game["name"],
                        "cover": game["cover"]["url"].replace("//", "https://"),
                        "description": game["summary"],
                        "note": game["total_rating"],
                        "date": game["first_release_date"],
                        "genre": genres,
                        "id": game["id"],
                    }
                    return game_data
                except Exception:
                    log_message = f"Error while getting the game {game['name']} from IGDB"
                    log("ERROR", "GAME SCAN", log_message)
                    continue
        return None


def getMovies(library_name):
    all_movies_not_sorted = []
    path = Libraries.query.filter_by(lib_name=library_name).first().lib_folder

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

            real_title, extension = os.path.splitext(originalMovieTitle)
            cover = save_image(f"https://image.tmdb.org/t/p/original{res['poster_path']}", f"{IMAGES_PATH}/{movie_id}_Movie_Cover")
            banner = save_image(f"https://image.tmdb.org/t/p/original{res['backdrop_path']}", f"{IMAGES_PATH}/{movie_id}_Movie_Banner")

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
                actorImage = save_image(f"https://www.themovieDB.org/t/p/w600_and_h900_bestv2{cast.profile_path}", f"{IMAGES_PATH}/Actor_{actor_id}")
                if actor_id not in theCast:
                    theCast.append(actor_id)
                else:
                    break
                person = Person()
                p = person.details(cast.id)
                exists = Actors.query.filter_by(actor_id=cast.id).first() is not None
                if not exists:
                    actor = Actors(
                        name=cast.name,
                        actor_image=actorImage,
                        actor_description=p.biography,
                        actor_birth_date=p.birthday,
                        actor_birth_place=p.place_of_birth,
                        actor_programs=f"{movie_id}",
                        actor_id=cast.id,
                    )
                    DB.session.add(actor)
                    DB.session.commit()
                else:
                    actor = Actors.query.filter_by(actor_id=cast.id).first()
                    actor.actor_programs = f"{actor.actor_programs} {movie_id}"
                    DB.session.commit()
            theCast = ",".join([str(i) for i in theCast])
            try:
                date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                date = "Unknown"
            except UnboundLocalError:
                date = "Unknown"

            genre = res["genre_ids"]
            try:
                length = length_video(video_path)
                length = str(datetime.timedelta(seconds=length))
                length = length.split(":")
            except Exception:
                length = []

            if len(length) == 3:
                hours = length[0]
                minutes = length[1]
                seconds = str(round(float(length[2])))
                if int(seconds) < 10:
                    seconds = f"0{seconds}"
                length = f"{hours}:{minutes}:{seconds}"
            elif len(length) == 2:
                minutes = length[0]
                seconds = str(round(float(length[1])))
                if int(seconds) < 10:
                    seconds = f"0{seconds}"
                length = f"{minutes}:{seconds}"
            elif len(length) == 1:
                seconds = str(round(float(length[0])))
                if int(seconds) < 10:
                    seconds = f"0{seconds}"
                length = f"00:{seconds}"
            else:
                length = "0"

            duration = length

            movieGenre = []
            for genre_id in genre:
                movieGenre.append(genre_list[genre_id])
            movieGenre = ",".join(movieGenre)

            bandeAnnonce = details.videos.results
            bande_annonce_url = ""
            if len(bandeAnnonce) > 0:
                for video in bandeAnnonce:
                    bandeAnnonceType = video.type
                    bandeAnnonceHost = video.site
                    bandeAnnonceKey = video.key
                    if bandeAnnonceType == "Trailer":
                        try:
                            bande_annonce_url = (
                                websites_trailers[bandeAnnonceHost] + bandeAnnonceKey
                            )
                            break
                        except KeyError:
                            bande_annonce_url = "Unknown"

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

            alternatives_names = ",".join(alternatives_names)

            filmData = Movies(
                id=movie_id,
                title=movieTitle,
                real_title=name,
                cover=cover,
                banner=banner,
                slug=video_path,
                description=description,
                note=note,
                date=date,
                genre=movieGenre,
                duration=str(duration),
                cast=theCast,
                bande_annonce_url=bande_annonce_url,
                adult=str(res["adult"]),
                library_name=library_name,
                alternatives_names=alternatives_names,
                file_date=os.path.getmtime(video_path),
            )
            DB.session.add(filmData)
            DB.session.commit()



def getSeries(library_name):
    allSeriesPath = Libraries.query.filter_by(lib_name=library_name).first().lib_folder
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

        if (
            DB.session.query(Series).filter_by(original_name=serieTitle).first()
            is not None
        ):
            serie_id = (
                DB.session.query(Series).filter_by(original_name=serieTitle).first().id
            )

        exists = DB.session.query(Series).filter_by(id=serie_id).first() is not None

        details = show.details(serie_id)
        defaultNbOfSeasons = details.number_of_seasons
        defaultNbOfEpisodes = details.number_of_episodes
        seasonsInfo = details.seasons

        seasonsNumber = []
        seasons = os.listdir(seriePath)
        for season in seasons:
            if os.path.isdir(f"{seriePath}/{season}") and season != "":
                season = re.sub(r"\D", "", season)
                if season == "":
                    continue
                seasonsNumber.append(int(season))

        episodes = []
        for season in seasons:
            allEpisodes = os.listdir(f"{seriePath}/{season}")
            for episode in allEpisodes:
                if os.path.isfile(
                    f"{seriePath}/{season}/{episode}"
                ):
                    episodes.append(episode)

        nbEpisodes = len(episodes)
        nbSeasons = len(seasons)

        episodeGroups = show.episode_groups(serie_id).results

        if len(episodeGroups) > 0 and nbEpisodes > defaultNbOfEpisodes and nbSeasons > defaultNbOfSeasons:
            seasonsInfo = None
            for group in episodeGroups:
                groupNbEpisodes = group.episode_count
                groupNbSeasons = group.group_count

                if nbEpisodes >= groupNbEpisodes * 0.95 and nbSeasons == groupNbSeasons:
                    theGroup = Group()
                    seasonsInfo = theGroup.details(group.id).groups
                    for season in seasonsInfo:
                        season = season.__dict__
                        if len(season["episodes"]) > 0:
                            season["season_number"] = season["order"]
                            season["episode_count"] = len(season["episodes"])
                            print(len(season["episodes"]))
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
            banner = save_image(f"https://image.tmdb.org/t/p/original{res['backdrop_path']}", f"{IMAGES_PATH}/{serie_id}_Serie_Banner")
            cover = save_image(f"https://image.tmdb.org/t/p/original{res['poster_path']}", f"{IMAGES_PATH}/{serie_id}_Serie_Cover")

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
            bande_annonce_url = ""
            if len(bandeAnnonce) > 0:
                for video in bandeAnnonce:
                    bandeAnnonceType = video.type
                    bandeAnnonceHost = video.site
                    bandeAnnonceKey = video.key
                    if bandeAnnonceType == "Trailer" or len(bandeAnnonce) == 1:
                        try:
                            bande_annonce_url = (
                                websites_trailers[bandeAnnonceHost] + bandeAnnonceKey
                            )
                            break
                        except KeyError as e:
                            log_message = f"Error while getting trailer for serie {serieTitle}: {e}"
                            log("ERROR", "SERIE SCAN", log_message)
                            bande_annonce_url = "Unknown"

            genreList = []
            for genre in serieGenre:
                genreList.append(str(genre.name))
            genreList = ",".join(genreList)
            newCast = []
            cast = list(cast)[:5]
            for actor in cast:
                actor_id = actor.id
                actorImage = save_image(f"https://image.tmdb.org/t/p/original{actor.profile_path}", f"{IMAGES_PATH}/Actor_{actor_id}")
                actor.profile_path = str(actorImage)
                newCast.append(actor_id)

                person = Person()
                p = person.details(actor.id)
                exists = Actors.query.filter_by(actor_id=actor.id).first() is not None
                if not exists:
                    actor = Actors(
                        name=actor.name,
                        actor_id=actor.id,
                        actor_image=actorImage,
                        actor_description=p.biography,
                        actor_birth_date=p.birthday,
                        actor_birth_place=p.place_of_birth,
                        actor_programs=f"{serie_id}",
                    )
                    DB.session.add(actor)
                    DB.session.commit()
                else:
                    actor = Actors.query.filter_by(actor_id=actor.id).first()
                    if serie_id not in actor.actor_programs:
                        actor.actor_programs = f"{actor.actor_programs} {serie_id}"
                    DB.session.commit()

            newCast = newCast[:5]
            newCast = ",".join([str(i) for i in newCast])
            isAdult = str(details["adult"])
            serieObject = Series(
                id=serie_id,
                name=name,
                original_name=originalSerieTitle,
                genre=genreList,
                duration=duration,
                description=description,
                cast=newCast,
                bande_annonce_url=bande_annonce_url,
                cover=cover,
                banner=banner,
                note=note,
                date=date,
                serie_modified_time=serie_modified_time,
                adult=isAdult,
                library_name=library_name,
            )
            DB.session.add(serieObject)
            DB.session.commit()

        for season in seasonsInfo:
            season = transformToDict(season)
            allSeasons = os.listdir(seriePath)
            url = None
            for season_dir in allSeasons:
                season_dir_number = re.sub(r"\D", "", season_dir)
                if season_dir_number != "" and int(season_dir_number) == int(season["season_number"]):
                    url = f"{seriePath}/{season_dir}"
                    break
            if not url:
                #print(f"\nCan't find {serieTitle} season {season['season_number']}")
                continue
            season_dir = url
            #print(f"\nSeason {season['season_number']} of {serieTitle} found: {season_dir}")
            seasonInDB = Seasons.query.filter_by(season_id=season["id"]).first()
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
                        Seasons.query.filter_by(season_id=season_id)
                        .first()
                        .seasonModifiedTime
                    )
                except AttributeError:
                    seasonModifiedTime = os.path.getmtime(season_dir)

                if len(allEpisodes) > 0 or (seasonModifiedTime != savedModifiedTime):
                    try:
                        exists = (
                            Seasons.query.filter_by(season_id=season_id).first()
                            is not None
                        )
                    except sqlalchemy.exc.PendingRollbackError:
                        DB.session.rollback()
                        exists = (
                            Seasons.query.filter_by(season_id=season_id).first()
                            is not None
                        )
                    # number of episodes in the season
                    savedModifiedTime = 0
                    if not exists or (seasonModifiedTime != savedModifiedTime):
                        season_cover_path = save_image(f"https://image.tmdb.org/t/p/original{seasonPoster}", f"{IMAGES_PATH}/{season_id}_Cover")

                        allSeasons = os.listdir(seriePath)

                        try:
                            modified_date = os.path.getmtime(season_dir)
                        except FileNotFoundError:
                            modified_date = 0

                    allEpisodesInDB = Episodes.query.filter_by(
                        season_id=season_id
                    ).all()
                    allEpisodesInDB = [
                        episode.episode_name for episode in allEpisodesInDB
                    ]

                    exists = (
                        Seasons.query.filter_by(season_id=season_id).first() is not None
                    )
                    if not exists:
                        thisSeason = Seasons(
                            serie=serie_id,
                            release=releaseDate,
                            episodes_number=episodes_number,
                            season_number=season_number,
                            season_id=season_id,
                            season_name=season_name,
                            season_description=season_description,
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
                    if len(allEpisodes) != len(allEpisodesInDB):
                        for episode in allEpisodes:
                            slug = f"{season_dir}/{episode}"
                            episodeName = slug.split("/")[-1]
                            guess = guessit(episodeName)
                            if "episode" in guess:
                                episodeIndex = guess["episode"]
                            elif "episode_title" in guess:
                                episodeIndex = guess["episode_title"]
                            elif "season" in guess and isinstance(guess["season"], list) and len(guess["season"]) == 2:
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

                            exists = Episodes.query.filter_by(episode_number=int(episodeIndex), season_id=season_id).first() is not None

                            if not exists:
                                #print(f"Episode {episodeIndex} of {serieTitle} for the Season {season_id} not found")
                                if isinstance(season_id, int) or season_id.isnumeric():
                                    showEpisode = Episode()
                                    #print(f"Get episodeInfo of : E{episodeIndex} S{season_number} of {serieTitle}")
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

                                coverEpisode = save_image(f"https://image.tmdb.org/t/p/original{episodeInfo['still_path']}", f"{IMAGES_PATH}/{season_id}_{episode_id}_Episode_Banner")

                                try:
                                    exists = (
                                        Episodes.query.filter_by(
                                            episode_id=episode_id
                                        ).first()
                                        is not None
                                    )
                                except sqlalchemy.exc.PendingRollbackError:
                                    DB.session.rollback()
                                    exists = (
                                        Episodes.query.filter_by(
                                            episode_id=episode_id
                                        ).first()
                                        is not None
                                    )
                                if not exists:
                                    episodeData = Episodes(
                                        episode_id=episode_id,
                                        episode_name=realEpisodeName,
                                        season_id=season_id,
                                        episode_number=episodeIndex,
                                        episode_description=episodeInfo["overview"],
                                        episode_cover_path=coverEpisode,
                                        release_date=episodeInfo["air_date"],
                                        slug=slug,
                                        intro_start=0.0,
                                        intro_end=0.0,
                                    )
                                    thisSeason = Seasons.query.filter_by(
                                        season_id=season_id
                                    ).first()
                                    thisSeason.number_of_episode_in_folder += 1
                                    try:
                                        DB.session.add(episodeData)
                                        DB.session.commit()
                                    except Exception:
                                        DB.session.rollback()
                                        DB.session.add(episodeData)
                                        DB.session.commit()
                        else:
                            pass

    allFiles = [
        name
        for name in os.listdir(allSeriesPath)
        if os.path.isfile(path_join(allSeriesPath, name))
        and is_video_file(name)
    ]
    index = 0
    for file in allFiles:
        index += 1
        print_loading(allFiles, index, file)

        slug = path_join(allSeriesPath, file)
        exists = Episodes.query.filter_by(slug=slug).first() is not None
        if not exists:
            guess = guessit(file)
            #print(f"\n {guess}")
            title = guess["title"]
            if "episode" not in guess:
                season = guess["season"]
                if isinstance(guess["season"], list):
                    season, episode = guess["season"]
                else:
                    season = guess["season"]
                    episode = int(guess["episode_title"])
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

            serieExists = Series.query.filter_by(id=serie_id).first() is not None
            if not serieExists:
                name = res.name
                cover = save_image(f"https://image.tmdb.org/t/p/original{res.poster_path}", f"{IMAGES_PATH}/{serie_id}_Serie_Cover")
                banner = save_image(f"https://image.tmdb.org/t/p/original{res.backdrop_path}", f"{IMAGES_PATH}/{serie_id}_Serie_Banner")

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
                bande_annonce_url = ""
                if len(bandeAnnonce) > 0:
                    for video in bandeAnnonce:
                        bandeAnnonceType = video.type
                        bandeAnnonceHost = video.site
                        bandeAnnonceKey = video.key
                        if bandeAnnonceType == "Trailer" or len(bandeAnnonce) == 1:
                            try:
                                bande_annonce_url = (
                                    websites_trailers[bandeAnnonceHost]
                                    + bandeAnnonceKey
                                )
                                break
                            except KeyError:
                                bande_annonce_url = "Unknown"

                genreList = []
                for genre in serieGenre:
                    genreList.append(str(genre.name))
                genreList = ",".join(genreList)
                newCast = []
                cast = list(cast)[:5]
                for actor in cast:
                    actor_id = actor.id
                    actorImage = save_image(f"https://image.tmdb.org/t/p/original{actor.profile_path}", f"{IMAGES_PATH}/Actor_{actor_id}")
                    actor.profile_path = str(actorImage)
                    thisActor = actor_id
                    newCast.append(thisActor)

                    person = Person()
                    p = person.details(actor.id)
                    exists = (
                        Actors.query.filter_by(actor_id=actor.id).first() is not None
                    )
                    if not exists:
                        actor = Actors(
                            name=actor.name,
                            actor_id=actor.id,
                            actor_image=actorImage,
                            actor_description=p.biography,
                            actor_birth_date=p.birthday,
                            actor_birth_place=p.place_of_birth,
                            actor_programs=f"{serie_id}",
                        )
                        DB.session.add(actor)
                        DB.session.commit()
                    else:
                        actor = Actors.query.filter_by(actor_id=actor.id).first()
                        actor.actor_programs = f"{actor.actor_programs} {serie_id}"
                        DB.session.commit()

                newCast = newCast[:5]
                newCast = ",".join([str(i) for i in newCast])
                isAdult = str(details["adult"])
                serieObject = Series(
                    id=serie_id,
                    name=name,
                    original_name=originalSerieTitle,
                    genre=genreList,
                    duration=duration,
                    description=description,
                    cast=newCast,
                    bande_annonce_url=bande_annonce_url,
                    cover=cover,
                    banner=banner,
                    note=note,
                    date=date,
                    serie_modified_time=serie_modified_time,
                    adult=isAdult,
                    library_name=library_name,
                )
                DB.session.add(serieObject)
                DB.session.commit()

            # print(f"Pour {file}, serie_id = {serie_id} et season_id = {season_id}")

            seasonExists = (
                Seasons.query.filter_by(serie=serie_id, season_id=season_id).first()
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

                season_cover_path = save_image("https://image.tmdb.org/t/p/original{seasonPoster}", f"{IMAGES_PATH}/{season_id}_Cover")

                try:
                    modified_date = os.path.getmtime(f"{allSeriesPath}{slug}")
                except Exception:
                    modified_date = 0

                seasonObject = Seasons(
                    serie=serie_id,
                    season_id=season_id,
                    season_name=season_name,
                    season_description=season_description,
                    cover=season_cover_path,
                    season_number=season_number,
                    episodes_number=episodes_number,
                    release=releaseDate,
                    modified_date=modified_date,
                    number_of_episode_in_folder=0,
                )

                DB.session.add(seasonObject)
                DB.session.commit()

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
                        episode_number=episodeIndex, season_id=season_id
                    ).first()
                    is not None
                )
            except sqlalchemy.exc.PendingRollbackError:
                DB.session.rollback()
                exists = (
                    Episodes.query.filter_by(
                        episode_number=episodeIndex, season_id=season_id
                    ).first()
                    is not None
                )
            if not exists:
                if isinstance(season_id, int) or season_id.isnumeric():
                    showEpisode = Episode()
                    episodeDetails = showEpisode.details(
                        serie_id, season_number, episodeIndex
                    )
                    realEpisodeName = episodeDetails.name
                    episodeInfo = showEpisode.details(
                        serie_id, season_number, episodeIndex
                    )
                    episode_id = episodeInfo.id
                else:
                    episodeInfo = bigSeason["episodes"][int(episodeIndex) - 1]
                    episode_id = episodeInfo["id"]
                    realEpisodeName = episodeInfo["name"]

                coverEpisode = save_image(f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}", f"{IMAGES_PATH}/{season_id}_{episode_id}_Episode_Banner")

                try:
                    exists = (
                        Episodes.query.filter_by(episode_id=episode_id).first()
                        is not None
                    )
                except sqlalchemy.exc.PendingRollbackError:
                    DB.session.rollback()
                    exists = (
                        Episodes.query.filter_by(episode_id=episode_id).first()
                        is not None
                    )
                if not exists:
                    # Mprint(f"Pour le fichier {file}, j'ai trouvé : \n  -  episode_number: {episodeIndex} \n  -  season_id: {season_id} \n  -  Serie: {serie_id} \n  -  Episode ID: {episode_id}")

                    episodeData = Episodes(
                        episode_id=episode_id,
                        episode_name=realEpisodeName,
                        season_id=season_id,
                        episode_number=episodeIndex,
                        episode_description=episodeInfo.overview,
                        episode_cover_path=coverEpisode,
                        release_date=episodeInfo.air_date,
                        slug=slug,
                        intro_start=0.0,
                        intro_end=0.0,
                    )
                    thisSeason = Seasons.query.filter_by(season_id=season_id).first()
                    thisSeason.number_of_episode_in_folder += 1
                    try:
                        DB.session.add(episodeData)
                        DB.session.commit()
                    except Exception:
                        DB.session.rollback()
                        DB.session.add(episodeData)
                        DB.session.commit()

    allSeriesInDB = Series.query.all()
    allSeriesInDB = [
        serie.original_name
        for serie in allSeriesInDB
        if serie.library_name == library_name
    ]

    for serie in allSeriesInDB:
        serie_id = Series.query.filter_by(original_name=serie).first().id
        allSeasons = Seasons.query.filter_by(serie=serie_id).all()
        if serie not in allSeriesName:
            for season in allSeasons:
                season_id = season.season_id
                allEpisodes = Episodes.query.filter_by(season_id=season_id).all()
                for episode in allEpisodes:
                    if not os.path.exists(episode.slug):
                        try:
                            DB.session.delete(episode)
                            DB.session.commit()
                        except Exception:
                            DB.session.rollback()
                            DB.session.delete(episode)
                            DB.session.commit()

        for season in allSeasons:
            season_id = season.season_id
            allEpisodes = Episodes.query.filter_by(season_id=season_id).all()
            if len(allEpisodes) == 0:
                try:
                    DB.session.delete(season)
                    DB.session.commit()
                except Exception:
                    DB.session.rollback()
                    DB.session.delete(season)
                    DB.session.commit()
        allSeasons = Seasons.query.filter_by(serie=serie_id).all()
        if len(allSeasons) == 0:
            try:
                DB.session.delete(Series.query.filter_by(id=serie_id).first())
                DB.session.commit()
            except Exception:
                DB.session.rollback()
                DB.session.delete(Series.query.filter_by(id=serie_id).first())
                DB.session.commit()


def getGames(library_name):
    allGamesPath = Libraries.query.filter_by(lib_name=library_name).first().lib_folder
    try:
        allConsoles = [
            name
            for name in os.listdir(allGamesPath)
            if os.path.isdir(path_join(allGamesPath, name))
            and is_video_file(name)
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
                            gameCover = save_image(gameCover, f"{IMAGES_PATH}/{console}_{gameRealTitle}")

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


def getOthersVideos(library, allVideosPath=None):
    if not allVideosPath:
        allVideosPath = Libraries.query.filter_by(lib_name=library).first().lib_folder
        try:
            allVideos = os.listdir(allVideosPath)
        except Exception as e:
            log_message = f"Error while getting others videos in {allVideosPath} : {e}"
            log("ERROR", "OTHER SCAN", log_message)
            return
    else:
        allVideos = os.listdir(f"{allVideosPath}")

    allDirectories = [
        video for video in allVideos if os.path.isdir(f"{allVideosPath}/{video}")
    ]
    allVideos = [
        video
        for video in allVideos
        if is_video_file(video)
    ]

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
            video_hash = video_hash_hex[:10]
            videoDuration = length_video(slug)
            middle = videoDuration // 2
            banner = f"{IMAGES_PATH}/Other_Banner_{library}_{video_hash}.webp"
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
                banner = f"{IMAGES_PATH}/Other_Banner_{library}_{video_hash}.webp"
            except Exception:
                banner = "/static/img/broken.webp"
            video = OthersVideos(
                video_hash=video_hash,
                title=title,
                slug=slug,
                banner=banner,
                duration=videoDuration,
                library_name=library,
            )
            DB.session.add(video)
            DB.session.commit()

    for video in OthersVideos.query.filter_by(library_name=library).all():
        path = video.slug
        if not os.path.exists(path):
            DB.session.delete(video)
            DB.session.commit()


def getMusics(library):
    allMusicsPath = Libraries.query.filter_by(lib_name=library).first().lib_folder
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
            allTracks = [
                track
                for track in allTracks
                if is_music_file(track)
            ]
            album_id = createAlbum(albumName, artist_id, allTracks, library)

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
                    library_name=library,
                )
                DB.session.add(track)
                DB.session.commit()
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
                library_name=library,
            )
            DB.session.add(track)
            DB.session.commit()

    allTracks = Tracks.query.filter_by(library_name=library).all()
    for track in allTracks:
        path = track.slug
        if not os.path.exists(path):
            DB.session.delete(track)
            DB.session.commit()

    allAlbums = Albums.query.filter_by(library_name=library).all()
    for album in allAlbums:
        tracks = album.tracks
        if tracks == "":
            DB.session.delete(album)
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


def getBooks(library):
    allBooks = Libraries.query.filter_by(lib_name=library)
    allBooksPath = allBooks.first().lib_folder

    allBooks = os.walk(allBooksPath)
    books = []

    for root, dirs, files in allBooks:
        for file in files:
            path = f"{root}/{file}".replace("\\", "/")

            if is_book_file(file):
                books.append(path)

    allBooks = books

    imageFunctions = {
        ".pdf": getPDFCover,
        ".epub": getEPUBCover,
        ".cbz": getCBZCover,
        ".cbr": getCBRCover,
    }

    index = 0
    for book in allBooks:
        index += 1
        name, extension = os.path.splitext(book)
        name = name.split("/")[-1]

        print_loading(allBooks, index, name)

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
                    library_name=library,
                )
                DB.session.add(book)
                DB.session.commit()
                book_id = book.id
                book_cover, book_type = imageFunctions[extension](slug, name, book_id)
                book.cover = book_cover
                book.book_type = book_type
                DB.session.commit()
    allBooksInDb = Books.query.filter_by(library_name=library).all()
    for book in allBooksInDb:
        if not os.path.exists(book.slug):
            DB.session.delete(book)
            DB.session.commit()


def getPDFCover(path, name, id):
    pdfDoc = fitz.open(path)
    # Récupérez la page demandée
    page = pdfDoc[0]
    # Créez une image à partir de la page
    pix = page.get_pixmap()
    # Enregistre l'image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    if os.path.exists(f"{IMAGES_PATH}/Books_Banner_{id}.webp"):
        os.remove(f"{IMAGES_PATH}/Books_Banner_{id}.webp")

    img.save(f"{IMAGES_PATH}/Books_Banner_{id}.webp", "webp")
    path = f"{IMAGES_PATH}/Books_Banner_{id}.webp"
    return path, "PDF"


def getEPUBCover(path, name, id):
    pdfDoc = fitz.open(path)
    # Récupérez la page demandée
    page = pdfDoc[0]
    # Créez une image à partir de la page
    pix = page.get_pixmap()
    # Enregistre l'image
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
            # Parcourt tous les fichiers à l'intérieur du CBZ
            for file in zip_ref.filelist:
                # Vérifie si le fichier est une image
                if is_image_file(file.filename):
                    # Ouvre le fichier image
                    with zip_ref.open(file) as image_file:
                        img = Image.open(io.BytesIO(image_file.read()))
                        img.save(f"{IMAGES_PATH}/Books_Banner_{id}.webp", "webp")
                        img.close()
                        break
                elif file.filename.endswith("/"):
                    with zip_ref.open(file) as image_file:
                        for file in zip_ref.filelist:
                            if is_image_file(file.filename):
                                # Ouvre le fichier image
                                with zip_ref.open(file) as image_file:
                                    img = Image.open(io.BytesIO(image_file.read()))
                                    # Enregistre l'image
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
            # Parcourt tous les fichiers à l'intérieur du CBR
            for file in rar_ref.infolist():
                # Vérifie si le fichier est une image
                if is_image_file(file.filename):
                    # Ouvre le fichier image
                    with rar_ref.open(file) as image_file:
                        img = Image.open(io.BytesIO(image_file.read()))
                        # Enregistre l'image
                        img.save(f"{IMAGES_PATH}/Books_Banner_{id}.webp", "webp")
                        img.close()
                        break
                elif file.filename.endswith("/"):
                    with rar_ref.open(file) as image_file:
                        img = Image.open(io.BytesIO(image_file.read()))
                        # Enregistre l'image
                        img.save(f"{IMAGES_PATH}/Books_Banner_{id}.webp", "webp")
                        img.close()
                        break

            return f"{IMAGES_PATH}/Books_Banner_{id}.webp", "CBR"
    except rarfile.NotRarFile:
        return getCBZCover(path, name, id)
