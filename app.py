from sqlite3 import IntegrityError
from flask import Flask, url_for, request, render_template, redirect, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from tmdbv3api import TMDb, Movie, TV, Episode, Person
from tmdbv3api.exceptions import TMDbException
from videoprops import get_video_properties
from pathlib import Path
import requests, os, subprocess, configparser, socket, datetime, subprocess, socket, platform, GPUtil, json, random, time, rpc, sqlalchemy, warnings
from Levenshtein import distance as lev
from fuzzywuzzy import fuzz
from ask_lib import AskResult, ask
from time import mktime

start_time = mktime(time.localtime())

with warnings.catch_warnings():
   warnings.simplefilter("ignore", category = sqlalchemy.exc.SAWarning)

app = Flask(__name__)
CORS(app)

currentCWD = os.getcwd()
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{currentCWD}/database.db'
app.config['MAX_CONTENT_LENGTH'] = 4096 * 4096
app.config['UPLOAD_FOLDER'] = f"{currentCWD}/static/img/"
app.config["SECRET_KEY"] = "ChocolateDBPassword"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
loginManager = LoginManager()
loginManager.init_app(app)
loginManager.login_view = 'login'

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    profilePicture = db.Column(db.String(255))
    accountType = db.Column(db.String(255))

    def __init__(self, name, password, profilePicture, accountType):
        self.name = name
        self.password = generate_password_hash(password)
        self.profilePicture = profilePicture
        self.accountType = accountType

    def __repr__(self) -> str:
        return f'<Name {self.name}>'

    def verify_password(self, pwd):
        return check_password_hash(self.password, pwd)

class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), primary_key=True)
    realTitle = db.Column(db.String(255), primary_key=True)
    cover = db.Column(db.String(255))
    banner = db.Column(db.String(255))
    slug = db.Column(db.String(255))
    description = db.Column(db.String(2550))
    note = db.Column(db.String(255))
    date = db.Column(db.String(255))
    genre = db.Column(db.String(255))
    duration = db.Column(db.String(255))
    cast = db.Column(db.String(255))
    bandeAnnonceUrl = db.Column(db.String(255))

    def __init__(self, id, title, realTitle, cover, banner, slug, description, note, date, genre, duration, cast, bandeAnnonceUrl):
        self.id = id
        self.title = title
        self.realTitle = realTitle
        self.cover = cover
        self.banner = banner
        self.slug = slug
        self.description = description
        self.note = note
        self.date = date
        self.genre = genre
        self.duration = duration
        self.cast = cast
        self.bandeAnnonceUrl = bandeAnnonceUrl
    
    def __repr__(self) -> str:
        return f"<Movies {self.title}>"

class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), primary_key=True)
    originalName = db.Column(db.String(255), primary_key=True)
    genre = db.Column(db.String(255))
    duration = db.Column(db.String(255))
    description = db.Column(db.String(2550))
    cast = db.Column(db.String(255))
    bandeAnnonceUrl = db.Column(db.String(255))
    serieCoverPath = db.Column(db.String(255))
    banniere = db.Column(db.String(255))
    note = db.Column(db.String(255))
    date = db.Column(db.String(255))

    def __init__(self, id, name, originalName, genre, duration, description, cast, bandeAnnonceUrl, serieCoverPath, banniere, note, date):
        self.id = id
        self.name = name
        self.originalName = originalName
        self.genre = genre
        self.duration = duration
        self.description = description
        self.cast = cast
        self.bandeAnnonceUrl = bandeAnnonceUrl
        self.serieCoverPath = serieCoverPath
        self.banniere = banniere
        self.note = note
        self.date = date
    
    def __repr__(self) -> str:
        return f"<Series {self.name}>"


class Seasons(db.Model):
    
    serie = db.Column(db.Integer, nullable=False)
    seasonId = db.Column(db.Integer, primary_key=True)
    seasonNumber = db.Column(db.Integer, primary_key=True)
    release = db.Column(db.String(255))
    episodesNumber = db.Column(db.String(255))
    seasonName = db.Column(db.String(255))
    seasonDescription = db.Column(db.Text)
    seasonCoverPath = db.Column(db.String(255))

    def __init__(self, serie, release, episodesNumber, seasonNumber, seasonId, seasonName, seasonDescription, seasonCoverPath):
        self.serie = serie
        self.release = release
        self.episodesNumber = episodesNumber
        self.seasonNumber = seasonNumber
        self.seasonId = seasonId
        self.seasonName = seasonName
        self.seasonDescription = seasonDescription
        self.seasonCoverPath = seasonCoverPath

    def __repr__(self) -> str:
        return f"<Seasons {self.serie} {self.seasonNumber}>"

class Episodes(db.Model):
    seasonId = db.Column(db.Integer, nullable=False)
    episodeId = db.Column(db.Integer, primary_key=True)
    episodeName = db.Column(db.String(255), primary_key=True)
    episodeNumber = db.Column(db.Integer, primary_key=True)
    episodeDescription = db.Column(db.Text)
    episodeCoverPath = db.Column(db.String(255))
    releaseDate = db.Column(db.String(255))
    slug = db.Column(db.String(255))

    def __init__(self, episodeId, episodeName, seasonId, episodeNumber, episodeDescription, episodeCoverPath, releaseDate, slug):
        self.episodeId = episodeId
        self.seasonId = seasonId
        self.episodeName = episodeName
        self.episodeNumber = episodeNumber
        self.episodeDescription = episodeDescription
        self.episodeCoverPath = episodeCoverPath
        self.releaseDate = releaseDate
        self.slug = slug

    def __repr__(self) -> str:
        return f"<Episodes {self.seasonId} {self.episodeNumber}>"

class Language(db.Model):
    language = db.Column(db.String(255), primary_key=True)
    
    def __init__(self, language):
        self.language = language
    
    def __repr__(self) -> str:
        return f"<Language {self.language}>"

with app.app_context():
  db.create_all()
  db.init_app(app)

@loginManager.user_loader
def load_user(id):
    return Users.query.get(int(id))

tmdb = TMDb()
tmdb.api_key = "cb862a91645ec50312cf636826e5ca1f"

config = configparser.ConfigParser()
config.read("config.ini")
if config["ChocolateSettings"]["language"] == "Empty":
    config["ChocolateSettings"]["language"] = "en-US"

tmdb.language = config["ChocolateSettings"]["language"]
tmdb.debug = True
movie = Movie()
show = TV()
errorMessage = True
client_id = "771837466020937728"
rpc_obj = rpc.DiscordIpcClient.for_platform(client_id)
searchedFilms = []
allMoviesNotSorted = []
allMoviesDict = {}

searchedSeries = []
simpleDataSeries = {}
allSeriesNotSorted = []
allSeriesDict = {}
allSeriesDictTemp = {}

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
config.set("ChocolateSettings", "localIP", local_ip)
serverPort = config["ChocolateSettings"]["port"]
configLanguage = config["ChocolateSettings"]["language"]
with app.app_context():
    languageDB = db.session.query(Language).first()
    exists = db.session.query(Language).first() is not None
    if not exists:
        newLanguage = Language(language="en-US")
        db.session.add(newLanguage)
        db.session.commit()
    languageDB = db.session.query(Language).first()
    if languageDB.language != configLanguage:
        db.session.query(Movies).delete()
        db.session.query(Series).delete()
        db.session.query(Seasons).delete()
        db.session.query(Episodes).delete()
        languageDB.language = configLanguage
        db.session.commit()

CHUNK_LENGTH = 5
genreList = {
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

genresUsed = []
moviesGenre = []
movieExtension = ""
websitesTrailers = {
    "YouTube": "https://www.youtube.com/embed/",
    "Dailymotion": "https://www.dailymotion.com/video/",
    "Vimeo": "https://vimeo.com/",
}

def getMovies():
    movie = Movie()
    try:
        if config["ChocolateSettings"]["MoviesPath"] == "Empty":
            path = str(Path.home() / "Downloads")
        else:
            path = os.path.normpath(config["ChocolateSettings"]["MoviesPath"])
    except KeyError:
        path = str(Path.home() / "Downloads")
    os.chdir(path)
    filmFileList = []
    movies = os.listdir(path)
    for movieFile in movies:
        if os.path.isfile(f"{path}/{movieFile}"):
            filmFileList.append(movieFile)

    filmFileList = filmFileList
    filmFileList.sort()

    for searchedFilm in filmFileList:
        if not isinstance(searchedFilm, str):
            continue
        if not searchedFilm.endswith("/") and searchedFilm.endswith(("mp4", "mp4v", "mov", "avi", "flv", "wmv", "asf", "mpeg", "mpg", "mkv", "ts")):
            movieTitle = searchedFilm
            originalMovieTitle = movieTitle
            size = len(movieTitle)
            movieTitle, extension = os.path.splitext(movieTitle)
            index = filmFileList.index(searchedFilm) + 1
            percentage = index * 100 / len(filmFileList)

            loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
            loadingFirstPart = f"{loadingFirstPart}➤"
            loadingSecondPart = "•" * (20 - int(percentage * 0.2))
            loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {movieTitle} | {index}/{len(filmFileList)}                                                      "
            print("\033[?25l", end="")
            print(loading, end="\r", flush=True)
            
            with app.app_context():
                exists = db.session.query(Movies).filter_by(title=movieTitle).first() is not None
                if not exists:
                    movie = Movie()
                    try:
                        search = movie.search(movieTitle)
                    except TMDbException:
                        print(TMDbException)
                        allMoviesNotSorted.append(search)
                        continue

                    if not search:
                        allMoviesNotSorted.append(originalMovieTitle)
                        continue
                    if config["ChocolateSettings"]["askwhichmovie"] == "false" or len(search)==1:
                        bestMatch = search[0]
                        for i in range(len(search)):
                            if (lev(movieTitle, search[i].title) < lev(movieTitle, bestMatch.title)
                                and bestMatch.title not in filmFileList):
                                bestMatch = search[i]
                            elif (lev(movieTitle, search[i].title) == lev(movieTitle, bestMatch.title)
                                and bestMatch.title not in filmFileList):
                                bestMatch = bestMatch
                            if (lev(movieTitle, bestMatch.title) == 0
                                and bestMatch.title not in filmFileList):
                                break
                    else:
                        print(f"I found {len(search)} movies for {movieTitle}                                       ")
                        for serieSearched in search:
                            indexOfTheSerie = search.index(serieSearched)
                            try:
                                print(f"{serieSearched.title} id:{indexOfTheSerie} date:{serieSearched.release_date}")
                            except:
                                print(f"{serieSearched.title} id:{indexOfTheSerie} date:Unknown")
                        valueSelected = int(input("Which movie is it (id):"))
                        if valueSelected < len(search):
                            bestMatch = search[valueSelected]

                    res = bestMatch
                    try:
                        name = res.title
                    except AttributeError as e:
                        name = res.original_title

                    movieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
                    banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
                    rewritedName = movieTitle.replace(" ", "_")
                    if not os.path.exists(
                        f"{currentCWD}/static/img/mediaImages/{rewritedName}_Cover.png"):
                        with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Cover.png", "wb") as f:
                            f.write(requests.get(movieCoverPath).content)

                    if not os.path.exists(
                        f"{currentCWD}/static/img/mediaImages/{rewritedName}_Banner.png"):
                        with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Banner.png", "wb") as f:
                            f.write(requests.get(banniere).content)
                    banniere = f"/static/img/mediaImages/{rewritedName}_Banner.png"
                    movieCoverPath = f"/static/img/mediaImages/{rewritedName}_Cover.png"

                    size1 = os.path.getsize(f"{currentCWD}{movieCoverPath}")
                    size2 = os.path.getsize(f"{currentCWD}{banniere}")
                    if size1 < 10240:
                        movieCoverPath = "/static/img/broken.png"
                    if size2 < 10240:
                        banniere = "/static/img/brokenBanner.png"
                    description = res.overview
                    note = res.vote_average
                    try:
                        date = res.release_date
                    except AttributeError as e:
                        date = "Unknown"
                    movieId = res.id
                    details = movie.details(movieId)

                    casts = details.casts.cast
                    theCast = []
                    for cast in casts:
                        while len(theCast) < 5:
                            characterName = cast.character
                            actorName = (
                                cast.name.replace(" ", "_")
                                .replace("/", "")
                                .replace("\"", "")
                            )
                            imagePath = f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{cast.profile_path}"
                            if not os.path.exists(
                                f"{currentCWD}/static/img/mediaImages/Actor_{actorName}.png"):
                                with open(
                                    f"{currentCWD}/static/img/mediaImages/Actor_{actorName}.png",
                                    "wb",
                                ) as f:
                                    f.write(requests.get(imagePath).content)
                            imagePath = f"/static/img/mediaImages/Actor_{actorName}.png"
                            actor = [cast.name, characterName, imagePath]
                            if actor not in theCast:
                                theCast.append(actor)
                            else:
                                break
                    try:
                        date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime(
                            "%d/%m/%Y"
                        )
                    except ValueError as e:
                        date = "Unknown"
                    except UnboundLocalError:
                        date = "Unknown"

                    genre = res.genre_ids
                    video_path = f"{path}\{originalMovieTitle}"
                    # convert seconds to hours, minutes and seconds
                    length = length_video(video_path)
                    length = str(datetime.timedelta(seconds=length))
                    length = length.split(":")

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

                    for genreId in genre:
                        if genreList[genreId] not in genresUsed:
                            genresUsed.append(genreList[genreId])
                        if genreList[genreId] not in moviesGenre:
                            moviesGenre.append(genreList[genreId])
                    # replace the id with the name of the genre
                    movieGenre = []
                    for genreId in genre:
                        movieGenre.append(genreList[genreId])

                    bandeAnnonce = details.videos.results
                    bandeAnnonceUrl = ""
                    if len(bandeAnnonce) > 0:
                        for video in bandeAnnonce:
                            bandeAnnonceType = video.type
                            bandeAnnonceHost = video.site
                            bandeAnnonceKey = video.key
                            if bandeAnnonceType == "Trailer":
                                try:
                                    bandeAnnonceUrl = (
                                        websitesTrailers[bandeAnnonceHost] + bandeAnnonceKey
                                    )
                                    break
                                except KeyError as e:
                                    bandeAnnonceUrl = "Unknown"
                                    print(e)
                    filmData = Movies(movieId, movieTitle, name, movieCoverPath, banniere, originalMovieTitle, description, note, date, json.dumps(movieGenre), str(duration), json.dumps(theCast), bandeAnnonceUrl)
                    movieDict = {"title": filmData.title, "realTitle": filmData.realTitle, "cover": filmData.cover, "banner": filmData.banner, "slug": filmData.slug, "description": filmData.description, "note": filmData.note, "date": filmData.date, "genre": filmData.genre, "duration":str(duration), "cast": filmData.cast, "bandeAnnonceUrl": filmData.bandeAnnonceUrl, "id": filmData.id}
                    db.session.add(filmData)
                    db.session.commit()
                    allMoviesDict[filmData.title] = movieDict
                else:
                    movie = db.session.query(Movies).filter_by(title=movieTitle).first()
                    movieDict = {"title": movie.title, "realTitle": movie.realTitle, "cover": movie.cover, "banner": movie.banner, "slug": movie.slug, "description": movie.description, "note": movie.note, "date": movie.date, "genre": movie.genre, "duration":str(movie.duration), "cast": movie.cast, "bandeAnnonceUrl": movie.bandeAnnonceUrl, "id": movie.id}
                    allMoviesDict[movie.title] = movieDict
        elif searchedFilm.endswith("/") == False:
            allMoviesNotSorted.append(searchedFilm)


def getSeries():
    try:
        if config["ChocolateSettings"]["SeriesPath"] == "Empty":
            allSeriesPath = str(Path.home() / "Downloads")
        else:
            allSeriesPath = os.path.normpath(config["ChocolateSettings"]["SeriesPath"])
    except KeyError as e:
        print(e)
        allSeriesPath = str(Path.home() / "Downloads")
    if allSeriesPath == ".":
        allSeriesPath = str(Path.home() / "Downloads")
    try:
        allSeries = [
            name
            for name in os.listdir(allSeriesPath)
            if os.path.isdir(os.path.join(allSeriesPath, name))
            and name.endswith((".rar", ".zip", ".part")) == False
        ]
    except OSError as e:
        print("No series found")
        print(e)
        return

    allSeasonsAppelations = ["S"]
    allEpisodesAppelations = ["E"]
    for series in allSeries:
        uglySeasonAppelations = ["Saison", "Season", series.replace(" ", ".")]
        seasons = os.listdir(f"{allSeriesPath}\\{series}")
        serieSeasons = {}
        for season in seasons:
            path = f"{allSeriesPath}/{series}"
            if (
                not (
                    season.startswith(tuple(allSeasonsAppelations))
                    and not season.endswith(
                        ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
                    )
                )
                or season.startswith(tuple(uglySeasonAppelations))
                and season.endswith((".rar", ".zip", ".part")) == False
            ):
                allSeasons = os.listdir(f"{path}")
                for allSeason in allSeasons:
                    untouchedSeries = config["ChocolateSettings"][
                        "untouchedSeries"
                    ].split(";")
                    if (
                        (
                            allSeriesPath != str(Path.home() / "Downloads")
                            or allSeriesPath != "."
                        )
                        and allSeason not in untouchedSeries
                        and (
                            allSeason.startswith(tuple(allSeasonsAppelations)) == False
                            and allSeason.endswith(
                                ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
                            )
                            == False
                        )
                        or season.startswith(tuple(uglySeasonAppelations))
                    ):
                        if os.path.isdir(f"{path}/{allSeason}") and not (allSeason.startswith(tuple(allSeasonsAppelations)) and allSeason.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))):
                            print(f"For {uglySeasonAppelations[2]} : {allSeason}")
                            reponse = ask(
                                f"I found that folder, can I rename it from {allSeason} to S{allSeasons.index(allSeason)+1}",
                                AskResult.YES,
                            )
                            if reponse:
                                try:
                                    os.rename(
                                        f"{path}/{allSeason}",
                                        f"{path}/S{allSeasons.index(allSeason)+1}",
                                    )
                                except Exception as e:
                                    print(f"Something went wrong : {e}")
                            else:
                                renameNewName = input("In what do you want rename this folder ? ex: S7, S22...")
                                if renameNewName.isnumeric():
                                    renameNewName = f"S{renameNewName}"
                                elif renameNewName.startswith("S"):
                                    renameNewName=renameNewName
                                try:
                                    os.rename(
                                        f"{path}/{allSeason}",
                                        f"{path}/{renameNewName}",
                                    )
                                except Exception as e:
                                    print(f"Something went wrong : {e}")



            episodesPath = f"{path}\{season}"
            try:
                seasonNumber = season.split(" ")[1]
            except Exception as e:
                seasonNumber = season.replace("S", "")
            if os.path.isdir(episodesPath):
                episodes = os.listdir(episodesPath)
                seasonEpisodes = {}
                oldIndex = 0
                for episode in episodes:
                    episodeName, episodeExtension = os.path.splitext(episode)
                    if os.path.isfile(f"{episodesPath}/{episode}"):
                        if episodeName.startswith(
                            tuple(allEpisodesAppelations)
                        ) and episodeName.endswith(
                            ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
                        ):
                            oldIndex = episodes.index(episode)
                        else:
                            actualName = f"{episodesPath}/{episode}"
                            oldIndex = episodes.index(episode)
                            if episode.endswith((".rar", ".zip", ".part")) == False:
                                newName = f"E{episodes.index(episode)+1}{episodeExtension}"
                                reponse = ask(
                                    f"Can i rename {actualName} to {episodesPath}/{newName}",
                                    AskResult.YES,
                                )
                                if reponse:
                                    try:
                                        os.rename(
                                            actualName,
                                            f"{episodesPath}/{newName}",
                                        )
                                        episode = f"{newName}"
                                    except Exception as e:
                                        print(f"Something went wrong : {e}")
                                else:
                                    renameNewName = input("In what do you want rename this file ? ex: E7, E22...")
                                    if renameNewName.isnumeric():
                                        renameNewName = f"E{renameNewName}"
                                    elif renameNewName.startswith("E"):
                                        renameNewName=renameNewName
                                    try:
                                        os.rename(
                                            actualName,
                                            f"{episodesPath}/{renameNewName}{episodeExtension}",
                                        )
                                        episode = f"{renameNewName}{episodeExtension}"
                                    except Exception as e:
                                        print(f"Something went wrong : {e}")



                        seasonEpisodes[oldIndex + 1] = f"{path}/{season}/{episode}"
                serieSeasons[seasonNumber] = seasonEpisodes
        serieData = {}
        serieData["seasons"] = serieSeasons
        allSeriesDictTemp[series] = serieData

    allSeries = allSeriesDictTemp
    allSeriesName = []
    for series in allSeries:
        allSeriesName.append(series)
        for season in allSeries[series]["seasons"]:
            for episode in allSeries[series]["seasons"][season]:
                actualPath = allSeries[series]["seasons"][season][episode]
                HTTPPath = actualPath.replace(allSeriesPath, "")
                HTTPPath = HTTPPath.replace("\\", "/")
    for serie in allSeriesName:
        if not isinstance(serie, str):
            print(f"{serie} is not 'isinstance'")
            continue
        index = allSeriesName.index(serie) + 1
        percentage = index * 100 / len(allSeriesName)

        loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
        loadingFirstPart = f"{loadingFirstPart}➤"
        loadingSecondPart = "•" * (20 - int(percentage * 0.2))
        loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {serie} | {index}/{len(allSeriesName)}                              "
        print("\033[?25l", end="")
        print(loading, end="\r", flush=True)
        with app.app_context():
            exists = db.session.query(Series).filter_by(originalName=serie).first() is not None
            if not exists:
                show = TV()
                serieTitle = serie
                originalSerieTitle = serieTitle

                try:
                    search = show.search(serieTitle)
                except TMDbException as e:
                    allSeriesNotSorted.append(serieTitle)
                    break

                if not search:
                    allSeriesNotSorted.append(serieTitle)
                    print(f"{originalSerieTitle} return nothing, try to rename it, the english name return more results.")
                    continue

                askForGoodSerie = config["ChocolateSettings"]["askWhichSerie"]
                if askForGoodSerie == "false" or len(search)==1:
                    bestMatch = search[0]
                    for i in range(len(search)):
                        if (
                            lev(serieTitle, search[i].name) < lev(serieTitle, bestMatch.name)
                            and bestMatch.name not in allSeriesName
                        ):
                            bestMatch = search[i]
                        elif (
                            lev(serieTitle, search[i].name) == lev(serieTitle, bestMatch.name)
                            and bestMatch.name not in allSeriesName
                        ):
                            bestMatch = bestMatch
                        if (
                            lev(serieTitle, bestMatch.name) == 0
                            and bestMatch.name not in allSeriesName
                        ):
                            break
                else:
                    print(f"I found {len(search)} series that can be the one you want")
                    for serieSearched in search:
                        indexOfTheSerie = search.index(serieSearched)
                        print(f"{serieSearched.name} id:{indexOfTheSerie}")
                    valueSelected = int(input("Which serie is it (id):"))
                    if valueSelected < len(search):
                        bestMatch = search[valueSelected]

                res = bestMatch
                name = res.name
                serieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
                banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
                rewritedName = serieTitle.replace(" ", "_")
                if not os.path.exists(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Cover.png"):
                    with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Cover.png","wb") as f:
                        f.write(requests.get(serieCoverPath).content)
                if not os.path.exists(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Banner.png"):
                    with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}_Banner.png","wb") as f:
                        f.write(requests.get(banniere).content)
                banniere = f"/static/img/mediaImages/{rewritedName}_Banner.png"
                serieCoverPath = f"/static/img/mediaImages/{rewritedName}_Cover.png"
                description = res["overview"]
                note = res.vote_average
                date = res.first_air_date
                serieId = res.id
                details = show.details(serieId)
                cast = details.credits.cast
                runTime = details.episode_run_time
                duration = ""
                for i in range(len(runTime)):
                    if i != len(runTime) - 1:
                        duration += f"{str(runTime[i])}:"
                    else:
                        duration += f"{str(runTime[i])}"
                seasonsInfo = details.seasons
                serieGenre = details.genres
                bandeAnnonce = details.videos.results
                bandeAnnonceUrl = ""
                if len(bandeAnnonce) > 0:
                    for video in bandeAnnonce:
                        bandeAnnonceType = video.type
                        bandeAnnonceHost = video.site
                        bandeAnnonceKey = video.key
                        if bandeAnnonceType == "Trailer" or len(bandeAnnonce) == 1:
                            try:
                                bandeAnnonceUrl = (websitesTrailers[bandeAnnonceHost] + bandeAnnonceKey
                                )
                                break
                            except KeyError as e:
                                bandeAnnonceUrl = "Unknown"
                                print(e)
                genreList = []
                for genre in serieGenre:
                    genreList.append(str(genre.name))
                cast = cast[:5]
                newCast = []
                for actor in cast:
                    actorName = actor.name.replace(" ", "_").replace("/", "")
                    actorImage = f"https://image.tmdb.org/t/p/original{actor.profile_path}"
                    if not os.path.exists(f"{currentCWD}/static/img/mediaImages/Actor_{actorName}.png"):
                        with open(f"{currentCWD}/static/img/mediaImages/Actor_{actorName}.png", "wb") as f:
                            f.write(requests.get(actorImage).content)
                    actorImage = f"/static/img/mediaImages/Actor_{actorName}.png"
                    actorCharacter = actor.character
                    actor.profile_path = str(actorImage)
                    thisActor = [str(actorName), str(actorCharacter), str(actorImage), str(actor.id)]
                    newCast.append(thisActor)
                newCast = json.dumps(newCast)
                genreList = json.dumps(genreList)
                serieObject = Series(id=serieId, name=name, originalName=originalSerieTitle, genre=genreList, duration=duration, description=description, cast=newCast, bandeAnnonceUrl=bandeAnnonceUrl, serieCoverPath=serieCoverPath, banniere=banniere, note=note, date=date)
                db.session.add(serieObject)
                db.session.commit
                for season in seasonsInfo:
                    releaseDate = season.air_date
                    episodesNumber = season.episode_count
                    seasonNumber = season.season_number
                    seasonId = season.id
                    seasonName = season.name
                    seasonDescription = season.overview
                    seasonCoverPath = (f"https://image.tmdb.org/t/p/original{season.poster_path}")
                    if not os.path.exists(f"{currentCWD}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png"):
                        with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png", "wb") as f:
                            f.write(requests.get(seasonCoverPath).content)
                    seasonCoverPath = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png"

                    allSeasonsUglyDict = os.listdir(f"{allSeriesPath}/{serie}")
                    try:
                        allSeasons = [int(season.replace("S", "")) for season in allSeasonsUglyDict]
                    except ValueError as e:
                        break
                    if seasonNumber in allSeasons:
                        thisSeason = Seasons(serie=serieId, release=releaseDate, episodesNumber=episodesNumber, seasonNumber=seasonNumber, seasonId=seasonId, seasonName=seasonName, seasonDescription=seasonDescription, seasonCoverPath=seasonCoverPath)
                        
                        try:
                            db.session.add(thisSeason)
                            db.session.commit()
                        except sqlalchemy.exc.PendingRollbackError as e:
                            db.session.rollback()
                            db.session.add(thisSeason)
                            db.session.commit()

                        allEpisodes = os.listdir(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        for episode in allEpisodes:
                            slug = f"/{serie}/S{seasonNumber}/{episode}"
                            episodeName = slug.split("/")[-1]
                            episodeName, extension = os.path.splitext(episodeName)

                            try:
                                episodeIndex = int(episodeName.replace("E", ""))
                            except:
                                break
                            showEpisode = Episode()
                            try:
                                episodeInfo = showEpisode.details(serieId, seasonNumber, episodeIndex)
                                coverEpisode = f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}"
                                rewritedName = originalSerieTitle.replace(" ", "_")
                                if not os.path.exists(f"{currentCWD}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png"):
                                    with open(f"{currentCWD}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png","wb") as f:
                                        f.write(requests.get(coverEpisode).content)
                                coverEpisode = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png"

                                try:
                                    episodeData = Episodes(episodeId=episodeInfo.id, episodeName=episodeName, seasonId=seasonId, episodeNumber=episodeIndex, episodeDescription=episodeInfo.overview, episodeCoverPath=coverEpisode, releaseDate=episodeInfo.air_date, slug=slug)
                                    db.session.add(episodeData)
                                    db.session.commit()
                                except:
                                    pass
                            except TMDbException as e:
                                print(f"I didn't find an the episode {episodeIndex} of the season {seasonNumber} of the serie with ID {serieId}",e)



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
    return float(seconds.stdout)



def getGpuInfo() -> str:
    if platform.system() == "Windows":
        return gpuname()
    elif platform.system() == "Darwin":
        return subprocess.check_output(
            ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"]
        ).strip()
    elif platform.system() == "Linux":
        return "impossible d'accéder au GPU"
    return ""


def gpuname() -> str:
    """Returns the model name of the first available GPU"""
    try:
        gpus = GPUtil.getGPUs()
    except:
        print("Unable to detect GPU model. Is your GPU configured? Are you running with nvidia-docker?")
        return "UNKNOWN"
    if len(gpus) == 0:
        raise ValueError("No GPUs detected in the system")
    return gpus[0].name

@app.route("/video/<video_name>.m3u8", methods=["GET"])
def create_m3u8(video_name):
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"
    duration = length_video(video_path)
    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    #EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunk/{video_name}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{video_name}.m3u8"
    )

    return response

@app.route("/videoSerie/<episodeId>.m3u8", methods=["GET"])
def create_serie_m3u8(episodeId):
    seriesPath = config.get("ChocolateSettings", "SeriesPath")
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    episodePath = episode.slug
    episodePath = episodePath.replace("/", "\\")
    episodePath = f"{seriesPath}{episodePath}"
    duration = length_video(episodePath)
    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    #EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunkSerie/{episodeId}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set("Content-Disposition", "attachment", filename=f"{episodeId}.m3u8")

    return response
@app.route("/chunkSerie/<episodeId>-<int:idx>.ts", methods=["GET"])
def get_chunk_serie(episodeId, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    seriesPath = config.get("ChocolateSettings", "SeriesPath")
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    episode = episode.__dict__
    slug = episode["slug"]
    episodePath = f"{seriesPath}\{slug}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    videoProperties = get_video_properties(episodePath)
    width = videoProperties["width"]
    height = videoProperties["height"]
    newWidth = 1080
    newHeight = round(width / height * newWidth)
    if (newHeight % 2) != 0:
        newHeight += 1
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        episodePath,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-vf",
        f"scale={newHeight}:{newWidth}",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ac",
        "2",
        "-preset",
        "ultrafast",
        "-f",
        "mpegts",
        "pipe:1",
    ]



    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{episodeId}-{idx}.ts"
    )

    return response


@app.route("/chunk/<video_name>-<int:idx>.ts", methods=["GET"])
def get_chunk(video_name, idx=0):
    global movieExtension
    seconds = (idx - 1) * CHUNK_LENGTH
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    videoProperties = get_video_properties(video_path)
    width = videoProperties["width"]
    height = videoProperties["height"]
    newWidth = 1080
    newHeight = round(width / height * newWidth)
    if (newHeight % 2) != 0:
        newHeight += 1
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        video_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-vf",
        f"scale={newHeight}:{newWidth}",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ac",
        "2",
        "-preset",
        "ultrafast",
        "-f",
        "mpegts",
        "pipe:1",
    ]



    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{video_name}-{idx}.ts"
    )

    return response


@app.route("/chunkCaption/<language>/<index>/<video_name>.vtt", methods=["GET"])
def chunkCaption(video_name, language, index):
    global movieExtension
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"
    extractCaptionsCommand = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-map",
        f"0:{index}",
        "-f",
        "webvtt",
        "pipe:1",
    ]


    extractCaptions = subprocess.run(extractCaptionsCommand, stdout=subprocess.PIPE)

    extractCaptionsResponse = make_response(extractCaptions.stdout)
    extractCaptionsResponse.headers.set("Content-Type", "text/VTT")
    extractCaptionsResponse.headers.set(
        "Content-Disposition", "attachment", filename=f"{video_name}-{index}.vtt"
    )

    return extractCaptionsResponse


@app.route("/chunkAudio/<language>/<index>/<video_name>.mp3", methods=["GET"])
def chunkAudio(video_name, language, index):
    global movieExtension
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"
    extractAudioCommand = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-map",
        f"a:{index}",
        "-f",
        "mp3",
        "pipe:1",
    ]

    extractAudio = subprocess.run(extractAudioCommand, stdout=subprocess.PIPE)

    extractAudioResponse = make_response(extractAudio.stdout)
    extractAudioResponse.headers.set("Content-Type", "audio/mpeg")
    extractAudioResponse.headers.set(
        "Content-Disposition", "attachment", filename=f"{video_name}-{index}.mp3"
    )

    return extractAudioResponse


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        accountName = request.form["name"]
        accountPassword = request.form["password"]
        try:
            f = request.files['profilePicture']
            name, extension = os.path.splitext(f.filename)
            thiscurrentCWD = currentCWD.replace('\\', '/')
            f.save(f"{thiscurrentCWD}/static/img/{accountName}{extension}")
            profilePicture = f"/static/img/{accountName}{extension}"
            if extension == "":
                profilePicture = "/static/img/defaultUserProfilePic.png"
        except:
            profilePicture = "/static/img/defaultUserProfilePic.png"
        accountTypeInput = request.form["type"]

        if accountTypeInput == "Kid":
            accountPassword = ""

        new_user = Users(name=accountName, password=accountPassword, profilePicture=profilePicture, accountType=accountTypeInput)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError as e:
            e=e
            db.session.commit()
        login_user(new_user)
        if accountTypeInput == "Admin":
            return redirect(url_for("settings"))
        else:
            return redirect(url_for("home"))
    if request.method == "GET":
        typeOfUser = current_user.accountType
        if typeOfUser == "Admin":
            global allMoviesNotSorted
            condition = len(allMoviesNotSorted) > 0
            return render_template("settings.html", notSorted=allMoviesNotSorted, conditionIfOne=condition)
        else:
            return redirect(url_for("home"))

@app.route("/login", methods=["GET", "POST"])
def login():
    allUsers = Users.query.filter().all()
    allUsersDict = []
    for user in allUsers:
        userDict = {"name": user.name, "profilePicture": user.profilePicture, "accountType": user.accountType}
        allUsersDict.append(userDict)
    
    if len(allUsersDict)==0:
        return redirect(url_for("createAccount"))
    if request.method == "POST":
        accountName = request.form["name"]
        accountPassword = request.form["password"]
        user = Users.query.filter_by(name=accountName).first()
        if user:
            if user.verify_password(accountPassword):
                login_user(user)

                return redirect(url_for("home"))
            elif user.accountType == "Kid":
                login_user(user)
                return redirect(url_for("home"))
            else:
                return "Wrong password"
        else:
            return "Wrong username"
    return render_template("login.html", allUsers=allUsersDict)

@app.route("/createAccount", methods=["POST", "GET"])
def createAccount():
    allUsers = Users.query.filter().all()
    allUsersDict = []
    for user in allUsers:
        userDict = {"name": user.name, "profilePicture": user.profilePicture}
        allUsersDict.append(userDict)
    
    if len(allUsersDict)>0:
        return redirect(url_for("home"))

    if request.method == "POST":
        accountName = request.form["name"]
        accountPassword = request.form["password"]
        try:
            f = request.files['profilePicture']
            name, extension = os.path.splitext(f.filename)
            thiscurrentCWD = currentCWD.replace('\\', '/')
            f.save(f"{thiscurrentCWD}/static/img/{accountName}{extension}")
            profilePicture = f"/static/img/{accountName}{extension}"
            if extension == "":
                profilePicture = "/static/img/defaultUserProfilePic.png"
        except:
            profilePicture = "/static/img/defaultUserProfilePic.png"

        accountTypeInput = request.form["type"]
        new_user = Users(name=accountName, password=accountPassword, profilePicture=profilePicture, accountType=accountTypeInput)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        if accountTypeInput == "Admin":
            return redirect(url_for("settings"))
        else:
            return redirect(url_for("home"))
    return render_template("createAccount.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/profil", methods=["GET", "POST"])
def profil():
    user = current_user
    currentUsername = user.name
    if request.method == "POST":
        userName = request.form["name"]
        password = request.form["password"]
        try:
            f = request.files['profilePicture']
            name, extension = os.path.splitext(f.filename)
            thiscurrentCWD = currentCWD.replace('\\', '/')
            profilePicture = f"/static/img/{userName}{extension}"
            if extension == "":
                profilePicture = "/static/img/defaultUserProfilePic.png"
        except:
            profilePicture = "/static/img/defaultUserProfilePic.png"
        userToEdit = Users.query.filter_by(name=currentUsername).first()
        if userToEdit.name != userName:
            userToEdit.name = userName
            logout_user()
            db.session.commit()
        if userToEdit.password != generate_password_hash(password) and len(password)>0:
            userToEdit.password = generate_password_hash(password)
            db.session.commit()
        if userToEdit.profilePicture != profilePicture and profilePicture != "/static/img/defaultUserProfilePic.png":
            f = request.files['profilePicture']
            f.save(f"{thiscurrentCWD}/static/img/{userName}{extension}")
            userToEdit.profilePicture = profilePicture
            db.session.commit()
    return render_template("profil.html", user=user)

@app.route("/chunkCaptionSerie/<language>/<index>/<episodeId>.vtt", methods=["GET"])
def chunkCaptionSerie(language, index, episodeId):
    seriesPath = config.get("ChocolateSettings", "SeriesPath")
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    episode = episode.__dict__
    slug = episode["slug"]
    video_path = f"{seriesPath}\{slug}"

    extractCaptionsCommand = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-map",
        f"0:{index}",
        "-f",
        "webvtt",
        "pipe:1",
    ]


    extractCaptions = subprocess.run(extractCaptionsCommand, stdout=subprocess.PIPE)

    extractCaptionsResponse = make_response(extractCaptions.stdout)
    extractCaptionsResponse.headers.set("Content-Type", "text/VTT")
    extractCaptionsResponse.headers.set(
        "Content-Disposition", "attachment", filename=f"{language}/{index}/{episodeId}.vtt"
    )

    return extractCaptionsResponse

@app.route("/saveSettings", methods=["POST"])
def saveSettings():
    MoviesPath = request.form["moviesPath"]
    SeriesPath = request.form["seriesPath"]
    language = request.form["language"]
    port = request.form["port"]
    if MoviesPath != "":
        config.set("ChocolateSettings", "moviespath", MoviesPath)
    if SeriesPath != "":
        config.set("ChocolateSettings", "seriespath", SeriesPath)
    if language != "":
        config.set("ChocolateSettings", "language", language)
    if port != "" or port != " ":
        config.set("ChocolateSettings", "port", port)
    with open(f"{currentCWD}/config.ini", "w") as conf:
        config.write(conf)
    return redirect(url_for("settings"))



@app.route("/getAllMovies", methods=["GET"])
def getAllMovies():
    global allMoviesDict, searchedFilms
    searchedFilms = list(allMoviesDict.values())
    thisSearchedFilms = searchedFilms
    return json.dumps(thisSearchedFilms, ensure_ascii=False)


@app.route("/getAllSeries", methods=["GET"])
def getAllSeries():
    global allSeriesDict
    thisAllSeriesDict = dict(sorted(allSeriesDict.items()))

    return json.dumps(thisAllSeriesDict, ensure_ascii=False, default=str, indent=4)


@app.route("/getRandomMovie")
def getRandomMovie():
    global searchedFilms
    thisSearchedFilms = searchedFilms
    randomMovie = random.choice(thisSearchedFilms)
    return json.dumps(randomMovie, ensure_ascii=False)


@app.route("/getRandomSerie")
def getRandomSeries():
    global allSeriesDict
    
    newSerie=""
    try:
        randomSerie = random.choice(list(allSeriesDict.keys()))
    except IndexError:
        randomSerie = random.choice(list(allSeriesDict.keys()))
    newSerie = allSeriesDict[randomSerie]
    del newSerie["_sa_instance_state"]
    return json.dumps(newSerie, ensure_ascii=False, default=str)


def getSimilarMovies(movieId):
    global allMoviesDict, searchedFilms
    similarMoviesPossessed = []
    movie = Movie()
    similarMovies = movie.recommendations(movieId)
    for movieInfo in similarMovies:
        movieName = movieInfo.title
        for movie in searchedFilms:
            if movieName == movie:
                similarMoviesPossessed.append(movie)
                break
    return similarMoviesPossessed


def getSimilarSeries(seriesId) -> list:
    global allSeriesDict
    similarSeriesPossessed = []
    show = TV()
    similarSeries = show.recommendations(seriesId)
    for serieInfo in similarSeries:
        serieName = serieInfo.name
        for serie in allSeriesDict:
            try:
                if serieName == allSeriesDict[serie]["name"]:
                    similarSeriesPossessed.append(allSeriesDict[serie])
                    break
            except KeyError as e:
                print(e)
                pass
    return similarSeriesPossessed


@app.route("/getMovieData/<title>", methods=["GET", "POST"])
def getMovieData(title):
    global allMoviesDict
    if title in allMoviesDict.keys():
        data = allMoviesDict[title]
        MovieId = data["id"]
        data["similarMovies"] = getSimilarMovies(MovieId)
        return json.dumps(data, ensure_ascii=False)
    else:
        return "Not Found"


@app.route("/getSerieData/<title>", methods=["GET", "POST"])
def getSeriesData(title):
    global allSeriesDict
    title = title.replace("%20", " ")
    if title in allSeriesDict:
        data = allSeriesDict[title]
        data["seasons"] = getSerieSeasons(data["id"])
        try:
            del data["_sa_instance_state"]
        except:
            pass
        data = dict(data)
        return json.dumps(data, ensure_ascii=False)
    else:
        return "Not Found"

def getSerieSeasons(id):
    seasons = Seasons.query.filter_by(serie=id).all()
    seasonsDict = {}
    for season in seasons:
        seasonsDict[season.seasonNumber] = dict(season.__dict__)
        del seasonsDict[season.seasonNumber]["_sa_instance_state"]
    return seasonsDict

@app.route("/getFirstSixMovies")
def getFirstEightMovies():
    global searchedFilms
    thisSearchedFilms = searchedFilms[:6]
    return json.dumps(thisSearchedFilms, ensure_ascii=False)


@app.route("/getFirstSixSeries")
def getFirstEightSeries():
    global allSeriesDict
    allSeriesDict6 = {k: allSeriesDict[k] for k in list(allSeriesDict.keys())[:6]}
    return json.dumps(list(allSeriesDict6.items()), ensure_ascii=False, default=str)


@app.route("/")
@app.route("/index")
@app.route("/home")
@login_required
def home():
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    filmIsntEmpty = moviesPath != "Empty"
    return render_template("index.html", moviesExist=filmIsntEmpty)


@app.route("/movies")
def films():
    global allMoviesDict, searchedFilms
    searchedFilms = list(allMoviesDict.values())
    searchedFilmsUp0 = len(searchedFilms) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getFirstSixMovies"

    return render_template("homeFilms.html", conditionIfOne=searchedFilmsUp0, errorMessage=errorMessage, routeToUse=routeToUse)


@app.route("/series")
def series():
    global allSeriesDict
    searchedSeriesUp0 = len(allSeriesDict) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getFirstSixSeries"

    return render_template("homeSeries.html", conditionIfOne=searchedSeriesUp0, errorMessage=errorMessage, routeToUse=routeToUse)


@app.route("/season/<theId>")
def season(theId):
    #do the request to get the season
    with app.app_context():
        season = Seasons.query.filter_by(seasonId=theId).first()
        season = season.__dict__
        serie = Series.query.filter_by(id=int(season["serie"])).first()
        serie = serie.__dict__
        serie = serie["name"]
        name = f"{serie} | {season['seasonName']}"
        del season["_sa_instance_state"]
        return render_template("season.html", serie=season, title=name)


@app.route("/getSeasonData/<seasonId>/", methods=["GET", "POST"])
def getSeasonData(seasonId):
    global allSeriesDict
    season = Seasons.query.filter_by(seasonId=seasonId).first()
    episodes = Episodes.query.filter_by(seasonId=seasonId).all()
    episodesDict = {}
    for episode in episodes:
        episodesDict[episode.episodeNumber] = dict(episode.__dict__)
        del episodesDict[episode.episodeNumber]["_sa_instance_state"]
    season = season.__dict__
    del season["_sa_instance_state"]
    season["episodes"] = episodesDict
    return json.dumps(season, ensure_ascii=False, default=str)

@app.route("/getEpisodeData/<serieName>/<seasonId>/<episodeId>/", methods=["GET", "POST"])
def getEpisodeData(serieName, seasonId, episodeId):
    global allSeriesDict
    seasonId = seasonId.replace("S", "")
    episodeId = episodeId
    if serieName in allSeriesDict.keys():
        data = allSeriesDict[serieName]
        season = data["seasons"][seasonId]
        episode = season["episodes"][str(episodeId)]
        return json.dumps(episode, ensure_ascii=False, default=str)
    else:
        response = {"response": "Not Found"}
        return json.dumps(response, ensure_ascii=False, default=str)


@app.route("/movieLibrary")
def library():
    global allMoviesDict
    searchedFilms = list(allMoviesDict.values())
    searchedFilmsUp0 = len(searchedFilms) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getAllMovies"
    return render_template("allFilms.html",
        conditionIfOne=searchedFilmsUp0,
        errorMessage=errorMessage,
        routeToUse=routeToUse,
    )


@app.route("/serieLibrary")
def seriesLibrary():
    global allSeriesDict
    searchedSeriesUp0 = len(allSeriesDict.keys()) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getAllSeries"
    return render_template("allSeries.html",conditionIfOne=searchedSeriesUp0, errorMessage=errorMessage, routeToUse=routeToUse)


@app.route("/searchInMovies/<search>")
def searchInAllMovies(search):
    global searchedFilms
    bestMatchs = {}
    movies = []
    points = {}
    #I have one or multiple arguments in a list, I want for each arguments, search in 5 columns of my Movies table, and order by most points
    args = search.split("%20")
    for arg in args:
        movies = Movies.query.filter((Movies.title.like(f"%{arg}%"), Movies.realTitle.like(f"%{arg}%"), Movies.description.like(f"%{arg}%"), Movies.slug.like(f"%{arg}%"), Movies.cast.like(f"%{arg}%"))).all()
        for movie in movies:
            if movie.title in points:
                points[movie.title] += 1
            else:
                points[movie.title] = 1

    for k in points:
        min = points[k]
        for l in points:
            if points[l] < min:
                min = points[l]
        points[k] = min

    points2 = points.copy()
    finalMovieList = []
    for k in sorted(points, key=points.get, reverse=True):
        finalMovieList.append(k)
        del points2[k]
        if len(points2) == 0:
            break

    return json.dumps(finalMovieList, ensure_ascii=False)


@app.route("/searchInSeries/<search>")
def searchInAllSeries(search):
    global allSeriesDict
    bestMatchs = {}
    series = []
    points = {}
    for serie in allSeriesDict:
        search = search.replace("%20", " ")
        distance = fuzz.ratio(search, serie["title"])
        points[serie["title"]] = distance

    bestMatchs = sorted(points.items(), key=lambda x: x[1], reverse=True)
    for serie in bestMatchs:
        thisSerie = serie[0]
        for series in allSeriesDict:
            if series["title"] == thisSerie:
                series.append(series)
                break

    return json.dumps(series, ensure_ascii=False)


@app.route("/search/movies/<search>")
def searchMovie(search):
    searchedFilmsUp0 = False
    errorMessage = "Verify your search terms"
    routeToUse = f"/searchInMovies/{search}"
    return render_template("allFilms.html",
        conditionIfOne=searchedFilmsUp0,
        errorMessage=errorMessage,
        routeToUse=routeToUse,
    )


@app.route("/search/series/<search>")
def searchSerie(search):
    searchedFilmsUp0 = False
    errorMessage = "Verify your search terms"
    routeToUse = f"/searchInSeries/{search}"
    return render_template("allSeries.html",
        conditionIfOne=searchedFilmsUp0,
        errorMessage=errorMessage,
        routeToUse=routeToUse,
    )


@app.route("/movie/<slug>")
def movie(slug):
    global movieExtension, searchedFilms
    if not slug.endswith("ttf"):
        rewriteSlug, movieExtension = os.path.splitext(slug)
        link = f"/video/{rewriteSlug}.m3u8".replace(" ", "%20")
        allCaptions = generateCaptionMovie(slug)
        title = rewriteSlug
        return render_template(
        "film.html", slug=slug, movieUrl=link, allCaptions=allCaptions, title=title
        )

@app.route("/serie/<episodeId>")
def serie(episodeId):
    global allSeriesDict
    if episodeId.endswith("ttf"):
        pass
    else:
        thisEpisode = Episodes.query.filter_by(episodeId=episodeId).first().__dict__
        del thisEpisode["_sa_instance_state"]
        seasonId = thisEpisode["seasonId"]
        slug = thisEpisode["slug"]
        episodeName = thisEpisode["episodeName"]
        slugUrl = slug.split("/")[-1]
        link = f"/videoSerie/{episodeId}.m3u8".replace(" ", "%20")
        allCaptions = generateCaptionSerie(episodeId)
        episodeId = int(episodeId)
        season = Seasons.query.filter_by(seasonId=seasonId).first()
        lenOfThisSeason = season.episodesNumber
        buttonNext = episodeId-1 < int(lenOfThisSeason)
        buttonPrevious = episodeId-1 > 0
        thisEpisodeName = thisEpisode["episodeName"].replace("E", "")
        nextEpisodeId = Episodes.query.filter_by(episodeName=f"E{str(int(thisEpisodeName)+1)}").filter_by(seasonId=seasonId).first()
        previousEpisodeId = Episodes.query.filter_by(episodeName=f"E{str(int(thisEpisodeName)-1)}").filter_by(seasonId=seasonId).first()
        buttonPreviousHREF = f"/serie/{nextEpisodeId}"
        buttonNextHREF = f"/serie/{previousEpisodeId}"
        return render_template("serie.html", slug=slug, movieUrl=link, allCaptions=allCaptions, title=episodeName, buttonNext=buttonNext, buttonPrevious=buttonPrevious, buttonNextHREF=buttonNextHREF, buttonPreviousHREF=buttonPreviousHREF)
    return "Error"

def generateCaptionSerie(episodeId):
    seriesPath = config.get("ChocolateSettings", "SeriesPath")
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    episode = episode.__dict__
    slug = episode["slug"]
    slug = f"{seriesPath}\{slug}"
    captionCommand = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index:stream_tags=language",
        "-of",
        "csv=p=0",
        slug,
    ]
    captionPipe = subprocess.Popen(captionCommand, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
    captionResponse = captionPipe.stdout.read().decode("utf-8")
    captionResponse = captionResponse.split("\n")

    allCaptions = []
    languages = {
        "eng": "English",
        "fre": "Français",
        "spa": "Español",
        "por": "Português",
        "ita": "Italiano",
        "ger": "Deutsch",
        "rus": "Русский",
        "pol": "Polski",
        "por": "Português",
        "chi": "中文",
        "srp": "Srpski",
    }

    captionResponse.pop()

    for line in captionResponse:
        line = line.rstrip()
        language = line.split(",")[1]
        index = line.split(",")[0]
        allCaptions.append(
            {
                "index": index,
                "languageCode": language,
                "language": languages[language],
                "url": f"/chunkCaptionSerie/{language}/{index}/{episodeId}.vtt",
            }
        )
    return allCaptions



def generateCaptionMovie(slug):
    captionCommand = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index:stream_tags=language",
        "-of",
        "csv=p=0",
        slug,
    ]
    captionPipe = subprocess.Popen(captionCommand, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
    rewriteSlug, movieExtension = os.path.splitext(slug)
    captionResponse = captionPipe.stdout.read().decode("utf-8")
    captionResponse = captionResponse.split("\n")

    allCaptions = []
    languages = {
        "eng": "English",
        "fre": "Français",
        "spa": "Español",
        "por": "Português",
        "ita": "Italiano",
        "ger": "Deutsch",
        "rus": "Русский",
        "pol": "Polski",
        "por": "Português",
        "chi": "中文",
        "srp": "Srpski",
    }

    captionResponse.pop()
    for line in captionResponse:
        line = line.rstrip()
        try:
            language = line.split(",")[1]
            index = line.split(",")[0]
            allCaptions.append(
                {
                    "index": index,
                    "languageCode": language,
                    "language": languages[language],
                    "url": f"/chunkCaption/{language}/{index}/{rewriteSlug}.vtt",
                }
            )
        except:
            break

    return allCaptions


@app.route("/generateAudio/<slug>")
def generateAudio(slug):
    audioCommand = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=index:stream_tags=language",
        "-of",
        "csv=p=0",
        slug,
    ]
    audioPipe = subprocess.Popen(audioCommand, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
    rewriteSlug, movieExtension = os.path.splitext(slug)
    audioResponse = audioPipe.stdout.read().decode("utf-8")
    audioResponse = audioResponse.split("\n")
    audioResponse.pop()
    allAudio = []
    languages = {
        "eng": "English",
        "fre": "Français",
        "spa": "Español",
        "por": "Português",
        "ita": "Italiano",
        "ger": "Deutsch",
        "rus": "Русский",
        "pol": "Polski",
        "por": "Português",
        "chi": "中文",
        "srp": "Srpski",
    }
    for line in audioResponse:
        line = line.rstrip()
        language = line.split(",")[1]
        index = line.split(",")[0]
        allAudio.append(
            {
                "index": index,
                "languageCode": language,
                "language": languages[language],
                "url": f"/chunkAudio/{language}/{index}/{rewriteSlug}.mp3",
            }
        )

    return allAudio


@app.route("/actor/<actorName>")
def actor(actorName):
    routeToUse = f"/getActorData/{actorName}"
    return render_template("actor.html", routeToUse=routeToUse)


@app.route("/getActorData/<actorName>", methods=["GET", "POST"])
def getActorData(actorName):
    global searchedFilms, searchedFilms
    movies = []
    person = Person()
    actorDatas = person.search(actorName)
    for movie in searchedFilms:
        actors = movie["cast"]
        for actor in actors:
            if actor[0] == actorName:
                for movieData in searchedFilms:
                    if movie["title"] == movieData["title"]:
                        movies.append(movie)
                        break
    actorId = actorDatas[0].id
    p = person.details(actorId)
    name = p["name"]
    birthday = p["birthday"]
    birthplace = p["place_of_birth"]
    actorDescription = p["biography"]
    rewritedName = name.replace(" ", "_")
    actorData = {
        "actorName": name,
        "actorImage": f"/static/img/mediaImages/Actor_{rewritedName}.png",
        "actorDescription": actorDescription,
        "actorBirthday": birthday,
        "actorBirthplace": birthplace,
        "actorMovies": movies,
    }
    return json.dumps(actorData, default=lambda o: o.__dict__, ensure_ascii=False)


@app.route("/sendDiscordPresence/<name>/<actualDuration>/<totalDuration>")
def sendDiscordPresence(name, actualDuration, totalDuration):
    global rpc_obj, activity
    actualDuration = actualDuration
    totalDuration = totalDuration
    newActivity = {
        "state": "Chocolate",  # anything you like
        "details": f"Watching {name} | {actualDuration}/{totalDuration}",  # anything you like
        "assets": {
            "small_text": "Chocolate",  # anything you like
            "small_image": "None",  # must match the image key
            "large_text": "Chocolate",  # anything you like
            "large_image": "largeimage",  # must match the image key
        },
    }
    try:
        rpc_obj.set_activity(newActivity)
    except:
        client_id = "771837466020937728"
        rpc_obj = rpc.DiscordIpcClient.for_platform(client_id)
        activity = {
            "state": "Chocolate",  # anything you like
            "details": "The all-in-one MediaManager",  # anything you like
            "timestamps": {"start": start_time},
            "assets": {
                "small_text": "Chocolate",  # anything you like
                "small_image": "None",  # must match the image key
                "large_text": "Chocolate",  # anything you like
                "large_image": "largeimage",  # must match the image key
            },
        }
        rpc_obj.set_activity(activity)
    return json.dumps(
        f"You sent richPresence Data with this informations : name:{name}, actualDuration:{actualDuration}, totalDuration:{totalDuration}"
    )

def sort_dict_by_key(unsorted_dict):

    sorted_keys = sorted(unsorted_dict.keys(), key=lambda x:x.lower())

    sorted_dict= {}
    for key in sorted_keys:
        sorted_dict.update({key: unsorted_dict[key]})

    return sorted_dict
        

if __name__ == "__main__":
    activity = {
        "state": "Loading Chocolate...",  # anything you like
        "details": "The all-in-one MediaManager",  # anything you like
        "timestamps": {"start": start_time},
        "assets": {
            "small_text": "Chocolate",  # anything you like
            "small_image": "None",  # must match the image key
            "large_text": "Chocolate",  # anything you like
            "large_image": "loader",  # must match the image key
        },
    }
    try:
        rpc_obj.set_activity(activity)
    except:
        pass
    getSeries()
    getMovies()
    print()
    print("\033[?25h", end="")
    activity = {
        "state": "Chocolate",  # anything you like
        "details": "The all-in-one MediaManager",  # anything you like
        "timestamps": {"start": start_time},
        "assets": {
            "small_text": "Chocolate",  # anything you like
            "small_image": "None",  # must match the image key
            "large_text": "Chocolate",  # anything you like
            "large_image": "largeimage",  # must match the image key
        },
    }
    try:
        rpc_obj.set_activity(activity)
    except:
        pass

    with app.app_context():
        allSeriesDict = {}
        for u in db.session.query(Series).all():
            allSeriesDict[u.name] = u.__dict__

    app.run(host="0.0.0.0", port=serverPort, use_reloader=False, debug=True)